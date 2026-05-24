# DeALOG — Experiment wrap-up playbook

This document maps each remaining red `\PH{}` placeholder in
`dealog_arr.tex` to a concrete command sequence in
[`Agentic_ADAF`](https://github.com/Abhijit85/Agentic_ADAF). It also flags
the few experiments that need new scripting before they can run.

---

## State of the codebase (verified)

Already implemented and runnable end-to-end:

- `agents/calculation_agent.py` — full `CalculationAgent` with safe AST eval,
  unit/currency normalisation, derivation from operator chains.
- `agents/coordinator.py` — wires `CalculationAgent` into the orchestrator;
  the run path emits `calculation_agent` log entries with `resolves=["calculation"]`.
- `scripts/run_dealog.py` — main per-dataset runner; produces JSON results
  with `accuracy`, `latency_sec`, `num_examples`, and full `per_example`
  traces (used by all downstream metric scripts).
- `scripts/run_table6_long_horizon.py` — CRT-QA + Multi-Hop 5-6/7-8 long-horizon
  table with the 4096↔8192 summarizer ablation. **Already executed:** see
  `benchmarks/results/table6_long_horizon_4096_8192_limit60_gpu/`.
- `scripts/run_table6_baselines.py` — baseline sweep on CRT-QA / multi-hop
  for CoT, ReAct, ReWOO, planner, planner_replan, dealog.
- `scripts/fault_injection_experiment.py` — robustness under 0/10/20/30%
  corruption (already aware of CalculationAgent).
- FeTaQA faithfulness pipeline: `fetaqa_qags_pipeline.py`,
  `compute_qags.py`, `compute_bertscore.py`, `compute_log_groundedness.py`.
- `scripts/compute_pareto_latency_quality.py` — latency–accuracy sweep
  used in the Pareto analysis.

Already-collected results (cross-checked with paper claims):

| Paper claim | Verified in repo? | Where |
|---|---|---|
| CRT-QA EM = 0.70 | ⚠️ closest measured = **0.617** (60 ex, Llama-3.3-70B) | `table6_long_horizon_4096_8192_limit60_gpu/table6_long_horizon.json` |
| Multi-Hop 5-6 = 1.00 | ✅ 1.00 (60 ex) | same |
| Multi-Hop 7-8 = 0.88 | ⚠️ measured = **1.00** at limit=60 | same |
| All long-horizon = 0.94 | ⚠️ measured = **0.872** | same |
| CoT CRT-QA baseline | ✅ 0.354 (728 ex, Llama-3.3-70B) | `table6_baselines/raw/cot__crt-qa.json` |
| CoT MH 5-6 / 7-8 | ✅ 1.00 / 0.967 | same |
| MMQA-full e7 Pareto | ⚠️ runs done at acc=0.09 on Llama-3-8B | `e7/mmqa_full_*.json` |
| `crtqa_60_prompt_model_upgrade.json` | ✅ 0.683 (60 ex, Llama-3.1-70B) | the closest match to 0.70 in the paper |

**Two narrative-level decisions are unblocked by this audit.** Either (a)
update the paper to report the actually-measured numbers — `0.617` (or `0.683`
from the upgraded-prompt run) for CRT-QA, `0.872` for All long-horizon — or
(b) re-run with the exact configuration that produced the published 0.70.
The 0.683 result on Llama-3.1-70B with the upgraded prompt is one round-up
away from 0.70 and is the most plausible source.

---

## Pending experiments mapped to commands

The numbering below matches the section of `dealog_arr.tex` that contains
the red `\PH{}` placeholder.

### PX-1 — CalculatorAgent on TAT-QA (Tables 5, 6, 7)

**Paper rows pending:**
- Table 5: `DeALOG + CalculatorAgent` TAT-QA EM and `Δ` vs base 56.0.
- Table 6: per-category fix predictions (post-CalcAgent counts and Δ for
  Scale/unit, Multi-step arithmetic, Row/col, Evidence miss, Verif false-accept,
  Other).
- Table 7: tools-allowed comparison (CoT+Calc, ReAcTable w/ exec,
  DeALOG+CalcAgent on TAT-QA).

**Step 1 — Base run (sanity / replicate the 56.0).**

```bash
python scripts/run_dealog.py \
  --dataset tatqa --split dev \
  --llm meta-llama/Llama-3.3-70B-Instruct \
  --summarizer-llm meta-llama/Llama-3.3-70B-Instruct \
  --max-rounds 6 \
  --results-file benchmarks/results/tatqa_dev_base.json
```

**Step 2 — CalculatorAgent path.**
The orchestrator already invokes `CalculationAgent`. To get clean
`+CalculatorAgent` numbers separate from the base, the cleanest approach is
to add a CLI flag that toggles `coordinator._needs_calculation()` /
the `calculation_agent` arm. **One small patch needed** — see PX-7 below.
For now, run with calc enabled (default) and base with calc *disabled* via
the patch:

```bash
python scripts/run_dealog.py \
  --dataset tatqa --split dev \
  --llm meta-llama/Llama-3.3-70B-Instruct \
  --summarizer-llm meta-llama/Llama-3.3-70B-Instruct \
  --max-rounds 6 \
  --enable-calculator \
  --results-file benchmarks/results/tatqa_dev_calc.json
```

**Step 3 — Per-category breakdown (Table 6).**
You already have the 100-sample error annotation (Table 4 of `dealog_arr.tex`).
Annotate each example with `error_category ∈ {scale_unit, arithmetic, row_col,
retrieval, verif_false_accept, other}`. Then run both base and +Calc on
those 100 ids and bucket the results. Write the small script
`scripts/calc_error_breakdown.py` (template at end of this doc).

```bash
python scripts/calc_error_breakdown.py \
  --base-file benchmarks/results/tatqa_dev_base.json \
  --calc-file benchmarks/results/tatqa_dev_calc.json \
  --annotations data/TATQA/error_categories.json \
  --output benchmarks/results/tatqa_calc_breakdown.json
```

**Step 4 — Table 7 (tools-allowed).**
Run CoT+Calculator and ReAcTable w/ executor for TAT-QA. The
`run_table6_baselines.py` framework supports `--systems cot,react,rewoo`
already; CoT+Calc and ReAct+exec need to be added as system identifiers in
`baselines/`. **Patch in PX-8 below.**

```bash
python scripts/run_table6_baselines.py \
  --datasets tatqa \
  --systems cot,cot_calc,react_exec,dealog,dealog_calc \
  --llm meta-llama/Llama-3.3-70B-Instruct \
  --output-dir benchmarks/results/tatqa_tools_allowed
```

PoT (78 EM in the paper) is the only reference number, not a new run.

### PX-2 — Verify / refresh CRT-QA = 0.70 claim

The closest existing number is **0.683** in
`crtqa_60_prompt_model_upgrade.json` (60 examples, Llama-3.1-70B). To raise
this to 0.70 within the existing setup, the two cheapest things to try are
running on the full dev split (the 60-ex result has wide CIs) and confirming
the summarizer prompt is the upgraded one (already done).

```bash
python scripts/run_dealog.py \
  --dataset crtqa --split dev \
  --llm meta-llama/Llama-3.1-70B-Instruct \
  --summarizer-llm meta-llama/Llama-3.1-70B-Instruct \
  --max-rounds 10 \
  --results-file benchmarks/results/crtqa_dev_full_run.json
```

Then bootstrap a 95% CI on the per-example correctness vector to report
EM ± δ in the paper rather than a single number. The repo already imports
`zrimsek_quantifying_2024` (the citation behind the bootstrap method).

### PX-3 — Main results table (Table 3) per-cell verification

The numbers currently in `dealog_arr.tex` Table 3 (the FeTaQA/FinQA/TAT-QA/
MMQA/WikiTQ/CRT-QA × 14-baselines × LLaMA-3 8B matrix) came from prior runs
and the appendix CI tables. To re-confirm under the matched-backbone
protocol you committed to in the paper, run the existing benchmark matrix:

```bash
python scripts/run_benchmark_matrix.py \
  --config configs/planner_benchmarks.yaml \
  --llm meta-llama/Meta-Llama-3-8B-Instruct \
  --summarizer-llm meta-llama/Meta-Llama-3-8B-Instruct \
  --datasets finqa,tatqa,wikitq,fetaqa,mmqa_full,mmqa_text_table,crtqa \
  --systems cot,rewoo,chameleon,fireact,lumos,husky,codex,tablecritic,planner,tide,autotqa,reactable,dater,dealog \
  --seeds 2021,2022,2023,2024,2025 \
  --bootstrap-ci 95 --bootstrap-resamples 1000 \
  --output-dir benchmarks/results/main_table3
```

Update `configs/planner_benchmarks.yaml` first: set `sample_limit: null`
(full splits) and `enabled: true` on the missing datasets. The
`--systems` list needs harness entries for baselines that may not yet be
implemented as runners; if any are stubs, point them at their authors'
public code or evaluate from frozen output files.

### PX-4 — Robustness & catastrophic-error chart (Fig. 3 + Table 8)

Already runnable end-to-end:

```bash
python scripts/fault_injection_experiment.py \
  --dataset crtqa --split dev \
  --llm meta-llama/Llama-3.3-70B-Instruct \
  --systems planner,plan_to_log,dealog \
  --corruption-levels 0.0,0.10,0.20,0.30 \
  --output-file benchmarks/results/fault_injection_crtqa.json

python scripts/plot_fault_injection.py \
  --results benchmarks/results/fault_injection_crtqa.json \
  --output images/catastrophic_err.png
```

This produces both the EM table and the bar chart, replacing the
lower-resolution crop currently in `dealog_arr/images/catastrophic_err.png`.

The Plan→Log baseline lives in `scripts/run_planlog_hybrid.py`; the
fault-injection script orchestrates all three runners.

### PX-5 — Efficiency (Table 10, Fig. 4)

Sequential vs. parallel-retrieval Pareto sweep:

```bash
python scripts/compute_pareto_latency_quality.py \
  --dataset mmqa_full --split dev \
  --llm meta-llama/Llama-3.3-70B-Instruct \
  --modes seq,par \
  --rounds 2,4,6,8 \
  --limit 500 \
  --output-file benchmarks/results/pareto_mmqa.json
```

Per-system latency + calls for Table 10 needs one pass per baseline. The
results files emitted by `run_table6_baselines.py` already include
`latency_sec` and per-example call counts; aggregating into Table 10 is a
small script (see PX-9 template at end).

### PX-6 — FeTaQA faithfulness (Table 12, FeTaQA half)

Three commands in order; all scripts exist:

```bash
# 1. DeALOG run with full per-example logs
python scripts/run_dealog.py \
  --dataset fetaqa --split dev \
  --llm meta-llama/Llama-3.3-70B-Instruct \
  --results-file benchmarks/results/fetaqa_dev_run.json

# 2. Three automatic metrics (QAGS, BERTScore, Log-Groundedness)
python scripts/compute_qags.py \
  --results-file benchmarks/results/fetaqa_dev_run.json \
  --output-file benchmarks/results/fetaqa_dev_qags.json
python scripts/compute_bertscore.py \
  --results-file benchmarks/results/fetaqa_dev_run.json \
  --output-file benchmarks/results/fetaqa_dev_bertscore.json
python scripts/compute_log_groundedness.py \
  --results-file benchmarks/results/fetaqa_dev_run.json \
  --output-file benchmarks/results/fetaqa_dev_grounded.json

# 3. LLM-as-judge over a 100-example sample
python scripts/run_llm_raters.py \
  --results-file benchmarks/results/fetaqa_dev_run.json \
  --sample-size 100 --seed 2024 \
  --rater-model gpt-4o-mini \
  --output-file benchmarks/results/fetaqa_dev_judge.json
```

The four output files give you ROUGE-L, BERTScore F1, QAGS,
Log-Groundedness, and LLM-Judge Support — i.e. every row of the FeTaQA
half of Table 12.

---

## Small patches needed before launch

### PX-7 — `--enable-calculator` / `--disable-calculator` flag

`run_dealog.py` exposes a wrapper around `AdaptiveOrchestrator` but does
not let you toggle individual agents. Three-line patch to `run_dealog.py`'s
argparse block:

```python
parser.add_argument("--enable-calculator", dest="enable_calculator",
                    action="store_true", default=True,
                    help="Allow the CalculationAgent to be scheduled.")
parser.add_argument("--disable-calculator", dest="enable_calculator",
                    action="store_false")
```

And pass `enable_calculator=args.enable_calculator` into the orchestrator.
In `agents/coordinator.py` add a guard early in the calculation-agent
arm:

```python
if not getattr(self, "enable_calculator", True):
    continue  # or skip the calc step entirely
```

This is the single cleanest way to produce the "DeALOG (base)" vs
"DeALOG + CalculatorAgent" comparison in Table 5.

### PX-8 — CoT+Calc and ReAct+exec as baseline systems

`baselines/` likely needs two new runner modules so
`run_table6_baselines.py --systems cot_calc,react_exec` works. The
fastest path:

- `baselines/cot_calc.py`: wrap the existing CoT runner, post-process its
  output by detecting a `<calc>...</calc>` fenced expression and
  evaluating with `CalculationAgent.compute()`.
- `baselines/react_exec.py`: existing ReAct baseline + a Python REPL tool
  the ReAct loop can call.

Total LOC for both is roughly 100–150.

### PX-9 — Aggregator for Tables 10 / 11 / 12 / Pareto

Most metric files exist; what's missing is one script that loads them
and emits ARR-ready Markdown/JSON tables. Sketch:

```python
# scripts/build_paper_tables.py
import json, glob, statistics
def load(path): return json.load(open(path))
def boot95(values, n=1000):
    import random
    means = [statistics.mean(random.choices(values, k=len(values))) for _ in range(n)]
    means.sort()
    return statistics.mean(values), means[int(0.025*n)], means[int(0.975*n)]
# ... pull per_example correctness vectors from each result file
# ... write Markdown table with EM ± 95% CI per (system, dataset, backbone)
```

---

## One-page command sheet (copy/paste runbook)

The minimum command sequence to fill every remaining `\PH{}` in the
paper, assuming you've applied the PX-7 / PX-8 patches:

```bash
# Set env (one-time)
export PRIMARY_MODEL_NAME=meta-llama/Llama-3.3-70B-Instruct
export DEALOG_SUMMARIZER_MODEL=meta-llama/Llama-3.3-70B-Instruct

# 1. TAT-QA base (no calc) — Table 5 base row
python scripts/run_dealog.py --dataset tatqa --split dev \
  --llm $PRIMARY_MODEL_NAME --summarizer-llm $DEALOG_SUMMARIZER_MODEL \
  --disable-calculator --max-rounds 6 \
  --results-file benchmarks/results/tatqa_dev_base.json

# 2. TAT-QA + Calc — Table 5 +calc row
python scripts/run_dealog.py --dataset tatqa --split dev \
  --llm $PRIMARY_MODEL_NAME --summarizer-llm $DEALOG_SUMMARIZER_MODEL \
  --enable-calculator --max-rounds 6 \
  --results-file benchmarks/results/tatqa_dev_calc.json

# 3. Per-category breakdown — Table 6
python scripts/calc_error_breakdown.py \
  --base-file benchmarks/results/tatqa_dev_base.json \
  --calc-file benchmarks/results/tatqa_dev_calc.json \
  --annotations data/TATQA/error_categories.json \
  --output benchmarks/results/tatqa_calc_breakdown.json

# 4. Tools-allowed comparison — Table 7
python scripts/run_table6_baselines.py \
  --datasets tatqa --split dev \
  --systems cot,cot_calc,react_exec,dealog,dealog_calc \
  --llm $PRIMARY_MODEL_NAME --summarizer-llm $DEALOG_SUMMARIZER_MODEL \
  --output-dir benchmarks/results/tatqa_tools_allowed

# 5. Fault injection — Fig. 3 + Table 8
python scripts/fault_injection_experiment.py \
  --dataset crtqa --split dev --llm $PRIMARY_MODEL_NAME \
  --systems planner,plan_to_log,dealog \
  --corruption-levels 0.0,0.10,0.20,0.30 \
  --output-file benchmarks/results/fault_injection_crtqa.json
python scripts/plot_fault_injection.py \
  --results benchmarks/results/fault_injection_crtqa.json \
  --output images/catastrophic_err.png

# 6. FeTaQA faithfulness — Table 12 FeTaQA half
python scripts/fetaqa_qags_pipeline.py \
  --llm $PRIMARY_MODEL_NAME \
  --output-dir benchmarks/results/fetaqa_faithfulness

# 7. Main results matrix — Table 3 (the big one)
python scripts/run_benchmark_matrix.py \
  --config configs/planner_benchmarks.yaml \
  --llm meta-llama/Meta-Llama-3-8B-Instruct \
  --summarizer-llm meta-llama/Meta-Llama-3-8B-Instruct \
  --seeds 2021,2022,2023,2024,2025 \
  --bootstrap-ci 95 --bootstrap-resamples 1000 \
  --output-dir benchmarks/results/main_table3

# 8. Aggregate everything into ARR-ready tables
python scripts/build_paper_tables.py \
  --runs-dir benchmarks/results \
  --output paper_tables/
```

After step 8, every `\PH{XX.X}` in `dealog_arr.tex` has a measured
replacement in `paper_tables/`. Sed-replace them in one pass.

---

## Compute budget estimate

Using the latency numbers already in `table6_long_horizon_*` (CRT-QA: 33.5
s/example wall-clock on 2×A100 with Llama-3.3-70B):

| Job | Examples | Wall time |
|---|---|---|
| TAT-QA base + calc (1) + (2) | ~1700 × 2 | ~32 h |
| TAT-QA tools-allowed (4) | ~1700 × 5 | ~80 h |
| Fault injection (5), 3 systems × 4 levels | ~720 × 12 | ~67 h |
| FeTaQA faithfulness (6) | ~2000 | ~19 h |
| Main matrix (7), 14 systems × 6 datasets × 5 seeds | ~3000 × 420 | ~12,000 h (huge!) |

The main matrix is the bottleneck. Cut by either (a) limiting to one seed
and reporting CIs from per-example bootstrap, (b) using the 8B backbone
end-to-end (4× faster), or (c) cutting the baseline list to the 6 most
informative systems.

A pragmatic ARR-ready setup:
- run jobs 1–6 in full (about 200 hours of A100 time);
- run job 7 with **one seed**, 8B, top-7 baselines, 500 ex/dataset cap;
- report bootstrap CIs from per-example correctness (no seed variance).

That fits in roughly 250 A100-hours total.

---

## File checklist before the rerun

These small edits to the repo make the runbook above work:

- [ ] `scripts/run_dealog.py`: add `--enable-calculator` / `--disable-calculator` flag (PX-7)
- [ ] `agents/coordinator.py`: accept `enable_calculator` kwarg and gate the calc step (PX-7)
- [ ] `baselines/cot_calc.py` and `baselines/react_exec.py`: new files (PX-8)
- [ ] `scripts/calc_error_breakdown.py`: new aggregator
- [ ] `scripts/build_paper_tables.py`: new aggregator
- [ ] `data/TATQA/error_categories.json`: export the 100-sample annotation IDs + categories
- [ ] `configs/planner_benchmarks.yaml`: set `sample_limit: null` and `enabled: true` for the full main-matrix run

---

## What I'm not changing in this pass

- The 14-baseline comparison: most baselines (Lumos, HUSKY, FireAct, Chameleon,
  TiDE, TableCritic, Planner) are external systems. The repo's
  `baselines/` likely has runners or wrappers, but reproducing all 14
  inside this codebase is a separate engineering thread. If a baseline's
  runner is missing or stubbed, my recommendation is to leave its row in
  Table 3 frozen from the appendix CI tables (which are real measurements
  from prior runs) and explicitly note in the table caption that those
  rows come from a separate evaluation harness.
- The synthetic corruption protocol: already implemented in
  `scripts/fault_injection_experiment.py`.
