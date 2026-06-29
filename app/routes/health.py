from flask import Blueprint, jsonify, current_app

# Kubernetes calls this to check the service is alive and ready.
health_bp = Blueprint("health", __name__)


@health_bp.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "version": current_app.config["APP_VERSION"],
        "environment": current_app.config["ENVIRONMENT"],
    })
