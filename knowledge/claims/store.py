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

# Process-lifetime cache of every approved claim, built once on first
# access. Callers (resolve_claims() chief among them) hit this dozens
# of times per daily-mode request; re-globbing and re-parsing all
# ~1,100+ approved-claim JSON files on every single call was real,
# measured latency. Nothing in this codebase writes claim JSON and
# then reads it back in the same process -- write_claims() runs as
# its own standalone script invocation -- so caching for the life of
# the process cannot serve stale data in any real run.
_ALL_CLAIMS_CACHE = None


def _load_all_claims():
    global _ALL_CLAIMS_CACHE

    if _ALL_CLAIMS_CACHE is not None:
        return _ALL_CLAIMS_CACHE

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
                theme_tags=tuple(
                    data.get(
                        "theme_tags",
                        [],
                    )
                ),
                life_domain=data.get(
                    "life_domain"
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

    _ALL_CLAIMS_CACHE = claims
    return claims


def load_approved_claims(
    lens_id=None,
):
    """
    Load approved claims.

    If lens_id is supplied, only claims belonging
    to that lens are returned.
    """

    claims = _load_all_claims()

    if lens_id is None:
        return claims

    return [
        claim
        for claim in claims
        if claim.lens_id == lens_id
    ]


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
