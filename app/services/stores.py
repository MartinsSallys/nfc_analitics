from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Store
from app.schemas.store import StoreCreate


def create_store(session: Session, data: StoreCreate) -> Store:
    store = Store(**data.model_dump())
    session.add(store)
    try:
        session.commit()
        session.refresh(store)
    except Exception:
        session.rollback()
        raise
    return store


def get_store(session: Session, store_id: UUID) -> Store | None:
    return session.get(Store, store_id)
