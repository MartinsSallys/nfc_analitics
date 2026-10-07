from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Plate, Store


def make_store(session):
    store = Store(name="Loja teste")
    session.add(store)
    session.flush()
    return store


def test_store_defaults_and_optional_fields_persist(db_session):
    store = make_store(db_session)
    db_session.commit()
    store_id = store.id
    db_session.expunge_all()
    saved = db_session.get(Store, store_id)
    assert isinstance(saved.id, UUID)
    assert saved.name == "Loja teste"
    assert saved.description is None
    assert saved.logo_url is None
    assert saved.is_active is True
    assert saved.created_at.tzinfo is not None


def test_store_description_logo_and_deactivation_persist(db_session):
    store = Store(
        name="Loja", description="Descrição", logo_url="/uploads/loja.png", is_active=False
    )
    db_session.add(store)
    db_session.commit()
    db_session.refresh(store)
    assert store.description == "Descrição"
    assert store.logo_url == "/uploads/loja.png"
    assert store.is_active is False


def test_store_requires_name(db_session):
    db_session.add(Store(name=None))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_store_can_have_multiple_plates_with_generated_codes(db_session):
    store = make_store(db_session)
    first = Plate(store_id=store.id, name="Balcão")
    second = Plate(store_id=store.id)
    db_session.add_all([first, second])
    db_session.commit()
    plates = db_session.scalars(select(Plate).where(Plate.store_id == store.id)).all()
    assert len(plates) == 2
    assert first.plate_code != second.plate_code
    for plate in plates:
        assert isinstance(plate.id, UUID)
        assert plate.plate_code
        assert all(char.isalnum() or char in "-_" for char in plate.plate_code)
        assert plate.is_active is True
        assert plate.created_at.tzinfo is not None
    assert second.name is None


def test_plate_code_survives_rename_and_deactivation(db_session):
    store = make_store(db_session)
    plate = Plate(store_id=store.id, name="Balcão")
    db_session.add(plate)
    db_session.commit()
    original_code = plate.plate_code
    plate.name = "Entrada"
    plate.is_active = False
    db_session.commit()
    db_session.refresh(plate)
    assert plate.plate_code == original_code
    assert plate.name == "Entrada"
    assert plate.is_active is False


def test_plate_code_is_unique_across_stores(db_session):
    first_store = make_store(db_session)
    second_store = make_store(db_session)
    db_session.add(Plate(store_id=first_store.id, plate_code="same-code"))
    db_session.commit()
    db_session.add(Plate(store_id=second_store.id, plate_code="same-code"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.parametrize("store_id", [None, uuid4()])
def test_plate_requires_existing_store(db_session, store_id):
    db_session.add(Plate(store_id=store_id))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_store_with_plate_cannot_be_deleted_accidentally(db_session):
    store = make_store(db_session)
    db_session.add(Plate(store_id=store.id))
    db_session.commit()
    db_session.delete(store)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
