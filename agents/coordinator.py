"""Adaptive controller that coordinates specialist agents via a shared log."""

from __future__ import annotations

from typing import Any, Dict

from .calculation_agent import CalculationAgent
from .context_agent import ContextAgent
from .summarizer_agent import SummarizingAgent
from .table_agent import TableAgent
from .verification_agent import VerificationAgent
from .visual_agent import VisualAgent
from utils.shared_log import SharedLog


class AdaptiveOrchestrator:
    """Controller that manages agent turn-taking and verification."""

    def __init__(self, model_name: str | None = None) -> None:
        self.table_agent = TableAgent(model_name)
        self.context_agent = ContextAgent(model_name)
        self.calc_agent = CalculationAgent()
        self.visual_agent = VisualAgent(model_name)
        self.summarizer = SummarizingAgent()
        self.verifier = VerificationAgent()

    def run(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single QA sample through the coordinated agent pipeline."""

        log = SharedLog()
        question = sample.get("question", "")

        initial_needs = ["context", "table", "calculation"]
        if sample.get("visuals"):
            initial_needs.append("visual")
        log.append(
            "controller",
            "question",
            question,
            metadata={"sample_id": sample.get("id")},
            needs=initial_needs,
        )

        progress = True
        while progress and any(log.pending_needs()):
            progress = False

            if log.has_pending("context"):
                context = self.context_agent.fetch_relevant_text(
                    question, sample.get("paragraphs")
                )
                log.append(
                    "context_agent",
                    "context",
                    context,
                    metadata={"source": "paragraphs"},
                    resolves=["context"],
                )
                progress = True

            if log.has_pending("table"):
                operation = (
                    sample.get("table_operation")
                    or sample.get("operation")
                    or sample.get("instruction")
                    or "noop"
                )
                table_result = self.table_agent.apply_operation(
                    sample.get("table") or [], operation
                )
                log.append(
                    "table_agent",
                    "table",
                    table_result,
                    metadata={"operation": operation},
                    resolves=["table"],
                )
                progress = True

            if log.has_pending("calculation"):
                expression = (
                    sample.get("calculation")
                    or sample.get("expression")
                    or sample.get("formula")
                )
                calc_result = (
                    self.calc_agent.compute(expression)
                    if isinstance(expression, str) and expression.strip()
                    else None
                )
                log.append(
                    "calculation_agent",
                    "calculation",
                    calc_result,
                    metadata={"expression": expression},
                    resolves=["calculation"],
                )
                progress = True

            if log.has_pending("visual"):
                visual_summary = self.visual_agent.describe(sample.get("visuals"))
                log.append(
                    "visual_agent",
                    "visual",
                    visual_summary,
                    resolves=["visual"],
                )
                progress = True

        # Request a summary and final verification if not already satisfied
        log.append(
            "controller",
            "request_summary",
            "Synthesize final answer",
            needs=["summary"],
        )

        summary_payload = self.summarizer.synthesize(
            question, log, fallback_answer=sample.get("answer")
        )
        log.append(
            "summarizer_agent",
            "summary",
            summary_payload,
            resolves=["summary"],
            needs=["verification"],
        )

        candidate_answer = summary_payload.get("answer", "")
        is_verified = self.verifier.verify(candidate_answer, sample.get("answer"))
        log.append(
            "verification_agent",
            "verification",
            {
                "verified": is_verified,
                "reference_available": sample.get("answer") is not None,
            },
            resolves=["verification"],
        )

        result = {
            "answer": candidate_answer,
            "rationale": summary_payload.get("rationale"),
            "verified": is_verified,
            "log": log.to_dict(),
        }
        return result
