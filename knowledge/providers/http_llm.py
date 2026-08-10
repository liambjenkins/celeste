"""
HTTP LLM provider for Celeste.

This is deliberately isolated from the knowledge pipeline.
The provider's only job is:

    source passage → model request → structured JSON payload

Validation happens downstream in the semantic extraction layer.
"""

import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()


class HTTPModelBackend:
    """
    Generic OpenAI-compatible HTTP backend.

    The endpoint and API key are supplied through environment
    variables so provider configuration never leaks into the
    knowledge model.
    """

    def __init__(
        self,
        *,
        endpoint=None,
        api_key=None,
        model=None,
        timeout=60,
    ):
        self.endpoint = (
            endpoint
            or os.getenv(
                "CELESTE_LLM_ENDPOINT"
            )
        )

        self.api_key = (
            api_key
            or os.getenv(
                "CELESTE_LLM_API_KEY"
            )
        )

        self.model = (
            model
            or os.getenv(
                "CELESTE_LLM_MODEL"
            )
        )

        self.timeout = timeout

        if not self.endpoint:
            raise ValueError(
                "CELESTE_LLM_ENDPOINT is required."
            )

        if not self.api_key:
            raise ValueError(
                "CELESTE_LLM_API_KEY is required."
            )

        if not self.model:
            raise ValueError(
                "CELESTE_LLM_MODEL is required."
            )

    def extract_claims(
        self,
        *,
        passage,
        lens_id,
    ):
        prompt = f"""
You are a source-grounded knowledge extraction system.

Lens:
{lens_id}

Source passage:
{passage.text}

Extract only claims explicitly supported by the passage.

Return JSON only:

{{
  "proposals": [
    {{
      "statement": "source-grounded claim",
      "concept_ids": ["concept"],
      "feature_ids": ["feature"]
    }}
  ]
}}

Do not add outside knowledge.
Do not interpret beyond the passage.
Do not approve claims.
"""

        response = requests.post(
            self.endpoint,
            headers={
                "Authorization": (
                    f"Bearer {self.api_key}"
                ),
                "Content-Type": (
                    "application/json"
                ),
            },
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "temperature": 0,
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        content = (
            data["choices"][0]["message"]["content"]
        )

        if isinstance(content, str):
            content = content.strip()

            if content.startswith(
                "```"
            ):
                content = content.strip(
                    "`"
                )

                if content.startswith(
                    "json"
                ):
                    content = content[4:]

            return json.loads(content)

        if isinstance(content, dict):
            return content

        raise ValueError(
            "LLM response did not contain "
            "structured JSON content."
        )
