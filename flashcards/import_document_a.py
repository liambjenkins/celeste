"""
One-time import of Document A's house-level reference data from a CSV
export, into this tool's own local SQLite storage.

Document A currently lives in Google Sheets. Per the brief: don't
leave this tool pointed at a live Sheet as a long-term dependency --
a one-time export is faster to build against than wiring up the
Sheets API (auth, quota, schema drift) for a tool only Liam uses, and
a fresh export takes one click whenever Document A's house rows
change ("File -> Download -> Comma-separated values (.csv)").

Expected CSV columns (header row required): house,tags,notes
  - house: integer 1-12
  - tags: Document A's signification tags for that house (free text --
    however they're currently formatted in the sheet is fine, this
    tool displays them verbatim rather than parsing them further)
  - notes: any accompanying notes column from the sheet

Usage:
    python -m flashcards.import_document_a path/to/document_a_export.csv

Re-running is safe and idempotent -- each run replaces the house rows
in this CSV, keyed by house number (upsert), doesn't touch
planet_house_cards (Liam's authored fragments) at all.
"""

import csv
import sys

from flashcards.storage import _connect, init_db


def import_document_a_csv(csv_path: str) -> int:
    init_db()
    imported = 0

    with open(csv_path, newline="", encoding="utf-8") as f, _connect() as conn:
        reader = csv.DictReader(f)

        missing = {"house", "tags", "notes"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"CSV is missing required column(s): {', '.join(sorted(missing))}. "
                f"Found columns: {reader.fieldnames}"
            )

        for row in reader:
            house = int(row["house"])
            if not (1 <= house <= 12):
                raise ValueError(f"House must be 1-12, got {house!r}")

            conn.execute(
                """
                INSERT INTO document_a_house (house, tags, notes)
                VALUES (?, ?, ?)
                ON CONFLICT (house) DO UPDATE SET
                    tags = excluded.tags,
                    notes = excluded.notes
                """,
                (house, row["tags"], row["notes"]),
            )
            imported += 1

    return imported


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m flashcards.import_document_a <path-to-csv>")
        sys.exit(1)

    count = import_document_a_csv(sys.argv[1])
    print(f"Imported {count} house row(s) from {sys.argv[1]}.")
