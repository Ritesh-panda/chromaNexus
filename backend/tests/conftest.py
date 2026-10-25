import os
import sys
import tempfile
import shutil
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.app.core.database import Base, get_db
from backend.app.core.config import settings
from backend.app.services.seed_data import seed_initial_data
from backend.app.main import app


@pytest.fixture(scope="session")
def test_isolation_env():
    """
    Session-level fixture providing isolated temporary SQLite and ChromaDB paths.
    Guarantees zero writes reach production databases or persistent vector store.
    """
    temp_dir = tempfile.mkdtemp(prefix="chronanexus_test_env_")
    temp_db_path = os.path.join(temp_dir, "test_isolated.db")
    temp_chroma_dir = os.path.join(temp_dir, "test_chroma")
    os.makedirs(temp_chroma_dir, exist_ok=True)

    orig_db_url = settings.DATABASE_URL
    orig_chroma_dir = settings.CHROMA_PERSIST_DIRECTORY
    orig_coll_name = settings.CHROMA_COLLECTION_NAME

    test_db_url = f"sqlite:///{temp_db_path.replace(os.sep, '/')}"
    settings.DATABASE_URL = test_db_url
    settings.CHROMA_PERSIST_DIRECTORY = temp_chroma_dir
    settings.CHROMA_COLLECTION_NAME = "test_clinical_chunks"

    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    app.state.engine = engine
    app.state.session_factory = TestingSessionLocal

    yield {
        "engine": engine,
        "session_factory": TestingSessionLocal,
        "temp_dir": temp_dir,
        "db_path": temp_db_path,
        "chroma_dir": temp_chroma_dir
    }

    # Teardown
    settings.DATABASE_URL = orig_db_url
    settings.CHROMA_PERSIST_DIRECTORY = orig_chroma_dir
    settings.CHROMA_COLLECTION_NAME = orig_coll_name
    if hasattr(app.state, "engine"):
        del app.state.engine
    if hasattr(app.state, "session_factory"):
        del app.state.session_factory

    engine.dispose()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def db_session(test_isolation_env):
    """
    Provides a clean, seeded database session for each test function,
    isolated completely from production databases.
    """
    engine = test_isolation_env["engine"]
    TestingSessionLocal = test_isolation_env["session_factory"]

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    seed_initial_data(session)
    session.close()

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session, test_isolation_env):
    """
    FastAPI TestClient with complete dependency overrides and isolated app.state.
    """
    TestingSessionLocal = test_isolation_env["session_factory"]

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
