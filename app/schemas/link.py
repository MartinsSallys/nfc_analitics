from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.link import Destination, validate_link_url


class LinkCreate(BaseModel):
    store_id: UUID
    destination: Destination
    url: str
    is_active: bool = True

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return validate_link_url(value)


class LinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    store_id: UUID
    destination: Destination
    url: str
    is_active: bool
    created_at: datetime
