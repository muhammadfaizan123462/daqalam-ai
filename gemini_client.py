"""Gemini (Google AI Studio) client for Da Qalam AI.

Second LLM provider, used when Qwen is unavailable. Same Da Qalam system
prompt and the same structured JSON contract as qwen_client.py, so the
server can fall back from Qwen to Gemini without changing the response
shape. Uses httpx. The key is read from the GEMINI_API_KEY environment
variable only, never from source code or the frontend.

Model gemini-3-flash-preview was verified working from this environment on
2026-11-25 (a generate call replied in ~2s). Auth is the x-goog-api-key
header, the same placement the registered custom.gemini connector uses.
"""

from __future__ import annotations

import os

import httpx

DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-3-flash-preview"


class GeminiUnavailable(Exception):
    """Raised when Gemini cannot be used (no key configured)."""


class GeminiClient:
    """Minimal Google AI Studio generateContent client (httpx)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
    ):
        self.api_key = api_key if api_key is not None else os.environ.get("GEMINI_API_KEY")
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.model = model or DEFAULT_MODEL

    def is_available(self) -> bool:
        """True only if a non-empty API key is set."""
        return bool(self.api_key and str(self.api_key).strip())

    def complete(
        self,
        messages: list[dict],
        temperature: float = 0.2,
        timeout: int = 45,
    ) -> dict:
        """Send a generateContent request.

        `messages` is the OpenAI-style list the server builds
        ([{role: system, content}, {role: user, content}]). The system
        message goes to systemInstruction, the user message to contents.
        Returns {"content": str, "model": str, "usage": {...}}.
        Raises GeminiUnavailable when no key is set; RuntimeError on
        HTTP / network errors or an unexpected response. Never returns
        fake content.
        """
        if not self.is_available():
            raise GeminiUnavailable(
                "No Gemini API key configured. Set GEMINI_API_KEY to use Gemini."
            )
        system_text = ""
        user_text = ""
        for msg in messages:
            if msg.get("role") == "system":
                system_text = msg.get("content", "")
            elif msg.get("role") == "user":
                user_text = msg.get("content", "")
        payload: dict = {
            "contents": [{"parts": [{"text": user_text}]}],
            "generationConfig": {"temperature": temperature},
        }
        if system_text:
            payload["systemInstruction"] = {"parts": [{"text": system_text}]}
        url = f"{self.base_url}/models/{self.model}:generateContent"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        try:
            # trust_env=False: the sandbox no_proxy list contains bracketed
            # IPv6 entries ([::1]) that httpx cannot parse as proxy patterns.
            # The egress proxy is passed explicitly instead. verify uses
            # SSL_CERT_FILE when set (the sandbox egress CA bundle, the same
            # one urllib reads); otherwise httpx's default bundle applies.
            proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
            verify = os.environ.get("SSL_CERT_FILE") or True
            with httpx.Client(
                timeout=timeout, trust_env=False, proxy=proxy, verify=verify
            ) as client:
                response = client.post(url, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Gemini request failed: {exc}") from exc
        if response.status_code != 200:
            raise RuntimeError(
                f"Gemini HTTP {response.status_code}: {response.text[:500]}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(f"Gemini returned invalid JSON: {exc}") from exc
        try:
            parts = data["candidates"][0]["content"]["parts"]
            content = "".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Gemini returned an unexpected response: {data}") from exc
        if not content.strip():
            raise RuntimeError(f"Gemini returned an empty response: {data}")
        return {
            "content": content,
            "model": data.get("model", self.model),
            "usage": data.get("usageMetadata", {}) or {},
        }


def get_client() -> GeminiClient:
    """Return a GeminiClient reading GEMINI_API_KEY from the environment."""
    return GeminiClient()
