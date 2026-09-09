# Flashcard authoring tool

Internal-only, single-user Flask app for Liam to write Document B
(the planet x house fragment library) one card at a time, with
Document A's house-level reference tags visible alongside. Never
served to a Celeste end user — completely separate from `web.py`'s
daily-reading pipeline (different port, no shared routes, no shared
templates).

## Running it

```bash
python -m flashcards.import_document_a path/to/document_a_export.csv  # once, and again whenever Document A changes
python -m flask --app flashcards.app run --port 5050
```

Then open `http://127.0.0.1:5050/`.

## Document A data source

Document A currently lives in Google Sheets. Per the brief, this tool
does **not** stay pointed at the live Sheet — it reads from its own
local SQLite table (`document_a_house`), populated by a one-time (and
re-runnable) CSV import (`import_document_a.py`). Export Document A
from Sheets via File → Download → CSV, matching the three columns in
`document_a_template.csv` (`house,tags,notes`), then run the import
command above. Re-running is idempotent (upserts by house number) and
never touches Liam's authored fragments.

This was the faster path given the current stack (plain Flask +
sqlite3, no Google API client already in the project) — a live Sheets
read would need OAuth/service-account setup, quota handling, and a
schema-drift story for a tool only one person uses. If Document A
starts changing frequently enough that re-exporting becomes a real
friction point, wiring up a live read (via `google-api-python-client`)
is a contained follow-up — the import boundary here
(`get_document_a_house`) is exactly where that swap would happen.

## Data model

- `planet_house_cards` (planet, house) → fragments (JSON array of
  strings), status (`draft` / `reviewed` / `locked`). This is Document
  B in progress.
- `document_a_house` (house) → tags, notes. Read-only from this tool's
  perspective; only `import_document_a.py` writes to it.

Both tables live in `flashcards/data/flashcards.db` — gitignored, not
committed (it's real authored content, not code).

## What's implemented from the brief

Core flow: single-card view (planet, house, Document A tags/notes),
one fragment per text input, "+ Add another variant" (capped at 5),
Save writing to `planet_house_cards`, Next/Previous navigation across
all 84 cards, and a progress indicator (cards with ≥1 fragment,
cards locked).

Also implemented from the "useful but not blocking" list: jump-to a
specific planet/house directly, the same planet's next house shown as
a voice-consistency reference, and a live per-fragment word count
(flagging anything over ~25 words as likely paragraph-length drift).

No AI generation anywhere in this tool, per its explicit scope —
content entry is manual; pasting in already-drafted text is fine.
