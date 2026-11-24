from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: float = Field(..., gt=0)


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    unit: Optional[str] = None
    quantity: float
    unit_price: float
    subtotal: float

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    delivery_address: str
    notes: Optional[str] = None
    payment_method: Literal["cash_on_delivery", "mobile_money"] = "cash_on_delivery"
    payment_reference: Optional[str] = Field(default=None, max_length=100)


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class OrderPaymentUpdate(BaseModel):
    payment_reference: Optional[str] = Field(default=None, max_length=100)


class DeliverySummaryRead(BaseModel):
    id: int
    status: str
    estimated_fee_ugx: int
    driver_id: Optional[int] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: int
    buyer_id: int
    status: str
    total_amount: float
    delivery_address: str
    notes: Optional[str] = None
    payment_method: str
    payment_status: str
    payment_reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemRead] = Field(default_factory=list)
    delivery: Optional[DeliverySummaryRead] = None

    model_config = ConfigDict(from_attributes=True)


class FarmerOrderItemRead(BaseModel):
    product_id: int
    product_name: str
    quantity: float
    unit: str
    unit_price: float
    subtotal: float


class FarmerOrderRead(BaseModel):
    id: int
    buyer_id: int
    status: str
    total_amount: float
    delivery_address: str
    notes: Optional[str] = None
    payment_method: str
    payment_status: str
    payment_reference: Optional[str] = None
    created_at: datetime
    items: List[FarmerOrderItemRead]
    delivery: Optional[DeliverySummaryRead] = None
