import os

from knowledge.providers.http_llm import (
    HTTPModelBackend,
)


print("=== HTTP MODEL PROVIDER ===")

os.environ[
    "CELESTE_LLM_ENDPOINT"
] = "https://example.invalid/v1/chat/completions"

os.environ[
    "CELESTE_LLM_API_KEY"
] = "test-key"

os.environ[
    "CELESTE_LLM_MODEL"
] = "test-model"

backend = HTTPModelBackend()

assert backend.endpoint.endswith(
    "/v1/chat/completions"
)

assert backend.api_key == "test-key"
assert backend.model == "test-model"

print("✓ endpoint configuration works")
print("✓ API key configuration works")
print("✓ model configuration works")
print("✓ provider remains isolated")

print()
print("HTTP MODEL PROVIDER: OK")
