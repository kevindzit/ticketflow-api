"""OpenAPI spec + a Swagger UI page at /docs (loads Swagger UI from a CDN,
so no extra Python dependency)."""

from flask import Blueprint, jsonify, Response

docs_bp = Blueprint("docs", __name__)

OPENAPI = {
    "openapi": "3.0.0",
    "info": {
        "title": "TicketFlow API",
        "version": "0.1.0",
        "description": "REST API for the TicketFlow ticket-triage system.",
    },
    "components": {
        "securitySchemes": {
            "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"}
        }
    },
    "paths": {
        "/api/health": {
            "get": {"summary": "Health check", "responses": {"200": {"description": "OK"}}}
        },
        "/api/tickets": {
            "get": {
                "summary": "List tickets",
                "security": [{"ApiKeyAuth": []}],
                "responses": {"200": {"description": "List of tickets"}},
            },
            "post": {
                "summary": "Create a ticket (classify + auto-assign)",
                "security": [{"ApiKeyAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {
                            "subject": {"type": "string"},
                            "description": {"type": "string"},
                            "client_name": {"type": "string"},
                            "client_id": {"type": "integer"},
                        },
                        "required": ["subject", "description"],
                    }}},
                },
                "responses": {
                    "201": {"description": "Created"},
                    "400": {"description": "Bad request"},
                    "401": {"description": "Unauthorized"},
                },
            },
        },
        "/api/tickets/{id}": {
            "get": {
                "summary": "Get a ticket by id",
                "security": [{"ApiKeyAuth": []}],
                "parameters": [{"name": "id", "in": "path", "required": True,
                                "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "Ticket"},
                              "404": {"description": "Not found"}},
            }
        },
        "/api/technicians": {
            "get": {
                "summary": "List technicians",
                "security": [{"ApiKeyAuth": []}],
                "responses": {"200": {"description": "List of technicians"}},
            }
        },
    },
}


@docs_bp.get("/api/openapi.json")
def openapi():
    return jsonify(OPENAPI)


SWAGGER_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>TicketFlow API docs</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({ url: '/api/openapi.json', dom_id: '#swagger' });
  </script>
</body>
</html>"""


@docs_bp.get("/docs")
def docs():
    return Response(SWAGGER_HTML, mimetype="text/html")
