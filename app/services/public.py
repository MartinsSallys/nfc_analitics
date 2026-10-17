from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Link, Plate, Store
from app.services.plates import PlateUnavailableError


def public_context(session: Session, plate_code: str):
    plate = session.scalar(
        select(Plate)
        .where(Plate.plate_code == plate_code, Plate.is_active.is_(True))
        .with_for_update(read=True)
        .execution_options(populate_existing=True)
    )
    if plate is None:
        raise PlateUnavailableError()
    store = session.scalar(
        select(Store)
        .where(Store.id == plate.store_id, Store.is_active.is_(True))
        .with_for_update(read=True)
        .execution_options(populate_existing=True)
    )
    if store is None:
        raise PlateUnavailableError()
    return plate, store


def active_links(session: Session, store_id):
    return session.scalars(
        select(Link)
        .where(Link.store_id == store_id, Link.is_active.is_(True))
        .order_by(Link.destination)
    ).all()
