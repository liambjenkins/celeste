"""
Celeste approved knowledge store.

Provides read-only access to claims that have passed
editorial review.
"""

import json
from pathlib import Path

from knowledge.claims.model import ApprovedClaim


APPROVED_DIR = Path(
    "knowledge/claims/approved"
)


def load_approved_claims(
    lens_id=None,
):
    """
    Load approved claims.

    If lens_id is supplied, only claims belonging
    to that lens are returned.
    """

    claims = []

    for path in sorted(
        APPROVED_DIR.glob("*.json")
    ):
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if data.get("status") != "approved":
            continue

        if (
            lens_id is not None
            and data.get("lens_id")
            != lens_id
        ):
            continue

        claims.append(
            ApprovedClaim(
                claim_id=data["claim_id"],
                lens_id=data["lens_id"],
                statement=data["statement"],
                passage_ids=tuple(
                    data.get(
                        "passage_ids",
                        [],
                    )
                ),
                concept_ids=tuple(
                    data.get(
                        "concept_ids",
                        [],
                    )
                ),
                feature_ids=tuple(
                    data.get(
                        "feature_ids",
                        [],
                    )
                ),
                source_ids=tuple(
                    data.get(
                        "source_ids",
                        [],
                    )
                ),
                editorial_note=data.get(
                    "editorial_note",
                    data.get(
                        "notes",
                        "",
                    ),
                ),
            )
        )

    return claims


def get_claim(
    claim_id,
):
    """
    Retrieve one approved claim.
    """

    for claim in load_approved_claims():
        if claim.claim_id == claim_id:
            return claim

    raise KeyError(
        f"Approved claim not found: "
        f"{claim_id}"
    )


if __name__ == "__main__":
    claims = load_approved_claims()

    print(
        f"Loaded {len(claims)} "
        "approved claim(s)."
    )

    for claim in claims:
        print()
        print(
            f"[{claim.lens_id}] "
            f"{claim.claim_id}"
        )
        print(
            claim.statement
        )
        print(
            "Concepts:",
            ", ".join(
                claim.concept_ids
            ),
        )
