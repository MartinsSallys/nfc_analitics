import subprocess
import time
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def postgres_url():
    """Cria somente um banco descartável; nunca lê o DATABASE_URL do usuário."""
    name = f"nfc-tests-{uuid4().hex[:12]}"
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "--tmpfs",
            "/var/lib/postgresql/data",
            "-e",
            "POSTGRES_USER=nfc_test",
            "-e",
            "POSTGRES_PASSWORD=test_only",
            "-e",
            "POSTGRES_DB=nfc_test",
            "-p",
            "127.0.0.1::5432",
            "postgres:17",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        address = subprocess.check_output(["docker", "port", name, "5432"], text=True).strip()
        port = address.rsplit(":", 1)[1]
        url = f"postgresql+psycopg://nfc_test:test_only@127.0.0.1:{port}/nfc_test"
        engine = create_engine(url)
        try:
            deadline = time.monotonic() + 30
            while True:
                try:
                    with engine.connect() as connection:
                        connection.execute(text("SELECT 1"))
                    break
                except OperationalError:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(0.2)
        finally:
            engine.dispose()
        yield url
    finally:
        subprocess.run(["docker", "rm", "-f", name], check=True, capture_output=True)


@pytest.fixture
def migrated_database(postgres_url, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", postgres_url)
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    command.upgrade(config, "head")
    engine = create_engine(postgres_url)
    try:
        yield engine, config
    finally:
        engine.dispose()
        command.downgrade(config, "base")


@pytest.fixture
def db_session(migrated_database):
    engine, _ = migrated_database
    with Session(engine) as session:
        yield session
