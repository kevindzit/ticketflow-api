import os


class Config:
    """All config in one spot, read from environment variables."""
    APP_VERSION = os.environ.get("APP_VERSION", "0.1.0")
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "local")
    API_KEY = os.environ.get("API_KEY", "dev-key")

    # Point DATABASE_URL at TicketFlow's MySQL to share the same data
    # (e.g. mysql+pymysql://user:pass@host/ticketflow). Falls back to a local
    # SQLite file so the API runs with zero setup for dev and tests.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///ticketflow_api.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
