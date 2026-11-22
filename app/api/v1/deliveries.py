from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.models.delivery import DeliveryVan, Delivery
from app.models.order import Order
from app.schemas.delivery import (
    DeliveryVanCreate,
    DeliveryVanRead,
    DeliveryCreate,
    DeliveryRead,
    DeliveryUpdate,
)

router = APIRouter(prefix="/deliveries", tags=["Deliveries & Vans"])


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
    # Update order status
    order.status = "confirmed"
    db.commit()
    db.refresh(delivery)
    return delivery


@router.get("/", response_model=List[DeliveryRead])
def list_deliveries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role in ("admin", "shop_manager"):
        return db.query(Delivery).order_by(Delivery.created_at.desc()).all()
    if current_user.role == "driver":
        # Deliveries assigned to vans driven by this user
        return (
            db.query(Delivery)
            .join(DeliveryVan)
            .filter(DeliveryVan.driver_id == current_user.id)
            .all()
        )
    # Buyers see deliveries of their own orders
    return (
        db.query(Delivery)
        .join(Order)
        .filter(Order.buyer_id == current_user.id)
        .all()
    )


@router.patch("/{delivery_id}", response_model=DeliveryRead)
def update_delivery(
    delivery_id: int,
    delivery_in: DeliveryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "driver", "shop_manager")),
):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

    update_data = delivery_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(delivery, field, value)

    # Sync order status
    if delivery.status == "delivered" and delivery.order:
        delivery.order.status = "delivered"
    elif delivery.status == "in_transit" and delivery.order:
        delivery.order.status = "in_transit"

    db.commit()
    db.refresh(delivery)
    return delivery
