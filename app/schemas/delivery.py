from datetime import datetime
from typing import Optional
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
    status: Optional[str] = None
    van_id: Optional[int] = None
    pickup_time: Optional[datetime] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    notes: Optional[str] = None


class DeliveryRead(DeliveryBase):
    id: int
    pickup_time: Optional[datetime] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
