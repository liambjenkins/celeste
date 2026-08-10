"""
Celeste knowledge extraction CLI.

Source text is passed through a model backend, converted into
validated claim proposals, and written only to the editorial
review queue.

Nothing is automatically approved.
"""

import argparse
import os
from pathlib import Path

from knowledge.claims.llm_extractor import LLMClaimExtractor
from knowledge.claims.model import SourcePassage
from knowledge.claims.pipeline import ingest_candidates
from knowledge.providers.http_llm import HTTPModelBackend


def main():
    parser = argparse.ArgumentParser(
        description="Extract candidate Celeste knowledge."
    )

    parser.add_argument(
        "source",
        help="Path to source text file.",
    )

    parser.add_argument(
        "--lens",
        required=True,
        help="Lens ID, e.g. astrology.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration without calling the model.",
    )

    args = parser.parse_args()

    path = Path(args.source)

    if not path.exists():
        raise SystemExit(
            f"Source file not found: {path}"
        )

    text = path.read_text(
        encoding="utf-8"
    ).strip()

    if not text:
        raise SystemExit(
            "Source file is empty."
        )

    if args.dry_run:
        required = (
            "CELESTE_LLM_ENDPOINT",
            "CELESTE_LLM_API_KEY",
            "CELESTE_LLM_MODEL",
        )

        missing = [
            name
            for name in required
            if not os.getenv(name)
        ]

        if missing:
            print("=== EXTRACTION DRY RUN ===")
            print()
            print("Source:", path)
            print("Lens:", args.lens)
            print()
            print("Missing configuration:")

            for name in missing:
                print("-", name)

            print()
            print(
                "No model request was made."
            )
            return

        print("=== EXTRACTION DRY RUN ===")
        print()
        print("Source:", path)
        print("Lens:", args.lens)
        print("Endpoint:", os.environ[
            "CELESTE_LLM_ENDPOINT"
        ])
        print("Model:", os.environ[
            "CELESTE_LLM_MODEL"
        ])
        print()
        print(
            "✓ configuration is complete"
        )
        print(
            "✓ no model request was made"
        )
        return

    passage = SourcePassage(
        passage_id=path.stem,
        document_id=path.name,
        text=text,
    )

    backend = HTTPModelBackend()

    extractor = LLMClaimExtractor(
        backend
    )

    paths = ingest_candidates(
        passages=[passage],
        lens_id=args.lens,
        extractor=extractor,
    )

    print("=== KNOWLEDGE EXTRACTION ===")
    print()
    print("Source:", path)
    print("Lens:", args.lens)
    print()
    print(
        f"Candidate claims created: {len(paths)}"
    )

    for output_path in paths:
        print("-", output_path)

    print()
    print(
        "Claims remain candidates pending "
        "editorial approval."
    )


if __name__ == "__main__":
    main()
