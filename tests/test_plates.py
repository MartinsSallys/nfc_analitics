from datetime import UTC, datetime

import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Plate, Store
from app.services.plates import PlateUnavailableError, require_active_plate


def make_plate(session, **fields):
    store = Store(name="Loja da placa")
    session.add(store)
    session.flush()
    plate = Plate(store_id=store.id, **fields)
    session.add(plate)
    session.commit()
    return plate


def test_active_plate_is_available(db_session):
    plate = make_plate(db_session)
    available = require_active_plate(db_session, plate.plate_code)
    assert available.id == plate.id
    assert available.store_id == plate.store_id


def test_inactive_plate_is_unavailable(db_session):
    plate = make_plate(db_session, is_active=False)
    with pytest.raises(PlateUnavailableError):
        require_active_plate(db_session, plate.plate_code)


def test_unknown_plate_is_unavailable(db_session):
    with pytest.raises(PlateUnavailableError):
        require_active_plate(db_session, "unknown-code")


def test_deactivated_plate_is_blocked_even_when_loaded_in_session(db_session):
    plate = make_plate(db_session)
    code = plate.plate_code
    plate_id = plate.id
    assert require_active_plate(db_session, code).id == plate_id
    with Session(db_session.get_bind()) as other_session:
        other_session.execute(update(Plate).where(Plate.id == plate_id).values(is_active=False))
        other_session.commit()
    with pytest.raises(PlateUnavailableError):
        require_active_plate(db_session, code)


def test_plate_updated_at_changes_without_changing_code_or_creation_date(db_session):
    old = datetime(2000, 1, 1, tzinfo=UTC)
    plate = make_plate(db_session, created_at=old, updated_at=old)
    code = plate.plate_code
    plate.name = "Balcão"
    db_session.commit()
    db_session.refresh(plate)
    assert plate.created_at == old
    assert plate.updated_at > old
    assert plate.updated_at.tzinfo is not None
    assert plate.plate_code == code


def test_plate_dates_are_filled_on_creation(db_session):
    plate = make_plate(db_session)
    assert plate.created_at.tzinfo is not None
    assert plate.updated_at.tzinfo is not None
