from flask import Flask

from app.core.config import Config
from app.core.database import db
from app.routes.health import health_bp
from app.routes.tickets import tickets_bp
from app.routes.technicians import technicians_bp
from app.routes.docs import docs_bp


def create_app(config_class=Config):
    """App factory - builds and returns the Flask app."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # import models so SQLAlchemy registers the tables
    from app import models  # noqa: F401

    app.register_blueprint(health_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(technicians_bp)
    app.register_blueprint(docs_bp)
    return app
