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

import base64
import json
import os
import secrets
import threading
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from astrology.chart import build_chart
from astrology.time import local_to_utc
from chinese.pillars import build_four_pillars
from daily import build_daily_reading

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent / "data"
CACHE_PATH = DATA_DIR / "daily_cache.json"
FEEDBACK_LOG_PATH = DATA_DIR / "feedback_log.jsonl"
GITHUB_FEEDBACK_PATH = "data/feedback_log.jsonl"
GITHUB_CACHE_PATH = "data/daily_cache.json"
GITHUB_API = "https://api.github.com"

app = Flask(__name__)
# Only used for flash() messages -- this is a single-user tool with no
# real session-security requirement, so a random per-boot key is fine.
# A restart occasionally losing an in-flight flash message is a
# trivial, acceptable edge case.
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(16)


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


def _github_config() -> tuple[str, str, str] | None:
    """(token, repo, branch) if GitHub persistence is configured, else
    None -- the shared check both the feedback log and the daily-
    reading cache use before attempting any GitHub Contents API call."""

    token = os.environ.get("CELESTE_GITHUB_TOKEN")
    repo = os.environ.get("CELESTE_GITHUB_REPO")
    branch = os.environ.get("CELESTE_GITHUB_BRANCH", "main")
    if not token or not repo:
        return None
    return token, repo, branch


def _load_cache_from_github() -> dict:
    """Best-effort durable-cache read via the GitHub Contents API --
    the only thing that survives a Render free-tier cold start. A real
    live incident confirmed the actual bug this closes: CACHE_PATH is
    a local file on an EPHEMERAL filesystem (same reasoning already
    documented on _commit_feedback_entry, just never applied to this
    cache) -- the free tier spins the container down after ~15 minutes
    idle and spins up a fresh one on the next request, silently
    wiping today's cached reading. Every reload after any idle gap
    looked like a brand-new day and triggered a full 2-LLM-call
    regeneration -- both "caching isn't working" and "very slow" were
    the same bug. Returns {} on any failure (unconfigured, network
    error, 404, malformed content) -- never raises; a durability-layer
    failure must always degrade to "regenerate", never crash the
    page."""

    config = _github_config()
    if config is None:
        return {}
    token, repo, branch = config
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    url = f"{GITHUB_API}/repos/{repo}/contents/{GITHUB_CACHE_PATH}"

    try:
        resp = requests.get(url, headers=headers, params={"ref": branch}, timeout=15)
    except requests.RequestException:
        return {}
    if resp.status_code != 200:
        return {}
    try:
        content = base64.b64decode(resp.json()["content"]).decode("utf-8")
        return json.loads(content)
    except (KeyError, ValueError):
        return {}


def _save_cache_to_github(cache: dict) -> None:
    """Best-effort durable-cache write, mirroring
    _commit_feedback_entry's own fail-open discipline: a GitHub-side
    failure here must never take down the request -- the caller
    already has the real result to serve regardless, this only
    affects whether the NEXT cold-started container can skip a full
    regeneration. The cache is a single overwritten entry (today's
    date only, same as the local file), not an append-only log, so
    this produces at most one commit per real regeneration -- no
    unbounded history growth."""

    config = _github_config()
    if config is None:
        return
    token, repo, branch = config
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    url = f"{GITHUB_API}/repos/{repo}/contents/{GITHUB_CACHE_PATH}"

    try:
        get_resp = requests.get(url, headers=headers, params={"ref": branch}, timeout=15)
        sha = get_resp.json()["sha"] if get_resp.status_code == 200 else None
        payload = {
            "message": f"Daily cache: {date.today().isoformat()}",
            "content": base64.b64encode(json.dumps(cache, indent=2).encode("utf-8")).decode("utf-8"),
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha
        requests.put(url, headers=headers, json=payload, timeout=15)
    except requests.RequestException:
        pass


# Guards cache-miss regeneration: without this, two overlapping
# requests (e.g. a double page-load, or a future multi-threaded/
# multi-worker deploy) can each independently see an empty cache and
# fire their own full build_daily_reading() -- two full LLM synthesis
# + fact-check round trips for the exact same reading, doubling real
# API cost for no benefit. Any request that arrives while another is
# already generating waits for the lock and then re-checks the cache
# (now warm) instead of generating its own copy.
_generation_lock = threading.Lock()


def _get_today_reading(force: bool = False) -> dict:
    """Generates once per calendar date, cached in data/daily_cache.json
    keyed by ISO date. `force=True` (the page's own "Regenerate" link,
    ?force=1) bypasses and overwrites the cache -- the manual
    regeneration trigger the brief asks for, so testing doesn't
    require waiting for an actual new day.

    Real live incident, root-caused directly: the local cache file
    alone is NOT durable on Render's free tier -- the container spins
    down after ~15 minutes idle and a fresh one spins up on the next
    request, with an empty filesystem. Every reload after any idle gap
    silently regenerated the full reading (two LLM calls) even though
    "caching" looked like it should have applied -- both "caching
    isn't working" and "very slow" were this one bug. The local file
    stays as the fast path for repeat requests within one warm
    container's lifetime; the GitHub-backed copy (_load_cache_from_
    github/_save_cache_to_github) is the actual durable layer, checked
    on a local miss before paying for a real regeneration."""

    today_key = date.today().isoformat()
    cache = _load_cache()

    if not force and today_key in cache:
        return cache[today_key]

    with _generation_lock:
        # Re-check after acquiring the lock: another thread may have
        # already generated (and saved) today's reading while this
        # one was waiting. A force=True request still regenerates
        # even if it finds a fresh cache entry here -- that's the
        # explicit point of the manual "Regenerate" trigger.
        cache = _load_cache()
        if not force and today_key in cache:
            return cache[today_key]

        if not force:
            # Local miss doesn't necessarily mean no one has generated
            # today's reading yet -- a PREVIOUS container (before this
            # one cold-started) may have, and persisted it durably.
            # force=True skips this on purpose: it means "regenerate
            # for real right now", not "check elsewhere first".
            github_cache = _load_cache_from_github()
            if today_key in github_cache:
                _save_cache(github_cache)  # warm the local file for the rest of this container's lifetime
                return github_cache[today_key]

        result = _build_today(datetime.now(timezone.utc))
        cache = {today_key: result}  # only today's entry needs keeping
        _save_cache(cache)
        _save_cache_to_github(cache)
        return result


@app.route("/")
def index():
    force = request.args.get("force") == "1"
    result = _get_today_reading(force=force)
    return render_template(
        "daily.html",
        result=result,
        today=date.today().isoformat(),
        # Render sets RENDER_GIT_COMMIT automatically on every deploy,
        # no config needed -- surfaced on the page so "is this deploy
        # actually running the latest code" is answerable by looking
        # at the page, not by guessing from output shape. A real live
        # incident (this exact page shown, stale content suspected)
        # had no way to confirm this at all.
        deploy_commit=os.environ.get("RENDER_GIT_COMMIT", "unknown (RENDER_GIT_COMMIT not set -- local/dev run)"),
        was_forced=force,
    )


def _commit_feedback_entry(entry: dict) -> tuple[bool, str]:
    """
    Appends one JSON line to data/feedback_log.jsonl in the GitHub
    repo via the Contents API (plain requests, matching this
    project's existing house style for external HTTP calls --
    providers/atmosphere.py, lenses/narrative_backend.py -- no new
    SDK dependency). This is the durable copy: Render's free tier has
    an ephemeral filesystem, so a purely local log would be lost on
    every spin-down.

    Returns (success, message) -- never raises, so a GitHub-side
    failure can't take down the /edit request; the caller decides
    what to do with the result rather than this function hiding it.
    """

    config = _github_config()
    if config is None:
        return False, (
            "GitHub persistence not configured (CELESTE_GITHUB_TOKEN / "
            "CELESTE_GITHUB_REPO unset) -- edit saved locally only."
        )
    token, repo, branch = config

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    url = f"{GITHUB_API}/repos/{repo}/contents/{GITHUB_FEEDBACK_PATH}"

    try:
        get_resp = requests.get(url, headers=headers, params={"ref": branch}, timeout=15)

        if get_resp.status_code == 200:
            current = get_resp.json()
            existing_content = base64.b64decode(current["content"]).decode("utf-8")
            sha = current["sha"]
        elif get_resp.status_code == 404:
            existing_content = ""
            sha = None
        else:
            return False, f"GitHub read failed ({get_resp.status_code}): {get_resp.text[:200]}"

        new_content = existing_content + json.dumps(entry) + "\n"
        payload = {
            "message": f"Feedback edit: {entry['element_type']} ({entry['date']})",
            "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8"),
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha

        put_resp = requests.put(url, headers=headers, json=payload, timeout=15)
    except requests.RequestException as error:
        return False, f"GitHub commit failed (network error): {error}"

    if put_resp.status_code in (200, 201):
        return True, "Edit committed to GitHub."

    return False, f"GitHub commit failed ({put_resp.status_code}): {put_resp.text[:200]}"


@app.route("/edit", methods=["POST"])
def edit():
    """Crude feedback-capture: every edit is committed durably to the
    GitHub repo (_commit_feedback_entry) AND written to the local
    data/feedback_log.jsonl as a same-container best-effort mirror --
    never silently drop an edit, matching the "never silently
    discard" discipline already established for e.g. fact_check()
    findings in lenses/narrative_validation.py. Capture only; nothing
    here feeds edits back into generation yet (explicitly out of
    scope for this pass)."""

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

    committed, message = _commit_feedback_entry(entry)
    flash(message, "success" if committed else "warning")

    return redirect(url_for("index"))


if __name__ == "__main__":
    # No debug/reloader: this is a minimal scaffold, not something
    # under active hot-reload development, and the reloader's
    # subprocess re-exec was observed to break the ephemeris file
    # path resolution in providers/astronomy.py (works fine without
    # it -- confirmed directly, not a bug in that module).
    app.run(host="0.0.0.0", port=5000)
