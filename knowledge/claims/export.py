"""
Celeste approved-claim exporter.

Only reviewed claims with status == "approved"
may enter the trusted knowledge store.

The exporter is intentionally conservative:
- candidate claims stay in review/
- rejected claims stay in review/
- needs_edit claims stay in review/
- only approved claims are copied
"""

import json
from pathlib import Path


REVIEW_DIR = Path("knowledge/claims/review")
APPROVED_DIR = Path("knowledge/claims/approved")

APPROVED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def export_approved():
    exported = []

    for path in sorted(
        REVIEW_DIR.glob("*.json")
    ):
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if data.get("status") != "approved":
            continue

        required_fields = (
            "claim_id",
            "lens_id",
            "statement",
        )

        missing = [
            field
            for field in required_fields
            if not data.get(field)
        ]

        if missing:
            print(
                f"⚠ Skipping {path.name}: "
                f"missing {', '.join(missing)}"
            )
            continue

        output = (
            APPROVED_DIR
            / path.name
        )

        output.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        exported.append(output)

    return exported


def main():
    exported = export_approved()

    if not exported:
        print(
            "No approved claims to export."
        )
        return

    print(
        "=== APPROVED KNOWLEDGE ==="
    )

    for path in exported:
        print(
            f"✓ {path}"
        )

    print()
    print(
        f"Exported {len(exported)} claim(s)."
    )


if __name__ == "__main__":
    main()
