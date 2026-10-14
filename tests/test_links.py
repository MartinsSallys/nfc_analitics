from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.models import Destination, Link, Store
from app.schemas.link import LinkCreate, LinkRead


def store(session):
    item = Store(name="Loja")
    session.add(item)
    session.flush()
    return item


@pytest.mark.parametrize("destination", list(Destination))
def test_link_is_saved_and_read_with_store_and_destination(db_session, destination):
    owner = store(db_session)
    data = LinkCreate(store_id=owner.id, destination=destination, url="https://example.com/path")
    link = Link(**data.model_dump())
    db_session.add(link)
    db_session.commit()
    link_id = link.id
    db_session.expunge_all()
    saved = LinkRead.model_validate(db_session.get(Link, link_id))
    assert saved.store_id == data.store_id
    assert saved.destination == destination
    assert saved.url == "https://example.com/path"
    assert saved.is_active is True
    assert saved.created_at.tzinfo is not None


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not-a-url",
        "javascript:alert(1)",
        "ftp://example.com",
        "//example.com",
        "https://user:password@example.com",
    ],
)
def test_bad_url_rejected_by_schema_and_model(url):
    with pytest.raises((ValueError, ValidationError)):
        LinkCreate(store_id=uuid4(), destination="google", url=url)
    with pytest.raises((ValueError, ValidationError)):
        Link(store_id=uuid4(), destination=Destination.GOOGLE, url=url)


def test_unknown_destination_rejected_by_schema():
    with pytest.raises(ValidationError):
        LinkCreate(store_id=uuid4(), destination="unknown", url="https://example.com")


def test_unknown_destination_rejected_by_database(db_session):
    owner = store(db_session)
    with pytest.raises(IntegrityError):
        db_session.execute(
            text(
                "INSERT INTO links (id, store_id, destination, url) "
                "VALUES (:id, :store_id, 'unknown', 'https://example.com')"
            ),
            {"id": uuid4(), "store_id": owner.id},
        )
    db_session.rollback()


@pytest.mark.parametrize("store_id", [None, uuid4()])
def test_link_requires_existing_store(db_session, store_id):
    db_session.add(
        Link(store_id=store_id, destination=Destination.GOOGLE, url="https://example.com")
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_link_can_be_deactivated_reactivated_and_have_url_changed(db_session):
    owner = store(db_session)
    link = Link(store_id=owner.id, destination=Destination.INSTAGRAM, url="https://example.com")
    db_session.add(link)
    db_session.commit()
    link.is_active = False
    link.url = "https://example.com/new"
    db_session.commit()
    db_session.refresh(link)
    assert link.is_active is False
    assert link.url == "https://example.com/new"
    link.is_active = True
    db_session.commit()
    assert db_session.scalar(select(Link).where(Link.id == link.id)).is_active is True


def test_link_url_validation_also_applies_to_changes(db_session):
    owner = store(db_session)
    link = Link(store_id=owner.id, destination=Destination.GOOGLE, url="https://example.com")
    db_session.add(link)
    db_session.commit()
    with pytest.raises(ValueError):
        link.url = "javascript:alert(1)"
    db_session.refresh(link)
    assert link.url == "https://example.com/"


def test_same_store_cannot_repeat_destination_even_when_link_is_inactive(db_session):
    owner = store(db_session)
    first = Link(
        store_id=owner.id,
        destination=Destination.WHATSAPP,
        url="https://example.com/first",
        is_active=False,
    )
    db_session.add(first)
    db_session.commit()
    db_session.add(
        Link(store_id=owner.id, destination=Destination.WHATSAPP, url="https://example.com/second")
    )
    with pytest.raises(IntegrityError) as error:
        db_session.commit()
    assert error.value.orig.sqlstate == "23505"
    db_session.rollback()


def test_different_stores_can_use_same_destination(db_session):
    first_owner = store(db_session)
    second_owner = store(db_session)
    db_session.add_all(
        [
            Link(
                store_id=first_owner.id,
                destination=Destination.INSTAGRAM,
                url="https://example.com/first",
            ),
            Link(
                store_id=second_owner.id,
                destination=Destination.INSTAGRAM,
                url="https://example.com/second",
            ),
        ]
    )
    db_session.commit()
    assert len(db_session.scalars(select(Link)).all()) == 2


def test_same_store_can_have_all_destinations(db_session):
    owner = store(db_session)
    for destination in Destination:
        db_session.add(Link(store_id=owner.id, destination=destination, url="https://example.com"))
    db_session.commit()
    assert len(db_session.scalars(select(Link)).all()) == len(Destination)
