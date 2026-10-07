from datetime import datetime
from secrets import token_urlsafe
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, Uuid, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def generate_plate_code() -> str:
    return token_urlsafe(12)


class Plate(Base):
    __tablename__ = "plates"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    store_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("stores.id"), nullable=False, index=True
    )
    plate_code: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, default=generate_plate_code
    )
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
