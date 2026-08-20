"""
Celeste daily-mode web scaffold -- deliberately minimal plumbing, not
a design pass, per "Celeste — Web Scaffold Brief."

Plain Flask + Jinja2, default HTML styling only. No design decisions
belong here -- this exists so the real pipeline -> storage -> web
display path is proven out and ready to skin once Figma design work
lands, and so Liam has several distinct real content elements (not
just one paragraph) to design around.

Reuses daily.py's build_daily_reading() directly -- no new
astrological computation here, only caching, routing, and the crude
feedback-capture loop.

Birth-data config comes from the environment (a local, gitignored
.env file via python-dotenv, already a project dependency) rather
than being hardcoded here -- same principle as this project's own
earlier "un-hardcode birth data in main.py" fix.
"""

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for

from astrology.chart import build_chart
from astrology.time import local_to_utc
from chinese.pillars import build_four_pillars
from daily import build_daily_reading

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent / "data"
CACHE_PATH = DATA_DIR / "daily_cache.json"
FEEDBACK_LOG_PATH = DATA_DIR / "feedback_log.jsonl"

app = Flask(__name__)


def _birth_config() -> dict:
    """Reads birth-data config from the environment. Raises a clear
    error naming the missing variable rather than a bare KeyError, so
    a missing .env is obvious instead of a stack trace on first run."""

    required = (
        "CELESTE_BIRTH_DATE",
        "CELESTE_BIRTH_TIME",
        "CELESTE_TIMEZONE",
        "CELESTE_LATITUDE",
        "CELESTE_LONGITUDE",
    )
    missing = [name for name in required if not os.environ.get(name)]

    if missing:
        raise RuntimeError(
            "Missing birth-data config in the environment: "
            f"{', '.join(missing)}. Set these in a local .env file "
            "(see .env.example) -- birth data is intentionally not "
            "hardcoded here."
        )

    return {
        "birth_date": os.environ["CELESTE_BIRTH_DATE"],
        "birth_time": os.environ["CELESTE_BIRTH_TIME"],
        "timezone": os.environ["CELESTE_TIMEZONE"],
        "latitude": float(os.environ["CELESTE_LATITUDE"]),
        "longitude": float(os.environ["CELESTE_LONGITUDE"]),
    }


def _build_today(as_of_utc_time: datetime) -> dict:
    """Runs the real pipeline end to end: natal chart -> four pillars
    -> build_daily_reading(). Same construction main.py/daily.py's
    CLI already does, just parameterized from env config instead of
    argparse."""

    config = _birth_config()
    birth_date = datetime.strptime(config["birth_date"], "%Y-%m-%d").date()
    birth_hour, birth_minute = (int(x) for x in config["birth_time"].split(":"))
    local_time = datetime(
        birth_date.year, birth_date.month, birth_date.day, birth_hour, birth_minute
    )
    aware_utc = local_to_utc(local_time, config["timezone"])
    utc_time = (
        aware_utc.replace(tzinfo=timezone.utc) if aware_utc.tzinfo is None else aware_utc
    )

    natal_chart = build_chart(
        utc_time, config["latitude"], config["longitude"], house_system="placidus"
    )
    four_pillars = build_four_pillars(natal_chart, local_time)

    return build_daily_reading(natal_chart, four_pillars, as_of_utc_time)


def _load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}
    with open(CACHE_PATH) as f:
        return json.load(f)


def _save_cache(cache: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def _get_today_reading(force: bool = False) -> dict:
    """Generates once per calendar date, cached in data/daily_cache.json
    keyed by ISO date. `force=True` (the page's own "Regenerate" link,
    ?force=1) bypasses and overwrites the cache -- the manual
    regeneration trigger the brief asks for, so testing doesn't
    require waiting for an actual new day."""

    today_key = date.today().isoformat()
    cache = _load_cache()

    if not force and today_key in cache:
        return cache[today_key]

    result = _build_today(datetime.now(timezone.utc))
    cache = {today_key: result}  # only today's entry needs keeping
    _save_cache(cache)
    return result


@app.route("/")
def index():
    force = request.args.get("force") == "1"
    result = _get_today_reading(force=force)
    return render_template("daily.html", result=result, today=date.today().isoformat())


@app.route("/edit", methods=["POST"])
def edit():
    """Crude feedback-capture: appends one JSON line per edit to
    data/feedback_log.jsonl. Append-only -- no read-modify-write of
    the whole file, no database. Capture only; nothing here feeds
    edits back into generation yet (explicitly out of scope for this
    pass)."""

    entry = {
        "date": date.today().isoformat(),
        "element_type": request.form.get("element_type", ""),
        "original_text": request.form.get("original_text", ""),
        "sources": request.form.get("sources", ""),
        "edited_text": request.form.get("edited_text", ""),
    }

    DATA_DIR.mkdir(exist_ok=True)
    with open(FEEDBACK_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return redirect(url_for("index"))


if __name__ == "__main__":
    # No debug/reloader: this is a minimal scaffold, not something
    # under active hot-reload development, and the reloader's
    # subprocess re-exec was observed to break the ephemeris file
    # path resolution in providers/astronomy.py (works fine without
    # it -- confirmed directly, not a bug in that module).
    app.run(host="0.0.0.0", port=5000)
