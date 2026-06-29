"""Seed some demo data so the API has something to work with locally.

Run:  python scripts/seed_demo_data.py

Creates the tables (handy for SQLite/dev) and inserts a few clients,
technicians, a calendar entry, a known issue, and a sample ticket.
Safe to run twice - it skips if data already exists.
"""

import json
import os
import sys
from datetime import datetime, timedelta

# make the project root importable when running this file directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.core.database import db
from app.models import Client, Technician, CalendarEntry, KnownIssue, Ticket

app = create_app()

with app.app_context():
    db.create_all()

    if Technician.query.first():
        print("Data already present - skipping seed.")
    else:
        clients = [
            Client(name="Cremation Society of Illinois"),
            Client(name="Hyde Park Office"),
            Client(name="Crystal Lake Clinic"),
        ]
        db.session.add_all(clients)
        db.session.flush()  # assigns ids

        techs = [
            Technician(user_id=1, name="Jason Thomas", email="jason@jatag.com",
                       skills=json.dumps(["network", "security", "windows"]), ticket_count=2),
            Technician(user_id=2, name="Sarah Mueller", email="sarah@jatag.com",
                       skills=json.dumps(["hardware", "printers", "macos"]), ticket_count=0),
            Technician(user_id=3, name="Kurt Romano", email="kurt@jatag.com",
                       skills=json.dumps(["account", "email", "m365"]), ticket_count=1),
        ]
        db.session.add_all(techs)
        db.session.flush()

        now = datetime.utcnow()
        db.session.add(CalendarEntry(
            technician_id=techs[0].id, title="On site - Hyde Park",
            start_time=now, end_time=now + timedelta(hours=2), status="busy"))

        db.session.add(KnownIssue(
            title="Outlook certificate error",
            description="Users see a certificate warning when opening Outlook.",
            category="Email", status="active",
            suggested_fix="Remove cached credentials and re-add the account."))

        db.session.add(Ticket(
            client_id=clients[0].id, subject="VPN is down",
            description="Whole office cannot connect to the VPN.",
            priority="High", category="Network", status="New"))

        db.session.commit()
        print("Seeded demo data.")
