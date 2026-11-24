from collections import defaultdict
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.delivery import Delivery
from app.models.order import Order, OrderItem, PaymentStatus
from app.models.product import Product
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.services.payment_fees import (
    SERVICE_FEE_RATE,
    VAT_ON_SERVICE_FEE_RATE,
    percentage_ugx,
    round_ugx,
)


def wallet_balance_ugx(db: Session, user_id: int) -> int:
    completed_balance = (
        db.query(func.coalesce(func.sum(WalletTransaction.balance_delta_ugx), 0))
        .filter(
            WalletTransaction.user_id == user_id,
            WalletTransaction.status == "completed",
        )
        .scalar()
    )
    pending_withdrawals = (
        db.query(func.coalesce(func.sum(WalletTransaction.balance_delta_ugx), 0))
        .filter(
            WalletTransaction.user_id == user_id,
            WalletTransaction.status == "pending",
            WalletTransaction.transaction_type == "withdrawal",
        )
        .scalar()
    )
    return int(completed_balance + pending_withdrawals)


def settle_order_if_ready(db: Session, order: Order) -> None:
    if (
        order.status != "delivered"
        or order.payment_status != PaymentStatus.PAID.value
    ):
        return

    delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
    if not delivery:
        return

    subtotals: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    for item in (
        db.query(OrderItem, Product)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(OrderItem.order_id == order.id)
        .all()
    ):
        order_item, product = item
        subtotals[product.farmer_id] += Decimal(str(order_item.subtotal))

    for farmer_id, subtotal in subtotals.items():
        exists = (
            db.query(WalletTransaction.id)
            .filter(
                WalletTransaction.user_id == farmer_id,
                WalletTransaction.order_id == order.id,
                WalletTransaction.transaction_type == "sale_earning",
            )
            .first()
        )
        if exists:
            continue
        gross = round_ugx(subtotal)
        service_fee = percentage_ugx(subtotal, SERVICE_FEE_RATE)
        vat = percentage_ugx(service_fee, VAT_ON_SERVICE_FEE_RATE)
        db.add(
            WalletTransaction(
                user_id=farmer_id,
                order_id=order.id,
                transaction_type="sale_earning",
                amount_ugx=gross,
                balance_delta_ugx=gross,
                status="completed",
                payment_method=order.payment_method,
                reference=f"order-{order.id}",
                description=f"Produce sale proceeds from completed order #{order.id}",
            )
        )
        if service_fee:
            db.add(
                WalletTransaction(
                    user_id=farmer_id,
                    order_id=order.id,
                    transaction_type="service_fee",
                    amount_ugx=service_fee,
                    service_fee_ugx=service_fee,
                    balance_delta_ugx=-service_fee,
                    status="completed",
                    payment_method=order.payment_method,
                    reference=f"order-{order.id}",
                    description=f"Harvesta service fee for order #{order.id}",
                )
            )
        if vat:
            db.add(
                WalletTransaction(
                    user_id=farmer_id,
                    order_id=order.id,
                    transaction_type="tax_charge",
                    amount_ugx=vat,
                    tax_amount_ugx=vat,
                    balance_delta_ugx=-vat,
                    status="completed",
                    payment_method=order.payment_method,
                    reference=f"order-{order.id}",
                    description=f"Estimated VAT on service fee for order #{order.id}",
                )
            )

    driver = delivery.driver or (delivery.van.driver if delivery.van else None)
    if driver:
        driver_earning_exists = (
            db.query(WalletTransaction.id)
            .filter(
                WalletTransaction.user_id == driver.id,
                WalletTransaction.order_id == order.id,
                WalletTransaction.transaction_type == "driver_earning",
            )
            .first()
        )
        if not driver_earning_exists:
            fee = delivery.estimated_fee_ugx
            db.add(
                WalletTransaction(
                    user_id=driver.id,
                    order_id=order.id,
                    transaction_type="driver_earning",
                    amount_ugx=fee,
                    balance_delta_ugx=fee,
                    status="completed",
                    payment_method=order.payment_method,
                    reference=f"order-{order.id}",
                    description=f"Delivery fee for completed order #{order.id}",
                )
            )

    db.flush()
