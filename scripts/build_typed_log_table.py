#!/usr/bin/env python3
"""Build the typed-log ablation table for the paper from one or more JSON outputs."""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _bootstrap_ci(
    values: List[bool],
    n_resamples: int = 1000,
    conf: float = 0.95,
    seed: int = 0,
) -> Tuple[float, float, float]:
    """Return (mean, lower, upper) for a bootstrap confidence interval."""

    if not values:
        return (0.0, 0.0, 0.0)

    rng = random.Random(seed)
    n = len(values)
    means: List[float] = []
    for _ in range(n_resamples):
        sample = rng.choices(values, k=n)
        means.append(sum(sample) / n)
    means.sort()

    lo_idx = int(((1 - conf) / 2) * n_resamples)
    hi_idx = min(n_resamples - 1, int(((1 + conf) / 2) * n_resamples))
    return (statistics.mean(values), means[lo_idx], means[hi_idx])


DATASET_LABEL = {
    "tatqa": "TAT-QA",
    "finqa": "FinQA",
    "wikitq": "WikiTQ",
    "fetaqa": "FeTaQA",
    "mmqa": "MMQA",
    "crtqa": "CRT-QA",
}
DATASET_ORDER = ["tatqa", "finqa", "wikitq", "fetaqa", "mmqa", "crtqa"]
VARIANT_LABEL = {
    "full_types": "Typed (baseline)",
    "uniform_types": "Untyped",
    "random_types": "Random types",
}
VARIANT_ORDER = ["full_types", "uniform_types", "random_types"]


def build_row(record: Dict) -> Dict:
    """Compute mean and CI statistics per variant for one dataset file."""

    dataset = record["dataset"]
    per_example = record.get("per_example_by_variant") or {}
    output = {"dataset": dataset, "n": record["n"], "variants": {}}

    for variant in VARIANT_ORDER:
        if variant not in per_example:
            continue
        flags = [bool(entry.get("correct")) for entry in per_example[variant]]
        mean, lo, hi = _bootstrap_ci(flags)
        output["variants"][variant] = {
            "mean": mean,
            "ci_lo": lo,
            "ci_hi": hi,
            "half": max(mean - lo, hi - mean),
        }

    return output


def format_markdown(rows: List[Dict]) -> str:
    """Render a Markdown table with accuracy percentages and CI half-widths."""

    header = ["Dataset", "N"] + [VARIANT_LABEL[v] for v in VARIANT_ORDER] + ["Δ Untyped", "Δ Random"]
    lines = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join(["---"] * len(header)) + "|",
    ]

    rows_sorted = sorted(
        rows,
        key=lambda row: DATASET_ORDER.index(row["dataset"]) if row["dataset"] in DATASET_ORDER else 999,
    )

    for row in rows_sorted:
        cells = [DATASET_LABEL.get(row["dataset"], row["dataset"]), str(row["n"])]
        full = row["variants"].get("full_types", {}).get("mean")

        for variant in VARIANT_ORDER:
            stats = row["variants"].get(variant)
            if not stats:
                cells.append("—")
                continue
            cells.append(f"{stats['mean'] * 100:.1f} ± {stats['half'] * 100:.1f}")

        for variant in ("uniform_types", "random_types"):
            stats = row["variants"].get(variant)
            if not stats or full is None:
                cells.append("—")
                continue
            delta = (stats["mean"] - full) * 100
            cells.append(f"{delta:+.1f}")

        lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines)


def format_latex(rows: List[Dict]) -> str:
    """Render a LaTeX table fragment for the appendix."""

    lines = [
        r"\begin{table}[t]",
        r"\centering\small",
        r"\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{lrccccc}",
        r"\toprule",
        r"\textbf{Dataset} & \textbf{N} & \textbf{Typed} & \textbf{Untyped} & \textbf{Random} & \textbf{$\Delta$Unt.} & \textbf{$\Delta$Rand.} \\",
        r"\midrule",
    ]

    rows_sorted = sorted(
        rows,
        key=lambda row: DATASET_ORDER.index(row["dataset"]) if row["dataset"] in DATASET_ORDER else 999,
    )

    for row in rows_sorted:
        full = row["variants"].get("full_types", {}).get("mean")
        cells = [DATASET_LABEL.get(row["dataset"], row["dataset"]), f"{row['n']:,}"]

        for variant in VARIANT_ORDER:
            stats = row["variants"].get(variant)
            if not stats:
                cells.append("---")
                continue
            cells.append(f"{stats['mean'] * 100:.1f}\\(\\pm\\){stats['half'] * 100:.1f}")

        for variant in ("uniform_types", "random_types"):
            stats = row["variants"].get(variant)
            if not stats or full is None:
                cells.append("---")
                continue
            delta = (stats["mean"] - full) * 100
            cells.append(f"\\textbf{{{delta:+.1f}}}")

        lines.append(" & ".join(cells) + r" \\")

    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            (
                r"\caption{\textbf{Typed-log ablation.} Each cell is EM (\%) $\pm$ half-width of a 95\% "
                r"bootstrap CI (1{,}000 resamples over per-example correctness). \textit{Typed} is the "
                r"standard \method{} configuration. \textit{Untyped} replaces every log entry's Type field "
                r"with a single placeholder. \textit{Random} shuffles each entry to a different valid type. "
                r"Both perturbations leave content, agent, metadata, and \texttt{needs}/\texttt{resolves} "
                r"unchanged---only the Type field is altered. The drop under Untyped quantifies how much of "
                r"\method's performance depends on typed log routing; the gap between Untyped and Random "
                r"isolates whether the type values are informative or only their presence matters.}"
            ),
            r"\label{tab:typed_log_ablation}",
            r"\end{table}",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        type=Path,
        help="One or more typed_log_ablation.py JSON outputs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output stem; writes .md and .tex files.",
    )
    args = parser.parse_args()

    rows = []
    for path in args.inputs:
        with path.open("r", encoding="utf-8") as handle:
            record = json.load(handle)
        rows.append(build_row(record))

    markdown = format_markdown(rows)
    latex = format_latex(rows)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".md").write_text(markdown + "\n", encoding="utf-8")
    args.output.with_suffix(".tex").write_text(latex + "\n", encoding="utf-8")

    print(markdown)
    print()
    print(f"Wrote {args.output.with_suffix('.md')}")
    print(f"Wrote {args.output.with_suffix('.tex')}")


if __name__ == "__main__":
    main()
