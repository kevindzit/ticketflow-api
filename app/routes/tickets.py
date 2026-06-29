from flask import Blueprint, request, jsonify

from app.core.database import db
from app.core.auth import require_api_key
from app.services.classifier import classify
from app.services.assignment import assign_technician
from app.models import Client, Ticket

tickets_bp = Blueprint("tickets", __name__)


def _ticket_json(t):
    return {
        "id": t.id,
        "client_id": t.client_id,
        "subject": t.subject,
        "description": t.description,
        "category": t.category,
        "priority": t.priority,
        "status": t.status,
        "ai_summary": t.ai_summary,
        "assigned_tech_id": t.assigned_tech_id,
    }


@tickets_bp.post("/api/tickets")
@require_api_key
def create_ticket():
    """Submit a ticket: classify it, auto-assign a technician, save it."""
    data = request.get_json(silent=True) or {}
    subject = (data.get("subject") or "").strip()
    description = (data.get("description") or "").strip()
    if not subject or not description:
        return jsonify({"error": "subject and description are required"}), 400

    # resolve the client by id, or get-or-create by name
    client_id = data.get("client_id")
    client_name = data.get("client_name")
    if client_id:
        client = db.session.get(Client, client_id)
        if not client:
            return jsonify({"error": f"client_id {client_id} not found"}), 404
    elif client_name:
        client = Client.query.filter_by(name=client_name).first()
        if not client:
            client = Client(name=client_name)
            db.session.add(client)
            db.session.flush()
    else:
        return jsonify({"error": "client_id or client_name is required"}), 400

    result = classify(subject, description)
    tech = assign_technician(result["category"])

    ticket = Ticket(
        client_id=client.id,
        subject=subject,
        description=description,
        category=result["category"],
        priority=result["priority"],
        ai_summary=result["summary"],
        ai_classified=True,
        status="Assigned" if tech else "New",
        assigned_tech_id=tech.id if tech else None,
    )
    db.session.add(ticket)
    if tech:
        tech.ticket_count = (tech.ticket_count or 0) + 1
    db.session.commit()

    return jsonify({
        "ticket": _ticket_json(ticket),
        "classification": result,
        "assigned_to": {"id": tech.id, "name": tech.name} if tech else None,
    }), 201


@tickets_bp.get("/api/tickets")
@require_api_key
def list_tickets():
    tickets = Ticket.query.order_by(Ticket.id.desc()).all()
    return jsonify([_ticket_json(t) for t in tickets])


@tickets_bp.get("/api/tickets/<int:ticket_id>")
@require_api_key
def get_ticket(ticket_id):
    t = db.session.get(Ticket, ticket_id)
    if not t:
        return jsonify({"error": "ticket not found"}), 404
    return jsonify(_ticket_json(t))
