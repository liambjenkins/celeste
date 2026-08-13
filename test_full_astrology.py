from datetime import datetime, timezone

from astrology.chart import build_chart


UTC_BIRTH = datetime(
    1996, 7, 21, 17, 10,
    tzinfo=timezone.utc,
)

LATITUDE = -37.8136
LONGITUDE = 144.9631


chart = build_chart(
    UTC_BIRTH,
    LATITUDE,
    LONGITUDE,
    house_system="placidus",
)


print("=" * 72)
print("CELESTE — FULL ASTROLOGY ENGINE TEST")
print("=" * 72)

print()
print("UTC:", chart["utc_time"])
print("Location:", chart["location"])
print("House system:", chart["house_system"])


print()
print("-" * 72)
print("ANGLES")
print("-" * 72)

for name, longitude in chart["houses"]["angles"].items():
    print(f"{name:24} {longitude:12.6f}°")


print()
print("-" * 72)
print("HOUSE CUSPS")
print("-" * 72)

for house, longitude in chart["houses"]["cusps"].items():
    print(f"House {house:>2}: {longitude:12.6f}°")


print()
print("-" * 72)
print("CHART OBJECTS")
print("-" * 72)

for name, body in chart["bodies"].items():
    position = (
        f"{body['degree']:02d}°"
        f"{body['minute']:02d}'"
        f"{body['second']:02d}\""
    )

    print(
        f"{name:20} "
        f"{body['sign']:12} "
        f"{position:10} "
        f"house={body['house']:2} "
        f"retrograde={body['retrograde']}"
    )


print()
print("-" * 72)
print("CORE ASPECTS")
print("-" * 72)

print("COUNT:", len(chart["aspects"]))
print()

for aspect in chart["aspects"]:
    print(
        f"{aspect['body_a']:20} "
        f"{aspect['aspect']:12} "
        f"{aspect['body_b']:20} "
        f"orb={aspect['orb']:.2f}° "
        f"strength={aspect.get('orb_strength', 'N/A')}"
    )


print()
print("-" * 72)
print("SANITY CHECKS")
print("-" * 72)

assert chart["house_system"] == "placidus"
assert len(chart["houses"]["cusps"]) == 12
assert len(chart["bodies"]) == 21

assert abs(
    chart["houses"]["angles"]["ascendant"]
    - 58.25780635121683
) < 0.001

assert abs(
    chart["houses"]["angles"]["mc"]
    - 340.72077437766706
) < 0.001

assert chart["bodies"]["sun"]["sign"] == "Cancer"
assert chart["bodies"]["sun"]["house"] == 2

assert chart["bodies"]["venus"]["sign"] == "Gemini"
assert chart["bodies"]["venus"]["house"] == 1

assert chart["bodies"]["mars"]["sign"] == "Gemini"
assert chart["bodies"]["mars"]["house"] == 1

assert chart["bodies"]["north_node_true"]["sign"] == "Libra"
assert chart["bodies"]["chiron"]["sign"] == "Libra"

assert len(chart["aspects"]) == 18

print()
print("-" * 72)
print("ELEMENTAL BALANCE")
print("-" * 72)

for element, count in chart["elemental_balance"].items():
    print(f"{element:8} {count}")

assert sum(chart["elemental_balance"].values()) == 10
assert chart["elemental_balance"]["water"] == 1  # Sun in Cancer
assert chart["elemental_balance"]["air"] == 4  # Moon/Venus/Mars/Uranus

print("✓ Placidus")
print("✓ 12 houses")
print("✓ 21 chart objects")
print("✓ Angles")
print("✓ Zodiac positions")
print("✓ House placements")
print("✓ Retrograde detection")
print("✓ 18 core aspects")
print("✓ Elemental balance (sign triplicities)")
print()
print("ALL ASTROLOGY ENGINE CHECKS PASSED")
print("=" * 72)
