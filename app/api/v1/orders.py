from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import (
    FarmerOrderItemRead,
    FarmerOrderRead,
    OrderCreate,
    OrderRead,
    OrderUpdate,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("buyer")),
):
    if not order_in.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    total = 0.0
    order_items = []

    for item in order_in.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product.status != "available":
            raise HTTPException(status_code=400, detail=f"Product {product.name} is not available")
        if product.quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient quantity for {product.name}. Available: {product.quantity}",
            )

        subtotal = item.quantity * product.price_per_unit
        total += subtotal
        order_items.append(
            {
                "product": product,
                "quantity": item.quantity,
                "unit_price": product.price_per_unit,
                "subtotal": subtotal,
            }
        )

    # Create order
    order = Order(
        buyer_id=current_user.id,
        total_amount=total,
        delivery_address=order_in.delivery_address,
        notes=order_in.notes,
        status=OrderStatus.PENDING.value,
    )
    db.add(order)
    db.flush()  # get order.id

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
    if current_user.role == "admin":
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
