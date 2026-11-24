from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict


class DeliveryVanBase(BaseModel):
    plate_number: str
    capacity_kg: float = 1000.0
    current_location: Optional[str] = None
    status: str = "available"
    brand_name: str = "Harvesta"


class DeliveryVanCreate(DeliveryVanBase):
    driver_id: Optional[int] = None


class DeliveryVanRead(DeliveryVanBase):
    id: int
    driver_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryBase(BaseModel):
    order_id: int
    van_id: Optional[int] = None
    status: str = "assigned"
    notes: Optional[str] = None


class DeliveryCreate(DeliveryBase):
    pass


class DeliveryUpdate(BaseModel):
    status: Optional[
        Literal["open", "assigned", "accepted", "picked_up", "in_transit", "delivered", "failed"]
    ] = None
    van_id: Optional[int] = None
    pickup_time: Optional[datetime] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    notes: Optional[str] = None


class DeliveryItemRead(BaseModel):
    product_name: str
    quantity: float
    unit: str
    pickup_district: str


class DeliveryRead(DeliveryBase):
    id: int
    driver_id: Optional[int] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    estimated_fee_ugx: int
    pickup_district: str
    delivery_district: str
    items: List[DeliveryItemRead]
    payment_method: str
    payment_status: str
    payment_reference: Optional[str] = None
    pickup_time: Optional[datetime] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
