import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.api.dependencies import get_db
from app.main import app
from app.models import Destination, Event, EventType, Link, Plate, Store


def request(path):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(path, follow_redirects=False)

    return asyncio.run(run())


@pytest.fixture
def tracking(db_session):
    def override():
        yield db_session

    app.dependency_overrides[get_db] = override
    store = Store(name="Loja <teste>", description="Descrição da loja")
    other = Store(name="Outra loja")
    db_session.add_all([store, other])
    db_session.flush()
    plate = Plate(store_id=store.id)
    other_plate = Plate(store_id=other.id)
    db_session.add_all([plate, other_plate])
    for destination in Destination:
        db_session.add(
            Link(
                store_id=store.id,
                destination=destination,
                url=f"https://example.com/{destination.value}",
            )
        )
        db_session.add(
            Link(
                store_id=other.id,
                destination=destination,
                url=f"https://other.example.com/{destination.value}",
            )
        )
    db_session.commit()
    try:
        yield db_session, store, plate, other_plate
    finally:
        app.dependency_overrides.pop(get_db, None)


def events(session):
    return session.scalars(select(Event)).all()


def test_public_page_renders_store_and_records_each_visit(tracking):
    session, store, plate, _ = tracking
    code = plate.plate_code
    for _ in range(2):
        response = request(f"/p/{code}")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert response.headers["cache-control"] == "no-store"
        assert "Loja &lt;teste&gt;" in response.text
        assert "Outra loja" not in response.text
        assert f"/r/{code}/whatsapp" in response.text
        assert "viewport" in response.text
    saved = events(session)
    assert len(saved) == 2
    assert all(
        event.plate_id == plate.id and event.event_type == EventType.PAGE_VIEW for event in saved
    )


@pytest.mark.parametrize(
    "destination,event_type",
    [
        ("google", EventType.GOOGLE_CLICK),
        ("whatsapp", EventType.WHATSAPP_CLICK),
        ("instagram", EventType.INSTAGRAM_CLICK),
    ],
)
def test_redirect_records_correct_event_before_returning(tracking, destination, event_type):
    session, _, plate, _ = tracking
    response = request(f"/r/{plate.plate_code}/{destination}")
    assert response.status_code == 302
    assert response.headers["location"] == f"https://example.com/{destination}"
    saved = events(session)
    assert len(saved) == 1
    assert saved[0].plate_id == plate.id
    assert saved[0].event_type == event_type


@pytest.mark.parametrize("state", ["invalid", "inactive_plate", "inactive_store"])
@pytest.mark.parametrize("path", ["p", "r"])
def test_unavailable_plate_or_store_never_records_event(tracking, state, path):
    session, store, plate, _ = tracking
    code = plate.plate_code
    if state == "invalid":
        code = "invalid"
    elif state == "inactive_plate":
        plate.is_active = False
    else:
        store.is_active = False
    session.commit()
    url = f"/p/{code}" if path == "p" else f"/r/{code}/google"
    response = request(url)
    assert response.status_code == 404
    assert "Página indisponível" in response.text
    assert not events(session)


def test_inactive_link_is_hidden_and_cannot_redirect(tracking):
    session, store, plate, _ = tracking
    link = session.scalar(
        select(Link).where(Link.store_id == store.id, Link.destination == Destination.GOOGLE)
    )
    link.is_active = False
    session.commit()
    code = plate.plate_code
    assert request(f"/r/{code}/google").status_code == 404
    assert not events(session)
    response = request(f"/p/{code}")
    assert f"/r/{code}/google" not in response.text
    assert f"/r/{code}/instagram" in response.text


def test_missing_and_unknown_destination_cannot_redirect(tracking):
    session, store, plate, _ = tracking
    link = session.scalar(
        select(Link).where(Link.store_id == store.id, Link.destination == Destination.GOOGLE)
    )
    session.delete(link)
    session.commit()
    for destination in ["google", "unknown"]:
        assert request(f"/r/{plate.plate_code}/{destination}").status_code == 404
    assert not events(session)


def test_destination_url_is_only_taken_from_database(tracking):
    session, _, plate, _ = tracking
    response = request(f"/r/{plate.plate_code}/google?url=https://attacker.example")
    assert response.headers["location"] == "https://example.com/google"
    assert session.scalar(select(func.count()).select_from(Event)) == 1


@pytest.mark.parametrize("route", ["p", "r"])
def test_database_failure_rolls_back_and_never_redirects(tracking, monkeypatch, route):
    from sqlalchemy.exc import IntegrityError

    session, _, plate, _ = tracking
    code = plate.plate_code

    def fail_commit():
        raise IntegrityError("INSERT", {}, Exception("simulated failure"))

    monkeypatch.setattr(session, "commit", fail_commit)
    path = f"/p/{code}" if route == "p" else f"/r/{code}/google"
    response = request(path)
    assert response.status_code == 503
    assert "location" not in response.headers
    assert not events(session)
