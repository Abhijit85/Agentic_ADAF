# Revision tables: execution status and next steps

This note maps the new rebuttal/revision tables in
[dealog_revision_tables.tex](/mnt/data1/achakr40/Agentic_ADAF/dealog_revision_tables.tex)
onto the current `Agentic_ADAF` codebase.

The main paper `.tex` source is not present in this workspace, so the table file
is standalone by design.

## Status at a glance

`Exp 1` dynamic-order ablation: not implemented in current code.

`Exp 2a` active-repair ablation: partially analogous machinery exists, but the
requested table is not directly measurable yet.

`Exp 2b` VLM re-verifier integration: prototype exists, not wired into the main
orchestrator.

`Exp 3` CRT-QA long-horizon stratification: closest to runnable now; it mostly
needs a stratification script over existing runners/results.

`Exp 4` hard semantic corruption: mostly supported by the revision harness, but
the specific corruption families in the table need to be added explicitly.

`Headline robustness` summary: fill from existing measured results plus one
lookup for the HuggingGPT row.

## What already exists

Relevant code already in repo:

- [scripts/run_revision_pack_experiments.py](/mnt/data1/achakr40/Agentic_ADAF/scripts/run_revision_pack_experiments.py:1)
  has a paired-seed robustness harness for `planner`, `planlog`, `autotqa`,
  `rewoo`, and `dealog`.
- [utils/perturbations.py](/mnt/data1/achakr40/Agentic_ADAF/utils/perturbations.py:1)
  plus [dealog_experiments/perturbations.py](/mnt/data1/achakr40/Agentic_ADAF/dealog_experiments/perturbations.py:1)
  already support structural and semantic corruption families.
- [scripts/fault_injection_experiment.py](/mnt/data1/achakr40/Agentic_ADAF/scripts/fault_injection_experiment.py:1)
  already records `flagged`, one re-engagement pass, `repaired`, and final
  accuracy under corruption, but it is a coarse global re-run rather than the
  targeted repair ablation your table asks for.
- [utils/vlm_verifier.py](/mnt/data1/achakr40/Agentic_ADAF/utils/vlm_verifier.py:1)
  is already a reviewer-facing prototype for caption-vs-image re-verification
  on flagged visual entries.
- [scripts/run_table6_long_horizon.py](/mnt/data1/achakr40/Agentic_ADAF/scripts/run_table6_long_horizon.py:1)
  and [scripts/run_table6_baselines.py](/mnt/data1/achakr40/Agentic_ADAF/scripts/run_table6_baselines.py:1)
  already cover CRT-QA, Planner-style baselines, and DeALOG.

## Per-table assessment

### Exp 1: Dynamic-order ablation

Current blocker:

- The orchestrator can choose actions dynamically in LLM-control mode, but the
  requested experiment is a deterministic keyword router with explicit
  content-based skipping and a measured `Skip-err %`.
- The repo does not currently log whether an agent was skipped despite holding
  gold evidence.

Minimum code needed:

1. Add a `controller_mode="rule"` path in
   [agents/coordinator.py](/mnt/data1/achakr40/Agentic_ADAF/agents/coordinator.py:1)
   that uses question keywords to decide which agents to skip.
2. Define gold-evidence ownership for MMQA examples so `Skip-err %` is
   measurable.
3. Emit per-example fields like `skipped_agents`, `gold_agents`,
   `skip_error`.

Recommendation:

- Do this only if the reviewer pressure is strong. This is new instrumentation,
  not a small fill-in run.

### Exp 2a: Active-repair ablation

Current blocker:

- The requested protocol needs targeted repair from the flagged upstream agent,
  then fallback only if the repair still flags.
- The current verifier only returns a boolean, and the current fault-injection
  script performs a full second pass with corruption disabled instead of a
  local targeted re-run.
- The repo already documents this logging gap:
  [scripts/run_revision_pack_experiments.py](/mnt/data1/achakr40/Agentic_ADAF/scripts/run_revision_pack_experiments.py:317)
  explicitly says fallback breakdown is not yet runnable because verification
  logs do not include `flagged_item_id` or `fallback_answer`.

Minimum code needed:

1. Extend verifier/coordinator outputs with `flagged_item_id`,
   `pre_flag_answer`, `fallback_answer`, and `final_answer_source`.
2. Add one-step targeted repair hooks per agent.
3. Record `repair_attempted`, `repair_fixed_wrong`, and
   `repair_harmed_correct`.

Recommendation:

- If you only need the argument, a narrower and cheaper table based on the
  existing `fault_injection_experiment.py` is possible, but it would not match
  the exact draft table semantics.

### Exp 2b: VLM re-verifier integrated

Current blocker:

- The VLM verifier exists as a prototype but is not integrated into the main
  `AdaptiveOrchestrator` flow.
- The current `VerificationAgent` is answer-level only and has no path for
  flagged visual log entries.

Minimum code needed:

1. Wire flagged visual entries from the shared log into the VLM verifier.
2. Add an MMQA image-subset selector.
3. Measure visual/OCR detection rate, MMQA-image EM, MMQA-full EM, and added
   latency.

Recommendation:

- This is a good targeted revision experiment if you want one concrete
  multimodal fix. The prototype already reduces implementation risk.

### Exp 3: CRT-QA long-horizon stratification

This is the cheapest new table.

Why:

- CRT-QA is already loaded with `reasoning_steps` in
  [utils/data_loader.py](/mnt/data1/achakr40/Agentic_ADAF/utils/data_loader.py:88).
- The existing long-horizon runner already executes DeALOG by dataset/split.
- Baseline runners for planner-style systems already exist.

What is missing:

1. A bucket function over CRT-QA `reasoning_steps` or your existing
   operator-count definition.
2. A script that runs or aggregates `planner`, `planlog`, and `dealog` by
   bucket and reports `n`.
3. Optional paired bootstrap row-wise significance marking.

Recommendation:

- Prioritize this one first. It directly addresses the small-`n` complaint and
  reuses the most existing infrastructure.

### Exp 4: Hard semantic corruption

Current status:

- The revision harness already supports `family=semantic` corruption with
  shared seeds:
  [scripts/run_revision_pack_experiments.py](/mnt/data1/achakr40/Agentic_ADAF/scripts/run_revision_pack_experiments.py:264).
- What is missing is not the harness, but the exact corruption operators in the
  table: `conflicting sources`, `stale info`, and `misleading-but-true`.

Minimum code needed:

1. Add those three semantic perturbation modes in
   `utils/perturbations.py` or `dealog_experiments/perturbations.py`.
2. Expose them as selectable corruption families or subtypes.
3. Reuse the existing paired robustness runner on MMQA dev at `rate=0.20`.

Recommendation:

- This is more practical than Exp 1 or Exp 2a because the statistical harness
  is already in place.

### Headline robustness summary

This table should not trigger new experiments in this repo.

Rows already described in your note:

- Planner (single-call): `24.7`
- Planner++: `15.8`
- AutoTQA: `21.4`
- REWoO: `21.1`
- `\method`: `6.4`

Remaining lookup:

- `HuggingGPT` should be copied from the paper’s HybridQA/Table 28 source,
  which is not present in this workspace.

## Suggested execution order

If the goal is to maximize reviewer impact per unit time:

1. Run `Exp 3` first.
2. Run `Exp 4` second.
3. Decide whether `Exp 2b` is worth the integration effort.
4. Treat `Exp 1` and `Exp 2a` as optional unless the rebuttal explicitly
   hinges on them.

## If you want me to continue

The highest-leverage next implementation in this repo is:

- add a CRT-QA stratification script for `2-3 / 4-5 / 6-7 / 8+` buckets, or
- add the three hard semantic corruption operators to the existing revision
  harness.

Those are both materially cheaper than implementing dynamic skip-error logging
or targeted active repair from scratch.
