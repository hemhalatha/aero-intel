from app.database import DatabaseConfigurationError, DatabaseConnectionError, check_database_connection


def main() -> int:
    try:
        result = check_database_connection()
    except DatabaseConfigurationError as exc:
        print(f"Database configuration error: {exc}")
        return 2
    except DatabaseConnectionError as exc:
        print(f"Database connection failed: {exc}")
        return 1

    print("Database connection succeeded.")
    print(f"Database: {result['database']}")
    print(f"Driver: {result['driver']}")
    print(f"Server version: {result['server_version']}")
    print(f"URL: {result['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())