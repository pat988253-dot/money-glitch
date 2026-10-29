"""All SQLite access for Money Glitch. Pages call these functions; no SQL elsewhere."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "money_glitch.db"

CURRENCIES = ("USD", "COP")
STATUSES = ("pending", "paid")

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    source     TEXT    NOT NULL,
    amount     REAL    NOT NULL CHECK (amount > 0),
    currency   TEXT    NOT NULL CHECK (currency IN ('USD', 'COP')),
    date       TEXT    NOT NULL,              -- YYYY-MM-DD
    status     TEXT    NOT NULL CHECK (status IN ('pending', 'paid')),
    notes      TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Last good exchange rate, used when the live API can't be reached.
CREATE TABLE IF NOT EXISTS rate_cache (
    pair       TEXT PRIMARY KEY,              -- e.g. 'USD_COP'
    rate       REAL NOT NULL,
    fetched_at TEXT NOT NULL                  -- ISO timestamp (UTC)
);
"""


def connect():
    """Open the database, creating the folder and tables on first use."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def add_entry(source, amount, currency, date, status, notes=""):
    """Insert a new income entry and return its id."""
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO entries (source, amount, currency, date, status, notes)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (source.strip(), round(float(amount), 2), currency, str(date), status, notes.strip()),
        )
        return cur.lastrowid


def list_entries():
    """All entries, newest date first, as a list of dicts."""
    with connect() as conn:
        rows = conn.execute("SELECT * FROM entries ORDER BY date DESC, id DESC").fetchall()
    return [dict(r) for r in rows]


def get_entry(entry_id):
    """One entry as a dict, or None if it doesn't exist."""
    with connect() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    return dict(row) if row else None


def update_entry(entry_id, source, amount, currency, date, status, notes=""):
    """Overwrite an existing entry's fields."""
    with connect() as conn:
        conn.execute(
            "UPDATE entries SET source = ?, amount = ?, currency = ?, date = ?, status = ?, notes = ?"
            " WHERE id = ?",
            (source.strip(), round(float(amount), 2), currency, str(date), status, notes.strip(), entry_id),
        )


def delete_entry(entry_id):
    """Remove an entry permanently."""
    with connect() as conn:
        conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))


def list_sources():
    """Distinct source names already used, for suggestions in the form."""
    with connect() as conn:
        rows = conn.execute("SELECT DISTINCT source FROM entries ORDER BY source").fetchall()
    return [r["source"] for r in rows]


def save_rate(pair, rate, fetched_at):
    """Remember the latest good exchange rate."""
    with connect() as conn:
        conn.execute(
            "INSERT INTO rate_cache (pair, rate, fetched_at) VALUES (?, ?, ?)"
            " ON CONFLICT(pair) DO UPDATE SET rate = excluded.rate, fetched_at = excluded.fetched_at",
            (pair, rate, fetched_at),
        )


def load_rate(pair):
    """The cached rate as a dict {rate, fetched_at}, or None if never fetched."""
    with connect() as conn:
        row = conn.execute("SELECT rate, fetched_at FROM rate_cache WHERE pair = ?", (pair,)).fetchone()
    return dict(row) if row else None
