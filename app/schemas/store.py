from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class StoreCreate(BaseModel):
    name: str
    description: str | None = None
    logo_url: str | None = None
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("O nome da loja não pode estar vazio.")
        return value


class StoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    logo_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
