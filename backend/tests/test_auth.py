from tests.conftest import auth


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_admin_login_and_me(client, admin_token):
    r = client.get("/api/auth/me", headers=auth(admin_token))
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "ADMIN"
    assert body["username"] == "admin"


def test_client_login(client, client_token):
    r = client.get("/api/auth/me", headers=auth(client_token))
    assert r.status_code == 200
    assert r.json()["role"] == "CLIENT"


def test_wrong_password(client):
    r = client.post("/api/auth/login", json={"username": "lumina", "password": "nope"})
    assert r.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401


def test_admin_login_rejects_client(client):
    r = client.post("/api/auth/admin/login", json={"username": "lumina", "password": "Client@12345"})
    assert r.status_code == 403


def test_refresh(client):
    r = client.post("/api/auth/login", json={"username": "lumina", "password": "Client@12345"})
    refresh = r.json()["refresh_token"]
    r2 = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 200
    assert "access_token" in r2.json()
