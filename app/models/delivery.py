from datetime import datetime, timezone
from sqlalchemy import String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class VanStatus(str, enum.Enum):
    AVAILABLE = "available"
    ON_ROUTE = "on_route"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class DeliveryStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"


class DeliveryVan(Base):
    __tablename__ = "delivery_vans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plate_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    capacity_kg: Mapped[float] = mapped_column(Float, default=1000.0)
    current_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=VanStatus.AVAILABLE.value)
    brand_name: Mapped[str] = mapped_column(String(50), default="Harvesta")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    driver = relationship("User", back_populates="vans")
    deliveries = relationship("Delivery", back_populates="van")

    def __repr__(self) -> str:
        return f"<DeliveryVan {self.plate_number}>"


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True, nullable=False)
    van_id: Mapped[int | None] = mapped_column(ForeignKey("delivery_vans.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=DeliveryStatus.ASSIGNED.value)
    pickup_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    order = relationship("Order", back_populates="delivery")
    van = relationship("DeliveryVan", back_populates="deliveries")

    def __repr__(self) -> str:
        return f"<Delivery #{self.id} for Order {self.order_id}>"
