#!/usr/bin/env python3
"""Run the DeALoG orchestrator over a dataset and write benchmark metrics."""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.coordinator import AdaptiveOrchestrator
from utils.data_loader import load_benchmark


def _normalise_answer(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _numbers_match(ref: str, cand: str) -> bool:
    def extract_numbers(text: str) -> List[float]:
        matches = re.findall(r"[-+]?\d+(?:\.\d+)?", text.replace(",", ""))
        nums = []
        for match in matches:
            try:
                nums.append(float(match))
            except ValueError:
                continue
        return nums

    ref_nums = extract_numbers(ref)
    cand_nums = extract_numbers(cand)
    if not ref_nums or not cand_nums:
        return False
    tolerance = max(1e-3, 0.01 * abs(ref_nums[0]))
    return any(abs(ref_nums[0] - num) <= tolerance for num in cand_nums)


def run_dataset(
    dataset: str,
    split: str,
    llm: str,
    *,
    visual_caption_model: str | None,
    visual_caption_path: str | None,
    visual_ocr_engine: str | None,
    visual_ocr_model_dir: str | None,
    limit: int | None,
    max_rounds: int,
    scheduler_model: str | None,
    scheduler_threshold: float,
    parallel_retrieval: bool,
) -> Dict[str, Any]:
    data = load_benchmark(dataset, split=split, limit=limit)
    if limit:
        data = data[:limit]

    orchestrator = AdaptiveOrchestrator(
        model_name=llm,
        visual_model_name=visual_caption_model,
        visual_caption_model=visual_caption_model,
        visual_caption_model_path=visual_caption_path,
        visual_ocr_engine=visual_ocr_engine,
        visual_ocr_model_dir=visual_ocr_model_dir,
        max_rounds=max_rounds,
        scheduler_model_path=scheduler_model,
        scheduler_threshold=scheduler_threshold,
        parallel_retrieval=parallel_retrieval,
    )

    per_example: List[Dict[str, Any]] = []
    total_correct = 0
    total_latency = 0.0

    for idx, sample in enumerate(data):
        start = time.perf_counter()
        result = orchestrator.run(sample)
        latency = time.perf_counter() - start
        total_latency += latency

        gold = _normalise_answer(sample.get("answer"))
        pred = _normalise_answer(result.get("answer"))
        correct = bool(gold) and (gold == pred or _numbers_match(gold, pred))
        total_correct += int(correct)
        per_example.append(
            {
                "id": sample.get("id", f"{dataset}-{split}-{idx}"),
                "question": sample.get("question"),
                "prediction": result.get("answer"),
                "reference": sample.get("answer"),
                "rationale": result.get("rationale"),
                "log": result.get("log"),
                "correct": correct,
                "latency_sec": latency,
            }
        )

    n = len(per_example)
    accuracy = total_correct / n if n else 0.0
    avg_latency = total_latency / n if n else 0.0
    return {
        "dataset": dataset,
        "split": split,
        "model": llm,
        "accuracy": accuracy,
        "num_examples": n,
        "latency_sec": round(avg_latency, 3),
        "calls": None,
        "tokens": None,
        "api_cost": None,
        "per_example": per_example,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run DeALoG orchestrator and emit metrics.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--split", default="dev")
    parser.add_argument("--llm", required=True)
    parser.add_argument("--limit", type=int, default=None, help="Optional cap on the number of samples.")
    parser.add_argument("--results-file", type=Path, required=True)
    parser.add_argument("--visual-caption-model", default=None)
    parser.add_argument("--visual-caption-path", default=None)
    parser.add_argument("--visual-ocr-engine", default=None)
    parser.add_argument("--visual-ocr-model-dir", default=None)
    parser.add_argument("--max-rounds", type=int, default=6, help="Max coordination rounds (R).")
    parser.add_argument("--scheduler", default=None, help="Path to a joblib logistic gate.")
    parser.add_argument("--scheduler-threshold", type=float, default=0.4, help="p(continue) threshold.")
    parser.add_argument("--parallel-retrieval", action="store_true", help="Enable parallel retrieval micro-benchmark mode.")
    args = parser.parse_args()

    metrics = run_dataset(
        dataset=args.dataset,
        split=args.split,
        llm=args.llm,
        visual_caption_model=args.visual_caption_model,
        visual_caption_path=args.visual_caption_path,
        visual_ocr_engine=args.visual_ocr_engine,
        visual_ocr_model_dir=args.visual_ocr_model_dir,
        limit=args.limit,
        max_rounds=args.max_rounds,
        scheduler_model=args.scheduler,
        scheduler_threshold=args.scheduler_threshold,
        parallel_retrieval=args.parallel_retrieval,
    )

    args.results_file.parent.mkdir(parents=True, exist_ok=True)
    args.results_file.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(
        f"[DeALoG] dataset={args.dataset} split={args.split} model={args.llm} "
        f"accuracy={metrics['accuracy']:.3f} latency={metrics['latency_sec']}"
    )


if __name__ == "__main__":
    main()
