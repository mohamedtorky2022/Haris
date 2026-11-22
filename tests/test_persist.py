"""Saving the SQLite files to Postgres and bringing them back, with a stand-in for Postgres."""
import sqlite3

import pytest

from haris import inbox, persist

STORE: dict = {}


class FakeResult:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=()):
        if sql.startswith("SELECT"):
            return FakeResult((STORE[params[0]],) if params[0] in STORE else None)
        if sql.startswith("INSERT"):
            STORE[params[0]] = params[1]
        return FakeResult(None)


@pytest.fixture(autouse=True)
def fake_postgres(monkeypatch, tmp_path):
    STORE.clear()
    persist._saved.clear()
    monkeypatch.setattr(persist, "_connect", lambda: FakeConnection())
    for name in ("INBOX", "ALERTS", "RADAR"):
        monkeypatch.setenv(f"HARIS_{name}_DB", str(tmp_path / f"{name.lower()}.db"))


def test_a_report_survives_a_wiped_disk(tmp_path):
    case = inbox.submit({"incident_type": "money_sent", "description": "دفعت"}, "ar", "dubai", False)
    assert persist.save() >= 1
    assert persist.save() == 0  # nothing changed since
    (tmp_path / "inbox.db").unlink()  # a new deploy: the disk starts empty
    assert inbox.detail(case["reference"]) is None
    persist._saved.clear()
    assert persist.restore() >= 1
    assert inbox.detail(case["reference"])["emirate"] == "dubai"


def test_the_saved_copy_is_a_valid_database(tmp_path):
    inbox.submit({"incident_type": "account_hacked"}, "en", "sharjah", False)
    persist.save()
    copy = tmp_path / "copy.db"
    copy.write_bytes(STORE["inbox"])
    assert sqlite3.connect(copy).execute("SELECT count(*) FROM reports").fetchone()[0] == 1


def test_off_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(persist, "_connect", lambda: (_ for _ in ()).throw(AssertionError("no database")))
    persist.start()  # does nothing, raises nothing
