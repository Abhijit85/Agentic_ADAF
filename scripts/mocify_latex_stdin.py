#!/usr/bin/env python3
"""
MOCK DATA ONLY.
Replaces LaTeX placeholders like `70.x--72.x` with sampled decimals like `70.8`.
For formatting/testing only. Do not use as real benchmark results.
"""

from __future__ import annotations

import random
import re
import sys

RANGE_RE = re.compile(r"(\d+)\.x--(\d+)\.x")


def sample_from_range(match: re.Match[str]) -> str:
    lo = int(match.group(1))
    hi = int(match.group(2))
    value = round(random.uniform(lo, hi + 0.9), 1)
    if value > hi + 0.9:
        value = hi + 0.9
    return f"{value:.1f}"


def main() -> None:
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else None
    if seed is not None:
        random.seed(seed)

    text = sys.stdin.read()
    if not text.strip():
        raise SystemExit("No input provided on stdin.")

    print("% MOCK DATA ONLY.")
    print("% Auto-generated from placeholder ranges for formatting/pipeline testing.")
    print("% Do NOT treat these values as real benchmark results.")
    print()

    print(RANGE_RE.sub(sample_from_range, text), end="")


if __name__ == "__main__":
    main()