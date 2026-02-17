"""Thin HTTP client for invoking hosted LLM APIs (OpenRouter/OpenAI compatible)."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional


class LLMClient:
    """Best-effort wrapper around a chat/completions HTTP endpoint."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        retry_backoff_sec: float = 1.5,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = base_url or os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1"
        self.default_model = default_model or os.getenv("DEALOG_SUMMARIZER_MODEL") or os.getenv("PRIMARY_MODEL_NAME")
        self.site_url = os.getenv("OPENROUTER_SITE_URL") or os.getenv("OPENROUTER_SITE")
        self.app_name = os.getenv("OPENROUTER_APP_NAME") or os.getenv("OPENROUTER_SITE_NAME")
        self.timeout = timeout
        self.max_retries = max(1, int(max_retries))
        self.retry_backoff_sec = float(retry_backoff_sec)

    def _fail_or_none(self, message: str) -> Optional[Dict[str, Any]]:
        raise RuntimeError(message)

    def complete(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 256,
    ) -> Optional[Dict[str, Any]]:
        """
        Send ``prompt`` to the configured backend.

        Returns
        -------
        dict | None
            ``{"content": str, "usage": {"prompt_tokens": int, "completion_tokens": int}}``.
            Falls back to ``None`` when the client is unavailable or errors.
        """

        if not self.api_key:
            return self._fail_or_none("OPENROUTER_API_KEY is missing; cannot run LLM-only mode.")

        try:
            import requests  # type: ignore
        except ImportError:
            return self._fail_or_none("Missing dependency: requests")

        payload = {
            "model": model or self.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.app_name:
            headers["X-Title"] = self.app_name

        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=self.timeout,
                )
                response.raise_for_status()
                break
            except requests.RequestException as exc:
                last_exc = exc
                if attempt >= self.max_retries:
                    return self._fail_or_none(f"LLM request failed after {self.max_retries} attempts: {exc}")
                time.sleep(self.retry_backoff_sec * attempt)
        if last_exc is not None and "response" not in locals():
            return self._fail_or_none(f"LLM request failed: {last_exc}")

        try:
            data = response.json()
            choice = data["choices"][0]
            message = choice.get("message", {})
            content = message.get("content")
            usage = data.get("usage") or {}
            if content in (None, ""):
                return self._fail_or_none("LLM response did not include content.")
            return {
                "content": content,
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                },
            }
        except Exception as exc:
            return self._fail_or_none(f"Failed to parse LLM response payload: {exc}")
