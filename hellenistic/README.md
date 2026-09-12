# Hellenistic computation engine

Implements `celeste-variable-spec-for-code.md`'s natal and daily/
activation layers as pure structured data (JSON-able dicts) — no
prose, no interpretation. Entirely independent of `astrology/`
(Celeste's existing tropical + Vedic/sidereal pipeline): different
house convention (whole-sign, not Placidus), different dignity system
(Hellenistic essential dignity, not Parashari), different aspect
doctrine (whole-sign existence, not degree+orb). Nothing in this
package is imported by `daily.py`/`web.py`, and nothing here imports
`astrology/dignity.py` or `astrology/rulership.py` — see
`constants.py`'s docstring for why.

## Entry points

```python
from hellenistic.natal import build_natal_chart
from hellenistic.daily import build_daily_layer

natal = build_natal_chart(birth_utc_time, latitude, longitude)  # cache this
daily = build_daily_layer(natal, birth_utc_time, as_of_utc_time)  # per date
```

## Ephemeris

Swiss Ephemeris via `pyswisseph` (already a project dependency,
already vendored under `ephe/`) — same library the rest of Celeste
uses. No new dependency needed.

## Decisions this build made explicit (per the brief's own flags)

- **Aspect doctrine**: whole-sign for existence (binary, sign-to-sign,
  no orbs — `hellenistic/aspects.py`), with degree-based proximity
  layered on top only to decide applying/separating and effect. Two
  separate jobs, not competing methods, per the brief.
- **Void of course**: revised after this build's first pass. The
  original implementation cut the completion search off at the Moon's
  sign boundary — an engineering note from content development
  (source: Demetra George, *Ancient Astrology in Theory and Practice*
  Vol. 1, Ch. 28) identified that as actually the popular MODERN
  convention, not the Hellenistic one. The corrected version
  (`hellenistic/lunar_phase.py`) checks a fixed 30-degree forward
  window from the Moon's current degree that is allowed to run past
  the sign cusp into the next sign — this makes genuine void-of-course
  rarer, matching George's account, since fewer near-cusp completions
  get missed.
- **Egyptian bounds table**: verified via three independent sources
  during this build; an initial recollection of Virgo's Venus segment
  (7-13°) was wrong and caught by cross-checking — the table now in
  `constants.py` is confirmed 7-17°.
- **Dorothean/Valens triplicity table** (not Ptolemy's competing
  single-ruler version): verified via web search.
- **Zodiacal releasing sign-years, Cancer = 25** (not the less common
  27 reading) — a genuine textual ambiguity in Valens' own material;
  25 is the modern-consensus resolution, chosen deliberately and
  documented in `zr.py` rather than silently defaulted.
- **ZR uses a fixed 360-day "releasing year"** (12 x 30-day months) at
  every level, not the real 365.242-day tropical year used elsewhere
  in this engine (profections, transits) — this is what makes L1-L4
  nest without drift, and is a second explicit, flagged choice.
- **Loosing of the bond** is implemented as a real mechanism (not a
  lookup shortcut): a sub-level's release restarts at the sign
  opposite its parent's own sign exactly when an unmodified 12-sign
  lap would otherwise repeat the parent's sign. See `zr.py`'s
  docstring and `tests/test_hellenistic_zr.py`.
- **Combustion/cazimi/under-the-beams orbs** (17', 8°, 15°) are the
  commonly-cited classical/Lilly-tradition figures — a documented
  choice, not an attempt to reconcile every source's slightly
  different numbers.
- **Mercury's gender/sect**, which classical doctrine treats as
  "common" rather than fixed, is resolved from its own oriental/
  occidental status (a real classical tie-in, not an arbitrary
  default) rather than hardcoded to one value.
- **Zodiacal releasing's sign-years table is per-SIGN, not per-planet**
  — Saturn's two signs get different values (Capricorn 27, Aquarius
  30), unlike the general "planetary years" table (Saturn 30 for
  both) used elsewhere in the tradition. Confirmed correct for ZR
  specifically per an engineering note from content development that
  flagged the split for a closer look — see `zr.py`'s docstring.
- **Solar phase is now also computed LIVE for the daily/activation
  layer** (`daily_layer["solar_phase_today"]`), not just as a fixed
  natal fact — added per an engineering note: content needs Venus's
  oriental/occidental status and the Moon's phase checked against
  today's sky, not just birth. `lunar_phase_today_three_way` is an
  inferred New/Waxing-to-Full/Waning collapse of the 5-way phase,
  flagged back for label confirmation since content specified the
  three buckets without exact key names.

## Explicitly not built (per the brief)

Predominator/Oikodespotes/Kurios, length-of-life techniques, Hermetic
Lots beyond Fortune and Spirit, `other_lots`, `whole_nativity_rulers`,
and `doruphoria` beyond a stub `None` field.

## Tests

`tests/test_hellenistic_*.py` — dignity table regression guards
(including the Virgo bounds correction), whole-sign aspect/aversion
logic, the loosing-of-the-bond mechanism, void-of-course, and an
end-to-end smoke test against the same real chart already used
throughout `astrology/*.py`'s own `__main__` blocks (1996-07-22 03:10,
Melbourne).
