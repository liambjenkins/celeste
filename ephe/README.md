# Ephemeris data

These files are Swiss Ephemeris data, © Astrodienst AG, distributed
under the AGPL v3 (or a paid Astrodienst commercial license — see
https://www.astro.com/swisseph/ for details). They're vendored here
because `providers/astronomy.py` and `astrology/stars.py` need them
locally (`swe.set_ephe_path()` points at this directory).

- `seas_18.se1`, `semo_18.se1`, `sepl_18.se1` — planetary/lunar
  ephemeris data (asteroids, Moon, planets).
- `sefstars.txt` — the fixed-star catalog, required for
  `swe.fixstar2_ut()` to resolve named stars (Regulus, Aldebaran,
  etc.) beyond the handful Swiss Ephemeris otherwise falls back to
  internally.

`sefstars.txt` was sourced from the official `pyswisseph` PyPI source
distribution (`pip download --no-binary :all: pyswisseph==2.10.3.2`,
then `libswe/sefstars.txt`) rather than scraped from a website —
reproducible from a pinned dependency version.
