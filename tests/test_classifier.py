from app.services.classifier import classify


def test_security_is_critical():
    r = classify("Ransomware breach", "files are encrypted")
    assert r["category"] == "Security"
    assert r["priority"] == "Critical"
    assert r["classified_by"] == "rules"


def test_network_outage():
    r = classify("VPN is down", "whole office outage")
    assert r["category"] == "Network"
    assert r["priority"] == "Critical"


def test_hardware_medium():
    r = classify("printer is slow", "intermittent")
    assert r["category"] == "Hardware"
    assert r["priority"] == "Medium"


def test_plain_question_is_low():
    r = classify("question about policy", "")
    assert r["category"] == "Other"
    assert r["priority"] == "Low"
