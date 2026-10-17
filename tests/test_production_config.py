import pytest
from pydantic import ValidationError

from app.core.config import Settings


def config(**kwargs):
    values = dict(
        _env_file=None,
        database_url="postgresql+psycopg://u:p@db/nfc",
        environment="production",
        public_base_url="https://example.com",
        admin_username="admin",
        admin_password="strong-password-1234",
        secret_key="x" * 40,
    )
    values.update(kwargs)
    return Settings(**values)


@pytest.mark.parametrize(
    "changes",
    [
        {"secret_key": "short"},
        {"secret_key": "local-development-key-change-before-production"},
        {"admin_password": "short"},
        {"admin_username": None},
        {"public_base_url": "http://example.com"},
    ],
)
def test_production_rejects_unsafe_configuration(changes):
    with pytest.raises(ValidationError):
        config(**changes)


def test_production_accepts_explicit_secure_configuration():
    assert config().environment == "production"


@pytest.mark.parametrize(
    "url",
    [
        "https://user:pass@example.com",
        "https://example.com/path",
        "https://example.com?token=private",
    ],
)
def test_public_base_url_cannot_embed_credentials_or_extra_paths(url):
    with pytest.raises(ValidationError):
        config(public_base_url=url)


def test_configuration_errors_do_not_print_secrets():
    with pytest.raises(ValidationError) as error:
        config(admin_password="private-marker", secret_key="private-secret-marker")
    assert "private-marker" not in str(error.value)
    assert "private-secret-marker" not in str(error.value)
