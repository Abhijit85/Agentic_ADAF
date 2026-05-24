r"""
finqa_program.py — program-level faithfulness on FinQA (Table~\ref{tab:finqa_prog}).

Coverage = fraction of DeALOG answers that match the executed output of FinQA's
annotated gold reasoning program, under the official numeric tolerance (+/- 0.01).
This is execution-grounded, complementing the lexical log-groundedness metric.

FinQA programs look like:  "subtract(5829, 5735), divide(#0, 5735)"
  - ops are comma-separated and executed left to right
  - #k  references the result of the k-th op (0-indexed)
  - const_X are literals (const_100 -> 100, const_m1 -> -1)
  - bare args are numbers (commas/$/% stripped)
  - table_* ops need the table; if absent, the example is marked UNCHECKABLE
    (so it is excluded from the denominator rather than silently counted wrong).

Usage:
    res = matches(pred_answer, gold_program, table=table_rows)   # True / False / None
    # None == uncheckable; build the 0/1 vector over the checkable ones only.
"""

from __future__ import annotations
import re
from typing import Optional

# --------------------------------------------------------------------------- #
# Argument parsing
# --------------------------------------------------------------------------- #
_CONSTS = {
    "const_1": 1.0, "const_2": 2.0, "const_3": 3.0, "const_4": 4.0, "const_5": 5.0,
    "const_10": 10.0, "const_100": 100.0, "const_1000": 1000.0,
    "const_10000": 1e4, "const_100000": 1e5, "const_1000000": 1e6,
    "const_10000000": 1e7, "const_100000000": 1e8, "const_1000000000": 1e9,
    "const_m1": -1.0,
}

def _to_number(tok: str) -> Optional[float]:
    tok = tok.strip()
    if tok in _CONSTS:
        return _CONSTS[tok]
    cleaned = tok.replace(",", "").replace("$", "").replace("%", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _split_ops(program: str) -> list[tuple[str, list[str]]]:
    """Parse 'op(a, b), op(c, d)' -> [('op',['a','b']), ...]."""
    ops = []
    for m in re.finditer(r"([a-zA-Z_]+)\(([^)]*)\)", program):
        name = m.group(1).strip()
        args = [a.strip() for a in m.group(2).split(",") if a.strip() != ""]
        ops.append((name, args))
    return ops


# --------------------------------------------------------------------------- #
# Table reductions (optional; only needed for table_* programs)
# --------------------------------------------------------------------------- #
def _column_values(table, ref: str) -> list[float]:
    """Best-effort: pull numeric values for a table_* op. `ref` may name a column."""
    vals = []
    if table is None:
        return vals
    for row in table:
        for cell in row:
            v = _to_number(str(cell))
            if v is not None:
                vals.append(v)
    return vals  # NOTE: refine to the referenced column if your gold programs name one.


# --------------------------------------------------------------------------- #
# Executor
# --------------------------------------------------------------------------- #
def execute_program(program: str, table=None) -> Optional[float | str]:
    ops = _split_ops(program)
    if not ops:
        return None
    results: list[float | str] = []

    def resolve(tok: str):
        if tok.startswith("#"):
            k = int(tok[1:])
            return results[k] if 0 <= k < len(results) else None
        return _to_number(tok)

    for name, args in ops:
        try:
            if name in ("add", "subtract", "multiply", "divide", "exp", "greater"):
                a, b = resolve(args[0]), resolve(args[1])
                if a is None or b is None:
                    return None
                if name == "add":        results.append(a + b)
                elif name == "subtract": results.append(a - b)
                elif name == "multiply": results.append(a * b)
                elif name == "divide":   results.append(a / b if b != 0 else None)
                elif name == "exp":      results.append(a ** b)
                elif name == "greater":  results.append("yes" if a > b else "no")
            elif name in ("table_sum", "table_average", "table_max", "table_min"):
                vals = _column_values(table, args[0] if args else "")
                if not vals:
                    return None
                if name == "table_sum":     results.append(sum(vals))
                elif name == "table_average": results.append(sum(vals) / len(vals))
                elif name == "table_max":   results.append(max(vals))
                elif name == "table_min":   results.append(min(vals))
            else:
                return None  # unknown op -> uncheckable
        except (IndexError, TypeError, ZeroDivisionError):
            return None
    return results[-1] if results else None


# --------------------------------------------------------------------------- #
# Comparison
# --------------------------------------------------------------------------- #
def matches(pred_answer: str, gold_program: str, table=None,
            tol: float = 0.01) -> Optional[bool]:
    """
    Returns True / False, or None if the example is not program-checkable
    (table_* op without a usable table, parse failure, etc.).
    Handles the percentage-scale ambiguity (program yields a ratio, gold answer is %).
    """
    exec_val = execute_program(gold_program, table)
    if exec_val is None:
        return None

    if isinstance(exec_val, str):                       # greater() -> yes/no
        return pred_answer.strip().lower().startswith(exec_val)

    pred = _to_number(pred_answer)
    if pred is None:
        return False

    candidates = [exec_val, exec_val * 100.0, exec_val / 100.0]  # ratio<->percent
    return any(abs(pred - c) <= tol for c in candidates)


def coverage_vector(records: list[dict], tol: float = 0.01
                    ) -> tuple[list[int], int]:
    """
    records: [{'pred': str, 'program': str, 'table': optional}, ...]
    Returns (per_example_0_1_over_checkable, n_uncheckable).
    Feed the 0/1 list straight into stats.bootstrap_ci for the Table cell + CI.
    """
    vec, uncheckable = [], 0
    for r in records:
        res = matches(r["pred"], r["program"], r.get("table"), tol)
        if res is None:
            uncheckable += 1
        else:
            vec.append(1 if res else 0)
    return vec, uncheckable
