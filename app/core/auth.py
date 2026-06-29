"""Simple API-key auth for service-to-service calls.
Send the key in the X-API-Key header. The expected key comes from config
(API_KEY env var; in Kubernetes it's injected from a Secret)."""

from functools import wraps

from flask import request, jsonify, current_app


def require_api_key(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-Key")
        if not key or key != current_app.config["API_KEY"]:
            return jsonify({"error": "missing or invalid API key"}), 401
        return view(*args, **kwargs)
    return wrapper
