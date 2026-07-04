"""Pytest fixtures — isolated SQLite DB seeded with demo data."""
import os
import pathlib

os.environ["DATABASE_URL"] = "sqlite:///./test_crux.db"
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["RATE_LIMIT_PER_MINUTE"] = "100000"

_db = pathlib.Path("./test_crux.db")
if _db.exists():
    _db.unlink()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import init_db  # noqa: E402
from app.main import app  # noqa: E402
from app import seed  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _prepare_db():
    init_db()
    seed.run()
    yield
    if _db.exists():
        _db.unlink()


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def admin_token(client):
    r = client.post("/api/auth/admin/login", json={"username": "admin", "password": "Admin@12345"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture()
def client_token(client):
    r = client.post("/api/auth/login", json={"username": "lumina", "password": "Client@12345"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
