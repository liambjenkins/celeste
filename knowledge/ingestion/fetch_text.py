# knowledge/ingestion/fetch_text.py
"""
Celeste document acquisition.

This layer attempts to retrieve legitimately accessible material
from previously discovered scholarly sources.

It does NOT:
- bypass paywalls
- bypass authentication
- retry aggressively after rate limiting
- create claims
- interpret sources

It records retrieval outcomes so later stages can decide what
material is actually available for review.
"""

import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests


DOCUMENT_DIR = Path("knowledge/documents")
TEXT_DIR = DOCUMENT_DIR / "text"
RESULT_DIR = DOCUMENT_DIR / "retrieval_results"

TEXT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


HEADERS = {
    "User-Agent": (
        "CelesteResearch/0.1 "
        "(scholarly knowledge discovery)"
    )
}


def load_retrieval(path):
    return json.loads(
        Path(path).read_text(
            encoding="utf-8"
        )
    )


def document_id_from_retrieval(
    retrieval
):
    """
    Convert the OpenAlex work URL into a
    stable local document identifier.
    """

    openalex_id = retrieval.get(
        "openalex_id",
        ""
    )

    return (
        openalex_id
        .rstrip("/")
        .split("/")
        [-1]
    )


def fetch_url(url):
    """
    Fetch one public URL.

    Rate limiting and ordinary HTTP failures are
    returned to the caller rather than retried
    aggressively.
    """

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
        allow_redirects=True,
    )

    if response.status_code == 429:
        raise RuntimeError(
            "Source returned HTTP 429 "
            "(Too Many Requests). "
            "The repository is rate-limiting "
            "automated access."
        )

    if response.status_code == 403:
        raise RuntimeError(
            "Source returned HTTP 403 "
            "(Forbidden). "
            "Automated access is not permitted."
        )

    if response.status_code == 404:
        raise RuntimeError(
            "Source returned HTTP 404 "
            "(Not Found)."
        )

    response.raise_for_status()

    return response


def find_pdf_links(
    html,
    base_url,
):
    """
    Find obvious PDF links on a public
    HTML landing page.
    """

    links = re.findall(
        r'href=["\']([^"\']+)["\']',
        html,
        flags=re.IGNORECASE,
    )

    pdf_links = []

    for link in links:
        absolute = urljoin(
            base_url,
            link,
        )

        if (
            ".pdf" in absolute.lower()
            and absolute not in pdf_links
        ):
            pdf_links.append(
                absolute
            )

    return pdf_links


def get_accessible_locations(
    retrieval
):
    """
    Return all legitimate locations recorded
    by the discovery stage.
    """

    locations = retrieval.get(
        "accessible_locations",
        [],
    )

    if not isinstance(
        locations,
        list,
    ):
        return []

    return locations


def save_json(
    path,
    data,
):
    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def save_text(
    document_id,
    text,
):
    path = (
        TEXT_DIR
        / f"{document_id}.txt"
    )

    path.write_text(
        text,
        encoding="utf-8",
    )

    return path


def save_pdf(
    document_id,
    content,
):
    path = (
        TEXT_DIR
        / f"{document_id}.pdf"
    )

    path.write_bytes(
        content
    )

    return path


def inspect_response(
    response,
    document_id,
    original_url,
):
    """
    Handle a successfully retrieved response.
    """

    content_type = (
        response.headers
        .get(
            "content-type",
            "",
        )
        .lower()
    )

    final_url = response.url

    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    if (
        "application/pdf"
        in content_type
        or final_url.lower().endswith(
            ".pdf"
        )
    ):
        path = save_pdf(
            document_id,
            response.content,
        )

        return {
            "status": "pdf_downloaded",
            "url": final_url,
            "original_url": original_url,
            "path": str(path),
            "content_type": content_type,
        }

    # --------------------------------------------------------
    # Plain text
    # --------------------------------------------------------

    if (
        "text/plain"
        in content_type
    ):
        path = save_text(
            document_id,
            response.text,
        )

        return {
            "status": "text_saved",
            "url": final_url,
            "original_url": original_url,
            "path": str(path),
            "content_type": content_type,
        }

    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    if "text/html" in content_type:
        pdf_links = find_pdf_links(
            response.text,
            final_url,
        )

        return {
            "status": "landing_page",
            "url": final_url,
            "original_url": original_url,
            "content_type": content_type,
            "pdf_links": pdf_links,
        }

    # --------------------------------------------------------
    # Unknown content
    # --------------------------------------------------------

    return {
        "status": "unsupported_content",
        "url": final_url,
        "original_url": original_url,
        "content_type": content_type,
    }


def try_location(
    document_id,
    location,
):
    """
    Attempt one legitimate accessible location.
    """

    pdf_url = location.get(
        "pdf_url"
    )

    landing_page = location.get(
        "landing_page"
    )

    source = location.get(
        "source"
    )

    license_name = location.get(
        "license"
    )

    # Prefer an explicit PDF URL.
    url = (
        pdf_url
        or landing_page
    )

    if not url:
        return {
            "status": "no_url",
            "source": source,
            "license": license_name,
        }

    print(
        f"Fetching: {url}"
    )

    try:
        response = fetch_url(
            url
        )

    except RuntimeError as exc:
        return {
            "status": "temporarily_unavailable",
            "url": url,
            "source": source,
            "license": license_name,
            "reason": str(exc),
        }

    except requests.RequestException as exc:
        return {
            "status": "request_failed",
            "url": url,
            "source": source,
            "license": license_name,
            "reason": str(exc),
        }

    result = inspect_response(
        response,
        document_id,
        url,
    )

    result["source"] = source
    result["license"] = license_name

    # --------------------------------------------------------
    # If this is an HTML repository page, try any obvious
    # public PDF links it exposes.
    # --------------------------------------------------------

    if (
        result["status"]
        == "landing_page"
    ):
        pdf_links = result.get(
            "pdf_links",
            [],
        )

        for pdf_url in pdf_links:
            print(
                f"Trying PDF: {pdf_url}"
            )

            try:
                pdf_response = fetch_url(
                    pdf_url
                )

            except RuntimeError as exc:
                continue

            except requests.RequestException:
                continue

            pdf_result = inspect_response(
                pdf_response,
                document_id,
                pdf_url,
            )

            if (
                pdf_result["status"]
                == "pdf_downloaded"
            ):
                pdf_result[
                    "source"
                ] = source

                pdf_result[
                    "license"
                ] = license_name

                return pdf_result

        return result

    return result


def retrieve_work(
    retrieval
):
    """
    Try all legitimate locations recorded
    by the discovery layer.
    """

    document_id = (
        document_id_from_retrieval(
            retrieval
        )
    )

    locations = (
        get_accessible_locations(
            retrieval
        )
    )

    attempts = []

    if not locations:
        result = {
            "document_id": document_id,
            "status": "no_accessible_locations",
            "attempts": [],
        }

        return result

    for index, location in enumerate(
        locations,
        1,
    ):
        print(
            f"\nLocation {index} "
            f"of {len(locations)}"
        )

        result = try_location(
            document_id,
            location,
        )

        attempts.append(
            {
                "location": location,
                "result": result,
            }
        )

        # Stop as soon as we actually obtained
        # document material.
        if result["status"] in {
            "pdf_downloaded",
            "text_saved",
        }:
            return {
                "document_id": document_id,
                "status": result["status"],
                "path": result.get(
                    "path"
                ),
                "url": result.get(
                    "url"
                ),
                "source": result.get(
                    "source"
                ),
                "license": result.get(
                    "license"
                ),
                "attempts": attempts,
            }

    # Nothing was successfully retrieved.
    return {
        "document_id": document_id,
        "status": "no_document_retrieved",
        "attempts": attempts,
    }


def save_retrieval_result(
    result
):
    path = (
        RESULT_DIR
        / f"{result['document_id']}.json"
    )

    save_json(
        path,
        result,
    )

    return path


def main():
    if len(sys.argv) != 2:
        print(
            "Usage:"
        )
        print(
            "python -m "
            "knowledge.ingestion.fetch_text "
            "<retrieval.json>"
        )
        raise SystemExit(1)

    retrieval_path = sys.argv[1]

    retrieval = load_retrieval(
        retrieval_path
    )

    title = retrieval.get(
        "title",
        "Unknown work",
    )

    print(
        f"Inspecting: {title}"
    )

    result = retrieve_work(
        retrieval
    )

    result_path = (
        save_retrieval_result(
            result
        )
    )

    print()
    print(
        f"Status: "
        f"{result['status']}"
    )

    if result.get("path"):
        print(
            f"Saved: "
            f"{result['path']}"
        )

    print(
        f"Retrieval record: "
        f"{result_path}"
    )

    if result["status"] == (
        "no_document_retrieved"
    ):
        print()
        print(
            "No document was retrieved."
        )
        print(
            "The source remains recorded "
            "for later review or retry."
        )


if __name__ == "__main__":
    main()