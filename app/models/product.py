from datetime import datetime, timezone, date
from sqlalchemy import String, Float, Integer, Text, ForeignKey, DateTime, Date, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class ProductCategory(str, enum.Enum):
    CROP = "crop"
    LIVESTOCK = "livestock"
    PROCESSED = "processed"
    OTHER = "other"


class ProductStatus(str, enum.Enum):
    AVAILABLE = "available"
    SOLD_OUT = "sold_out"
    RESERVED = "reserved"
    INACTIVE = "inactive"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    farm_id: Mapped[int | None] = mapped_column(ForeignKey("farms.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(30), default=ProductCategory.CROP.value)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    unit: Mapped[str] = mapped_column(String(30), default="kg")  # kg, pieces, liters, etc.
    price_per_unit: Mapped[float] = mapped_column(Float, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=ProductStatus.AVAILABLE.value)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    farmer = relationship("User", back_populates="products")
    farm = relationship("Farm", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    shop_inventories = relationship("ShopInventory", back_populates="product")

    def __repr__(self) -> str:
        return f"<Product {self.name} ({self.quantity} {self.unit})>"
