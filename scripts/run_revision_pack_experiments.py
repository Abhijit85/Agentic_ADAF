#!/usr/bin/env python3
"""Revision-pack experiment harness for DeALoG."""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import string
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from agents.coordinator import AdaptiveOrchestrator
from baselines.run_autotqa import run_autotqa_on_sample
from baselines.runner import _build_prompt as build_baseline_prompt
from baselines.runner import _extract_answer as extract_baseline_answer
from scripts.run_planlog_hybrid import _build_needs, _build_plan
from utils.data_loader import load_benchmark
from utils.finqa_program import coverage_vector
from utils.llm_client import LLMClient
from utils.metrics import compute_f1
from utils.perturbations import EvidenceItem, corrupt_example, example_to_items, load_cache, save_cache
from utils.stats import bootstrap_ci, fmt_pm, paired_bootstrap_diff, seeds_ci

SEEDS = [2021, 2022, 2023, 2024, 2025]
SYSTEMS = ["planner", "planlog", "autotqa", "rewoo", "dealog"]


def _normalise_answer(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower().replace("−", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip(string.whitespace + string.punctuation)


def _extract_numbers(text: str) -> List[float]:
    matches = re.findall(r"[-+]?\d+(?:\.\d+)?", str(text).replace(",", ""))
    out: List[float] = []
    for match in matches:
        try:
            out.append(float(match))
        except ValueError:
            continue
    return out


def official_em(pred: Any, gold: Any) -> int:
    ref = _normalise_answer(gold)
    cand = _normalise_answer(pred)
    if not ref or not cand:
        return 0
    if ref == cand:
        return 1
    ref_nums = _extract_numbers(ref)
    cand_nums = _extract_numbers(cand)
    if ref_nums and cand_nums:
        tol = max(1e-3, 0.01 * abs(ref_nums[0]))
        return int(any(abs(ref_nums[0] - num) <= tol for num in cand_nums))
    return 0


def tatqa_em_f1_half(pred: Any, gold: Any) -> float:
    pred_text = _normalise_answer(pred)
    gold_text = _normalise_answer(gold)
    return 0.5 * official_em(pred_text, gold_text) + 0.5 * compute_f1(pred_text, gold_text)


def _normalize_finqa_example(example: Dict[str, Any]) -> Dict[str, Any]:
    qa = example.get("qa") or {}
    normalized = dict(example)
    normalized["question"] = qa.get("question") or example.get("question") or ""
    normalized["answer"] = qa.get("exe_ans") or qa.get("answer") or example.get("answer") or ""
    normalized["program"] = qa.get("program") or example.get("program") or ""
    normalized["gold_answer"] = qa.get("answer") or example.get("answer") or ""
    normalized["paragraphs"] = list(example.get("pre_text") or []) + list(example.get("post_text") or [])
    return normalized


def load_split(dataset: str, split: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    samples = load_benchmark(dataset, split=split, limit=limit)
    if dataset == "finqa":
        samples = [_normalize_finqa_example(sample) for sample in samples]
    return samples


def _items_to_example(example: Dict[str, Any], items: List[EvidenceItem]) -> Dict[str, Any]:
    cloned = deepcopy(example)
    cell_items = [it for it in items if it.kind == "cell"]
    if cell_items:
        max_row = max((it.row or 0) for it in cell_items)
        table: List[List[str]] = []
        for row_idx in range(max_row + 1):
            row_items = [it for it in cell_items if (it.row or 0) == row_idx]
            if not row_items:
                table.append([])
                continue
            max_col = max((it.col or 0) for it in row_items)
            row = [""] * (max_col + 1)
            for item in row_items:
                row[item.col or 0] = item.text
            table.append(row)
        cloned["table"] = table
    text_items = [it.text for it in items if it.kind == "text"]
    if "pre_text" in cloned or "post_text" in cloned:
        cloned["paragraphs"] = text_items
        mid = len(text_items) // 2
        cloned["pre_text"] = text_items[:mid]
        cloned["post_text"] = text_items[mid:]
    else:
        cloned["paragraphs"] = text_items
    return cloned


def _llm_paraphrase(prompt: str) -> str:
    client = LLMClient(default_model=os.getenv("PRIMARY_MODEL_NAME"))
    result = client.complete(prompt, model=os.getenv("PRIMARY_MODEL_NAME"), temperature=0.2, max_tokens=256)
    if not result:
        raise RuntimeError("LLM paraphrase call failed")
    return str(result.get("content") or "").strip()


def _run_dealog(example: Dict[str, Any], llm: str, summarizer_llm: Optional[str], max_rounds: int) -> Dict[str, Any]:
    orchestrator = AdaptiveOrchestrator(
        model_name=llm,
        summarizer_model_name=summarizer_llm,
        summarizer_temperature=float(os.getenv("DEALOG_SUMMARIZER_TEMPERATURE", "0.2")),
        summarizer_max_tokens=int(os.getenv("DEALOG_SUMMARIZER_MAX_TOKENS", "256")),
        max_rounds=max_rounds,
    )
    return orchestrator.run(example)


def _run_planlog(example: Dict[str, Any], llm: str, summarizer_llm: Optional[str], max_rounds: int) -> Dict[str, Any]:
    orchestrator = AdaptiveOrchestrator(
        model_name=llm,
        summarizer_model_name=summarizer_llm,
        summarizer_max_tokens=int(os.getenv("DEALOG_SUMMARIZER_MAX_TOKENS", "256")),
        max_rounds=max_rounds,
    )
    return orchestrator.run(example, initial_plan=_build_plan(example), initial_needs=_build_needs(example))


def _run_prompt_baseline(strategy: str, example: Dict[str, Any], model: str) -> str:
    client = LLMClient(default_model=model)
    prompt = build_baseline_prompt(strategy, example)
    response = client.complete(prompt, model=model, temperature=0.2, max_tokens=256)
    content = str((response or {}).get("content") or "")
    return extract_baseline_answer(content)


def run_system(name: str, example: Dict[str, Any], items: List[EvidenceItem], *, llm: str, summarizer_llm: Optional[str], max_rounds: int) -> str:
    corrupted_example = _items_to_example(example, items)
    if name == "dealog":
        return str(_run_dealog(corrupted_example, llm, summarizer_llm, max_rounds).get("answer") or "")
    if name == "planlog":
        return str(_run_planlog(corrupted_example, llm, summarizer_llm, max_rounds).get("answer") or "")
    if name in {"planner", "rewoo"}:
        return _run_prompt_baseline(name, corrupted_example, llm)
    if name == "autotqa":
        return run_autotqa_on_sample(sample=corrupted_example, evidence=corrupted_example, model=llm)
    raise ValueError(f"Unsupported system: {name}")


def run_finqa_coverage(args: argparse.Namespace) -> None:
    samples = load_split("finqa", args.split, limit=args.limit)
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    per_seed_vectors: List[List[int]] = []
    uncheckable_counts: List[int] = []
    for seed in args.seeds:
        result_path = results_dir / f"finqa_{args.split}_seed{seed}.json"
        if result_path.exists():
            metrics = json.loads(result_path.read_text())
        elif not args.run_missing:
            raise FileNotFoundError(f"Missing {result_path}; rerun with --run-missing to generate predictions.")
        else:
            random.seed(seed)
            per_example = []
            for sample in samples:
                result = _run_dealog(sample, args.llm, args.summarizer_llm, args.max_rounds)
                per_example.append({
                    "id": sample["id"],
                    "prediction": result.get("answer"),
                    "reference": sample.get("answer"),
                    "program": sample.get("program"),
                    "table": sample.get("table"),
                })
            metrics = {"seed": seed, "per_example": per_example}
            result_path.write_text(json.dumps(metrics, indent=2))
        records = [
            {"pred": ex.get("prediction") or "", "program": ex.get("program") or "", "table": ex.get("table")}
            for ex in metrics.get("per_example", [])
        ]
        vec, n_uncheckable = coverage_vector(records, tol=args.tol)
        per_seed_vectors.append(vec)
        uncheckable_counts.append(n_uncheckable)
    ci = seeds_ci(per_seed_vectors, n_boot=args.n_boot)
    payload = {
        "metric": "finqa_program_coverage",
        "split": args.split,
        "seeds": args.seeds,
        "limit": args.limit,
        "ci": ci,
        "formatted": fmt_pm(ci, scale=1, decimals=2),
        "uncheckable_per_seed": uncheckable_counts,
    }
    print(json.dumps(payload, indent=2))


def _load_seed_metric_files(paths: Iterable[str], key: str) -> List[List[float]]:
    vectors: List[List[float]] = []
    for path_str in paths:
        path = Path(path_str)
        data = json.loads(path.read_text())
        per_example = data.get("per_example") or []
        vectors.append([float(ex[key]) for ex in per_example if key in ex])
    return vectors


def _load_judge_vectors(paths: Iterable[str], model: Optional[str]) -> List[List[float]]:
    vectors: List[List[float]] = []
    for path_str in paths:
        path = Path(path_str)
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        if model:
            rows = [row for row in rows if row.get("model") == model]
        vectors.append([1.0 if str(row.get("label", "")).strip().lower() == "supported" else 0.0 for row in rows])
    return vectors


def run_faithfulness_ci(args: argparse.Namespace) -> None:
    payload: Dict[str, Any] = {}
    if args.qags:
        ci = seeds_ci(_load_seed_metric_files(args.qags, "qags"), n_boot=args.n_boot)
        payload["QAGS"] = {"ci": ci, "formatted": fmt_pm(ci, scale=1, decimals=2)}
    if args.qags_bs:
        ci = seeds_ci(_load_seed_metric_files(args.qags_bs, "qags_bs"), n_boot=args.n_boot)
        payload["QAGS_BS"] = {"ci": ci, "formatted": fmt_pm(ci, scale=1, decimals=2)}
    if args.grounded:
        ci = seeds_ci(_load_seed_metric_files(args.grounded, "score"), n_boot=args.n_boot)
        payload["Log_Groundedness"] = {"ci": ci, "formatted": fmt_pm(ci, scale=1, decimals=2)}
    if args.judge_a:
        ci = seeds_ci(_load_judge_vectors(args.judge_a, args.judge_a_model), n_boot=args.n_boot)
        payload["Judge_A"] = {"ci": ci, "formatted": fmt_pm(ci, scale=1, decimals=2)}
    if args.judge_b:
        ci = seeds_ci(_load_judge_vectors(args.judge_b, args.judge_b_model), n_boot=args.n_boot)
        payload["Judge_B"] = {"ci": ci, "formatted": fmt_pm(ci, scale=1, decimals=2)}
    print(json.dumps(payload, indent=2))


def _score_for_dataset(dataset: str, prediction: str, gold: Any) -> float:
    if dataset == "tatqa":
        return tatqa_em_f1_half(prediction, gold)
    return float(official_em(prediction, gold))


def run_robustness(args: argparse.Namespace) -> None:
    samples = load_split(args.dataset, args.split, limit=args.limit)
    para_cache_path = Path(args.paraphrase_cache)
    para_cache = load_cache(str(para_cache_path)) if args.family == "semantic" else {}
    per_example_scores: Dict[str, List[float]] = {system: [] for system in args.systems}
    for sample in samples:
        items = example_to_items(sample)
        for seed in args.seeds:
            corrupted_items, _ = corrupt_example(
                items,
                args.rate,
                args.family,
                seed,
                sample.get("id", "unknown"),
                llm=_llm_paraphrase if args.family == "semantic" else None,
                para_cache=para_cache,
            )
            for system in args.systems:
                pred = run_system(system, sample, corrupted_items, llm=args.llm, summarizer_llm=args.summarizer_llm, max_rounds=args.max_rounds)
                per_example_scores[system].append(_score_for_dataset(args.dataset, pred, sample.get("answer")))
    if args.family == "semantic":
        para_cache_path.parent.mkdir(parents=True, exist_ok=True)
        save_cache(para_cache, str(para_cache_path))
    out: Dict[str, Any] = {"dataset": args.dataset, "split": args.split, "family": args.family, "rate": args.rate}
    for system, values in per_example_scores.items():
        ci = bootstrap_ci(values, n_boot=args.n_boot)
        out[system] = {"ci": ci, "formatted": fmt_pm(ci, scale=100.0 if args.dataset != 'tatqa' else 100.0, decimals=1), "per_example": values}
    if "dealog" in per_example_scores and len(args.systems) > 1:
        dealog_values = per_example_scores["dealog"]
        best_other_name = None
        best_other_values = None
        best_other_mean = float("-inf")
        for system, values in per_example_scores.items():
            if system == "dealog":
                continue
            mean_val = sum(values) / len(values) if values else 0.0
            if mean_val > best_other_mean:
                best_other_name = system
                best_other_values = values
                best_other_mean = mean_val
        if best_other_values is not None:
            out["dealog_vs_best_other"] = {
                "other_system": best_other_name,
                "paired": paired_bootstrap_diff(dealog_values, best_other_values, n_boot=max(args.n_boot, 10000)),
            }
    print(json.dumps(out, indent=2))


def run_fallback_breakdown(args: argparse.Namespace) -> None:
    raise SystemExit(
        "Fallback breakdown is not runnable yet in this repo: verification logs do not include flagged_item_id or fallback_answer. "
        "Instrument VerificationAgent/coordinator first, then rerun."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run revision-pack experiments.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    finqa = sub.add_parser("finqa-coverage")
    finqa.add_argument("--split", default="official_test")
    finqa.add_argument("--limit", type=int, default=None)
    finqa.add_argument("--results-dir", default="benchmarks/results/revision_pack_finqa")
    finqa.add_argument("--llm", default=os.getenv("PRIMARY_MODEL_NAME"))
    finqa.add_argument("--summarizer-llm", default=os.getenv("DEALOG_SUMMARIZER_MODEL"))
    finqa.add_argument("--max-rounds", type=int, default=6)
    finqa.add_argument("--tol", type=float, default=0.01)
    finqa.add_argument("--n-boot", type=int, default=1000)
    finqa.add_argument("--run-missing", action="store_true")
    finqa.add_argument("--seeds", type=int, nargs="+", default=SEEDS)
    finqa.set_defaults(func=run_finqa_coverage)

    faith = sub.add_parser("faithfulness-ci")
    faith.add_argument("--qags", nargs="*")
    faith.add_argument("--qags-bs", nargs="*")
    faith.add_argument("--grounded", nargs="*")
    faith.add_argument("--judge-a", nargs="*")
    faith.add_argument("--judge-a-model", default=None)
    faith.add_argument("--judge-b", nargs="*")
    faith.add_argument("--judge-b-model", default=None)
    faith.add_argument("--n-boot", type=int, default=1000)
    faith.set_defaults(func=run_faithfulness_ci)

    robust = sub.add_parser("robustness")
    robust.add_argument("--dataset", required=True, choices=["mmqa", "tatqa", "finqa", "fetaqa", "crtqa"])
    robust.add_argument("--split", default="dev")
    robust.add_argument("--family", required=True, choices=["structural", "semantic"])
    robust.add_argument("--rate", type=float, required=True)
    robust.add_argument("--systems", nargs="+", default=["dealog"])
    robust.add_argument("--limit", type=int, default=None)
    robust.add_argument("--llm", default=os.getenv("PRIMARY_MODEL_NAME"))
    robust.add_argument("--summarizer-llm", default=os.getenv("DEALOG_SUMMARIZER_MODEL"))
    robust.add_argument("--max-rounds", type=int, default=6)
    robust.add_argument("--paraphrase-cache", default="cache/para_default.json")
    robust.add_argument("--n-boot", type=int, default=1000)
    robust.add_argument("--seeds", type=int, nargs="+", default=SEEDS)
    robust.set_defaults(func=run_robustness)

    fallback = sub.add_parser("fallback-breakdown")
    fallback.set_defaults(func=run_fallback_breakdown)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
