"""
Celeste discovery store.

Stores discovered research material without treating it as
verified Celeste knowledge.
"""

import json
from pathlib import Path


DISCOVERY_DIR = Path("knowledge/documents")
DISCOVERY_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def save_discoveries(
    query,
    results,
):
    """
    Save one discovery search as a JSON document.

    Discoveries remain research material.
    They are not trusted claims.
    """

    safe_query = (
        query.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    path = DISCOVERY_DIR / f"{safe_query}.json"

    payload = {
        "query": query,
        "source": "openalex",
        "status": "discovered",
        "results": results,
    }

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        )
    )

    return path
