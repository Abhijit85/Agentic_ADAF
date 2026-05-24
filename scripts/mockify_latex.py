#!/usr/bin/env python3
"""
MOCK DATA ONLY.
This script replaces LaTeX range placeholders like `70.x--72.x`
with random decimal values like `70.8`.

It is for formatting/pipeline testing only.
Do not use its output as experimental results.
"""

from __future__ import annotations

import random
import re
import sys
from pathlib import Path

RANGE_RE = re.compile(r"(\d+)\.x--(\d+)\.x")


def sample_from_range(match: re.Match[str]) -> str:
    lo = int(match.group(1))
    hi = int(match.group(2))
    value = round(random.uniform(float(lo), float(hi)), 1)
    value = max(float(lo), min(value, float(hi)))
    return f"{value:.1f}"


def convert_text(text: str, seed: int | None = None) -> str:
    if seed is not None:
        random.seed(seed)

    header = (
        "% MOCK DATA ONLY.\n"
        "% Auto-generated from placeholder ranges for formatting/pipeline testing.\n"
        "% Do NOT treat these values as real benchmark results.\n\n"
    )

    converted = RANGE_RE.sub(sample_from_range, text)

    if text.lstrip().startswith("% MOCK DATA ONLY."):
        return converted
    return header + converted


def print_usage() -> None:
    print(
        "Usage: python scripts/mockify_latex.py input.tex [output.tex] [seed]\n"
        "   or: python scripts/mockify_latex.py [seed] < input.tex > output.tex"
    )


def main() -> None:
    args = sys.argv[1:]

    if not args:
        text = sys.stdin.read()
        if not text.strip():
            print_usage()
            sys.exit(1)
        print(convert_text(text), end="")
        return

    if len(args) == 1 and args[0].isdigit():
        text = sys.stdin.read()
        if not text.strip():
            print_usage()
            sys.exit(1)
        print(convert_text(text, seed=int(args[0])), end="")
        return

    input_path = Path(args[0])
    output_path = (
        Path(args[1])
        if len(args) >= 2 and not args[1].isdigit()
        else input_path.with_name(f"{input_path.stem}_mock.tex")
    )
    seed = None
    if len(args) >= 2 and args[1].isdigit():
        seed = int(args[1])
    elif len(args) >= 3:
        seed = int(args[2])

    text = input_path.read_text()
    converted = convert_text(text, seed=seed)
    output_path.write_text(converted)

    print(output_path)


if __name__ == "__main__":
    main()
