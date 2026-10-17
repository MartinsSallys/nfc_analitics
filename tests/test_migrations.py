from alembic import command
from sqlalchemy import inspect, text


def test_migrations_match_models_and_are_reversible(migrated_database):
    engine, config = migrated_database
    command.check(config)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0007"
    assert {"stores", "plates", "links", "events"} <= set(inspect(engine).get_table_names())
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


def test_plate_date_migration_preserves_existing_records(migrated_database):
    from uuid import uuid4

    engine, config = migrated_database
    command.downgrade(config, "0003")
    store_id, plate_id = uuid4(), uuid4()
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO stores (id, name) VALUES (:id, 'Loja existente')"),
            {"id": store_id},
        )
        connection.execute(
            text(
                "INSERT INTO plates (id, store_id, plate_code) "
                "VALUES (:id, :store_id, 'existing-code')"
            ),
            {"id": plate_id, "store_id": store_id},
        )
    command.upgrade(config, "head")
    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT plate_code, updated_at FROM plates WHERE id = :id"), {"id": plate_id}
        ).one()
        assert row.plate_code == "existing-code"
        assert row.updated_at.tzinfo is not None
    command.downgrade(config, "0003")
    with engine.connect() as connection:
        assert (
            connection.scalar(text("SELECT count(*) FROM plates WHERE id = :id"), {"id": plate_id})
            == 1
        )
    command.upgrade(config, "head")
