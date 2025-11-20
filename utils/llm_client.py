"""Thin HTTP client for invoking hosted LLM APIs (OpenRouter/OpenAI compatible)."""

from __future__ import annotations

import json
import os
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
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1"
        self.default_model = default_model or os.getenv("DEALOG_SUMMARIZER_MODEL") or os.getenv("PRIMARY_MODEL_NAME")
        self.timeout = timeout

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
            return None

        try:
            import requests  # type: ignore
        except ImportError:
            return None

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

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException:
            return None

        try:
            data = response.json()
            choice = data["choices"][0]
            message = choice.get("message", {})
            content = message.get("content")
            usage = data.get("usage") or {}
            return {
                "content": content,
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                },
            }
        except Exception:
            return None
