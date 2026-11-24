from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.order import OrderItemCreate

class WalletQuoteRequest(BaseModel):
    operation: Literal["deposit", "withdrawal"]
    amount_ugx: int = Field(gt=0, le=1_000_000_000)


class OrderQuoteRequest(BaseModel):
    items: list[OrderItemCreate]


class WalletDepositCreate(BaseModel):
    amount_ugx: int = Field(gt=0, le=1_000_000_000)
    payment_method: Literal["mobile_money", "card", "paypal"]
    reference: Optional[str] = Field(default=None, max_length=100)


class WalletWithdrawalCreate(BaseModel):
    amount_ugx: int = Field(gt=0, le=1_000_000_000)
    destination: str = Field(min_length=8, max_length=100)


class WalletTransactionDecision(BaseModel):
    status: Literal["completed", "rejected"]
    reference: Optional[str] = Field(default=None, max_length=100)


class FeeBreakdown(BaseModel):
    operation: str
    base_amount_ugx: int
    delivery_fee_ugx: int
    service_fee_ugx: int
    withdrawal_levy_ugx: int
    vat_ugx: int
    total_tax_ugx: int
    total_payable_ugx: int
    net_amount_ugx: int
    service_fee_payer: Optional[str] = None
    tax_estimate: bool
    tax_note: str


class WalletTransactionRead(BaseModel):
    id: int
    order_id: Optional[int] = None
    transaction_type: str
    amount_ugx: int
    service_fee_ugx: int
    tax_amount_ugx: int
    balance_delta_ugx: int
    status: str
    payment_method: Optional[str] = None
    reference: Optional[str] = None
    destination: Optional[str] = None
    description: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WalletOverview(BaseModel):
    balance_ugx: int
    transactions: list[WalletTransactionRead]


class WalletTransactionAdminRead(WalletTransactionRead):
    user_id: Optional[int] = None
