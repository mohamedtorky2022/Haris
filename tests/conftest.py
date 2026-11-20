import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _private_alerts_db(tmp_path, monkeypatch):
    """WhatsApp alert subscribers are real phone numbers in production: tests never touch data/alerts.db."""
    monkeypatch.setenv("HARIS_ALERTS_DB", str(tmp_path / "alerts.db"))
    monkeypatch.delenv("WHATSAPP_ALERT_TEMPLATE", raising=False)
