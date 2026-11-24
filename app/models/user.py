from datetime import datetime, date, timezone
from sqlalchemy import String, Boolean, DateTime, Float, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    FARMER = "farmer"
    DRIVER = "driver"
    SHOP_MANAGER = "shop_manager"
    ADMIN = "admin"
    BUYER = "buyer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default=UserRole.BUYER.value, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    privacy_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    privacy_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    nin: Mapped[str | None] = mapped_column(String(14), unique=True, nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subcounty: Mapped[str | None] = mapped_column(String(100), nullable=True)
    village: Mapped[str | None] = mapped_column(String(100), nullable=True)
    next_of_kin_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    next_of_kin_contact: Mapped[str | None] = mapped_column(String(30), nullable=True)
    primary_farm_enterprise: Mapped[str | None] = mapped_column(String(30), nullable=True)
    farm_size_acres: Mapped[float | None] = mapped_column(Float, nullable=True)
    dfa_cooperative_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    driving_permit_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    driving_permit_class: Mapped[str | None] = mapped_column(String(30), nullable=True)
    vehicle_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    vehicle_plate: Mapped[str | None] = mapped_column(String(30), nullable=True)
    goods_insurance_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    farms = relationship("Farm", back_populates="owner", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="farmer", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="buyer", foreign_keys="Order.buyer_id")
    vans = relationship("DeliveryVan", back_populates="driver")
    deliveries = relationship("Delivery", back_populates="driver", foreign_keys="Delivery.driver_id")
    managed_shops = relationship("Shop", back_populates="manager")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
