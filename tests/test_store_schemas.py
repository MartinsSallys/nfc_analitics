import pytest
from pydantic import ValidationError

from app.schemas.store import StoreCreate


@pytest.mark.parametrize("name", ["", "   ", "\t\n", None, 123])
def test_invalid_store_name_is_rejected(name):
    with pytest.raises(ValidationError):
        StoreCreate(name=name)


def test_store_name_is_required():
    with pytest.raises(ValidationError):
        StoreCreate()


def test_store_optional_fields_can_be_omitted():
    data = StoreCreate(name="Loja")
    assert data.description is None
    assert data.logo_url is None
    assert data.is_active is True
