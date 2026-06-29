"""Shared pytest fixtures.

Tests run against a throwaway SQLite file and force the rule-based classifier,
so they need no MySQL and no Ollama - they pass anywhere, including CI.
"""

import json
import os
import tempfile

import pytest

# force the deterministic rule-based classifier for tests
os.environ["CLASSIFIER"] = "rule"

_DB_PATH = os.path.join(tempfile.gettempdir(), "ticketflow_api_test.db")


class TestConfig:
    APP_VERSION = "test"
    ENVIRONMENT = "test"
    API_KEY = "test-key"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{_DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


@pytest.fixture
def app():
    if os.path.exists(_DB_PATH):
        os.remove(_DB_PATH)

    from app import create_app
    from app.core.database import db
    from app.models import Technician

    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        db.session.add_all([
            Technician(user_id=1, name="Jason Thomas", email="j@x.com",
                       skills=json.dumps(["network", "security"]), ticket_count=2),
            Technician(user_id=2, name="Sarah Mueller", email="s@x.com",
                       skills=json.dumps(["hardware"]), ticket_count=0),
        ])
        db.session.commit()

    yield application

    if os.path.exists(_DB_PATH):
        os.remove(_DB_PATH)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth():
    return {"X-API-Key": "test-key"}
