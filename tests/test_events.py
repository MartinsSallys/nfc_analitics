from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.models import Event, EventType, Plate, Store
from app.services.events import record_event
from app.services.plates import PlateUnavailableError


def make_plate(session):
    store = Store(name="Loja")
    session.add(store)
    session.flush()
    plate = Plate(store_id=store.id)
    session.add(plate)
    session.commit()
    return plate


@pytest.mark.parametrize("event_type", list(EventType))
def test_active_plate_records_event(db_session, event_type):
    plate = make_plate(db_session)
    event = record_event(db_session, plate.plate_code, event_type)
    db_session.commit()
    db_session.refresh(event)
    assert event.plate_id == plate.id
    assert event.event_type == event_type
    assert event.created_at.tzinfo is not None


def test_deactivation_blocks_new_events_and_preserves_history(db_session):
    plate = make_plate(db_session)
    record_event(db_session, plate.plate_code, EventType.PAGE_VIEW)
    db_session.commit()
    plate.is_active = False
    db_session.commit()
    with pytest.raises(PlateUnavailableError):
        record_event(db_session, plate.plate_code, EventType.PAGE_VIEW)
    db_session.rollback()
    assert db_session.scalar(select(func.count()).select_from(Event)) == 1


def test_inactive_plate_rejects_sql_insert(db_session):
    plate = make_plate(db_session)
    plate_id = plate.id
    plate.is_active = False
    db_session.commit()
    with pytest.raises(IntegrityError) as error:
        db_session.execute(
            text(
                "INSERT INTO events (id, plate_id, event_type) VALUES (:id, :plate_id, 'page_view')"
            ),
            {"id": uuid4(), "plate_id": plate_id},
        )
    assert error.value.orig.sqlstate == "23514"
    db_session.rollback()
    assert db_session.scalar(select(func.count()).select_from(Event)) == 0


def test_event_cannot_be_moved_to_inactive_plate(db_session):
    active = make_plate(db_session)
    inactive = make_plate(db_session)
    inactive.is_active = False
    db_session.commit()
    event = record_event(db_session, active.plate_code, EventType.PAGE_VIEW)
    db_session.commit()
    event.plate_id = inactive.id
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_event_requires_existing_plate(db_session):
    db_session.add(Event(plate_id=uuid4(), event_type=EventType.PAGE_VIEW))
    with pytest.raises(IntegrityError) as error:
        db_session.commit()
    assert error.value.orig.sqlstate == "23503"
    db_session.rollback()


def test_database_rejects_unknown_event_type(db_session):
    plate = make_plate(db_session)
    with pytest.raises(IntegrityError):
        db_session.execute(
            text(
                "INSERT INTO events (id, plate_id, event_type) VALUES (:id, :plate_id, 'unknown')"
            ),
            {"id": uuid4(), "plate_id": plate.id},
        )
    db_session.rollback()
