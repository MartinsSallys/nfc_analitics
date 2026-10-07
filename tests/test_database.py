from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import create_session_factory
from app.models import Store


def test_session_factory_connects_using_environment(migrated_database):
    factory = create_session_factory(Settings(_env_file=None))
    engine = factory.kw["bind"]
    try:
        with factory() as session:
            assert isinstance(session, Session)
            assert session.scalar(text("SELECT 1")) == 1
            session.add(Store(name="Loja via fábrica de sessões"))
            session.commit()
        with factory() as session:
            saved = session.scalar(select(Store))
            assert saved.name == "Loja via fábrica de sessões"
    finally:
        engine.dispose()
