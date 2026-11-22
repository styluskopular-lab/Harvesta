from datetime import datetime, timezone
from sqlalchemy import String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from datetime import date


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    size_hectares: Mapped[float | None] = mapped_column(Float, nullable=True)
    crop_types: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated
    livestock: Mapped[str | None] = mapped_column(Text, nullable=True)   # comma-separated
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    owner = relationship("User", back_populates="farms")
    products = relationship("Product", back_populates="farm")

    def __repr__(self) -> str:
        return f"<Farm {self.name}>"
