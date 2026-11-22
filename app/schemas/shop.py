from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ShopBase(BaseModel):
    name: str
    location: str
    description: Optional[str] = None
    is_open: bool = True
    phone: Optional[str] = None


class ShopCreate(ShopBase):
    manager_id: Optional[int] = None


class ShopRead(ShopBase):
    id: int
    manager_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShopInventoryBase(BaseModel):
    product_id: int
    quantity: float = 0.0


class ShopInventoryCreate(ShopInventoryBase):
    shop_id: int


class ShopInventoryRead(ShopInventoryBase):
    id: int
    shop_id: int
    last_restocked: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
