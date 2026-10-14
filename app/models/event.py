from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Uuid, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EventType(str, Enum):
    PAGE_VIEW = "page_view"
    GOOGLE_CLICK = "google_click"
    WHATSAPP_CLICK = "whatsapp_click"
    INSTAGRAM_CLICK = "instagram_click"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    plate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("plates.id"), nullable=False, index=True
    )
    event_type: Mapped[EventType] = mapped_column(
        SqlEnum(
            EventType,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            name="event_type",
            validate_strings=True,
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
