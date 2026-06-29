def test_health_is_open(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_create_requires_api_key(client):
    resp = client.post("/api/tickets",
                       json={"subject": "a", "description": "b", "client_name": "c"})
    assert resp.status_code == 401


def test_create_ticket_classifies_and_assigns(client, auth):
    resp = client.post("/api/tickets", headers=auth, json={
        "client_name": "Acme Co",
        "subject": "VPN is down",
        "description": "office outage, urgent",
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["ticket"]["category"] == "Network"
    assert data["ticket"]["priority"] == "Critical"
    assert data["ticket"]["status"] == "Assigned"
    assert data["assigned_to"]["name"] == "Jason Thomas"


def test_create_validates_input(client, auth):
    resp = client.post("/api/tickets", headers=auth, json={"subject": ""})
    assert resp.status_code == 400


def test_list_tickets(client, auth):
    client.post("/api/tickets", headers=auth, json={
        "client_name": "Acme Co", "subject": "laptop won't boot",
        "description": "battery error"})
    resp = client.get("/api/tickets", headers=auth)
    assert resp.status_code == 200
    assert len(resp.get_json()) >= 1
