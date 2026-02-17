"""Agent that verifies candidate answers before finalisation."""

from __future__ import annotations

import re
from typing import Any, Optional

from utils.llm_client import LLMClient


class VerificationAgent:
    """Perform LLM-only answer verification against references."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        *,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 64,
    ) -> None:
        self._llm = llm_client or LLMClient()
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def verify(self, candidate: str, reference: Optional[Any]) -> bool:
        """Return ``True`` if ``candidate`` satisfies ``reference``."""

        if reference is None:
            # Without a reference answer we cannot verify automatically.
            return False

        prompt = (
            "You are a strict QA verifier.\n"
            "Task: Decide if the candidate answer semantically matches the reference answer.\n"
            "Output format is mandatory. Return exactly one line:\n"
            "VERDICT: true\n"
            "or\n"
            "VERDICT: false\n\n"
            "Examples:\n"
            "Reference: 42\nCandidate: 42\nVERDICT: true\n"
            "Reference: Paris\nCandidate: London\nVERDICT: false\n\n"
            f"Reference: {reference}\n"
            f"Candidate: {candidate}\n"
        )
        content = self._complete_text(prompt)
        verdict = self._extract_verdict(content)
        if verdict is not None:
            return verdict

        # Retry once with an even tighter instruction, still LLM-only.
        retry_prompt = (
            "You must answer with exactly one token: true or false.\n"
            "Do not ask questions. Do not add explanation.\n\n"
            f"Reference: {reference}\n"
            f"Candidate: {candidate}\n"
            f"Previous response (invalid): {content}\n"
            "Answer:"
        )
        retry_content = self._complete_text(retry_prompt)
        verdict = self._extract_verdict(retry_content)
        if verdict is not None:
            return verdict

        raise RuntimeError(
            "Verification LLM response missing verdict after retry. "
            f"first={content!r} retry={retry_content!r}"
        )

    def _complete_text(self, prompt: str) -> str:
        result = self._llm.complete(
            prompt,
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        if not result or not isinstance(result, dict):
            raise RuntimeError("Verification LLM call failed; heuristic fallback is disabled.")
        return str(result.get("content") or "").strip()

    def _extract_verdict(self, content: str) -> Optional[bool]:
        match = re.search(r"verdict\s*:\s*(true|false)", content, flags=re.IGNORECASE)
        if match:
            return match.group(1).lower() == "true"

        token = content.strip().lower()
        if token in {"true", "false"}:
            return token == "true"
        return None
