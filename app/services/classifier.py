"""Pluggable ticket classifier.

Tries an LLM (Ollama / Llama 3.1) when it's available, and falls back to fast
rule-based logic when it isn't or returns invalid output. The service runs and
tests anywhere (laptop, Kubernetes, CI). To enable the LLM path: `pip install ollama` and have
Ollama running with the model pulled. Otherwise it uses the rules automatically.

Categories and priorities match TicketFlow's values so results line up with the
dashboard.
"""

import json
import os

# keyword -> category (checked in order; first match wins)
CATEGORIES = {
    "Security": ["breach", "ransomware", "phishing", "malware", "virus", "hacked"],
    "Network": ["vpn", "wifi", "network", "internet", "dns", "outage", "connection"],
    "Email": ["outlook", "email", "exchange", "smtp", "mailbox", "m365", "office 365"],
    "Hardware": ["laptop", "monitor", "printer", "device", "battery", "screen", "keyboard"],
    "Software": ["install", "application", "app crash", "update", "license", "software"],
}

VALID_CATEGORIES = set(CATEGORIES) | {"Other"}
VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}

CRITICAL = ["breach", "ransomware", "data loss", "down", "outage", "critical"]
HIGH = ["urgent", "cannot", "can't", "asap", "locked", "security"]
MEDIUM = ["slow", "error", "failing", "intermittent", "degraded"]


class RuleBasedClassifier:
    name = "rules"

    def classify(self, subject, description):
        text = f"{subject} {description}".lower()

        category = "Other"
        for cat, words in CATEGORIES.items():
            if any(w in text for w in words):
                category = cat
                break

        if any(w in text for w in CRITICAL):
            priority = "Critical"
        elif any(w in text for w in HIGH):
            priority = "High"
        elif any(w in text for w in MEDIUM):
            priority = "Medium"
        else:
            priority = "Low"

        summary = f"{category} issue, {priority.lower()} priority (auto-classified)."
        return {"category": category, "priority": priority,
                "summary": summary, "classified_by": self.name}


class OllamaClassifier:
    name = "ollama"

    def __init__(self, model=None):
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3.1")

    def classify(self, subject, description):
        import ollama  # imported lazily so the app runs without it installed

        prompt = (
            "Classify this IT support ticket. Respond ONLY with JSON containing: "
            "category (one of Network, Hardware, Software, Security, Email, Other), "
            "priority (one of Low, Medium, High, Critical), and summary (one sentence).\n"
            f"Subject: {subject}\nDescription: {description}"
        )
        resp = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            format="json",
        )
        data = json.loads(resp["message"]["content"])
        if not isinstance(data, dict):
            raise ValueError("classification must be a JSON object")

        category = data.get("category")
        priority = data.get("priority")
        summary = data.get("summary")
        if not all(isinstance(value, str) for value in (category, priority, summary)):
            raise ValueError("category, priority, and summary must be strings")

        category = category.strip()
        priority = priority.strip()
        summary = summary.strip()
        if category not in VALID_CATEGORIES:
            raise ValueError("unsupported ticket category")
        if priority not in VALID_PRIORITIES:
            raise ValueError("unsupported ticket priority")
        if not summary:
            raise ValueError("summary must not be empty")

        return {
            "category": category,
            "priority": priority,
            "summary": summary,
            "classified_by": self.name,
        }


def classify(subject, description):
    """Classify a ticket using the configured strategy, with automatic fallback.

    CLASSIFIER env var: "auto" (default) tries Ollama then falls back to rules;
    "ollama" tries Ollama first; "rule" forces rules only.
    """
    mode = os.environ.get("CLASSIFIER", "auto").lower()

    if mode in ("auto", "ollama"):
        try:
            return OllamaClassifier().classify(subject, description)
        except Exception:
            # use rules if the LLM is unavailable or returns invalid output
            pass

    return RuleBasedClassifier().classify(subject, description)
