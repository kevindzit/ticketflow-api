from flask import Blueprint, jsonify

from app.core.auth import require_api_key
from app.models import Technician

technicians_bp = Blueprint("technicians", __name__)


@technicians_bp.get("/api/technicians")
@require_api_key
def list_technicians():
    techs = Technician.query.all()
    return jsonify([
        {
            "id": t.id,
            "name": t.name,
            "email": t.email,
            "skills": t.get_skills(),
            "ticket_count": t.ticket_count,
        }
        for t in techs
    ])
