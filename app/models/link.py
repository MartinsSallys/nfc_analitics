from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import HttpUrl, TypeAdapter
from sqlalchemy import Boolean, DateTime, ForeignKey, Text, UniqueConstraint, Uuid, func, true
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.core.database import Base


class Destination(str, Enum):
    GOOGLE = "google"
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"


url_adapter = TypeAdapter(HttpUrl)


def validate_link_url(value: str) -> str:
    url = url_adapter.validate_python(value)
    if url.username is not None or url.password is not None:
        raise ValueError("A URL não pode conter credenciais.")
    return str(url)


class Link(Base):
    __tablename__ = "links"
    __table_args__ = (
        UniqueConstraint("store_id", "destination", name="uq_links_store_destination"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    store_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("stores.id"), nullable=False, index=True
    )
    destination: Mapped[Destination] = mapped_column(
        SqlEnum(
            Destination,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            name="link_destination",
            validate_strings=True,
        ),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    @validates("url")
    def validate_url(self, key: str, value: str) -> str:
        return validate_link_url(value)
