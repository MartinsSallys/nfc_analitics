import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


def test_health_responds_without_database(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

    asyncio.run(request())


def test_development_docs_allow_required_assets(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")

    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/docs")
            assert response.status_code == 200
            assert "https://cdn.jsdelivr.net" in response.headers["content-security-policy"]
            response = await client.get("/static/style.css")
            assert response.status_code == 200
            assert "'unsafe-inline'" not in response.headers["content-security-policy"]

    asyncio.run(request())
