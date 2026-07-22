from pathlib import Path

from sqlalchemy import create_engine

from app.database import get_database_url, safe_database_url


MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "database" / "migrations"


def migration_files() -> list[Path]:
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def apply_migrations() -> None:
    files = migration_files()
    if not files:
        raise RuntimeError(f"No migration files found in {MIGRATIONS_DIR}")

    database_url = get_database_url()
    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.begin() as connection:
        for migration in files:
            print(f"Applying {migration.name}...")
            connection.exec_driver_sql(migration.read_text(encoding="utf-8"))

    print(f"Applied {len(files)} migrations to {safe_database_url(database_url)}")


def main() -> int:
    apply_migrations()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

