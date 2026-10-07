from functools import lru_cache
from secrets import compare_digest

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import Settings
from app.core.database import create_session_factory

security = HTTPBasic()


@lru_cache
def session_factory():
    return create_session_factory(Settings())


def get_db():
    with session_factory()() as session:
        yield session


def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    settings = Settings()
    if not settings.admin_username or not settings.admin_password:
        raise HTTPException(status_code=503, detail="Acesso administrativo não configurado.")
    valid_user = compare_digest(credentials.username.encode(), settings.admin_username.encode())
    valid_password = compare_digest(
        credentials.password.encode(), settings.admin_password.get_secret_value().encode()
    )
    if not (valid_user and valid_password):
        raise HTTPException(
            status_code=401,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Basic"},
        )
