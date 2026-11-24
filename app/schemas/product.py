from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    category: str = "crop"
    description: Optional[str] = None
    quantity: float = Field(..., gt=0)
    unit: str = "kg"
    price_per_unit: float = Field(..., gt=0)
    image_url: Optional[str] = None
    harvest_date: Optional[date] = None
    status: str = "available"
    farm_id: Optional[int] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    price_per_unit: Optional[float] = None
    image_url: Optional[str] = None
    harvest_date: Optional[date] = None
    status: Optional[str] = None


class ProductRead(ProductBase):
    id: int
    farmer_id: int
    farmer_name: Optional[str] = None
    farmer_location: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
