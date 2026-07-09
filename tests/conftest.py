import sys
import os

# Make project root importable from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base
from db.session import get_db
from api.main import app

TEST_DB_URL = "sqlite:///./test_visa_flow.db"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_visa_flow.db"):
        os.remove("test_visa_flow.db")


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def new_application(client):
    """Create a fresh application and return its id."""
    res = client.post("/api/application/start")
    assert res.status_code == 200
    data = res.json()
    app_id = data["application_id"]
    # Set destination to japan
    client.patch(f"/api/application/{app_id}/destination", json={"destination": "japan"})
    return app_id
