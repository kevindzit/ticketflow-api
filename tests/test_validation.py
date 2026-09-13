import json
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.core.database import db
from app.models import Client, Ticket, Technician


@pytest.fixture
def ticket_data():
    return {
        "client_name": "Acme Co",
        "subject": "VPN is down",
        "description": "whole office outage",
    }


def assert_nothing_saved(app):
    with app.app_context():
        assert Ticket.query.count() == 0
        assert Client.query.count() == 0
        assert sum(tech.ticket_count for tech in Technician.query.all()) == 2


@pytest.mark.parametrize("body", [None, [], [{"subject": "VPN"}], "text", 42, True])
def test_body_must_be_a_json_object(client, app, auth, body):
    resp = client.post("/api/tickets", headers=auth,
                       data=json.dumps(body), content_type="application/json")
    assert resp.status_code == 400
    assert isinstance(resp.get_json()["error"], str)
    assert_nothing_saved(app)


@pytest.mark.parametrize("body, content_type", [
    ("{", "application/json"),
    ("", "application/json"),
    ('{"subject":"VPN"}', "text/plain"),
])
def test_invalid_json_request_is_rejected(client, app, auth, body, content_type):
    resp = client.post("/api/tickets", headers=auth,
                       data=body, content_type=content_type)
    assert resp.status_code == 400
    assert isinstance(resp.get_json()["error"], str)
    assert_nothing_saved(app)


@pytest.mark.parametrize("field", ["subject", "description"])
@pytest.mark.parametrize("value", [42, True, None, ["text"], {"text": "value"}, "", "   "])
def test_ticket_text_must_be_nonempty_strings(client, app, auth, ticket_data, field, value):
    ticket_data[field] = value
    resp = client.post("/api/tickets", headers=auth, json=ticket_data)
    assert resp.status_code == 400
    assert isinstance(resp.get_json()["error"], str)
    assert_nothing_saved(app)


def test_subject_cannot_exceed_database_limit(client, app, auth, ticket_data):
    ticket_data["subject"] = "x" * 201
    resp = client.post("/api/tickets", headers=auth, json=ticket_data)
    assert resp.status_code == 400
    assert_nothing_saved(app)


@pytest.mark.parametrize("fields", [
    {"client_id": True},
    {"client_id": "1"},
    {"client_id": [1]},
    {"client_id": 0},
    {"client_id": -1},
    {"client_id": 2 ** 63},
    {"client_id": None},
    {"client_name": 42},
    {"client_name": ["Acme"]},
    {"client_name": None},
    {"client_name": "   "},
    {"client_name": "x" * 101},
])
def test_invalid_client_fields_are_rejected(client, app, auth, ticket_data, fields):
    ticket_data.update(fields)
    resp = client.post("/api/tickets", headers=auth, json=ticket_data)
    assert resp.status_code == 400
    assert isinstance(resp.get_json()["error"], str)
    assert_nothing_saved(app)


def test_client_selector_is_required(client, app, auth, ticket_data):
    del ticket_data["client_name"]
    resp = client.post("/api/tickets", headers=auth, json=ticket_data)
    assert resp.status_code == 400
    assert_nothing_saved(app)


def test_unknown_client_id_does_not_create_a_client(client, app, auth, ticket_data):
    ticket_data["client_id"] = 123
    resp = client.post("/api/tickets", headers=auth, json=ticket_data)
    assert resp.status_code == 404
    assert_nothing_saved(app)


def test_existing_client_id_takes_precedence(client, app, auth, ticket_data):
    with app.app_context():
        existing = Client(name="Existing client")
        db.session.add(existing)
        db.session.commit()
        client_id = existing.id

    ticket_data["client_id"] = client_id
    resp = client.post("/api/tickets", headers=auth, json=ticket_data)
    assert resp.status_code == 201
    assert resp.get_json()["ticket"]["client_id"] == client_id
    with app.app_context():
        assert Client.query.count() == 1
        assert Client.query.one().name == "Existing client"


def test_valid_text_is_trimmed_and_length_limits_are_inclusive(client, app, auth, ticket_data):
    ticket_data.update({
        "subject": "  " + "x" * 200 + "  ",
        "description": "  Details here  ",
        "client_name": "  " + "c" * 100 + "  ",
    })
    resp = client.post("/api/tickets", headers=auth, json=ticket_data)
    assert resp.status_code == 201
    ticket = resp.get_json()["ticket"]
    assert ticket["subject"] == "x" * 200
    assert ticket["description"] == "Details here"
    with app.app_context():
        assert Client.query.one().name == "c" * 100


@pytest.fixture
def ollama_chat(monkeypatch):
    # exercise the model path without installing Ollama or making network calls
    chat = Mock()
    monkeypatch.setitem(sys.modules, "ollama", SimpleNamespace(chat=chat))
    monkeypatch.setenv("CLASSIFIER", "auto")
    return chat


@pytest.mark.parametrize("content", [
    "not JSON",
    "[]",
    "null",
    json.dumps({"category": "Unknown", "priority": "Low", "summary": "A ticket."}),
    json.dumps({"category": "Network", "priority": "Urgent", "summary": "A ticket."}),
    json.dumps({"category": ["Network"], "priority": "Low", "summary": "A ticket."}),
    json.dumps({"category": "Network", "priority": 1, "summary": "A ticket."}),
    json.dumps({"category": "Network", "priority": "Low", "summary": {"text": "A ticket."}}),
    json.dumps({"category": "Network", "priority": "Low", "summary": "   "}),
    json.dumps({"priority": "Low", "summary": "A ticket."}),
    json.dumps({"category": "Network", "summary": "A ticket."}),
    json.dumps({"category": "Network", "priority": "Low"}),
])
def test_invalid_model_output_uses_rules(client, app, auth, ticket_data, ollama_chat, content):
    ollama_chat.return_value = {"message": {"content": content}}
    resp = client.post("/api/tickets", headers=auth, json=ticket_data)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["classification"]["classified_by"] == "rules"
    assert data["ticket"]["category"] == "Network"
    assert data["ticket"]["priority"] == "Critical"
    assert data["ticket"]["ai_summary"] == "Network issue, critical priority (auto-classified)."
    assert data["assigned_to"]["name"] == "Jason Thomas"
    ollama_chat.assert_called_once()
    with app.app_context():
        saved = Ticket.query.one()
        assert saved.category == "Network"
        assert saved.priority == "Critical"
        assert saved.ai_summary == data["ticket"]["ai_summary"]
        assert db.session.get(Technician, saved.assigned_tech_id).ticket_count == 3


@pytest.mark.parametrize("mode, category, priority", [
    ("auto", "Network", "High"),
    ("ollama", "Other", "Low"),
])
def test_valid_model_output_is_preserved(client, app, auth, ticket_data, ollama_chat,
                                         monkeypatch, mode, category, priority):
    monkeypatch.setenv("CLASSIFIER", mode)
    ollama_chat.return_value = {"message": {"content": json.dumps({
        "category": " " + category + " ",
        "priority": " " + priority + " ",
        "summary": " The VPN needs investigation. ",
    })}}
    resp = client.post("/api/tickets", headers=auth, json=ticket_data)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["classification"]["classified_by"] == "ollama"
    assert data["ticket"]["category"] == category
    assert data["ticket"]["priority"] == priority
    assert data["ticket"]["ai_summary"] == "The VPN needs investigation."
    ollama_chat.assert_called_once()
    with app.app_context():
        saved = Ticket.query.one()
        assert saved.category == category
        assert saved.priority == priority


@pytest.mark.parametrize("mode", ["auto", "ollama"])
def test_unavailable_model_still_uses_rules(client, auth, ticket_data, ollama_chat, monkeypatch, mode):
    monkeypatch.setenv("CLASSIFIER", mode)
    ollama_chat.side_effect = RuntimeError("model unavailable")
    resp = client.post("/api/tickets", headers=auth, json=ticket_data)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["classification"]["classified_by"] == "rules"
    assert data["ticket"]["category"] == "Network"
    assert data["ticket"]["priority"] == "Critical"
    ollama_chat.assert_called_once()
