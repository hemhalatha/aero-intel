import pytest

from app import database


def test_database_url_comes_from_environment(monkeypatch) -> None:
    expected = "postgresql+psycopg://postgres:secret@127.0.0.1:5432/aerointel"

    monkeypatch.setenv("DATABASE_URL", expected)
    monkeypatch.setattr(database, "ENV_FILES", ())

    assert database.get_database_url() == expected


def test_missing_database_url_has_actionable_message(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(database, "ENV_FILES", ())

    with pytest.raises(database.DatabaseConfigurationError) as exc_info:
        database.get_database_url()

    message = str(exc_info.value)
    assert "DATABASE_URL is not configured" in message
    assert "YOUR_PASSWORD" in message
    assert "aerointel" in message


def test_safe_database_url_masks_password() -> None:
    masked = database.safe_database_url(
        "postgresql+psycopg://postgres:super-secret@127.0.0.1:5432/aerointel"
    )

    assert masked == "postgresql+psycopg://postgres:***@127.0.0.1:5432/aerointel"
    assert "super-secret" not in masked