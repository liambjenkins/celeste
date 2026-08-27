"""
Celeste Key Events Engine CLI -- mirrors daily.py's argparse shape.

Given a natal chart and a date range, prints the ranked, tiered list
of significant events astrology/key_events.py::build_key_events()
assembles (see that module for the full engine).
"""

import argparse
import json as json_module
from datetime import datetime, timedelta, timezone

from astrology.chart import build_chart
from astrology.key_events import DEFAULT_HORIZON_MONTHS, build_key_events
from astrology.time import local_to_utc


def _parse_args():
    parser = argparse.ArgumentParser(description="Celeste Key Events Engine")
    parser.add_argument("--birth-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--birth-time", required=True, help="HH:MM, 24h, local")
    parser.add_argument("--timezone", required=True, help="IANA tz, e.g. Australia/Melbourne")
    parser.add_argument("--latitude", type=float, required=True)
    parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--start", default=None, help="YYYY-MM-DD (UTC); default: today")
    parser.add_argument(
        "--months",
        type=int,
        default=DEFAULT_HORIZON_MONTHS,
        help=f"horizon length in months from --start (default {DEFAULT_HORIZON_MONTHS})",
    )
    parser.add_argument(
        "--tiers",
        default="standout,background",
        help="comma-separated tiers to include (standout,background,appendix)",
    )
    parser.add_argument("--json", action="store_true", help="print full JSON instead of a plain list")
    return parser.parse_args()


def main():
    args = _parse_args()

    birth_date = datetime.strptime(args.birth_date, "%Y-%m-%d").date()
    birth_hour, birth_minute = (int(x) for x in args.birth_time.split(":"))
    local_time = datetime(birth_date.year, birth_date.month, birth_date.day, birth_hour, birth_minute)
    aware_utc = local_to_utc(local_time, args.timezone)
    birth_utc_time = aware_utc.replace(tzinfo=timezone.utc) if aware_utc.tzinfo is None else aware_utc

    if args.start:
        start = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        start = datetime.now(timezone.utc)
    end = start + timedelta(days=30 * args.months)

    natal_chart = build_chart(birth_utc_time, args.latitude, args.longitude, house_system="placidus")

    tiers = tuple(t.strip() for t in args.tiers.split(","))
    result = build_key_events(natal_chart, birth_utc_time, start, end, tiers=tiers)

    if args.json:
        def default(o):
            if isinstance(o, datetime):
                return o.isoformat()
            raise TypeError
        print(json_module.dumps(result, default=default, indent=2))
        return

    print(f"Key events: {result['range']['start'][:10]} -> {result['range']['end'][:10]}")
    print(f"Counts by tier: {result['counts_by_tier']}")
    if result["quiet"]:
        print(result["quiet_note"])
    print()
    for e in result["events"]:
        when = e.get("peak_utc_time") or e.get("utc_time")
        label = e["kind"]
        if e["kind"] in ("transit_aspect", "return"):
            label = f"{e['transiting_body']} {e['aspect']} natal {e['target_role']}"
            if e.get("is_repeating"):
                label += f" (repeats x{e['pass_count']})"
        elif e["kind"] == "station":
            label = f"{e['body']} stations {e['direction']} at {e['sign']} {e['degree']}"
        elif e["kind"] in ("sign_ingress", "natal_house_ingress"):
            label = f"{e['body']} {e['kind']}"
        elif e["kind"] == "eclipse":
            label = (f"{e['eclipse_kind']} eclipse ({e['type']}) at {e['sign']} {e['degree']} "
                     f"-- nodal: {e['nodal']['relationship']}")
        elif e["kind"] in ("new_moon", "full_moon"):
            label = f"{e['kind']} at {e['sign']} {e['degree']}"
        elif e["kind"] == "dasha_change":
            label = f"Dasha {e['level']} begins: {e['lord']}"

        print(f"  {when.date()}  [{e['tier']:9s}] {label}")
        if e.get("recurrence_note"):
            print(f"      {e['recurrence_note']}")


if __name__ == "__main__":
    main()
