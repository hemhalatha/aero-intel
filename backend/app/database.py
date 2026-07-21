import os
from collections.abc import Generator
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


class DatabaseConfigurationError(RuntimeError):
    pass


class DatabaseConnectionError(RuntimeError):
    pass


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
ENV_FILES = (PROJECT_ROOT / ".env", BACKEND_ROOT / ".env")
DATABASE_ENV_NAME = "DATABASE_URL"
DATABASE_URL_EXAMPLE = "postgresql+psycopg://postgres:YOUR_PASSWORD@127.0.0.1:5432/aerointel"


def load_env_files() -> None:
    for env_file in ENV_FILES:
        if env_file.exists():
            _load_env_file(env_file)


def _load_env_file(path: Path) -> None:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = _strip_env_quotes(value.strip())


def _strip_env_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def get_database_url() -> str:
    load_env_files()
    database_url = os.getenv(DATABASE_ENV_NAME)
    if not database_url:
        raise DatabaseConfigurationError(
            "DATABASE_URL is not configured. Create .env or backend/.env with "
            f"DATABASE_URL={DATABASE_URL_EXAMPLE} and replace YOUR_PASSWORD with your local PostgreSQL password."
        )
    return database_url


def safe_database_url(database_url: str | None = None) -> str:
    value = database_url or os.getenv(DATABASE_ENV_NAME) or ""
    if not value:
        return "<not configured>"
    parts = urlsplit(value)
    if parts.password is None:
        return value
    username = parts.username or ""
    host = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    masked_netloc = f"{username}:***@{host}{port}"
    return urlunsplit((parts.scheme, masked_netloc, parts.path, parts.query, parts.fragment))


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(get_database_url(), pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_session_local() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)


def check_database_connection() -> dict[str, str]:
    database_url = get_database_url()
    try:
        with create_engine(database_url, pool_pre_ping=True).connect() as connection:
            database_name = connection.execute(text("select current_database()")).scalar_one()
            driver_name = connection.engine.dialect.driver
            server_version = str(connection.dialect.server_version_info)
    except OperationalError as exc:
        message = _diagnose_operational_error(exc, database_url)
        raise DatabaseConnectionError(message) from exc
    return {
        "status": "ok",
        "database": database_name,
        "driver": driver_name,
        "server_version": server_version,
        "url": safe_database_url(database_url),
    }


def _diagnose_operational_error(exc: OperationalError, database_url: str) -> str:
    raw = str(exc.orig if getattr(exc, "orig", None) else exc)
    lowered = raw.lower()
    if "password authentication failed" in lowered:
        return (
            "PostgreSQL rejected the configured username/password. Check DATABASE_URL in .env or backend/.env. "
            f"Current URL is {safe_database_url(database_url)}. Keep the password out of source code and replace "
            "YOUR_PASSWORD with your real local PostgreSQL password."
        )
    if "database" in lowered and "does not exist" in lowered:
        return f"PostgreSQL is reachable, but the configured database does not exist. Current URL is {safe_database_url(database_url)}."
    if "connection refused" in lowered or "could not connect" in lowered:
        return f"PostgreSQL is not reachable at the configured host/port. Current URL is {safe_database_url(database_url)}."
    return f"Database connection failed for {safe_database_url(database_url)}: {raw}"


def get_db() -> Generator[Session, None, None]:
    try:
        db = get_session_local()()
    except (DatabaseConfigurationError, OperationalError) as exc:
        raise DatabaseConnectionError(str(exc)) from exc
    try:
        yield db
    finally:
        db.close()
