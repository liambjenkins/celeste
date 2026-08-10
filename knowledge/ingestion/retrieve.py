"""
Celeste document retrieval.

Attempts to locate legitimately accessible full text for a
previously discovered scholarly work.

This layer does NOT:
- bypass paywalls
- scrape restricted material
- create claims
- interpret the source

It only records what is legitimately accessible.
"""

import json
import sys
from pathlib import Path

import requests


DOCUMENT_DIR = Path("knowledge/documents")
TEXT_DIR = Path("knowledge/documents/text")

TEXT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def load_discoveries(path):
    return json.loads(
        Path(path).read_text()
    )


def find_result(payload, index):
    results = payload.get(
        "results",
        [],
    )

    if index < 1 or index > len(results):
        raise ValueError(
            f"Result number must be "
            f"between 1 and {len(results)}"
        )

    return results[index - 1]


def get_openalex_work(openalex_id):
    work_id = openalex_id.rstrip("/").split("/")[-1]

    api_url = (
        "https://api.openalex.org/works/"
        + work_id
    )

    response = requests.get(
        api_url,
        timeout=20,
    )

    response.raise_for_status()

    return response.json()


def extract_accessible_locations(work):
    """
    Return legitimate locations supplied by OpenAlex.
    """

    locations = []

    for location in work.get(
        "locations",
        [],
    ):
        if not location:
            continue

        landing = location.get(
            "landing_page_url"
        )

        pdf = location.get(
            "pdf_url"
        )

        is_oa = location.get(
            "is_oa",
            False,
        )

        if is_oa and (
            landing or pdf
        ):
            locations.append({
                "landing_page": landing,
                "pdf_url": pdf,
                "source": (
                    location.get(
                        "source"
                    ) or {}
                ).get(
                    "display_name"
                ),
                "license": location.get(
                    "license"
                ),
            })

    return locations


def retrieve_work(result):
    """
    Inspect a discovered work and determine
    whether accessible locations exist.
    """

    openalex_id = result.get(
        "id"
    )

    if not openalex_id:
        raise ValueError(
            "Discovery has no OpenAlex ID."
        )

    work = get_openalex_work(
        openalex_id
    )

    locations = (
        extract_accessible_locations(
            work
        )
    )

    return {
        "title": work.get(
            "display_name"
        ),
        "openalex_id": openalex_id,
        "doi": work.get("doi"),
        "publication_year": work.get(
            "publication_year"
        ),
        "type": work.get("type"),
        "abstract": work.get(
            "abstract_inverted_index"
        ),
        "accessible_locations": locations,
        "status": (
            "accessible"
            if locations
            else "metadata_only"
        ),
    }


def save_retrieval(
    result,
    retrieved,
):
    """
    Save retrieval metadata alongside the
    discovery record.
    """

    work_id = (
        result["id"]
        .rstrip("/")
        .split("/")
        [-1]
    )

    path = (
        DOCUMENT_DIR
        / f"{work_id}_retrieval.json"
    )

    path.write_text(
        json.dumps(
            retrieved,
            indent=2,
            ensure_ascii=False,
        )
    )

    return path


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: "
            "python -m knowledge.ingestion.retrieve "
            "<discovery.json> <result_number>"
        )
        raise SystemExit(1)

    discovery_path = sys.argv[1]
    result_number = int(
        sys.argv[2]
    )

    payload = load_discoveries(
        discovery_path
    )

    result = find_result(
        payload,
        result_number,
    )

    print(
        f"Inspecting: "
        f"{result.get('title')}"
    )
    print()

    retrieved = retrieve_work(
        result
    )

    save_path = save_retrieval(
        result,
        retrieved,
    )

    print(
        f"Status: "
        f"{retrieved['status']}"
    )

    print(
        f"DOI: "
        f"{retrieved['doi'] or 'None'}"
    )

    print()

    locations = retrieved[
        "accessible_locations"
    ]

    if not locations:
        print(
            "No openly accessible full-text "
            "location was identified."
        )
    else:
        print(
            "Accessible locations:"
        )

        for location in locations:
            print(
                f"- "
                f"{location['source'] or 'Unknown'}"
            )

            print(
                f"  PDF: "
                f"{location['pdf_url'] or 'None'}"
            )

            print(
                f"  Page: "
                f"{location['landing_page'] or 'None'}"
            )

            print(
                f"  License: "
                f"{location['license'] or 'Unknown'}"
            )

    print()
    print(
        f"Saved retrieval record: "
        f"{save_path}"
    )


if __name__ == "__main__":
    main()
