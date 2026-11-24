from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.delivery import (
    DEFAULT_DELIVERY_FEE_UGX,
    Delivery,
    DeliveryStatus,
)
from app.schemas.order import (
    FarmerOrderItemRead,
    FarmerOrderRead,
    OrderCreate,
    OrderPaymentUpdate,
    OrderRead,
    OrderUpdate,
)
from app.schemas.wallet import FeeBreakdown, OrderQuoteRequest
from app.models.wallet import WalletTransaction
from app.services.notification_dispatcher import dispatch_user_notification
from app.services.payment_fees import order_fee_quote
from app.services.wallet import settle_order_if_ready, wallet_balance_ugx

router = APIRouter(prefix="/orders", tags=["Orders"])


def _priced_items(db: Session, items):
    total = 0.0
    order_items = []
    seller_subtotals: dict[int, Decimal] = {}
    requested_quantities: dict[int, float] = {}
    for item in items:
        requested_quantities[item.product_id] = (
            requested_quantities.get(item.product_id, 0) + item.quantity
        )

    for product_id in sorted(requested_quantities):
        quantity = requested_quantities[product_id]
        product = (
            db.query(Product)
            .filter(Product.id == product_id)
            .with_for_update()
            .first()
        )
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        if product.status != "available":
            raise HTTPException(status_code=400, detail=f"Product {product.name} is not available")
        if product.quantity < quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient quantity for {product.name}. Available: {product.quantity}",
            )

        subtotal = quantity * product.price_per_unit
        total += subtotal
        seller_subtotals[product.farmer_id] = (
            seller_subtotals.get(product.farmer_id, Decimal("0"))
            + Decimal(str(quantity)) * Decimal(str(product.price_per_unit))
        )
        order_items.append(
            {
                "product": product,
                "quantity": quantity,
                "unit_price": product.price_per_unit,
                "subtotal": subtotal,
            }
        )
    return total, order_items, seller_subtotals


@router.post("/quote", response_model=FeeBreakdown)
def quote_order_payment(
    quote_in: OrderQuoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("buyer")),
):
    if not quote_in.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")
    _, _, seller_subtotals = _priced_items(db, quote_in.items)
    return order_fee_quote(seller_subtotals)


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("buyer")),
):
    if not order_in.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    total, order_items, seller_subtotals = _priced_items(db, order_in.items)
    fee_quote = order_fee_quote(seller_subtotals)
    if order_in.payment_method == "wallet":
        db.query(User.id).filter(User.id == current_user.id).with_for_update().first()
        available_balance = wallet_balance_ugx(db, current_user.id)
        if available_balance < fee_quote["total_payable_ugx"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Insufficient Harvesta Wallet balance. "
                    f"Available: UGX {available_balance:,.0f}; "
                    f"required: UGX {fee_quote['total_payable_ugx']:,.0f}."
                ),
            )

    # Create order
    order = Order(
        buyer_id=current_user.id,
        total_amount=total,
        delivery_address=order_in.delivery_address,
        notes=order_in.notes,
        status=OrderStatus.PENDING.value,
        payment_method=order_in.payment_method,
        payment_status=(
            PaymentStatus.PAID.value
            if order_in.payment_method == "wallet"
            else PaymentStatus.PENDING.value
        ),
        payment_reference=order_in.payment_reference,
    )
    db.add(order)
    db.flush()  # get order.id
    db.add(
        Delivery(
            order_id=order.id,
            status=DeliveryStatus.OPEN.value,
            estimated_fee_ugx=DEFAULT_DELIVERY_FEE_UGX,
        )
    )
    if order_in.payment_method == "wallet":
        db.add(
            WalletTransaction(
                user_id=current_user.id,
                order_id=order.id,
                transaction_type="order_deduction",
                amount_ugx=fee_quote["total_payable_ugx"],
                balance_delta_ugx=-fee_quote["total_payable_ugx"],
                status="completed",
                payment_method="wallet",
                reference=f"order-{order.id}",
                description=f"Wallet payment for order #{order.id}, including delivery",
            )
        )

    for item_data in order_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data["product"].id,
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            subtotal=item_data["subtotal"],
        )
        db.add(order_item)
        # Reduce stock
        item_data["product"].quantity -= item_data["quantity"]
        if item_data["product"].quantity <= 0:
            item_data["product"].status = "sold_out"

    db.commit()
    db.refresh(order)
    dispatch_user_notification(
        db,
        current_user,
        "order_created",
        "Harvesta order received",
        (
            f"Order #{order.id} was placed. Payment status: "
            f"{order.payment_status}. Delivery fee estimate: "
            f"UGX {DEFAULT_DELIVERY_FEE_UGX:,}."
        ),
    )
    for farmer in (
        db.query(User)
        .filter(User.id.in_(set(seller_subtotals)))
        .all()
    ):
        dispatch_user_notification(
            db,
            farmer,
            "incoming_order",
            "New Harvesta produce order",
            f"Order #{order.id} includes your produce. Check Harvesta for details.",
        )
    return order


@router.get("/incoming", response_model=List[FarmerOrderRead])
def incoming_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("farmer", "admin")),
):
    rows = (
        db.query(Order, OrderItem, Product)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(Product.farmer_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    orders_by_id = {}
    for order, item, product in rows:
        if order.id not in orders_by_id:
            orders_by_id[order.id] = {
                "id": order.id,
                "buyer_id": order.buyer_id,
                "status": order.status,
                "total_amount": 0,
                "delivery_address": order.delivery_address,
                "notes": order.notes,
                "created_at": order.created_at,
                "payment_method": order.payment_method,
                "payment_status": order.payment_status,
                "payment_reference": order.payment_reference,
                "delivery": order.delivery,
                "items": [],
            }
        orders_by_id[order.id]["total_amount"] += item.subtotal
        orders_by_id[order.id]["items"].append(
            FarmerOrderItemRead(
                product_id=product.id,
                product_name=product.name,
                quantity=item.quantity,
                unit=product.unit,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
            )
        )

    return [FarmerOrderRead(**order) for order in orders_by_id.values()]


@router.get("/", response_model=List[OrderRead])
def list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role in ("admin", "shop_manager"):
        return db.query(Order).order_by(Order.created_at.desc()).all()
    if current_user.role == "farmer":
        return (
            db.query(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(Product.farmer_id == current_user.id)
            .distinct()
            .order_by(Order.created_at.desc())
            .all()
        )
    return (
        db.query(Order)
        .filter(Order.buyer_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )


@router.patch("/{order_id}/payment", response_model=OrderRead)
def confirm_order_payment(
    order_id: int,
    payment_in: OrderPaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "shop_manager")),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.payment_status == PaymentStatus.PAID.value:
        raise HTTPException(status_code=409, detail="Order payment is already marked paid")

    if payment_in.payment_reference is not None:
        order.payment_reference = payment_in.payment_reference.strip() or None
    order.payment_status = PaymentStatus.PAID.value
    settle_order_if_ready(db, order)
    db.commit()
    db.refresh(order)
    recipients = {}
    buyer = db.query(User).filter(User.id == order.buyer_id).first()
    if buyer:
        recipients[buyer.id] = buyer
    for product in (
        db.query(Product)
        .join(OrderItem, OrderItem.product_id == Product.id)
        .filter(OrderItem.order_id == order.id)
        .all()
    ):
        farmer = db.query(User).filter(User.id == product.farmer_id).first()
        if farmer:
            recipients[farmer.id] = farmer
    if order.delivery:
        driver = order.delivery.driver or (
            order.delivery.van.driver if order.delivery.van else None
        )
        if driver:
            recipients[driver.id] = driver

    for recipient in recipients.values():
        dispatch_user_notification(
            db,
            recipient,
            "order_payment_confirmed",
            "Harvesta payment confirmed",
            f"Payment for order #{order.id} has been verified.",
        )
    return order


@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.buyer_id != current_user.id and current_user.role not in ("admin", "driver", "shop_manager"):
        raise HTTPException(status_code=403, detail="Not authorized")
    return order


@router.patch("/{order_id}", response_model=OrderRead)
def update_order(
    order_id: int,
    order_in: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "driver", "shop_manager")),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    update_data = order_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    db.commit()
    db.refresh(order)
    return order
