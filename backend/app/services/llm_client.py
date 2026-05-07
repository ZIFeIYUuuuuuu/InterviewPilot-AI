"""Optional OpenAI-compatible LLM client with schema validation and local fallback support."""

from __future__ import annotations

import json
from typing import TypeVar
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from backend.app.core.config import get_settings
from backend.app.schemas.common import SchemaModel


T = TypeVar("T", bound=SchemaModel)


class LLMClientError(RuntimeError):
    """Raised when an optional LLM call cannot produce valid schema output."""


def is_llm_enabled() -> bool:
    """Return whether external LLM calls should be attempted."""

    return get_settings().llm_enabled


def generate_structured_output(prompt: str, schema: type[T]) -> T | None:
    """Call an OpenAI-compatible chat completion endpoint and validate JSON output.

    Returns None when the LLM is disabled or unavailable so callers can preserve
    the deterministic local MVP fallback.
    """

    settings = get_settings()
    if not settings.llm_enabled or not settings.llm_api_key:
        return None

    try:
        content = _chat_completion(prompt)
        payload = _extract_json_object(content)
        return schema.model_validate(payload)
    except (LLMClientError, ValidationError, ValueError, TypeError):
        return None


def _chat_completion(prompt: str) -> str:
    settings = get_settings()
    url = f"{settings.llm_base_url}/chat/completions"
    body = {
        "model": settings.llm_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a structured-output agent for InterviewPilot AI. "
                    "Return only one valid JSON object matching the user's schema."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    request = Request(
        url=url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.llm_timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise LLMClientError(f"LLM HTTP error {error.code}: {detail}") from error
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise LLMClientError("LLM request failed") from error

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise LLMClientError("LLM response did not include message content") from error
    if not isinstance(content, str) or not content.strip():
        raise LLMClientError("LLM response content was empty")
    return content


def _extract_json_object(content: str) -> dict:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.casefold().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end < start:
            raise
        parsed = json.loads(cleaned[start : end + 1])
    if not isinstance(parsed, dict):
        raise LLMClientError("LLM output was not a JSON object")
    return parsed
