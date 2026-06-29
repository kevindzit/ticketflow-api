"""SQLAlchemy models that map to TicketFlow's existing MySQL tables.
Same table and column names, so this API reads/writes the same database
TicketFlow's dashboard uses. (User/notification tables are omitted - this
service only needs clients, tickets, technicians, calendar, known issues.)"""

import json
from datetime import datetime

from app.core.database import db


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Technician(db.Model):
    __tablename__ = "technicians"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)            # FK to users in TicketFlow; not needed here
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    skills = db.Column(db.Text)                # JSON list stored as text (matches TicketFlow)
    ticket_count = db.Column(db.Integer, default=0)

    def get_skills(self):
        return json.loads(self.skills) if self.skills else []

    def set_skills(self, skill_list):
        self.skills = json.dumps(skill_list)


class CalendarEntry(db.Model):
    __tablename__ = "calendar_entries"

    id = db.Column(db.Integer, primary_key=True)
    technician_id = db.Column(db.Integer, db.ForeignKey("technicians.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="busy")   # busy, out_of_office, free


class KnownIssue(db.Model):
    __tablename__ = "known_issues"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    status = db.Column(db.String(20), default="active")  # active or resolved
    suggested_fix = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default="Medium")   # Low, Medium, High, Critical
    category = db.Column(db.String(50))                     # Network, Hardware, Software, Security, Email, Other
    urgency = db.Column(db.String(20), default="Medium")
    ai_summary = db.Column(db.Text)
    ai_classified = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(30), default="New")       # New, Assigned, In Progress, ...
    assigned_tech_id = db.Column(db.Integer, db.ForeignKey("technicians.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
