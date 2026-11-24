from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.models.delivery import (
    Delivery,
    DeliveryStatus,
    DeliveryVan,
)
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.order import OrderItem
from app.schemas.delivery import (
    DeliveryVanCreate,
    DeliveryVanRead,
    DeliveryCreate,
    DeliveryRead,
    DeliveryUpdate,
)
from app.services.notification_dispatcher import dispatch_user_notification
from app.services.wallet import settle_order_if_ready

router = APIRouter(prefix="/deliveries", tags=["Deliveries & Vans"])

_DRIVER_STATUS_TRANSITIONS = {
    DeliveryStatus.ACCEPTED.value: DeliveryStatus.PICKED_UP.value,
    DeliveryStatus.PICKED_UP.value: DeliveryStatus.IN_TRANSIT.value,
    DeliveryStatus.IN_TRANSIT.value: DeliveryStatus.DELIVERED.value,
}


def _delivery_payload(delivery: Delivery) -> dict:
    order = delivery.order
    driver = delivery.driver or (delivery.van.driver if delivery.van else None)
    item_rows = []
    pickup_districts = set()
    for order_item in order.items:
        product = order_item.product
        if not product:
            continue
        farmer = product.farmer
        pickup_district = (
            (farmer.district or farmer.location_name) if farmer else None
        ) or "District unavailable"
        pickup_districts.add(pickup_district)
        item_rows.append(
            {
                "product_name": product.name,
                "quantity": order_item.quantity,
                "unit": product.unit,
                "pickup_district": pickup_district,
            }
        )

    buyer = order.buyer
    address_parts = [
        part.strip()
        for part in order.delivery_address.split(",")
        if part.strip()
    ]
    address_district = next(
        (
            part
            for part in reversed(address_parts)
            if part.casefold() not in {"uganda", "east africa"}
        ),
        "District unavailable",
    )
    return {
        "id": delivery.id,
        "order_id": delivery.order_id,
        "van_id": delivery.van_id,
        "driver_id": driver.id if driver else None,
        "driver_name": driver.full_name if driver else None,
        "driver_phone": driver.phone if driver else None,
        "status": delivery.status,
        "estimated_fee_ugx": delivery.estimated_fee_ugx,
        "pickup_district": ", ".join(sorted(pickup_districts))
        if pickup_districts
        else "District unavailable",
        "delivery_district": (buyer.district if buyer else None)
        or address_district,
        "items": item_rows,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "payment_reference": order.payment_reference,
        "notes": delivery.notes,
        "pickup_time": delivery.pickup_time,
        "estimated_delivery": delivery.estimated_delivery,
        "actual_delivery": delivery.actual_delivery,
        "created_at": delivery.created_at,
    }


def _delivery_response(delivery: Delivery) -> DeliveryRead:
    return DeliveryRead.model_validate(_delivery_payload(delivery))


def _assigned_driver_id(delivery: Delivery) -> int | None:
    if delivery.driver_id:
        return delivery.driver_id
    if delivery.van:
        return delivery.van.driver_id
    return None


def _notify_delivery_participants(db: Session, delivery: Delivery) -> None:
    recipients = {delivery.order.buyer.id: delivery.order.buyer}
    for order_item in delivery.order.items:
        farmer = order_item.product.farmer if order_item.product else None
        if farmer:
            recipients[farmer.id] = farmer
    driver = delivery.driver or (delivery.van.driver if delivery.van else None)
    if driver:
        recipients[driver.id] = driver

    for user in recipients.values():
        dispatch_user_notification(
            db,
            user,
            "delivery_status",
            "Harvesta delivery update",
            (
                f"Order #{delivery.order_id} delivery status is now "
                f"{delivery.status.replace('_', ' ').title()}."
            ),
        )


# --- Vans ---
@router.post("/vans", response_model=DeliveryVanRead, status_code=status.HTTP_201_CREATED)
def create_van(
    van_in: DeliveryVanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    existing = db.query(DeliveryVan).filter(DeliveryVan.plate_number == van_in.plate_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Plate number already registered")
    van = DeliveryVan(**van_in.model_dump())
    db.add(van)
    db.commit()
    db.refresh(van)
    return van


@router.get("/vans", response_model=List[DeliveryVanRead])
def list_vans(db: Session = Depends(get_db)):
    return db.query(DeliveryVan).all()


# --- Deliveries ---
@router.post("/", response_model=DeliveryRead, status_code=status.HTTP_201_CREATED)
def create_delivery(
    delivery_in: DeliveryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "shop_manager")),
):
    order = db.query(Order).filter(Order.id == delivery_in.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    existing = db.query(Delivery).filter(Delivery.order_id == delivery_in.order_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Delivery already exists for this order")

    delivery = Delivery(**delivery_in.model_dump())
    db.add(delivery)
    order.status = OrderStatus.CONFIRMED.value
    db.commit()
    db.refresh(delivery)
    _notify_delivery_participants(db, delivery)
    return _delivery_response(delivery)


@router.get("/open", response_model=List[DeliveryRead])
def list_open_deliveries(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("driver")),
):
    deliveries = (
        db.query(Delivery)
        .outerjoin(DeliveryVan)
        .filter(
            Delivery.status.in_(
                (DeliveryStatus.OPEN.value, DeliveryStatus.ASSIGNED.value)
            ),
            Delivery.driver_id.is_(None),
            or_(Delivery.van_id.is_(None), DeliveryVan.driver_id.is_(None)),
            Delivery.order.has(Order.status != OrderStatus.CANCELLED.value),
        )
        .order_by(Delivery.created_at.asc())
        .all()
    )
    return [_delivery_response(delivery) for delivery in deliveries]


@router.post("/{delivery_id}/accept", response_model=DeliveryRead)
def accept_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("driver")),
):
    result = (
        db.query(Delivery)
        .filter(
            Delivery.id == delivery_id,
            Delivery.status.in_(
                (DeliveryStatus.OPEN.value, DeliveryStatus.ASSIGNED.value)
            ),
            Delivery.driver_id.is_(None),
            or_(Delivery.van_id.is_(None), Delivery.van.has(DeliveryVan.driver_id.is_(None))),
            Delivery.order.has(Order.status != OrderStatus.CANCELLED.value),
        )
        .update(
            {
                Delivery.driver_id: current_user.id,
                Delivery.status: DeliveryStatus.ACCEPTED.value,
            },
            synchronize_session=False,
        )
    )
    if result != 1:
        db.rollback()
        if not db.query(Delivery.id).filter(Delivery.id == delivery_id).first():
            raise HTTPException(status_code=404, detail="Delivery not found")
        raise HTTPException(
            status_code=409,
            detail="Delivery is no longer available to accept",
        )

    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    delivery.order.status = OrderStatus.CONFIRMED.value
    db.commit()
    db.refresh(delivery)
    _notify_delivery_participants(db, delivery)
    return _delivery_response(delivery)


@router.get("/", response_model=List[DeliveryRead])
def list_deliveries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Delivery)
    if current_user.role in ("admin", "shop_manager"):
        query = query.order_by(Delivery.created_at.desc())
    elif current_user.role == "driver":
        query = (
            query.outerjoin(DeliveryVan)
            .filter(
                or_(
                    Delivery.driver_id == current_user.id,
                    DeliveryVan.driver_id == current_user.id,
                )
            )
            .order_by(Delivery.created_at.desc())
        )
    elif current_user.role == "farmer":
        query = (
            query.join(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(Product.farmer_id == current_user.id)
            .distinct()
            .order_by(Delivery.created_at.desc())
        )
    else:
        query = (
            query.join(Order)
            .filter(Order.buyer_id == current_user.id)
            .order_by(Delivery.created_at.desc())
        )
    return [_delivery_response(delivery) for delivery in query.all()]


@router.patch("/{delivery_id}", response_model=DeliveryRead)
def update_delivery(
    delivery_id: int,
    delivery_in: DeliveryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "driver", "shop_manager")),
):
    delivery = (
        db.query(Delivery)
        .filter(Delivery.id == delivery_id)
        .with_for_update()
        .first()
    )
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    order = (
        db.query(Order)
        .filter(Order.id == delivery.order_id)
        .with_for_update()
        .first()
    )
    delivery.order = order

    update_data = delivery_in.model_dump(exclude_unset=True)
    if current_user.role == "driver":
        if _assigned_driver_id(delivery) != current_user.id:
            raise HTTPException(status_code=403, detail="This delivery is assigned to another driver")
        if set(update_data) != {"status"}:
            raise HTTPException(status_code=400, detail="Drivers can only advance delivery status")
        expected_status = _DRIVER_STATUS_TRANSITIONS.get(delivery.status)
        if update_data["status"] != expected_status:
            raise HTTPException(
                status_code=409,
                detail=f"Next valid delivery status is {expected_status or 'none'}",
            )

    previous_status = delivery.status
    for field, value in update_data.items():
        setattr(delivery, field, value)

    if delivery.status == DeliveryStatus.PICKED_UP.value and not delivery.pickup_time:
        delivery.pickup_time = datetime.now(timezone.utc)
    if delivery.status == DeliveryStatus.DELIVERED.value and not delivery.actual_delivery:
        delivery.actual_delivery = datetime.now(timezone.utc)

    if delivery.status == DeliveryStatus.ACCEPTED.value:
        delivery.order.status = OrderStatus.CONFIRMED.value
    elif delivery.status == DeliveryStatus.IN_TRANSIT.value:
        delivery.order.status = OrderStatus.IN_TRANSIT.value
    elif delivery.status == DeliveryStatus.DELIVERED.value:
        delivery.order.status = OrderStatus.DELIVERED.value

    if delivery.status != previous_status:
        settle_order_if_ready(db, delivery.order)
    db.commit()
    db.refresh(delivery)
    if delivery.status != previous_status:
        _notify_delivery_participants(db, delivery)
    return _delivery_response(delivery)
