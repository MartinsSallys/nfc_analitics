import asyncio
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_db
from app.main import app


@pytest.fixture
def api(db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "test_admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "test_password")

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)


def client(auth=("test_admin", "test_password")):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test", auth=auth)


def test_create_and_retrieve_store(api):
    async def scenario():
        async with client() as http:
            created = await http.post("/stores", json={"name": "  Loja teste  "})
            assert created.status_code == 201
            data = created.json()
            assert data["name"] == "Loja teste"
            assert data["logo_url"] is None
            assert data["is_active"] is True
            assert data["created_at"] and data["updated_at"]
            retrieved = await http.get(created.headers["Location"])
            assert retrieved.status_code == 200
            assert retrieved.json() == data

    asyncio.run(scenario())


@pytest.mark.parametrize("payload", [{}, {"name": "   "}, {"name": None}])
def test_invalid_store_returns_422(api, payload):
    async def scenario():
        async with client() as http:
            response = await http.post("/stores", json=payload)
            assert response.status_code == 422

    asyncio.run(scenario())


def test_missing_store_returns_404(api):
    async def scenario():
        async with client() as http:
            response = await http.get(f"/stores/{uuid4()}")
            assert response.status_code == 404

    asyncio.run(scenario())


def test_invalid_id_returns_422(api):
    async def scenario():
        async with client() as http:
            response = await http.get("/stores/invalid")
            assert response.status_code == 422

    asyncio.run(scenario())


@pytest.mark.parametrize("auth", [None, ("test_admin", "wrong"), ("wrong", "test_password")])
def test_admin_credentials_required_for_create_and_read(api, auth):
    async def scenario():
        async with client(auth) as http:
            created = await http.post("/stores", json={"name": "Loja"})
            retrieved = await http.get(f"/stores/{uuid4()}")
            assert created.status_code == retrieved.status_code == 401

    asyncio.run(scenario())


def test_unconfigured_admin_access_is_disabled(api, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "")

    async def scenario():
        async with client() as http:
            response = await http.post("/stores", json={"name": "Loja"})
            assert response.status_code == 503

    asyncio.run(scenario())
