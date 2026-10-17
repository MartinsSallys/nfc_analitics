import asyncio
from datetime import UTC, datetime, timedelta
from io import BytesIO

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.api.dependencies import get_db
from app.core.config import Settings
from app.main import app
from app.models import Event, EventType, Plate, Store
from app.services.metrics import metrics_for_store

AUTH = ("admin_test", "admin_test_password")


def request(method, path, auth=AUTH, **kwargs):
    async def run():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", auth=auth
        ) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(run())


@pytest.fixture
def admin_api(db_session, monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_USERNAME", AUTH[0])
    monkeypatch.setenv("ADMIN_PASSWORD", AUTH[1])
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://test")
    monkeypatch.setenv("SECRET_KEY", "a" * 40)

    def override():
        yield db_session

    app.dependency_overrides[get_db] = override
    try:
        yield db_session
    finally:
        app.dependency_overrides.pop(get_db, None)


def new_store(name="Loja"):
    response = request("POST", "/stores", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_admin_complete_setup_and_private_metrics(admin_api):
    store_id = new_store()
    plate = request("POST", "/admin/plates", json={"store_id": store_id, "name": "Balcão"})
    assert plate.status_code == 201
    plate = plate.json()
    assert plate["url"] == f"http://test/p/{plate['code']}"
    for destination in ("google", "whatsapp", "instagram"):
        response = request(
            "PUT",
            f"/admin/stores/{store_id}/links/{destination}",
            json={"url": f"https://example.com/{destination}"},
        )
        assert response.status_code == 200
    assert request("GET", f"/p/{plate['code']}", auth=None).status_code == 200
    assert request("GET", f"/r/{plate['code']}/whatsapp", auth=None).status_code == 302
    response = request("POST", f"/admin/stores/{store_id}/metrics-token")
    assert response.status_code == 200
    url = response.json()["url"]
    assert url not in str(admin_api.get(Store, store_id).metrics_token_hash)
    metrics = request("GET", url + "/data", auth=None)
    assert metrics.status_code == 200
    assert metrics.json()["page_views"] == metrics.json()["whatsapp_clicks"] == 1
    dashboard = request("GET", url, auth=None)
    assert dashboard.status_code == 200
    assert "Consulta privada" in dashboard.text
    assert dashboard.headers["cache-control"] == "no-store"
    assert dashboard.headers["referrer-policy"] == "no-referrer"
    assert request("GET", "/admin", auth=None).status_code == 401
    assert (
        request("POST", "/admin/plates", auth=None, json={"store_id": store_id}).status_code == 401
    )


def test_private_token_rotation_revocation_and_isolation(admin_api):
    first, second = new_store("Loja A"), new_store("Loja B")
    first_url = request("POST", f"/admin/stores/{first}/metrics-token").json()["url"]
    second_url = request("POST", f"/admin/stores/{second}/metrics-token").json()["url"]
    data = request("GET", first_url + f"/data?store_id={second}", auth=None).json()
    assert data["store_name"] == "Loja A"
    assert request("GET", second_url + "/data", auth=None).json()["store_name"] == "Loja B"
    rotated = request("POST", f"/admin/stores/{first}/metrics-token").json()["url"]
    assert request("GET", first_url, auth=None).status_code == 404
    assert request("GET", rotated, auth=None).status_code == 200
    assert request("DELETE", f"/admin/stores/{first}/metrics-token").status_code == 204
    assert request("GET", rotated, auth=None).status_code == 404
    assert request("GET", "/metrics/invalid", auth=None).status_code == 404
    assert (
        request("PUT", f"/admin/stores/{second}", auth=None, json={"name": "Invadida"}).status_code
        == 401
    )


def test_metrics_date_boundaries_and_store_filter(admin_api):
    session = admin_api
    a, b = Store(name="A"), Store(name="B")
    session.add_all([a, b])
    session.flush()
    pa, pb = Plate(store_id=a.id), Plate(store_id=b.id)
    session.add_all([pa, pb])
    session.flush()
    # 01:00 em Fortaleza = 04:00 UTC. Meia-noite local = 03:00 UTC.
    now = datetime(2026, 10, 17, 4, tzinfo=UTC)
    for date in [
        now,
        datetime(2026, 10, 17, 2, 59, tzinfo=UTC),
        now - timedelta(days=6),
        now - timedelta(days=8),
    ]:
        session.add(Event(plate_id=pa.id, event_type=EventType.PAGE_VIEW, created_at=date))
    session.add(Event(plate_id=pb.id, event_type=EventType.PAGE_VIEW, created_at=now))
    session.add(Event(plate_id=pa.id, event_type=EventType.GOOGLE_CLICK, created_at=now))
    session.commit()
    data = metrics_for_store(session, a, Settings(), now=now)
    assert data["page_views"] == 4
    assert data["today"] == 1
    assert data["last_7_days"] == 3
    assert data["google_clicks"] == 1
    assert len(data["plates"]) == 1
    assert data["plates"][0]["page_views"] == 4


def test_link_update_does_not_create_duplicate_and_plate_code_stable(admin_api):
    store_id = new_store()
    plate = request("POST", "/admin/plates", json={"store_id": store_id}).json()
    for url in ["https://example.com/old", "https://example.com/new"]:
        assert (
            request("PUT", f"/admin/stores/{store_id}/links/google", json={"url": url}).status_code
            == 200
        )
    detail = request("GET", f"/admin/stores/{store_id}").json()
    assert len(detail["links"]) == 1
    assert detail["links"][0]["url"] == "https://example.com/new"
    response = request(
        "PATCH", f"/admin/plates/{plate['id']}", json={"name": "Entrada", "is_active": False}
    )
    assert response.json()["code"] == plate["code"]
    assert request("GET", f"/p/{plate['code']}", auth=None).status_code == 404
    assert (
        request(
            "PATCH",
            f"/admin/plates/{plate['id']}",
            json={"name": "X", "is_active": True, "plate_code": "changed"},
        ).status_code
        == 422
    )


def test_qr_is_png_and_uses_public_plate_url(admin_api, monkeypatch):
    store_id = new_store()
    plate = request("POST", "/admin/plates", json={"store_id": store_id}).json()
    import qrcode

    import app.api.admin as module

    original = qrcode.make
    captured = []

    def capture(url):
        captured.append(url)
        return original(url)

    monkeypatch.setattr(module.qrcode, "make", capture)
    response = request("GET", f"/admin/plates/{plate['id']}/qr.png")
    assert response.status_code == 200
    assert captured == [plate["url"]]
    assert response.headers["content-type"] == "image/png"
    image = Image.open(BytesIO(response.content))
    assert image.width == image.height and image.width > 100


def test_logo_upload_validation_and_filesystem(admin_api, tmp_path):
    store_id = new_store()
    image = BytesIO()
    Image.new("RGB", (20, 20), "red").save(image, format="PNG")
    response = request(
        "POST",
        f"/admin/stores/{store_id}/logo",
        files={"file": ("../../unsafe.png", image.getvalue(), "image/png")},
    )
    assert response.status_code == 200
    logo_url = response.json()["logo_url"]
    assert logo_url.startswith("/uploads/") and "unsafe" not in logo_url
    file = tmp_path / "uploads" / logo_url.split("/")[-1]
    assert file.exists()
    for content in [b"<svg><script>alert(1)</script></svg>", b"not an image"]:
        assert (
            request(
                "POST",
                f"/admin/stores/{store_id}/logo",
                files={"file": ("file.png", content, "image/png")},
            ).status_code
            == 422
        )
    assert (
        request(
            "POST",
            f"/admin/stores/{store_id}/logo",
            files={"file": ("large.png", b"x" * (2 * 1024 * 1024 + 1), "image/png")},
        ).status_code
        == 413
    )


def test_cross_origin_writes_rejected(admin_api):
    response = request(
        "POST", "/stores", json={"name": "Outra"}, headers={"Origin": "https://evil.example"}
    )
    assert response.status_code == 403


def test_no_token_or_database_secrets_exposed_in_store_listing(admin_api):
    store_id = new_store()
    url = request("POST", f"/admin/stores/{store_id}/metrics-token").json()["url"]
    token = url.rsplit("/", 1)[-1]
    stores = request("GET", "/admin/stores").text
    assert token not in stores and "metrics_token_hash" not in stores
    assert request("GET", "/admin").status_code == 200
