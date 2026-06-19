import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.db import execute_script, test_connection

SCHEMA_PATH = BASE_DIR.parent / "sql" / "schema.sql"
SEED_PATH = BASE_DIR.parent / "sql" / "seed.sql"


def load_sql(file_path: Path) -> str:
    if not file_path.exists():
        raise FileNotFoundError(f"SQL file not found: {file_path}")
    return file_path.read_text(encoding="utf-8")


def init_database(schema_path: Path = SCHEMA_PATH, seed_path: Path = SEED_PATH) -> None:
    schema_sql = load_sql(schema_path)
    seed_sql = load_sql(seed_path)

    execute_script(schema_sql)
    execute_script(seed_sql)


def main() -> None:
    print("Checking database connection...")
    if not test_connection():
        print("Database connection failed.")
        print("Please verify DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD.")
        return

    print("Connection successful. Running schema.sql...")
    print(f"Schema file: {SCHEMA_PATH}")
    print("Running seed.sql...")
    print(f"Seed file: {SEED_PATH}")

    init_database()
    print("Database initialization completed successfully.")


if __name__ == "__main__":
    main()
