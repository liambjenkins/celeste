"""
A curated set of classical Vedic astrology Yogas (planetary
combinations) — a documented technique layered on an already-computed
sidereal chart, not new astronomy.

Scoped deliberately to combinations that are well-documented,
unambiguous, and computable purely from sign placement, whole-sign
house distance, house lordship (via astrology.dignity's traditional
7-planet rulership table), planetary dignity (astrology.dignity, F4's
foundation), and classical graha drishti (planetary aspect): every
planet aspects the 7th house from its own position; Mars additionally
aspects the 4th and 8th; Jupiter additionally the 5th and 9th; Saturn
additionally the 3rd and 10th.

Original 7 (Gajakesari, Budhaditya, the 5 Pancha Mahapurusha Yogas)
plus a second tranche of ~28 more, researched and cross-referenced
against Brihat Parashara Hora Shastra, Phaladeepika, Saravali, and
independent technical Jyotish sources during curation. Every yoga
below states its own sourcing confidence in its section comment;
several genuinely-contested yogas researched (Putra/Kalatra/Arishta
Yoga as single named rules, the Dainya/Khala Parivartana naming split,
and Kalasarpa Yoga, which research found has NO classical BPHS/
Saravali/Brihat Jataka attestation at all) were deliberately left out
rather than implemented on a guessed or fabricated rule — this
project's "requires curation" allowance, applied at the yoga-selection
level rather than only within an individual yoga's sub-rules.

Every yoga here is independently satisfiable — a chart can carry any
combination of them, including none or several at once.
"""

from astrology.dignity import CLASSICAL_PLANETS, TRADITIONAL_RULERS, classify_dignity
from astrology.sidereal import whole_sign_house

ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

KENDRA_HOUSES = {1, 4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}
DUSTHANA_HOUSES = {6, 8, 12}
UPACHAYA_HOUSES = {3, 6, 10, 11}
KENDRA_TRIKONA_HOUSES = KENDRA_HOUSES | TRIKONA_HOUSES

# Natural benefic/malefic classification used for the "hemming"
# (Kartari) and Vasumati/Adhi yogas below. The Moon (waxing/waning-
# dependent) and the Sun (dignity-dependent, per some sources) are
# genuinely conditional cases classical texts don't treat uniformly —
# both are deliberately left out of these two fixed sets rather than
# guessed at, a documented simplification, not an oversight.
NATURAL_BENEFICS = {"jupiter", "venus", "mercury"}
NATURAL_MALEFICS = {"saturn", "mars", "rahu", "ketu"}

# Rahu/Ketu map to the true lunar nodes (not mean) — the actual node
# position rather than a smoothed approximation, consistent with this
# project's general preference elsewhere for computed-over-averaged
# astronomical values where both are available.
_NODE_BODY_NAMES = {"rahu": "north_node_true", "ketu": "south_node_true"}

# label, own signs, exaltation sign — verified via search against
# Brihat Parashara Hora Shastra's Pancha Mahapurusha definitions.
_MAHAPURUSHA = {
    "mars": {
        "id": "ruchaka",
        "label": "Ruchaka Yoga",
        "own_signs": {"Aries", "Scorpio"},
        "exaltation_sign": "Capricorn",
    },
    "mercury": {
        "id": "bhadra",
        "label": "Bhadra Yoga",
        "own_signs": {"Gemini", "Virgo"},
        "exaltation_sign": "Virgo",
    },
    "jupiter": {
        "id": "hamsa",
        "label": "Hamsa Yoga",
        "own_signs": {"Sagittarius", "Pisces"},
        "exaltation_sign": "Cancer",
    },
    "venus": {
        "id": "malavya",
        "label": "Malavya Yoga",
        "own_signs": {"Taurus", "Libra"},
        "exaltation_sign": "Pisces",
    },
    "saturn": {
        "id": "shasha",
        "label": "Shasha Yoga",
        "own_signs": {"Capricorn", "Aquarius"},
        "exaltation_sign": "Libra",
    },
}


# ------------------------------------------------------------
# Shared helpers: house lordship, house-of-planet, and graha drishti
# (planetary aspect), all whole-sign, all counted from the Ascendant
# unless otherwise noted.
# ------------------------------------------------------------

_ASPECT_EXTRA_HOUSES = {
    "mars": {4, 8},
    "jupiter": {5, 9},
    "saturn": {3, 10},
}


def _sign_of_house(house_number: int, reference_sign_index: int) -> int:
    return (reference_sign_index + house_number - 1) % 12


def _house_lord(house_number: int, ascendant_sign_index: int) -> str:
    sign_index = _sign_of_house(house_number, ascendant_sign_index)
    return TRADITIONAL_RULERS[ZODIAC_SIGNS[sign_index]]


def _owned_houses(planet: str, ascendant_sign_index: int) -> set:
    return {
        house
        for house in range(1, 13)
        if _house_lord(house, ascendant_sign_index) == planet
    }


def _house_of(sign_index: int, ascendant_sign_index: int) -> int:
    return whole_sign_house(sign_index, ascendant_sign_index)


def _aspects_sign(planet: str, planet_sign_index: int, target_sign_index: int) -> bool:
    distance = whole_sign_house(target_sign_index, planet_sign_index)
    aspected = {7} | _ASPECT_EXTRA_HOUSES.get(planet, set())
    return distance in aspected


def _connected(
    planet_a: str, sign_a: int, planet_b: str, sign_b: int
) -> bool:
    """
    Two planets are 'connected' (the BPHS Raja Yoga mechanism) if they
    are conjunct (same sign), in aspect (either direction), or in
    parivartana (sign exchange). Verified via a directly-quoted BPHS
    line during curation: "if there is an exchange between a Lord of
    a Kendra and a Lord of a Kona, or if a Lord of a Kendra is
    conjunct with a Lord of a Kona ..., or if there happens to be a
    full Aspect between [them], they cause a Yoga."
    """

    if sign_a == sign_b:
        return True

    if _aspects_sign(planet_a, sign_a, sign_b) or _aspects_sign(planet_b, sign_b, sign_a):
        return True

    if (
        TRADITIONAL_RULERS[ZODIAC_SIGNS[sign_a]] == planet_b
        and TRADITIONAL_RULERS[ZODIAC_SIGNS[sign_b]] == planet_a
    ):
        return True

    return False


def find_yogas(sidereal_chart: dict) -> list[dict]:
    """
    Return every yoga (from the curated set above) present in an
    already-built sidereal chart (astrology.sidereal.build_sidereal_chart's
    output).
    """

    bodies = sidereal_chart["bodies"]
    ascendant_sign_index = sidereal_chart["ascendant"]["sign_index"]
    yogas = []

    def _sign_index_of(planet_name):
        body = bodies.get(planet_name)
        return body["sign_index"] if body else None

    moon_sign_index = _sign_index_of("moon")
    sun_sign_index = _sign_index_of("sun")

    # ---------------- original 7 ----------------

    moon = bodies.get("moon")
    jupiter = bodies.get("jupiter")

    if moon and jupiter:
        house_from_moon = whole_sign_house(
            jupiter["sign_index"], moon["sign_index"]
        )
        if house_from_moon in KENDRA_HOUSES:
            yogas.append(
                {"id": "gajakesari", "label": "Gajakesari Yoga", "bodies": ["moon", "jupiter"]}
            )

    sun = bodies.get("sun")
    mercury = bodies.get("mercury")

    if sun and mercury and sun["sign"] == mercury["sign"]:
        yogas.append(
            {"id": "budhaditya", "label": "Budhaditya Yoga", "bodies": ["sun", "mercury"]}
        )

    for planet_name, info in _MAHAPURUSHA.items():
        planet = bodies.get(planet_name)

        if planet is None:
            continue

        in_own_or_exalted = (
            planet["sign"] in info["own_signs"]
            or planet["sign"] == info["exaltation_sign"]
        )

        if not in_own_or_exalted:
            continue

        if planet["house"] in KENDRA_HOUSES:
            yogas.append({"id": info["id"], "label": info["label"], "bodies": [planet_name]})

    # ---------------- Raja Yoga (kendra-trikona lord connection) ----------------
    # High confidence (BPHS Ch. 39, direct quote). A distinct pair of
    # planets, one a kendra lord and one a trikona lord, connected by
    # conjunction/aspect/exchange.

    kendra_lords = {_house_lord(h, ascendant_sign_index) for h in KENDRA_HOUSES}
    trikona_lords = {_house_lord(h, ascendant_sign_index) for h in TRIKONA_HOUSES}
    seen_raja_pairs = set()

    for kendra_lord in kendra_lords:
        for trikona_lord in trikona_lords:
            if kendra_lord == trikona_lord:
                continue

            pair_key = frozenset((kendra_lord, trikona_lord))
            if pair_key in seen_raja_pairs:
                continue

            sign_k = _sign_index_of(kendra_lord)
            sign_t = _sign_index_of(trikona_lord)
            if sign_k is None or sign_t is None:
                continue

            if _connected(kendra_lord, sign_k, trikona_lord, sign_t):
                seen_raja_pairs.add(pair_key)
                yogas.append(
                    {
                        "id": "raja_yoga",
                        "label": "Raja Yoga",
                        "bodies": sorted((kendra_lord, trikona_lord)),
                    }
                )

    # ---------------- Neecha Bhanga Raja Yoga ----------------
    # Medium confidence (concept multiply-attested; exact condition
    # list synthesized across sources, documented as a curated
    # synthesis rather than one verbatim classical formula). A
    # debilitated planet's debility is read as cancelled when its
    # dispositor is well-placed (kendra from Ascendant, mutual kendra
    # with the debilitated planet, or aspecting it) -- and rises to
    # RAJA YOGA grade specifically when the debilitated planet is
    # itself a kendra/trikona lord. Reuses astrology.dignity (F4).

    for planet in CLASSICAL_PLANETS:
        body = bodies.get(planet)
        if not body:
            continue

        degree_in_sign = body["longitude"] % 30.0
        dignity = classify_dignity(planet, body["sign"], degree_in_sign)
        if dignity != "debilitated":
            continue

        dispositor = TRADITIONAL_RULERS[body["sign"]]
        dispositor_sign = _sign_index_of(dispositor)
        if dispositor_sign is None:
            continue

        dispositor_house = _house_of(dispositor_sign, ascendant_sign_index)

        mutual_kendra = (
            whole_sign_house(dispositor_sign, body["sign_index"]) in KENDRA_HOUSES
            and whole_sign_house(body["sign_index"], dispositor_sign) in KENDRA_HOUSES
        )
        dispositor_aspects_planet = _aspects_sign(dispositor, dispositor_sign, body["sign_index"])

        cancelled = (
            dispositor_house in KENDRA_HOUSES or mutual_kendra or dispositor_aspects_planet
        )
        if not cancelled:
            continue

        # The stronger "Raja Yoga" grade requires the debilitated
        # planet to itself be a LORD of a kendra/trikona house (not
        # merely placed in one) -- its own dignity failure converting
        # into a yoga-capable house-lordship, per the research.
        if _owned_houses(planet, ascendant_sign_index) & KENDRA_TRIKONA_HOUSES:
            yogas.append(
                {"id": "neecha_bhanga_raja_yoga", "label": "Neecha Bhanga Raja Yoga", "bodies": [planet]}
            )

    # ---------------- Viparita Raja Yoga: Harsha / Sarala / Vimala ----------------
    # Medium-high confidence (Phaladeepika). A dusthana house's lord
    # confined to a dusthana house (6th/8th/12th) is read as auspicious.

    _VIPARITA = {6: ("harsha", "Harsha Yoga"), 8: ("sarala", "Sarala Yoga"), 12: ("vimala", "Vimala Yoga")}

    for house_num, (yoga_id, label) in _VIPARITA.items():
        lord = _house_lord(house_num, ascendant_sign_index)
        lord_sign = _sign_index_of(lord)
        if lord_sign is None:
            continue

        if _house_of(lord_sign, ascendant_sign_index) in DUSTHANA_HOUSES:
            yogas.append({"id": yoga_id, "label": label, "bodies": [lord]})

    # ---------------- Maha Parivartana Yoga ----------------
    # Medium confidence (exchange mechanism itself high confidence,
    # BPHS Ch. 39; the specific "Maha" label is modern-technical-
    # literature sourced). Mutual sign exchange between two planets
    # each of whose relevant owned houses are kendra/trikona.

    seen_parivartana = set()

    for planet_a in CLASSICAL_PLANETS:
        sign_a = _sign_index_of(planet_a)
        if sign_a is None:
            continue

        ruler_of_a = TRADITIONAL_RULERS[ZODIAC_SIGNS[sign_a]]
        if ruler_of_a == planet_a:
            continue

        sign_b = _sign_index_of(ruler_of_a)
        if sign_b is None:
            continue

        ruler_of_b = TRADITIONAL_RULERS[ZODIAC_SIGNS[sign_b]]
        if ruler_of_b != planet_a:
            continue

        pair_key = frozenset((planet_a, ruler_of_a))
        if pair_key in seen_parivartana:
            continue
        seen_parivartana.add(pair_key)

        owned_a = _owned_houses(planet_a, ascendant_sign_index)
        owned_b = _owned_houses(ruler_of_a, ascendant_sign_index)

        if owned_a & KENDRA_TRIKONA_HOUSES and owned_b & KENDRA_TRIKONA_HOUSES:
            yogas.append(
                {
                    "id": "maha_parivartana",
                    "label": "Maha Parivartana Yoga",
                    "bodies": sorted((planet_a, ruler_of_a)),
                }
            )

    # ---------------- Dhana Yoga (2nd-11th lord connection) ----------------
    # High confidence (BPHS wealth-yoga chapter).

    lord_2 = _house_lord(2, ascendant_sign_index)
    lord_11 = _house_lord(11, ascendant_sign_index)

    if lord_2 != lord_11:
        sign_2 = _sign_index_of(lord_2)
        sign_11 = _sign_index_of(lord_11)
        if sign_2 is not None and sign_11 is not None and _connected(lord_2, sign_2, lord_11, sign_11):
            yogas.append(
                {"id": "dhana_yoga", "label": "Dhana Yoga", "bodies": sorted((lord_2, lord_11))}
            )

    # ---------------- Kubera Yoga (2nd-11th lord exchange, both strong) ----------------
    # Medium confidence.

    if lord_2 != lord_11:
        sign_2 = _sign_index_of(lord_2)
        sign_11 = _sign_index_of(lord_11)
        if (
            sign_2 is not None
            and sign_11 is not None
            and TRADITIONAL_RULERS[ZODIAC_SIGNS[sign_2]] == lord_11
            and TRADITIONAL_RULERS[ZODIAC_SIGNS[sign_11]] == lord_2
        ):
            deg_2 = bodies[lord_2]["longitude"] % 30.0
            deg_11 = bodies[lord_11]["longitude"] % 30.0
            dignity_2 = classify_dignity(lord_2, bodies[lord_2]["sign"], deg_2)
            dignity_11 = classify_dignity(lord_11, bodies[lord_11]["sign"], deg_11)
            _good = {"exalted", "moolatrikona", "own_sign", "friendly_sign"}
            if dignity_2 in _good and dignity_11 in _good:
                yogas.append(
                    {"id": "kubera_yoga", "label": "Kubera Yoga", "bodies": sorted((lord_2, lord_11))}
                )

    # ---------------- Lakshmi Yoga ----------------
    # Medium-high confidence (BPHS Ch. 41).

    lord_9 = _house_lord(9, ascendant_sign_index)
    lord_1 = _house_lord(1, ascendant_sign_index)
    lord_9_body = bodies.get(lord_9)
    lord_1_body = bodies.get(lord_1)

    if lord_9_body and lord_1_body:
        deg_9 = lord_9_body["longitude"] % 30.0
        dignity_9 = classify_dignity(lord_9, lord_9_body["sign"], deg_9)
        house_9lord = _house_of(lord_9_body["sign_index"], ascendant_sign_index)

        deg_1 = lord_1_body["longitude"] % 30.0
        dignity_1 = classify_dignity(lord_1, lord_1_body["sign"], deg_1)
        house_1lord = _house_of(lord_1_body["sign_index"], ascendant_sign_index)

        if (
            dignity_9 in {"exalted", "moolatrikona", "own_sign"}
            and house_9lord in KENDRA_TRIKONA_HOUSES
            and house_1lord in KENDRA_TRIKONA_HOUSES
            and dignity_1 not in {"debilitated", "enemy_sign"}
        ):
            yogas.append({"id": "lakshmi_yoga", "label": "Lakshmi Yoga", "bodies": [lord_9, lord_1]})

    # ---------------- Vasumati Yoga ----------------
    # Medium confidence (house-set {3,6,10,11} vs {3,6,11} disputed
    # across sources -- the 4-house upachaya set used here, and
    # deliberately scoped to Jupiter/Venus/Mercury only, excluding a
    # conditionally-benefic waxing Moon per this module's documented
    # NATURAL_BENEFICS simplification).

    upachaya_count = 0
    for planet in NATURAL_BENEFICS:
        body = bodies.get(planet)
        if body and _house_of(body["sign_index"], ascendant_sign_index) in UPACHAYA_HOUSES:
            upachaya_count += 1

    if upachaya_count > 0:
        yogas.append(
            {
                "id": "vasumati_yoga",
                "label": "Vasumati Yoga",
                "bodies": [
                    p for p in NATURAL_BENEFICS
                    if bodies.get(p) and _house_of(bodies[p]["sign_index"], ascendant_sign_index) in UPACHAYA_HOUSES
                ],
                "strength": upachaya_count,
            }
        )

    # ---------------- Sunapha / Anapha / Durudhara / Kemadruma ----------------
    # High confidence (BPHS Ch. 37, the "Lunar Yogas" chapter).
    # Scoped to the 6 non-Sun, non-Moon classical planets, matching
    # this module's existing convention of computing over the 7
    # traditional planets rather than including the nodes here.

    if moon_sign_index is not None:
        _lunar_candidates = [p for p in CLASSICAL_PLANETS if p not in ("sun", "moon")]

        in_2nd_from_moon = [
            p for p in _lunar_candidates
            if bodies.get(p) and whole_sign_house(bodies[p]["sign_index"], moon_sign_index) == 2
        ]
        in_12th_from_moon = [
            p for p in _lunar_candidates
            if bodies.get(p) and whole_sign_house(bodies[p]["sign_index"], moon_sign_index) == 12
        ]

        if in_2nd_from_moon and in_12th_from_moon:
            yogas.append(
                {"id": "durudhara_yoga", "label": "Durudhara Yoga", "bodies": in_2nd_from_moon + in_12th_from_moon}
            )
        elif in_2nd_from_moon:
            yogas.append({"id": "sunapha_yoga", "label": "Sunapha Yoga", "bodies": in_2nd_from_moon})
        elif in_12th_from_moon:
            yogas.append({"id": "anapha_yoga", "label": "Anapha Yoga", "bodies": in_12th_from_moon})
        else:
            yogas.append({"id": "kemadruma_yoga", "label": "Kemadruma Yoga", "bodies": ["moon"]})

        # ---------------- Adhi Yoga ----------------
        # High confidence (BPHS Ch. 37). Jupiter/Venus/Mercury in the
        # 6th, 7th, or 8th from the Moon.

        adhi_planets = [
            p for p in NATURAL_BENEFICS
            if bodies.get(p) and whole_sign_house(bodies[p]["sign_index"], moon_sign_index) in (6, 7, 8)
        ]
        if adhi_planets:
            yogas.append(
                {"id": "adhi_yoga", "label": "Adhi Yoga", "bodies": adhi_planets, "strength": len(adhi_planets)}
            )

        # ---------------- Chandra-Mangala Yoga ----------------
        mars_body = bodies.get("mars")
        if mars_body and mars_body["sign_index"] == moon_sign_index:
            yogas.append({"id": "chandra_mangala_yoga", "label": "Chandra-Mangala Yoga", "bodies": ["moon", "mars"]})

        # ---------------- Vish Yoga ----------------
        saturn_body = bodies.get("saturn")
        if saturn_body and saturn_body["sign_index"] == moon_sign_index:
            yogas.append({"id": "vish_yoga", "label": "Vish Yoga", "bodies": ["moon", "saturn"]})

        # ---------------- Shakata Yoga ----------------
        # High confidence (Phaladeepika, incl. cancellation rule).
        jupiter_body = bodies.get("jupiter")
        if jupiter_body:
            house_moon_from_jupiter = whole_sign_house(moon_sign_index, jupiter_body["sign_index"])
            moon_house_from_asc = _house_of(moon_sign_index, ascendant_sign_index)
            if house_moon_from_jupiter in DUSTHANA_HOUSES and moon_house_from_asc not in KENDRA_HOUSES:
                yogas.append({"id": "shakata_yoga", "label": "Shakata Yoga", "bodies": ["moon", "jupiter"]})

    # ---------------- Vesi / Vasi / Ubhayachari Yoga ----------------
    # High confidence (BPHS Ch. 38 + Saravali exclusion clause).

    if sun_sign_index is not None:
        _solar_candidates = [p for p in CLASSICAL_PLANETS if p not in ("sun", "moon")]

        in_2nd_from_sun = [
            p for p in _solar_candidates
            if bodies.get(p) and whole_sign_house(bodies[p]["sign_index"], sun_sign_index) == 2
        ]
        in_12th_from_sun = [
            p for p in _solar_candidates
            if bodies.get(p) and whole_sign_house(bodies[p]["sign_index"], sun_sign_index) == 12
        ]

        if in_2nd_from_sun and in_12th_from_sun:
            yogas.append(
                {"id": "ubhayachari_yoga", "label": "Ubhayachari Yoga", "bodies": in_2nd_from_sun + in_12th_from_sun}
            )
        elif in_2nd_from_sun:
            yogas.append({"id": "vesi_yoga", "label": "Vesi Yoga", "bodies": in_2nd_from_sun})
        elif in_12th_from_sun:
            yogas.append({"id": "vasi_yoga", "label": "Vasi Yoga", "bodies": in_12th_from_sun})

    # ---------------- Guru Chandal Yoga / Angarak Yoga ----------------
    # Medium confidence (mechanism unambiguous; classical-textual
    # pedigree for the nodes' role in yoga-formation is weaker than
    # for the seven true grahas above).

    rahu_body = bodies.get(_NODE_BODY_NAMES["rahu"])
    ketu_body = bodies.get(_NODE_BODY_NAMES["ketu"])

    if rahu_body and jupiter and rahu_body["sign_index"] == jupiter["sign_index"]:
        yogas.append({"id": "guru_chandal_yoga", "label": "Guru Chandal Yoga", "bodies": ["jupiter", "rahu"]})

    mars_body = bodies.get("mars")
    if mars_body and rahu_body and mars_body["sign_index"] == rahu_body["sign_index"]:
        yogas.append({"id": "angarak_yoga", "label": "Angarak Yoga", "bodies": ["mars", "rahu"]})
    if mars_body and ketu_body and mars_body["sign_index"] == ketu_body["sign_index"]:
        yogas.append({"id": "angarak_yoga", "label": "Angarak Yoga", "bodies": ["mars", "ketu"]})

    # ---------------- Amala Yoga ----------------
    # High confidence (BPHS Ch. 36). Implemented as two independently-
    # attested variants (from Lagna, from Moon) rather than merged,
    # since sources don't agree which is primary.

    def _amala(reference_sign_index, variant_id, variant_label):
        tenth_sign = _sign_of_house(10, reference_sign_index)
        occupants = [
            p for p in CLASSICAL_PLANETS
            if bodies.get(p) and bodies[p]["sign_index"] == tenth_sign
        ]
        if occupants and all(p in NATURAL_BENEFICS for p in occupants):
            yogas.append({"id": variant_id, "label": variant_label, "bodies": occupants})

    _amala(ascendant_sign_index, "amala_yoga_lagna", "Amala Yoga (from Lagna)")
    if moon_sign_index is not None:
        _amala(moon_sign_index, "amala_yoga_chandra", "Amala Yoga (from Moon)")

    # ---------------- Saraswati Yoga ----------------
    # Medium-high confidence.

    _saraswati_houses = {1, 2, 4, 5, 7, 9, 10}
    saraswati_planets = [
        p for p in NATURAL_BENEFICS
        if bodies.get(p) and _house_of(bodies[p]["sign_index"], ascendant_sign_index) in _saraswati_houses
    ]
    if len(saraswati_planets) == 3:
        jupiter_dignity = None
        if jupiter:
            deg_j = jupiter["longitude"] % 30.0
            jupiter_dignity = classify_dignity("jupiter", jupiter["sign"], deg_j)
        if jupiter_dignity in {"exalted", "moolatrikona", "own_sign"}:
            yogas.append({"id": "saraswati_yoga", "label": "Saraswati Yoga", "bodies": saraswati_planets})

    # ---------------- Shubha Kartari / Papa Kartari Yoga (Lagna) ----------------
    # Medium-high confidence. "Hemming" of the Ascendant by benefics
    # or malefics in the 2nd and 12th houses, with no presence of the
    # opposite category in either.

    second_sign = _sign_of_house(2, ascendant_sign_index)
    twelfth_sign = _sign_of_house(12, ascendant_sign_index)

    def _occupants(sign_index, planet_pool):
        result = []
        for p in planet_pool:
            body = bodies.get(p) or bodies.get(_NODE_BODY_NAMES.get(p, ""))
            if body and body["sign_index"] == sign_index:
                result.append(p)
        return result

    _kartari_pool = list(CLASSICAL_PLANETS) + ["rahu", "ketu"]

    benefics_2nd = _occupants(second_sign, NATURAL_BENEFICS)
    benefics_12th = _occupants(twelfth_sign, NATURAL_BENEFICS)
    malefics_2nd = _occupants(second_sign, NATURAL_MALEFICS)
    malefics_12th = _occupants(twelfth_sign, NATURAL_MALEFICS)

    if benefics_2nd and benefics_12th and not malefics_2nd and not malefics_12th:
        yogas.append(
            {"id": "shubha_kartari_yoga", "label": "Shubha Kartari Yoga", "bodies": benefics_2nd + benefics_12th}
        )
    if malefics_2nd and malefics_12th and not benefics_2nd and not benefics_12th:
        yogas.append(
            {"id": "papa_kartari_yoga", "label": "Papa Kartari Yoga", "bodies": malefics_2nd + malefics_12th}
        )

    # ---------------- Guru-Mangala Yoga ----------------
    # Low-medium confidence (well-attested in contemporary practice;
    # no primary BPHS/Phaladeepika/Saravali citation found for this
    # specific named combination during curation).

    if jupiter and mars_body and jupiter["sign_index"] == mars_body["sign_index"]:
        yogas.append({"id": "guru_mangala_yoga", "label": "Guru-Mangala Yoga", "bodies": ["jupiter", "mars"]})

    return yogas


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.sidereal import build_sidereal_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    sidereal = build_sidereal_chart(tropical)
    yogas = find_yogas(sidereal)

    if yogas:
        for yoga in yogas:
            print(f"{yoga['label']:30s} ({', '.join(yoga['bodies'])})")
    else:
        print("No yogas from the curated set found in this chart.")

    print()
    print(f"Total: {len(yogas)} yoga(s) found.")
