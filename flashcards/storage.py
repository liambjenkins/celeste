"""
SQLite persistence for the flashcard authoring tool: the
`planet_house_cards` table (Document B in progress -- Liam's authored
fragments) and `document_a_house` (a one-time local import of
Document A's house-level reference tags/notes, per the brief's
explicit instruction not to leave this tool pointed at a live Google
Sheet long-term -- see import_document_a.py).

Internal-only tool, single user, no concurrency concerns beyond
sqlite3's own defaults -- no ORM, no connection pool, deliberately.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "flashcards.db"

PLANETS = ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn")
HOUSES = tuple(range(1, 13))
STATUSES = ("draft", "reviewed", "locked")


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS planet_house_cards (
                planet TEXT NOT NULL,
                house INTEGER NOT NULL,
                fragments TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'draft',
                updated_at TEXT NOT NULL,
                PRIMARY KEY (planet, house)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS document_a_house (
                house INTEGER PRIMARY KEY,
                tags TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT ''
            )
            """
        )


def card_index(planet: str, house: int) -> int:
    return PLANETS.index(planet) * len(HOUSES) + HOUSES.index(house)


def card_at_index(index: int) -> tuple:
    index = index % (len(PLANETS) * len(HOUSES))
    planet = PLANETS[index // len(HOUSES)]
    house = HOUSES[index % len(HOUSES)]
    return planet, house


def total_cards() -> int:
    return len(PLANETS) * len(HOUSES)


def get_card(planet: str, house: int) -> dict:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM planet_house_cards WHERE planet = ? AND house = ?", (planet, house)
        ).fetchone()

    if row is None:
        return {"planet": planet, "house": house, "fragments": [], "status": "draft"}

    return {
        "planet": row["planet"],
        "house": row["house"],
        "fragments": json.loads(row["fragments"]),
        "status": row["status"],
    }


def save_card(planet: str, house: int, fragments: list, status: str) -> None:
    if status not in STATUSES:
        raise ValueError(f"Unknown status: {status!r}")

    fragments = [f.strip() for f in fragments if f.strip()]

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO planet_house_cards (planet, house, fragments, status, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (planet, house) DO UPDATE SET
                fragments = excluded.fragments,
                status = excluded.status,
                updated_at = excluded.updated_at
            """,
            (planet, house, json.dumps(fragments), status, datetime.now(timezone.utc).isoformat()),
        )


def get_document_a(house: int) -> dict:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM document_a_house WHERE house = ?", (house,)
        ).fetchone()

    if row is None:
        return {"house": house, "tags": "", "notes": ""}

    return {"house": row["house"], "tags": row["tags"], "notes": row["notes"]}


def progress_summary() -> dict:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT planet, house, fragments, status FROM planet_house_cards"
        ).fetchall()

    with_fragments = 0
    locked = 0

    for row in rows:
        if json.loads(row["fragments"]):
            with_fragments += 1
        if row["status"] == "locked":
            locked += 1

    return {
        "total": total_cards(),
        "with_fragments": with_fragments,
        "locked": locked,
    }


def adjacent_planet_card(planet: str, house: int) -> dict:
    """Same planet, a different house (the next house, wrapping) --
    used as a voice-consistency reference alongside the current card,
    per the brief's 'useful but not blocking' suggestion."""

    reference_house = HOUSES[(HOUSES.index(house) + 1) % len(HOUSES)]
    return get_card(planet, reference_house)
