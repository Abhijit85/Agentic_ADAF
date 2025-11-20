"""Coordinator agent that distils log entries into a candidate answer."""

from __future__ import annotations

import re
from typing import Dict, Optional, List

from utils.llm_client import LLMClient

from utils.shared_log import SharedLog


class SummarizingAgent:
    """Synthesize an answer from accumulated log entries."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self._llm = llm_client or LLMClient()

    def synthesize(self, question: str, log: SharedLog) -> Dict[str, str]:
        """Return a candidate answer and supporting rationale."""

        context = log.latest("context")
        table = log.latest("table")
        calculation = log.latest("calculation")
        visual = log.latest("visual")

        evidence: List[str] = []
        if context and context.content:
            evidence.append(f"Context: {context.content}")
        if table and table.content not in (None, []):
            evidence.append(f"Table insight: {table.content}")
        if calculation and calculation.content not in (None, ""):
            evidence.append(f"Calculation: {calculation.content}")
        if visual and visual.content and visual.content != "No visual artefacts provided.":
            evidence.append(f"Visual cues: {visual.content}")

        rationale = " \n".join(["Question: " + question] + evidence)

        prompt = self._build_prompt(question, evidence)
        llm_result = self._llm.complete(prompt) if self._llm else None

        normalized = None
        confidence = 0.5
        prompt_tokens = None
        completion_tokens = None

        if llm_result and isinstance(llm_result, dict):
            llm_answer = llm_result.get("content") or ""
            usage = llm_result.get("usage") or {}
            prompt_tokens = usage.get("prompt_tokens")
            completion_tokens = usage.get("completion_tokens")
            confidence = self._confidence_from_usage(usage)
            answer, normalized = self._parse_answer(llm_answer)
        else:
            answer = self._fallback_answer(evidence) or question

        return {
            "answer": normalized or answer,
            "rationale": rationale,
            "confidence": confidence,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }

    def _build_prompt(self, question: str, evidence: List[str]) -> str:
        evidence_text = "\n".join(f"{idx+1}. {item}" for idx, item in enumerate(evidence)) or "1. (No evidence provided)"
        if self._looks_like_finqa(question):
            instructions = (
                "You are answering a financial report question. The tables list yearly metrics (e.g., revenue, profit, assets).\n"
                "Identify the year or row mentioned in the question, select the correct column (revenue/profit/etc.), and output only the requested number.\n"
                "Show intermediate arithmetic if necessary (e.g., 2020 value - 2019 value).\n"
                "Format:\n"
                "Reasoning: describe the lookup (year, column) and any arithmetic.\n"
                "Answer: <numeric value only>."
            )
        else:
            instructions = (
                "You are a financial/table reasoning assistant.\n"
                "1. Break the question down and note which row/column of the table or context provides each fact.\n"
                "2. When arithmetic is needed, show the intermediate calculation (e.g., 2020 value - 2019 value = X).\n"
                "3. End with a short final answer.\n"
                "Format:\n"
                "Reasoning: Step-by-step explanation referencing specific evidence items.\n"
                "Answer: <concise numeric or textual answer>."
            )
        return f"{instructions}\nQuestion: {question}\nEvidence:\n{evidence_text}"

    def _fallback_answer(self, evidence: List[str]) -> Optional[str]:
        for item in evidence:
            if ":" in item:
                return item.split(":", 1)[1].strip()
        return None

    def _parse_answer(self, llm_response: str) -> tuple[str, Optional[str]]:
        lines = [line.strip() for line in llm_response.strip().splitlines() if line.strip()]
        candidate = None
        for line in lines:
            lower = line.lower()
            if lower.startswith("answer:"):
                candidate = line.split(":", 1)[1].strip()
                break
        if not candidate:
            candidate = lines[-1] if lines else llm_response.strip()

        normalized = self._extract_numeric_span(candidate)
        return candidate, normalized

    def _looks_like_finqa(self, question: str) -> bool:
        lowered = question.lower()
        has_year = bool(re.search(r"(19|20)\d{2}", lowered))
        financial_terms = ["revenue", "profit", "earnings", "reported", "income"]
        return has_year and any(term in lowered for term in financial_terms)

    def _extract_numeric_span(self, text: str) -> Optional[str]:
        match = re.search(r"[-+]?[0-9]+(?:\.[0-9]+)?", text.replace(",", ""))
        if match:
            return match.group(0)
        return None

    def _confidence_from_usage(self, usage: Dict[str, Optional[int]]) -> float:
        # Simple heuristic: presence of token counts -> high-ish confidence, else fallback.
        if usage.get("prompt_tokens") is not None or usage.get("completion_tokens") is not None:
            return 0.8
        return 0.5
