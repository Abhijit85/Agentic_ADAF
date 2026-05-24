#!/usr/bin/env python3
"""
Run AutoTQA under the repo's existing corruption setup.

This script is intentionally wired to the current repository layout:
- MMQA is loaded via utils.data_loader.load_benchmark("mmqa", split=...)
- corruption logic is sourced from scripts.fault_injection_experiment

Current blocker:
- the repo does not contain an AutoTQA implementation entry point, so the
  script exits with a clear error until that hook is supplied.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.fault_injection_experiment import FaultInjector
from utils.data_loader import load_benchmark

try:
    from baselines.run_autotqa import run_autotqa_on_sample  # type: ignore
except ImportError:
    run_autotqa_on_sample = None


SEEDS = [2021, 2022, 2023, 2024, 2025]
CORRUPTION_LEVELS = [0.00, 0.10, 0.20, 0.30]

BACKBONE_CONFIGS = {
    "llama3-8b": {
        "model_path": "meta-llama/Meta-Llama-3-8B-Instruct",
        "temperature_summarizer": 0.0,
        "temperature_table_context": 0.3,
        "max_tokens": 4096,
    },
    "gpt-oss-20b": {
        "model_path": "openai/gpt-oss-20b",
        "temperature_summarizer": 0.0,
        "temperature_table_context": 0.0,
        "max_tokens": 512,
    },
}


def _normalise(value: Any) -> str:
    return str(value or "").strip().lower()


def _score_em(prediction: Any, gold: Any) -> int:
    return int(bool(_normalise(gold)) and _normalise(prediction) == _normalise(gold))


def _load_mmqa_dev() -> List[Dict[str, Any]]:
    try:
        return load_benchmark("mmqa", split="dev")
    except FileNotFoundError:
        return load_benchmark("mmqa_full", split="dev")


def _corrupt_sample(sample: Dict[str, Any], corruption_level: float, rng: random.Random) -> Dict[str, Any]:
    """
    Best-effort sample-level corruption aligned to the repo's fault injector.

    Important: the existing corruption protocol in this repo operates over
    shared-log context/table entries during orchestration. Because AutoTQA is
    not implemented here, we cannot faithfully replay that exact protocol.
    This function mutates sample fields using the same FaultInjector internals
    as a structural approximation.
    """
    injector = FaultInjector(corruption_level, rng)
    corrupted = json.loads(json.dumps(sample))

    for field_name, entry_type in (("paragraphs", "context"), ("table", "table")):
        if field_name not in corrupted:
            continue
        dummy_entry = type("Entry", (), {})()
        dummy_entry.type = entry_type
        dummy_entry.content = corrupted[field_name]
        dummy_entry.metadata = {}
        maybe_new = injector(dummy_entry)
        corrupted[field_name] = maybe_new.content

    return corrupted


def run_one_configuration(
    corruption_level: float,
    seed: int,
    backbone: str,
    dev_samples: List[Dict[str, Any]],
    smoke: bool = False,
) -> Dict[str, Any]:
    if run_autotqa_on_sample is None:
        raise RuntimeError(
            "AutoTQA entry point is missing. Expected baselines.run_autotqa.run_autotqa_on_sample."
        )

    rng = random.Random(seed)
    np.random.seed(seed)
    backbone_cfg = BACKBONE_CONFIGS[backbone]

    samples = dev_samples[:1] if smoke else dev_samples
    em_scores: List[int] = []
    failed = 0

    for i, sample in enumerate(samples):
        try:
            corrupted_sample = _corrupt_sample(sample, corruption_level, rng)
            prediction = run_autotqa_on_sample(
                sample=corrupted_sample,
                evidence=corrupted_sample,
                model=backbone_cfg["model_path"],
                temperature_summarizer=backbone_cfg["temperature_summarizer"],
                temperature_table_context=backbone_cfg["temperature_table_context"],
                max_tokens=backbone_cfg["max_tokens"],
            )
            em_scores.append(_score_em(prediction, sample.get("answer") or sample.get("gold_answer")))
        except Exception as exc:
            failed += 1
            em_scores.append(0)
            if failed <= 3:
                print(f"[warn] sample {i} failed: {exc}")

    return {
        "n": len(em_scores),
        "n_failed": failed,
        "em_per_sample": em_scores,
    }


def bootstrap_ci(values: List[float], n_resamples: int = 1000, ci: float = 0.95, seed: int = 12345) -> tuple[float, float]:
    rng = np.random.RandomState(seed)
    arr = np.asarray(values)
    if len(arr) == 0:
        return 0.0, 0.0
    means = [rng.choice(arr, size=len(arr), replace=True).mean() for _ in range(n_resamples)]
    means.sort()
    lo = means[int((1 - ci) / 2 * n_resamples)]
    hi = means[int((1 + ci) / 2 * n_resamples)]
    return float(lo), float(hi)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backbone", default="llama3-8b", choices=list(BACKBONE_CONFIGS))
    parser.add_argument("--dataset", default="mmqa", choices=["mmqa"])
    parser.add_argument("--out", default="results_autotqa_corruption.json")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    dev_samples = _load_mmqa_dev()
    print(f"Loaded {len(dev_samples)} MMQA dev samples.")

    if args.smoke:
        result = run_one_configuration(
            corruption_level=0.0,
            seed=SEEDS[0],
            backbone=args.backbone,
            dev_samples=dev_samples,
            smoke=True,
        )
        print(json.dumps(result, indent=2))
        return

    all_results: Dict[str, Any] = {}
    for level in CORRUPTION_LEVELS:
        per_seed_means: List[float] = []
        pooled_em: List[int] = []
        for seed in SEEDS:
            result = run_one_configuration(
                corruption_level=level,
                seed=seed,
                backbone=args.backbone,
                dev_samples=dev_samples,
            )
            mean_em = float(np.mean(result["em_per_sample"])) if result["em_per_sample"] else 0.0
            per_seed_means.append(mean_em)
            pooled_em.extend(result["em_per_sample"])
        ci_lo, ci_hi = bootstrap_ci(pooled_em)
        all_results[f"{int(level * 100)}%"] = {
            "mean_em_across_seeds": float(np.mean(per_seed_means)),
            "ci_95": [ci_lo, ci_hi],
            "per_seed_means": per_seed_means,
        }

    payload = {
        "backbone": args.backbone,
        "dataset": args.dataset,
        "seeds": SEEDS,
        "corruption_levels": CORRUPTION_LEVELS,
        "results": all_results,
    }
    Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[done] Results saved to {args.out}")


if __name__ == "__main__":
    main()
