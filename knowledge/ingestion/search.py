"""
Celeste knowledge discovery.

Searches scholarly metadata sources for material that may later
become part of the curated knowledge base.

Important:
This module discovers sources only.
It does not create trusted claims.
"""

import sys
import requests

from .store import save_discoveries


OPENALEX_URL = "https://api.openalex.org/works"


def search_openalex(query, limit=10):
    response = requests.get(
        OPENALEX_URL,
        params={
            "search": query,
            "per-page": limit,
        },
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for item in data.get("results", []):
        primary_location = (
            item.get("primary_location") or {}
        )

        source = (
            primary_location.get("source") or {}
        )

        authors = []

        for authorship in item.get(
            "authorships",
            []
        ):
            author = (
                authorship.get("author") or {}
            )

            name = author.get(
                "display_name"
            )

            if name:
                authors.append(name)

        results.append({
            "source": "openalex",
            "id": item.get("id"),
            "title": item.get(
                "display_name"
            ),
            "year": item.get(
                "publication_year"
            ),
            "type": item.get("type"),
            "doi": item.get("doi"),
            "authors": authors,
            "journal": source.get(
                "display_name"
            ),
            "open_access": (
                item.get("open_access") or {}
            ).get("is_oa"),
            "landing_page": (
                primary_location.get(
                    "landing_page_url"
                )
            ),
        })

    return results


def search(query, limit=10):
    results = search_openalex(
        query,
        limit=limit,
    )

    save_discoveries(
        query,
        results,
    )

    return results


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: "
            'python -m knowledge.ingestion.search '
            '"search terms"'
        )
        raise SystemExit(1)

    query = " ".join(
        sys.argv[1:]
    )

    print(
        f"Searching scholarly sources for: "
        f"{query}"
    )
    print()

    results = search(query)

    print(
        f"Found {len(results)} results."
    )
    print()

    for index, result in enumerate(
        results,
        start=1,
    ):
        print(
            f"{index}. "
            f"{result['title']}"
        )

        print(
            "   Authors: "
            + (
                ", ".join(
                    result["authors"]
                )
                or "Unknown"
            )
        )

        print(
            f"   Year: "
            f"{result['year']}"
        )

        print(
            f"   Type: "
            f"{result['type']}"
        )

        print(
            f"   DOI: "
            f"{result['doi'] or 'None'}"
        )

        print(
            f"   Open access: "
            f"{result['open_access']}"
        )

        print()


if __name__ == "__main__":
    main()
