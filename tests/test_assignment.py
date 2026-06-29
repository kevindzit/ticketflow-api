from app.services.assignment import assign_technician


def test_assigns_by_skill_match(app):
    with app.app_context():
        tech = assign_technician("Network")
        assert tech is not None
        assert tech.name == "Jason Thomas"   # has the "network" skill


def test_hardware_goes_to_sarah(app):
    with app.app_context():
        tech = assign_technician("Hardware")
        assert tech.name == "Sarah Mueller"
