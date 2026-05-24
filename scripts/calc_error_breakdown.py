#!/usr/bin/env python3
"""Aggregate TAT-QA error-category breakdown for Table 6 of dealog_arr.tex.

Given:
  - benchmarks/results/tatqa_dev_base.json     (DeALOG base, --disable-calculator)
  - benchmarks/results/tatqa_dev_calc.json     (DeALOG + CalculatorAgent)
  - data/TATQA/error_categories.json           ({example_id: category} for the 100-sample annotation)

This script computes, per error category:
  - N        : count in the 100-sample annotation
  - base %   : % of category solved by DeALOG base (typically 0 by construction
               for the categories you sampled FROM failures, but kept for completeness)
  - calc %   : % of category solved by DeALOG + CalculatorAgent
  - Δ%       : absolute improvement (calc % − base %)

Output (JSON + Markdown ready for the paper):
  benchmarks/results/tatqa_calc_breakdown.json
  benchmarks/results/tatqa_calc_breakdown.md

The Markdown is in the exact column order of Table 6:
  Error Category | N | Base % | +Calc % | Δ%

Usage:
  python scripts/calc_error_breakdown.py \\
    --base-file benchmarks/results/tatqa_dev_base.json \\
    --calc-file benchmarks/results/tatqa_dev_calc.json \\
    --annotations data/TATQA/error_categories.json \\
    --output benchmarks/results/tatqa_calc_breakdown
"""

from __future__ import annotations

import argparse
import json
import re
import string
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


CATEGORY_ORDER = [
    "scale_unit",
    "arithmetic",
    "row_col",
    "retrieval",
    "verif_false_accept",
    "other",
]

CATEGORY_LABEL = {
    "scale_unit": "Scale/unit mismatch",
    "arithmetic": "Multi-step arithmetic",
    "row_col": "Row/col misalignment",
    "retrieval": "Evidence retrieval miss",
    "verif_false_accept": "Verification false-accept",
    "other": "Other (parsing, OCR)",
}


def _normalise(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = text.replace("−", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip(string.whitespace + string.punctuation)


def _numbers_match(ref: str, cand: str) -> bool:
    def nums(text: str) -> List[float]:
        out: List[float] = []
        for match in re.findall(r"[-+]?\d+(?:\.\d+)?", text.replace(",", "")):
            try:
                out.append(float(match))
            except ValueError:
                pass
        return out

    ref_nums, cand_nums = nums(ref), nums(cand)
    if not ref_nums or not cand_nums:
        return False
    tolerance = max(1e-3, 0.01 * abs(ref_nums[0]))
    return any(abs(ref_nums[0] - value) <= tolerance for value in cand_nums)


def _is_correct(example: Dict[str, Any]) -> bool:
    """Mirror the correctness logic from scripts/run_dealog.py."""

    pred = _normalise(example.get("prediction"))
    ref = _normalise(example.get("reference"))
    if not ref:
        return False
    if pred == ref:
        return True
    return _numbers_match(ref, pred)


def _index_by_id(results_file: Path) -> Dict[str, Dict[str, Any]]:
    with results_file.open(encoding="utf-8") as handle:
        data = json.load(handle)

    per_example = data.get("per_example") or []
    out: Dict[str, Dict[str, Any]] = {}
    for example in per_example:
        example_id = example.get("id") or example.get("uid") or example.get("question_id")
        if example_id is None:
            example_id = example.get("question")
        if example_id is not None:
            out[str(example_id)] = example
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-file",
        type=Path,
        required=True,
        help="JSON from run_dealog.py with --disable-calculator",
    )
    parser.add_argument(
        "--calc-file",
        type=Path,
        required=True,
        help="JSON from run_dealog.py with --enable-calculator (default)",
    )
    parser.add_argument(
        "--annotations",
        type=Path,
        required=True,
        help="JSON mapping {example_id: error_category} for the 100-sample audit",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output stem (will write .json and .md)",
    )
    args = parser.parse_args()

    base = _index_by_id(args.base_file)
    calc = _index_by_id(args.calc_file)
    with args.annotations.open(encoding="utf-8") as handle:
        annotations: Dict[str, str] = json.load(handle)

    by_cat: Dict[str, List[Dict[str, bool]]] = defaultdict(list)
    missing_base: List[str] = []
    missing_calc: List[str] = []

    for example_id, category in annotations.items():
        example_key = str(example_id)
        if example_key not in base:
            missing_base.append(example_key)
            continue
        if example_key not in calc:
            missing_calc.append(example_key)
            continue
        by_cat[category].append(
            {
                "id": example_key,
                "base_correct": _is_correct(base[example_key]),
                "calc_correct": _is_correct(calc[example_key]),
            }
        )

    rows = []
    for category in CATEGORY_ORDER:
        items = by_cat.get(category, [])
        count = len(items)
        if count == 0:
            rows.append(
                {
                    "category": category,
                    "label": CATEGORY_LABEL[category],
                    "N": 0,
                    "base_pct": None,
                    "calc_pct": None,
                    "delta": None,
                }
            )
            continue

        base_pct = 100.0 * sum(item["base_correct"] for item in items) / count
        calc_pct = 100.0 * sum(item["calc_correct"] for item in items) / count
        rows.append(
            {
                "category": category,
                "label": CATEGORY_LABEL[category],
                "N": count,
                "base_pct": round(base_pct, 1),
                "calc_pct": round(calc_pct, 1),
                "delta": round(calc_pct - base_pct, 1),
            }
        )

    overall_n = sum(row["N"] for row in rows)
    if overall_n:
        overall_base = (
            100.0
            * sum(item["base_correct"] for items in by_cat.values() for item in items)
            / overall_n
        )
        overall_calc = (
            100.0
            * sum(item["calc_correct"] for items in by_cat.values() for item in items)
            / overall_n
        )
    else:
        overall_base = None
        overall_calc = None

    args.output.parent.mkdir(parents=True, exist_ok=True)
    json_out = args.output.with_suffix(".json")
    md_out = args.output.with_suffix(".md")

    payload = {
        "rows": rows,
        "total_N": overall_n,
        "overall_base_pct": round(overall_base, 1) if overall_base is not None else None,
        "overall_calc_pct": round(overall_calc, 1) if overall_calc is not None else None,
        "missing_in_base_file": missing_base,
        "missing_in_calc_file": missing_calc,
    }
    with json_out.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    lines = [
        "| Error Category | N | Base % | +Calc % | Δ% |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        if row["N"] == 0:
            lines.append(f"| {row['label']} | 0 | — | — | — |")
            continue
        lines.append(
            f"| {row['label']} | {row['N']} | "
            f"{row['base_pct']:.1f} | {row['calc_pct']:.1f} | "
            f"{row['delta']:+.1f} |"
        )
    if overall_n:
        lines.append(
            f"| **Total** | **{overall_n}** | "
            f"**{overall_base:.1f}** | **{overall_calc:.1f}** | "
            f"**{overall_calc - overall_base:+.1f}** |"
        )
    with md_out.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")

    print(f"Wrote {json_out}")
    print(f"Wrote {md_out}")
    if missing_base or missing_calc:
        print(
            f"WARNING: {len(missing_base)} ids missing in base, "
            f"{len(missing_calc)} ids missing in calc"
        )


if __name__ == "__main__":
    main()
