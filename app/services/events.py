from sqlalchemy.orm import Session

from app.models import Event, EventType
from app.services.plates import require_active_plate


def record_event(session: Session, plate_code: str, event_type: EventType) -> Event:
    """Prepara o evento; o chamador controla commit/rollback da transação."""
    plate = require_active_plate(session, plate_code)
    event = Event(plate_id=plate.id, event_type=event_type)
    session.add(event)
    session.flush()
    return event
