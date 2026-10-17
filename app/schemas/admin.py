from uuid import UUID

from pydantic import BaseModel, field_validator

from app.schemas.store import StoreCreate


class StoreUpdate(StoreCreate):
    pass


class PlateCreate(BaseModel):
    store_id: UUID
    name: str | None = None


class PlateUpdate(BaseModel):
    name: str | None = None
    is_active: bool

    model_config = {"extra": "forbid"}


class LinkUpdate(BaseModel):
    url: str
    is_active: bool = True

    @field_validator("url")
    @classmethod
    def valid_url(cls, value):
        from app.models.link import validate_link_url

        return validate_link_url(value)
