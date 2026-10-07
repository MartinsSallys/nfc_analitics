from app.core.config import Settings


def test_database_url_comes_from_environment(monkeypatch):
    url = "postgresql+psycopg://test:test@localhost/test_database"
    monkeypatch.setenv("DATABASE_URL", url)
    assert Settings(_env_file=None).database_url == url
