"""Coordinator agent that distils log entries into a candidate answer."""

from __future__ import annotations

from typing import Dict, Optional

from utils.shared_log import SharedLog


class SummarizingAgent:
    """Synthesize an answer from accumulated log entries."""

    def synthesize(
        self, question: str, log: SharedLog, *, fallback_answer: Optional[str] = None
    ) -> Dict[str, str]:
        """Return a candidate answer and supporting rationale."""

        context = log.latest("context")
        table = log.latest("table")
        calculation = log.latest("calculation")
        visual = log.latest("visual")

        parts = [f"Question: {question}"]

        if context and context.content:
            parts.append(f"Context: {context.content}")
        if table and table.content not in (None, []):
            parts.append(f"Table insight: {table.content}")
        if calculation and calculation.content not in (None, ""):
            parts.append(f"Calculation: {calculation.content}")
        if visual and visual.content and visual.content != "No visual artefacts provided.":
            parts.append(f"Visual cues: {visual.content}")

        rationale = " \n".join(parts)
        answer = fallback_answer or (parts[-1] if len(parts) > 1 else question)

        return {"answer": answer, "rationale": rationale}
