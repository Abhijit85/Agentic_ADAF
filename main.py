"""Entry point for running the adaptive table QA pipeline."""

from __future__ import annotations

import argparse
from typing import Any, Dict

from agents.coordinator import AdaptiveOrchestrator
from utils.data_loader import load_benchmark


def _format_result(sample: Dict[str, Any], result: Dict[str, Any]) -> str:
    status = "verified" if result.get("verified") else "unverified"
    return (
        f"Q: {sample.get('question', '')}\n"
        f"A ({status}): {result.get('answer', '')}\n"
    )


def main() -> None:
    """Run the orchestrator over a benchmark dataset."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="tatqa")
    parser.add_argument("--llm", type=str, default="mistral-7b")
    args = parser.parse_args()

    data = load_benchmark(args.dataset)
    orchestrator = AdaptiveOrchestrator(model_name=args.llm)
    for sample in data:
        result = orchestrator.run(sample)
        print(_format_result(sample, result))


if __name__ == "__main__":
    main()
