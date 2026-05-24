#!/usr/bin/env python3
"""B1 ablation: is the typed Type field load-bearing?"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import string
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.coordinator import AdaptiveOrchestrator
from utils.data_loader import load_benchmark


DEALOG_TYPES: List[str] = [
    "question",
    "plan",
    "context",
    "table",
    "calculation",
    "visual",
    "summary",
    "verification",
]
UNIFORM_PLACEHOLDER = "entry"
VARIANT_NAMES = ("full_types", "uniform_types", "random_types")

_NORM_RE = re.compile(r"\s+")


def make_full_types_transform() -> None:
    """Baseline: keep the type field unchanged."""

    return None


def make_uniform_types_transform() -> Callable:
    """Collapse all entry types to a single placeholder."""

    def _transform(entry):
        entry.type = UNIFORM_PLACEHOLDER
        return entry

    return _transform


def make_random_types_transform(seed: int = 0) -> Callable:
    """Assign a wrong-but-valid type to each entry."""

    rng = random.Random(seed)

    def _transform(entry):
        choices = [entry_type for entry_type in DEALOG_TYPES if entry_type != entry.type]
        entry.type = rng.choice(choices) if choices else entry.type
        return entry

    return _transform


VARIANTS = {
    "full_types": make_full_types_transform,
    "uniform_types": make_uniform_types_transform,
    "random_types": make_random_types_transform,
}


def _normalize(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = text.replace("\u2212", "-")
    text = _NORM_RE.sub(" ", text)
    return text.strip(string.whitespace + string.punctuation)


def _extract_numbers(text: str) -> List[float]:
    numbers: List[float] = []
    for match in re.findall(r"[-+]?\d+(?:\.\d+)?", text.replace(",", "")):
        try:
            numbers.append(float(match))
        except ValueError:
            continue
    return numbers


def _is_correct(prediction: Any, reference: Any) -> bool:
    pred = _normalize(prediction)
    ref = _normalize(reference)
    if not ref:
        return False
    if pred == ref:
        return True

    ref_numbers = _extract_numbers(ref)
    pred_numbers = _extract_numbers(pred)
    if ref_numbers and pred_numbers:
        tolerance = max(1e-3, 0.01 * abs(ref_numbers[0]))
        return any(abs(ref_numbers[0] - value) <= tolerance for value in pred_numbers)
    return False


def _resolve_reference(sample: Dict[str, Any]) -> Any:
    return sample.get("answer") or sample.get("reference") or sample.get("ground_truth")


def load_dataset(name: str, split: str, limit: Optional[int]) -> List[Dict[str, Any]]:
    """Load benchmark examples using the repo's canonical loader."""

    return load_benchmark(name, split=split, limit=limit)


def run_variant(
    variant_name: str,
    samples: List[Dict[str, Any]],
    *,
    llm: str,
    summarizer_llm: Optional[str],
    summarizer_temperature: float,
    summarizer_max_tokens: int,
    visual_caption_model: Optional[str],
    visual_caption_path: Optional[str],
    visual_ocr_engine: Optional[str],
    visual_ocr_model_dir: Optional[str],
    max_rounds: int,
    random_seed: int,
    scheduler_model: Optional[str],
    scheduler_threshold: float,
    parallel_retrieval: bool,
    enable_calculator: bool,
) -> Dict[str, Any]:
    """Run the orchestrator over samples with one type-field condition."""

    if variant_name == "random_types":
        transform = make_random_types_transform(seed=random_seed)
    else:
        transform = VARIANTS[variant_name]()

    orchestrator = AdaptiveOrchestrator(
        model_name=llm,
        summarizer_model_name=summarizer_llm,
        summarizer_temperature=summarizer_temperature,
        summarizer_max_tokens=summarizer_max_tokens,
        visual_model_name=visual_caption_model,
        visual_caption_model=visual_caption_model,
        visual_caption_model_path=visual_caption_path,
        visual_ocr_engine=visual_ocr_engine,
        visual_ocr_model_dir=visual_ocr_model_dir,
        max_rounds=max_rounds,
        entry_transform=transform,
        scheduler_model_path=scheduler_model,
        scheduler_threshold=scheduler_threshold,
        parallel_retrieval=parallel_retrieval,
        enable_calculator=enable_calculator,
    )

    per_example: List[Dict[str, Any]] = []
    total_correct = 0
    total_latency = 0.0
    started_at = time.perf_counter()

    for index, sample in enumerate(samples):
        example_start = time.perf_counter()
        try:
            result = orchestrator.run(sample)
            prediction = result.get("answer") or result.get("prediction") or ""
        except Exception as exc:  # pragma: no cover - defensive
            result = {"error": str(exc)}
            prediction = ""

        latency = time.perf_counter() - example_start
        total_latency += latency

        reference = _resolve_reference(sample)
        correct = _is_correct(prediction, reference)
        total_correct += int(correct)
        per_example.append(
            {
                "id": sample.get("id", f"{variant_name}-{index}"),
                "question": sample.get("question"),
                "prediction": prediction,
                "reference": reference,
                "correct": correct,
                "latency_sec": latency,
                "error": result.get("error"),
            }
        )

        if (index + 1) % 100 == 0:
            elapsed = time.perf_counter() - started_at
            print(
                f"[{variant_name}] {index + 1}/{len(samples)} "
                f"acc={total_correct / (index + 1):.4f} "
                f"elapsed={elapsed:.0f}s "
                f"avg={elapsed / (index + 1):.2f}s/ex"
            )

    n = len(samples)
    elapsed = time.perf_counter() - started_at
    return {
        "variant": variant_name,
        "n": n,
        "accuracy": total_correct / n if n else 0.0,
        "latency_sec_total": elapsed,
        "latency_sec_per_example": total_latency / n if n else 0.0,
        "per_example": per_example,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        required=True,
        choices=["tatqa", "finqa", "wikitq", "fetaqa", "mmqa", "crtqa"],
    )
    parser.add_argument("--split", default="dev")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--llm",
        default=os.getenv("PRIMARY_MODEL_NAME"),
        help="Primary model ID (defaults to PRIMARY_MODEL_NAME).",
    )
    parser.add_argument(
        "--summarizer-llm",
        default=os.getenv("DEALOG_SUMMARIZER_MODEL"),
        help="Model used by summarizer/verifier client (defaults to DEALOG_SUMMARIZER_MODEL).",
    )
    parser.add_argument(
        "--summarizer-temperature",
        type=float,
        default=float(os.getenv("DEALOG_SUMMARIZER_TEMPERATURE", "0.2")),
    )
    parser.add_argument(
        "--summarizer-max-tokens",
        type=int,
        default=int(os.getenv("DEALOG_SUMMARIZER_MAX_TOKENS", "256")),
    )
    parser.add_argument("--visual-caption-model", default=None)
    parser.add_argument("--visual-caption-path", default=None)
    parser.add_argument("--visual-ocr-engine", default=None)
    parser.add_argument("--visual-ocr-model-dir", default=None)
    parser.add_argument("--max-rounds", type=int, default=6)
    parser.add_argument("--seed", type=int, default=2024)
    parser.add_argument(
        "--variants",
        default="full_types,uniform_types,random_types",
        help="Comma-separated list of variants to run.",
    )
    parser.add_argument("--scheduler", default=None, help="Path to a joblib logistic gate.")
    parser.add_argument("--scheduler-threshold", type=float, default=0.4)
    parser.add_argument("--parallel-retrieval", action="store_true")
    parser.add_argument(
        "--enable-calculator",
        dest="enable_calculator",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--disable-calculator",
        dest="enable_calculator",
        action="store_false",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        required=True,
        help="Destination JSON file for aggregate and per-example results.",
    )
    parser.add_argument(
        "--cuda-visible-devices",
        default=os.getenv("DEALOG_CUDA_VISIBLE_DEVICES"),
        help="Optional CUDA_VISIBLE_DEVICES value for this run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    args.llm = str(args.llm or "").strip() or str(os.getenv("PRIMARY_MODEL_NAME") or "").strip()
    if not args.llm:
        raise SystemExit("Missing model ID. Pass --llm or set PRIMARY_MODEL_NAME in .env.")

    args.summarizer_llm = (
        str(args.summarizer_llm or "").strip()
        or str(os.getenv("DEALOG_SUMMARIZER_MODEL") or "").strip()
        or None
    )

    if args.cuda_visible_devices is not None and str(args.cuda_visible_devices).strip():
        os.environ["CUDA_VISIBLE_DEVICES"] = str(args.cuda_visible_devices).strip()
        print(f"[typed_log_ablation] CUDA_VISIBLE_DEVICES={os.environ['CUDA_VISIBLE_DEVICES']}")

    requested = [variant.strip() for variant in args.variants.split(",") if variant.strip()]
    for variant in requested:
        if variant not in VARIANTS:
            raise SystemExit(
                f"Unknown variant {variant!r}; expected a subset of {list(VARIANTS)}"
            )

    print(f"Loading {args.dataset} {args.split}...")
    samples = load_dataset(args.dataset, args.split, args.limit)
    print(f"Loaded {len(samples)} samples")

    results: Dict[str, Any] = {}
    for variant in requested:
        print(f"\n=== Variant: {variant} ===")
        results[variant] = run_variant(
            variant,
            samples,
            llm=args.llm,
            summarizer_llm=args.summarizer_llm,
            summarizer_temperature=args.summarizer_temperature,
            summarizer_max_tokens=args.summarizer_max_tokens,
            visual_caption_model=args.visual_caption_model,
            visual_caption_path=args.visual_caption_path,
            visual_ocr_engine=args.visual_ocr_engine,
            visual_ocr_model_dir=args.visual_ocr_model_dir,
            max_rounds=args.max_rounds,
            random_seed=args.seed,
            scheduler_model=args.scheduler,
            scheduler_threshold=args.scheduler_threshold,
            parallel_retrieval=args.parallel_retrieval,
            enable_calculator=args.enable_calculator,
        )

    deltas: Dict[str, float] = {}
    if "full_types" in results:
        baseline = results["full_types"]["accuracy"]
        for variant in requested:
            if variant == "full_types":
                continue
            deltas[f"{variant}_vs_full"] = results[variant]["accuracy"] - baseline

    payload = {
        "dataset": args.dataset,
        "split": args.split,
        "n": len(samples),
        "llm": args.llm,
        "summarizer_llm": args.summarizer_llm or args.llm,
        "max_rounds": args.max_rounds,
        "random_seed": args.seed,
        "variants": requested,
        "results": {
            variant: {
                "accuracy": results[variant]["accuracy"],
                "n": results[variant]["n"],
                "latency_sec_total": results[variant]["latency_sec_total"],
                "latency_sec_per_example": results[variant]["latency_sec_per_example"],
            }
            for variant in requested
        },
        "deltas": deltas,
        "per_example_by_variant": {
            variant: results[variant]["per_example"] for variant in requested
        },
    }

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.output_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"Dataset: {args.dataset} {args.split} (N={len(samples)})")
    print(f"Model:   {args.llm}")
    print("=" * 60)
    for variant in requested:
        result = results[variant]
        print(
            f"{variant:>16s}: acc={result['accuracy']:.4f} "
            f"latency={result['latency_sec_per_example']:.2f}s/ex"
        )
    if deltas:
        print()
        for key, value in deltas.items():
            sign = "+" if value >= 0 else ""
            print(f"{key:>20s}: {sign}{value:.4f} EM")
    print(f"\nFull results written to {args.output_file}")


if __name__ == "__main__":
    main()
