"""
Narrative synthesis backend boundary.

Mirrors knowledge.claims.model_backend's existing pattern (an
abstract interface the rest of the system depends on, rather than a
specific provider) for a different concern: turning a grounded prompt
into prose at read time, instead of extracting candidate claims at
curation time.

AnthropicNarrativeBackend is a real, concrete implementation — plain
`requests` calls, no SDK dependency, matching this codebase's existing
house style for external HTTP APIs (see providers/atmosphere.py and
siblings). It reads its API key from the ANTHROPIC_API_KEY environment
variable and is never invoked unless main.py's --narrate flag is set.
"""

import os

import requests

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
DEFAULT_MAX_TOKENS = 4096


class NarrativeBackend:
    """Interface implemented by narrative-synthesis backends."""

    def synthesize(self, prompt: str) -> str:
        """Return the finished narrative text for a given prompt."""

        raise NotImplementedError(
            "Narrative backend must implement synthesize()."
        )


class MissingAPIKeyError(RuntimeError):
    pass


class NarrativeBackendError(RuntimeError):
    pass


class AnthropicNarrativeBackend(NarrativeBackend):
    def __init__(self, model: str = DEFAULT_MODEL, max_tokens: int = DEFAULT_MAX_TOKENS):
        self.model = model
        self.max_tokens = max_tokens

    def synthesize(self, prompt: str) -> str:
        api_key = os.environ.get("ANTHROPIC_API_KEY")

        if not api_key:
            raise MissingAPIKeyError(
                "ANTHROPIC_API_KEY is not set. --narrate requires a real "
                "API key to call the synthesis backend; without one this "
                "flag cannot run (Celeste's own deterministic output is "
                "entirely unaffected either way)."
            )

        response = requests.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=120,
        )

        if response.status_code != 200:
            raise NarrativeBackendError(
                f"Narrative backend request failed ({response.status_code}): "
                f"{response.text[:500]}"
            )

        payload = response.json()
        blocks = payload.get("content", [])
        text = "".join(
            block.get("text", "") for block in blocks if block.get("type") == "text"
        )

        if not text:
            raise NarrativeBackendError(
                f"Narrative backend returned no text content: {payload}"
            )

        return text
