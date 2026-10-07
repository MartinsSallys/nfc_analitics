from alembic import command
from sqlalchemy import inspect, text


def test_migrations_match_models_and_are_reversible(migrated_database):
    engine, config = migrated_database
    command.check(config)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0002"
    assert {"stores", "plates"} <= set(inspect(engine).get_table_names())
    command.downgrade(config, "0001")
    assert "stores" in inspect(engine).get_table_names()
    assert "plates" not in inspect(engine).get_table_names()
    command.upgrade(config, "head")
    assert "plates" in inspect(engine).get_table_names()
    command.check(config)
    command.downgrade(config, "base")
    assert "stores" not in inspect(engine).get_table_names()
    assert "plates" not in inspect(engine).get_table_names()
    command.upgrade(config, "head")
    command.check(config)
