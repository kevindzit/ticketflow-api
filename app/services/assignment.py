"""Pick the best technician for a ticket - mirrors TicketFlow's idea:
match on skill, prefer whoever is available right now, then prefer the
lightest workload."""

from datetime import datetime

from app.models import Technician, CalendarEntry


def _is_available(tech, when=None):
    """Available unless they have a busy/out-of-office calendar entry now."""
    when = when or datetime.utcnow()
    conflict = CalendarEntry.query.filter(
        CalendarEntry.technician_id == tech.id,
        CalendarEntry.start_time <= when,
        CalendarEntry.end_time >= when,
        CalendarEntry.status.in_(["busy", "out_of_office"]),
    ).first()
    return conflict is None


def assign_technician(category):
    """Return the best-fit Technician (or None if there are no techs).
    Ranking: skill match first, then availability, then lowest ticket_count."""
    techs = Technician.query.all()
    if not techs:
        return None

    cat = (category or "").lower()

    def rank(t):
        skills = [s.lower() for s in t.get_skills()]
        skill_match = 1 if cat in skills else 0
        available = 1 if _is_available(t) else 0
        return (skill_match, available, -(t.ticket_count or 0))

    return max(techs, key=rank)
