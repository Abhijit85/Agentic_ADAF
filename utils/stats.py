"""
stats.py -- bootstrap confidence intervals for the DeALOG \\FILL cells.

Three things you need:
  1) bootstrap_ci(values)            -> per-cell mean + 95% CI (the +/- bands)
  2) seeds_ci(per_seed_values)       -> aggregate the 5 seeds into one mean + CI
  3) paired_bootstrap_diff(a, b)     -> is DeALOG's lead over a comparator real?

All resampling is at the EXAMPLE level. For paired tests the SAME resampled indices
are applied to both systems, which is only valid because perturbations.py guarantees
both systems were scored on identical corrupted inputs (same seed -> same corruption).

`values` are per-example scores: 0/1 for EM, or continuous in [0,1] for F1,
log-groundedness, QAGS, judge support rate, FinQA program coverage, etc.
"""

from __future__ import annotations

import numpy as np


def bootstrap_ci(values, n_boot: int = 1000, alpha: float = 0.05, seed: int = 0):
    """
    Percentile bootstrap over examples (matches the paper's 1,000-resample protocol).
    Returns dict(mean, lo, hi, halfwidth, n).
    """
    x = np.asarray(values, dtype=float)
    n = len(x)
    if n == 0:
        return {
            "mean": float("nan"),
            "lo": float("nan"),
            "hi": float("nan"),
            "halfwidth": float("nan"),
            "n": 0,
        }
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    boots = x[idx].mean(axis=1)
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    mean = float(x.mean())
    return {
        "mean": mean,
        "lo": float(lo),
        "hi": float(hi),
        "halfwidth": float((hi - lo) / 2),
        "n": n,
    }


def seeds_ci(per_seed_values, n_boot: int = 1000, alpha: float = 0.05, seed: int = 0):
    """
    Aggregate the 5 seeds for the faithfulness table ("mean over 5 seeds, 95% CI").
    `per_seed_values`: list of arrays, one per seed (same examples, same order).

    Reports the across-seed mean and a CI that captures BOTH example and seed
    variation by pooling all seed x example scores and bootstrapping examples
    (block-resampled so a drawn example contributes all its seeds together).
    """
    mats = [np.asarray(values, dtype=float) for values in per_seed_values]
    seed_count = len(mats)
    n = len(mats[0])
    assert all(len(values) == n for values in mats), "all seeds must score the same examples"
    matrix = np.stack(mats, axis=1)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    boots = matrix[idx].mean(axis=(1, 2))
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    mean = float(matrix.mean())
    per_seed_means = [float(values.mean()) for values in mats]
    return {
        "mean": mean,
        "lo": float(lo),
        "hi": float(hi),
        "halfwidth": float((hi - lo) / 2),
        "n": n,
        "n_seeds": seed_count,
        "per_seed_means": per_seed_means,
    }


def paired_bootstrap_diff(a, b, n_boot: int = 10000, alpha: float = 0.05, seed: int = 0):
    """
    Paired bootstrap of mean(a) - mean(b) on identical examples.
    Use for "DeALOG beats <comparator> under corruption" / per-column-best claims.

    Returns dict(diff, lo, hi, p_two_sided, significant).
    `significant` is True iff the (1-alpha) interval excludes 0 -> bold the lead;
    otherwise describe the two systems as statistically indistinguishable.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    assert len(a) == len(b), "paired test needs aligned per-example scores"
    n = len(a)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    diffs = a[idx].mean(axis=1) - b[idx].mean(axis=1)
    lo, hi = np.percentile(diffs, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    diff = float(a.mean() - b.mean())
    p = 2 * min((diffs <= 0).mean(), (diffs >= 0).mean())
    return {
        "diff": diff,
        "lo": float(lo),
        "hi": float(hi),
        "p_two_sided": float(min(p, 1.0)),
        "significant": bool(lo > 0 or hi < 0),
    }


def fmt_pm(ci: dict, scale: float = 100.0, decimals: int = 1) -> str:
    """
    Render a bootstrap_ci result in the paper's subscript style, e.g. '76.7_{\\pm1.0}'.
    scale=100 turns a [0,1] mean into a percentage; use scale=1 to keep raw.
    """
    mean = ci["mean"] * scale
    halfwidth = ci["halfwidth"] * scale
    return f"{mean:.{decimals}f}$_{{\\pm{halfwidth:.{decimals}f}}}$"


if __name__ == "__main__":
    import random

    rng = random.Random(0)
    em_dealog = [1 if rng.random() < 0.73 else 0 for _ in range(2441)]
    em_planner = [1 if rng.random() < 0.55 else 0 for _ in range(2441)]
    ci = bootstrap_ci(em_dealog, seed=1)
    print("DeALOG 30% EM:", fmt_pm(ci))
    print("paired vs Planner:", paired_bootstrap_diff(em_dealog, em_planner, seed=1))
