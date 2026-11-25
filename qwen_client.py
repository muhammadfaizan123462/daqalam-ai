"""Qwen (Alibaba DashScope, OpenAI-compatible) client for Da Qalam AI.

Follows the same pattern as the user's PashtoVoice project
(pashtovoice/ai/qwen_service.py): DashScope compatible-mode endpoint,
Bearer auth, model qwen-plus. Uses httpx (per this project's
requirements) instead of requests. No fake content is ever returned:
without an API key every call raises QwenUnavailable, and HTTP errors
raise RuntimeError. The key is read from the QWEN_API_KEY environment
variable only — never from source code or the frontend.
"""

from __future__ import annotations

import os

import httpx

DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"

SYSTEM_PROMPT = (
    "You are Da Qalam AI, an expert in Pashto literature, poetry and language. "
    "When a user provides Pashto poetry: "
    "1. Explain its meaning in simple Pashto. "
    "2. Translate it into Urdu. "
    "3. Translate it into English. "
    "4. Explain difficult words individually. "
    "5. Identify the emotions and themes. "
    "6. Explain the poet's possible message. "
    "Important: Respect Pashto culture and literature. "
    "Do not invent the poet's identity. "
    "If the meaning is uncertain, say so. "
    "Keep explanations easy for students. "
    "Preserve the original poetry. "
    "Never confuse literal translation with poetic interpretation. "
    "Always organize your answer with clear headings."
)


class QwenUnavailable(Exception):
    """Raised when Qwen cannot be used (no key configured)."""


class QwenClient:
    """Minimal DashScope OpenAI-compatible chat client (httpx)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
    ):
        self.api_key = api_key if api_key is not None else os.environ.get("QWEN_API_KEY")
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
        """Send a chat-completion request.

        Returns {"content": str, "model": str, "usage": {...}}.
        Raises QwenUnavailable when no key is set; RuntimeError on
        HTTP / network errors. Never returns fake content.
        """
        if not self.is_available():
            raise QwenUnavailable(
                "No Qwen API key configured. Set QWEN_API_KEY to use Qwen."
            )
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
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
            raise RuntimeError(f"Qwen request failed: {exc}") from exc
        if response.status_code != 200:
            raise RuntimeError(
                f"Qwen HTTP {response.status_code}: {response.text[:500]}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(f"Qwen returned invalid JSON: {exc}") from exc
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Qwen returned an unexpected response: {data}") from exc
        return {
            "content": content,
            "model": data.get("model", self.model),
            "usage": data.get("usage", {}) or {},
        }


def get_client() -> QwenClient:
    """Return a QwenClient reading QWEN_API_KEY from the environment."""
    return QwenClient()
