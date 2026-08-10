"""
Celeste interactive claim reviewer.

This is an editorial tool, not an interpretation engine.

A reviewer can:
    a = approve
    r = reject
    e = needs edit
    s = skip

Approved claims remain explicitly source-backed.
"""

from .review import (
    list_candidates,
    load_candidate,
    set_status,
)


def show_claim(claim):
    print()
    print("=" * 70)
    print("CELESTE — KNOWLEDGE REVIEW")
    print("=" * 70)
    print()

    print(f"Claim ID: {claim.claim_id}")
    print(f"Lens:     {claim.lens_id}")
    print(f"Status:   {claim.status}")
    print()

    print("CLAIM")
    print("-" * 70)
    print(claim.statement)
    print()

    print("CONCEPTS")
    print("-" * 70)

    if claim.concept_ids:
        for concept in claim.concept_ids:
            print(f"- {concept}")
    else:
        print("- none")

    print()

    print("EVIDENCE")
    print("-" * 70)

    if claim.passage_ids:
        for passage in claim.passage_ids:
            print(f"- {passage}")
    else:
        print("- none")

    print()

    print("SOURCES")
    print("-" * 70)

    if claim.source_ids:
        for source in claim.source_ids:
            print(f"- {source}")
    else:
        print("- none")

    print()

    print("NOTES")
    print("-" * 70)
    print(claim.notes or "- none")
    print()


def review_claim(claim_id):
    claim = load_candidate(
        claim_id
    )

    show_claim(claim)

    print("ACTION")
    print("-" * 70)
    print("[a] approve")
    print("[r] reject")
    print("[e] needs edit")
    print("[s] skip")
    print()

    action = input(
        "Choose: "
    ).strip().lower()

    if action == "a":
        notes = input(
            "Editorial note: "
        ).strip()

        set_status(
            claim_id,
            "approved",
            notes,
        )

        print()
        print(
            "✓ Claim approved."
        )

    elif action == "r":
        notes = input(
            "Reason for rejection: "
        ).strip()

        set_status(
            claim_id,
            "rejected",
            notes,
        )

        print()
        print(
            "✓ Claim rejected."
        )

    elif action == "e":
        notes = input(
            "What needs editing? "
        ).strip()

        set_status(
            claim_id,
            "needs_edit",
            notes,
        )

        print()
        print(
            "✓ Claim marked for editing."
        )

    elif action == "s":
        print(
            "Skipped."
        )

    else:
        print(
            "Unknown action. Nothing changed."
        )


def main():
    candidates = list_candidates()

    if not candidates:
        print(
            "Review queue is empty."
        )
        return

    print(
        "=== CELESTE REVIEW QUEUE ==="
    )
    print()

    for index, candidate in enumerate(
        candidates,
        1,
    ):
        print(
            f"{index}. "
            f"[{candidate.get('status', 'candidate')}] "
            f"{candidate['claim_id']}"
        )

    print()

    choice = input(
        "Review claim number: "
    ).strip()

    try:
        index = int(choice)
    except ValueError:
        print(
            "Please enter a number."
        )
        return

    if index < 1 or index > len(candidates):
        print(
            "Invalid claim number."
        )
        return

    claim_id = candidates[
        index - 1
    ]["claim_id"]

    review_claim(
        claim_id
    )


if __name__ == "__main__":
    main()
