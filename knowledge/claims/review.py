"""
Celeste claim review.

Manages the editorial boundary between:
    candidate knowledge
and:
    approved knowledge

Nothing becomes trusted knowledge without review.
"""

import json
from dataclasses import asdict
from pathlib import Path

from .model import CandidateClaim


REVIEW_DIR = Path("knowledge/claims/review")
REVIEW_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def save_candidate(claim):
    """
    Save one candidate claim for editorial review.
    """

    path = (
        REVIEW_DIR
        / f"{claim.claim_id}.json"
    )

    path.write_text(
        json.dumps(
            asdict(claim),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return path


def load_candidate(claim_id):
    """
    Load a candidate claim from the review queue.
    """

    path = (
        REVIEW_DIR
        / f"{claim_id}.json"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Candidate not found: {claim_id}"
        )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    return CandidateClaim(
        claim_id=data["claim_id"],
        lens_id=data["lens_id"],
        statement=data["statement"],
        passage_ids=data.get(
            "passage_ids",
            [],
        ),
        concept_ids=data.get(
            "concept_ids",
            [],
        ),
        source_ids=data.get(
            "source_ids",
            [],
        ),
        theme_tags=data.get(
            "theme_tags",
            [],
        ),
        status=data.get(
            "status",
            "candidate",
        ),
        notes=data.get(
            "notes",
            "",
        ),
    )


def set_status(
    claim_id,
    status,
    notes="",
):
    """
    Update editorial status.

    Valid statuses:
        candidate
        approved
        rejected
        needs_edit
    """

    valid_statuses = {
        "candidate",
        "approved",
        "rejected",
        "needs_edit",
    }

    if status not in valid_statuses:
        raise ValueError(
            f"Invalid status: {status}"
        )

    claim = load_candidate(
        claim_id
    )

    claim.status = status
    claim.notes = notes

    return save_candidate(
        claim
    )


def list_candidates():
    """
    Return all claims currently in the review queue.
    """

    candidates = []

    for path in sorted(
        REVIEW_DIR.glob("*.json")
    ):
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        candidates.append(
            data
        )

    return candidates


def print_queue():
    """
    Print a human-readable review queue.
    """

    candidates = list_candidates()

    if not candidates:
        print(
            "Review queue is empty."
        )
        return

    print(
        "=== CELESTE KNOWLEDGE REVIEW ==="
    )
    print()

    for candidate in candidates:
        print(
            f"[{candidate.get('status', 'candidate').upper()}]"
        )
        print(
            f"ID: {candidate['claim_id']}"
        )
        print(
            f"Lens: {candidate['lens_id']}"
        )
        print()
        print(
            candidate["statement"]
        )
        print()

        concepts = candidate.get(
            "concept_ids",
            [],
        )

        if concepts:
            print(
                "Concepts: "
                + ", ".join(concepts)
            )

        passages = candidate.get(
            "passage_ids",
            [],
        )

        if passages:
            print(
                "Evidence: "
                + ", ".join(passages)
            )

        print()
        print(
            "Notes: "
            + candidate.get(
                "notes",
                "",
            )
        )

        print()
        print(
            "-" * 60
        )
        print()


if __name__ == "__main__":
    print_queue()
