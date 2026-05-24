# DeALOG — Experiment Specs for the Revision-Pack `\FILL` Cells

These four modules generate the numbers behind every red `\FILL` in
`dealog_revision_pack.tex`. Nothing here invents data — they produce measurements you
run on your own pipeline.

```
dealog_experiments/
  perturbations.py   # corruption: structural + semantic, paired-across-systems seeding
  finqa_program.py   # FinQA program-execution faithfulness check
  stats.py           # bootstrap CIs, multi-seed aggregation, paired bootstrap, formatter
  EXPERIMENT_SPECS.md
```

## 0. The one invariant that makes the comparisons valid

Seeds: `{2021, 2022, 2023, 2024, 2025}` (your existing five).

Corruption is keyed by `(global_seed, example_id)` only — never by the system. So for a
given seed, Planner / Plan→Log / AutoTQA / REWoO / DeALOG are scored on **byte-identical
corrupted inputs**. That is the precondition for the paired bootstrap in `stats.py`; if
you ever corrupt per-system, the paired test is invalid and you must use the unpaired CI.

The only pipeline-specific code you write is two adapters and two run hooks:

```python
# 1) map a dataset example to corruptible evidence (perturbations.example_to_items stub)
items = example_to_items(example)

# 2) run any system on (possibly corrupted) evidence -> answer string
def run_system(name: str, example: dict, items: list[EvidenceItem]) -> str: ...
#    name in {"planner","planlog","autotqa","rewoo","dealog"}
```

## 1. Robustness table — `tab:robustness_em`

Fills: REWoO column, the semantic-noise panel, the TAT-QA panel, and every CI subscript.

## 2. Faithfulness CIs + second judge — `tab:fetaqa`

Fills: CI subscripts on QAGS / weighted-QAGS / log-groundedness / judge-A, and the judge-B row.

## 3. FinQA program coverage — `tab:finqa_prog`

Fills: the coverage value + CI.

## 4. Verifier fallback breakdown — `tab:fallback_breakdown`

Fills: preserved-correct / wrong-recoverable / wrong-unrecoverable, per corruption rate.
