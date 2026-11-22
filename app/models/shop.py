from datetime import datetime, timezone
from sqlalchemy import String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Shop(Base):
    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    manager = relationship("User", back_populates="managed_shops")
    inventory = relationship("ShopInventory", back_populates="shop", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Shop {self.name}>"


class ShopInventory(Base):
    __tablename__ = "shop_inventory"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    last_restocked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    shop = relationship("Shop", back_populates="inventory")
    product = relationship("Product", back_populates="shop_inventories")

    def __repr__(self) -> str:
        return f"<ShopInventory shop={self.shop_id} product={self.product_id}>"
