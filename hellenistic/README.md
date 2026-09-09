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
- **Void of course**: the Hellenistic-consistent definition — the Moon
  is void when it will complete no further whole-sign aspect before
  leaving its current sign (`hellenistic/lunar_phase.py`) — not the
  looser popular/modern convention.
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
