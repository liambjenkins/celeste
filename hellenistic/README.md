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
  today's sky, not just birth.
- **Lunar phase vocabulary**: the original 5-way phase (new/waxing/
  full/waning/balsamic, per the variable spec's own enum) is confirmed
  a cut of Dane Rudhyar's 1936 modern eight-phase model, not ancient
  doctrine. Added `moon_phase_hellenistic()` (New/Full/Dark — Artemis/
  Selene/Hecate; George Vol. 1 Ch. 29) as a genuine band around exact
  conjunction/opposition, exposed alongside (not replacing) the
  original 5-way enum. The band width is this author's inference —
  George's exact degree boundaries weren't findable via search — and
  is flagged in `lunar_phase.py` pending confirmation from content's
  Moon tab.
- **Void of course vs. aspect testimony are two separate checks**: a
  non-void Moon (has a next contact by degree) can still fail to
  improve the other planet's condition if no real whole-sign aspect
  connects them — confirmed `is_void_of_course` already gates every
  completion on `whole_sign_aspect()` existing, so this engine never
  reports "not void" without a genuine aspect behind it. Added the
  missing convenience pieces: every aspect now carries
  `degrees_to_exact`, and each planet gets `next_applying_aspect` (the
  soonest-to-perfect one, or `None`).
- **Master Planet Condition object** (`hellenistic/condition.py`,
  `chart["planet_conditions"]`): one structure per planet in the order
  George uses in her own worked examples (Vol. 1 Ch. 57-59) — nature,
  sect, sect rejoicing, lords, essential dignity, solar phase, lunar
  aspects, testimony, condition of domicile lord. Pure repackaging of
  facts this engine already computes, plus one new static fact
  (planetary nature). Deliberately stops short of a "judgment grade" —
  that final synthesis is the assembly layer's job, not this engine's.
- **Empty houses default to "check the ruler"**: most houses in most
  charts are empty (7 planets, 12 houses), and per George Vol. 2 Ch.
  83 an empty house's topics flow entirely through wherever its ruler
  sits — not suppressed. `chart["houses"]` gives every house's sign,
  ruler, occupants, `is_empty`, and the ruler's own house directly, so
  an interpretive layer can follow that rule without inverting
  `house_rulerships` itself.
- **Fortune-anchored house wheel + ZR intensity weighting**: per
  George Vol. 2 Ch. 88, Fortune's own house position generates a
  second whole-sign house wheel (`chart["fortune_houses"]`,
  `hellenistic/fortune_houses.py`) used to weight zodiacal releasing —
  a period landing on the house containing Fortune, or angular to it,
  is traditionally more dramatic. Every ZR level (both the Fortune and
  Spirit clocks) now carries `house_from_fortune` and
  `is_angular_to_fortune`.

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
