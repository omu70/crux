from tests.conftest import auth


def test_dashboard_summary(client, client_token):
    r = client.get("/api/dashboard/summary", headers=auth(client_token))
    assert r.status_code == 200
    body = r.json()
    assert body["greeting"] in {"Good Morning", "Good Afternoon", "Good Evening"}
    assert body["client"]["company_name"] == "Lumina Skincare"
    assert len(body["kpis"]) == 17  # all KPI cards present


def test_kpis_and_timeseries(client, client_token):
    r = client.get("/api/dashboard/kpis?range=7d", headers=auth(client_token))
    assert r.status_code == 200
    r2 = client.get("/api/dashboard/timeseries?metrics=revenue,orders&range=30d", headers=auth(client_token))
    assert r2.status_code == 200
    assert len(r2.json()["series"]) > 0


def test_marketing_endpoints(client, client_token):
    for path in ["/api/marketing/campaigns", "/api/marketing/ecommerce",
                 "/api/marketing/analytics", "/api/marketing/search-console", "/api/marketing/seo"]:
        assert client.get(path, headers=auth(client_token)).status_code == 200


def test_insights_and_plan(client, client_token):
    r = client.get("/api/insights", headers=auth(client_token))
    assert r.status_code == 200 and len(r.json()) > 0
    assert client.get("/api/insights/plan", headers=auth(client_token)).status_code == 200


def test_collab_endpoints(client, client_token):
    for path in ["/api/tasks", "/api/goals", "/api/notifications", "/api/documents",
                 "/api/tickets", "/api/chat", "/api/meeting-notes"]:
        assert client.get(path, headers=auth(client_token)).status_code == 200


def test_admin_overview(client, admin_token):
    r = client.get("/api/admin/overview", headers=auth(admin_token))
    assert r.status_code == 200
    assert r.json()["clients"]["total"] >= 2


def test_client_cannot_access_admin(client, client_token):
    assert client.get("/api/admin/overview", headers=auth(client_token)).status_code == 403


def test_admin_client_lifecycle(client, admin_token):
    payload = {"company_name": "Test Co", "contact_name": "Tester", "username": "testco",
               "password": "Passw0rd!", "email": "[email protected]"}
    r = client.post("/api/admin/clients", json=payload, headers=auth(admin_token))
    assert r.status_code == 201, r.text
    cid = r.json()["id"]

    # suspend then login should fail with 403 on client routes
    assert client.post(f"/api/admin/clients/{cid}/suspend", headers=auth(admin_token)).status_code == 200
    tok = client.post("/api/auth/login", json={"username": "testco", "password": "Passw0rd!"}).json()["access_token"]
    assert client.get("/api/dashboard/summary", headers=auth(tok)).status_code == 403

    assert client.delete(f"/api/admin/clients/{cid}", headers=auth(admin_token)).status_code == 200
