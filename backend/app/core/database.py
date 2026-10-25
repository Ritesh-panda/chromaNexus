import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

# Canonical protected database files (case-insensitive normalized paths)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROTECTED_DB_PATHS = {
    os.path.abspath(str(_PROJECT_ROOT / "chronanexus.db")).lower(),
    os.path.abspath(str(_PROJECT_ROOT / "backend" / "chronanexus.db")).lower()
}

_MUTATION_KEYWORDS = ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE")


@event.listens_for(Engine, "before_cursor_execute")
def enforce_protected_database_isolation(conn, cursor, statement, parameters, context, executemany):
    """
    Prevents tests from mutating production or root chronanexus.db databases.
    If running under pytest or test environment, any write query targeting a protected
    database path raises a fatal RuntimeError immediately before execution.
    """
    is_test_env = bool(
        os.environ.get("PYTEST_CURRENT_TEST") or
        os.environ.get("CHRONANEXUS_TEST_ENV")
    )
    if not is_test_env:
        return

    stmt_clean = statement.strip().upper() if isinstance(statement, str) else ""
    if not any(stmt_clean.startswith(kw) for kw in _MUTATION_KEYWORDS):
        return

    raw_url = str(conn.engine.url) if conn and hasattr(conn, "engine") else ""
    if "sqlite" in raw_url:
        db_file = conn.engine.url.database
        if db_file:
            abs_db_file = os.path.abspath(db_file).lower()
            if abs_db_file in PROTECTED_DB_PATHS or os.path.basename(abs_db_file) == "chronanexus.db":
                raise RuntimeError(
                    f"CRITICAL TEST ISOLATION FAILURE: Prohibited mutation query ({stmt_clean.split()[0]}) "
                    f"attempted against protected database file: {abs_db_file}. "
                    "Tests MUST use an isolated in-memory or temporary SQLite database."
                )


# Engine configuration (SQLite requires check_same_thread=False)
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    is_test_env = bool(
        os.environ.get("PYTEST_CURRENT_TEST") or
        os.environ.get("CHRONANEXUS_TEST_ENV")
    )
    if is_test_env:
        raw_url = str(engine.url)
        if "sqlite" in raw_url and engine.url.database:
            abs_path = os.path.abspath(engine.url.database).lower()
            if abs_path in PROTECTED_DB_PATHS or os.path.basename(abs_path) == "chronanexus.db":
                raise RuntimeError(
                    f"CRITICAL TEST ISOLATION FAILURE: Un-overridden get_db() called during test execution "
                    f"resolving to protected database: {abs_path}. "
                    "Tests must provide an isolated get_db dependency override."
                )

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
