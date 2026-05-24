"""
nli_grounding.py -- semantic (entailment-based) log-groundedness for DeALOG (W3).

WHY
  The reported log-groundedness (0.72) is LEXICAL: an answer token counts as grounded
  only if it appears verbatim in a log entry, so faithful paraphrase is scored as
  ungrounded. This module adds a SEMANTIC complement: an answer claim is grounded if
  some log entry *entails* it under an NLI model. Reporting both bounds faithfulness
  from two sides (lexical = conservative floor, entailment = paraphrase-aware).

WHAT IT PRODUCES (fills the \FILL cells in the faithfulness table, App. F.10):
  * nli_groundedness  : fraction of answer CLAIMS entailed by >=1 log entry  (per example, then averaged)
  * answer_supported  : per-answer flag = all claims entailed (for an answer-level support rate)

INTEGRATION
  Provide, per evaluated example:
    answer_text : str           -- DeALOG's final answer / summary text
    log_entries : list[str]     -- the Content fields of the shared-log entries for that example
  Then call score_example(...) and aggregate with stats.seeds_ci over your 5 seeds.

MODEL
  Default: a HF cross-encoder NLI head (DeBERTa-MNLI). Label order is read from the
  model config (do not hard-code) because MNLI checkpoints differ in index order.
  If transformers is unavailable, a clearly-marked lexical-overlap fallback runs so the
  pipeline does not crash -- but the fallback is NOT a semantic metric; only report
  numbers produced by the real NLI model in the paper.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Callable, Optional

DEFAULT_MODEL = "microsoft/deberta-large-mnli"
ENTAIL_THRESHOLD = 0.5   # P(entailment) above which a (premise, claim) pair counts as support


# --------------------------------------------------------------------------- #
# Claim segmentation
# --------------------------------------------------------------------------- #
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")

def split_claims(answer_text: str) -> list[str]:
    """Conservative claim segmentation: sentence-level, dropping empties.
    For short extractive answers this yields a single claim, which is correct."""
    parts = [s.strip() for s in _SENT_SPLIT.split(answer_text.strip()) if s.strip()]
    return parts or ([answer_text.strip()] if answer_text.strip() else [])


# --------------------------------------------------------------------------- #
# NLI backend
# --------------------------------------------------------------------------- #
class NLIModel:
    """Thin wrapper around a HF sequence-classification NLI model.

    entail_prob(premise, hypothesis) -> float in [0,1]
    Reads the entailment index from model.config.label2id so it is robust to
    checkpoints that order labels differently (a common, silent source of bugs).
    """
    def __init__(self, model_name: str = DEFAULT_MODEL, device: Optional[str] = None,
                 batch_size: int = 16):
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device).eval()
        self.batch_size = batch_size
        # Resolve the entailment logit index from the config, regardless of order.
        label2id = {k.lower(): v for k, v in (self.model.config.label2id or {}).items()}
        self.entail_idx = label2id.get("entailment",
                          label2id.get("entail", max(label2id.values()) if label2id else 2))

    def entail_probs(self, pairs: list[tuple[str, str]]) -> list[float]:
        """Batched P(entailment) for (premise, hypothesis) pairs."""
        torch = self.torch
        out: list[float] = []
        for i in range(0, len(pairs), self.batch_size):
            chunk = pairs[i:i + self.batch_size]
            enc = self.tok([p for p, _ in chunk], [h for _, h in chunk],
                           return_tensors="pt", truncation=True, padding=True,
                           max_length=256).to(self.device)
            with torch.no_grad():
                logits = self.model(**enc).logits
                probs = torch.softmax(logits, dim=-1)[:, self.entail_idx]
            out.extend(probs.detach().cpu().tolist())
        return out


# --------------------------------------------------------------------------- #
# Fallback (NOT semantic -- pipeline safety only; do not report)
# --------------------------------------------------------------------------- #
def _lexical_fallback_prob(premise: str, hypothesis: str) -> float:
    pt, ht = set(premise.lower().split()), set(hypothesis.lower().split())
    if not ht:
        return 0.0
    return len(pt & ht) / len(ht)


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #
@dataclass
class ExampleGrounding:
    n_claims: int
    n_entailed: int
    answer_supported: bool          # all claims entailed by some log entry
    @property
    def fraction(self) -> float:
        return self.n_entailed / self.n_claims if self.n_claims else 0.0

def score_example(answer_text: str, log_entries: list[str],
                  nli: Optional[NLIModel] = None,
                  entail_threshold: float = ENTAIL_THRESHOLD,
                  prob_fn: Optional[Callable[[str, str], float]] = None
                  ) -> ExampleGrounding:
    """A claim is grounded if MAX over log entries of P(entail | entry -> claim) >= threshold."""
    claims = split_claims(answer_text)
    entries = [e for e in log_entries if e and e.strip()]
    if not claims or not entries:
        return ExampleGrounding(len(claims), 0, False)

    if nli is not None:
        pairs = [(entry, claim) for claim in claims for entry in entries]
        flat = nli.entail_probs(pairs)
        per_claim_max, k = [], 0
        for _ in claims:
            seg = flat[k:k + len(entries)]; k += len(entries)
            per_claim_max.append(max(seg) if seg else 0.0)
    else:
        f = prob_fn or _lexical_fallback_prob
        per_claim_max = [max(f(entry, claim) for entry in entries) for claim in claims]

    flags = [p >= entail_threshold for p in per_claim_max]
    return ExampleGrounding(len(claims), sum(flags), all(flags))


def corpus_groundedness(examples: list[tuple[str, list[str]]],
                        nli: Optional[NLIModel] = None,
                        entail_threshold: float = ENTAIL_THRESHOLD
                        ) -> dict:
    """examples = [(answer_text, [log_entry, ...]), ...] for ONE seed.
    Returns claim-level NLI-groundedness and answer-level support rate for that seed."""
    per = [score_example(a, logs, nli, entail_threshold) for a, logs in examples]
    claims = sum(g.n_claims for g in per)
    entailed = sum(g.n_entailed for g in per)
    supported = sum(g.answer_supported for g in per)
    return {
        "nli_groundedness": entailed / claims if claims else 0.0,   # claim-level
        "answer_support_rate": supported / len(per) if per else 0.0,
        "n_examples": len(per),
        "backend": "nli" if nli is not None else "lexical-fallback(DO-NOT-REPORT)",
    }


if __name__ == "__main__":
    # Self-test with the fallback (no model download); proves wiring, not the metric.
    demo = [
        ("Revenue rose to $1.9B in 2021.",
         ["TableAgent: 2021 revenue cell = $1,910M.", "ContextAgent: revenue increased year over year."]),
        ("The margin fell.",
         ["TableAgent: 2020 margin 21%, 2021 margin 23%."]),  # contradicts -> low entail
    ]
    print(corpus_groundedness(demo, nli=None))
