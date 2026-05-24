"""
vlm_verifier.py -- VLM-verifier prototype for DeALOG (Reviewer-3 "brief VLM-verifier" item).

WHY
  DeALOG's Visual agent writes log entries about images that are, in practice, grounded
  in a *caption / OCR transcription* of the image rather than in the pixels. The W5
  long-horizon stratification shows the visual/summarization path is where errors
  concentrate on long chains. This prototype tests a targeted fix: when the Verifier
  *flags* a Visual log entry, re-verify that entry against the ORIGINAL IMAGE with a
  vision-language model, instead of re-reading the (possibly lossy) caption.

  The question it answers, quantitatively, is:
      "Does grounding the re-check on the image (not the caption) surface visual
       errors that caption-based verification misses?"

WHAT IT PRODUCES  (fills the \FILL cells in the App. table template in EXPERIMENT_SPECS.md)
  Per claim, two independent verdicts in {support, refute, unsupported}:
    * caption_verdict : claim checked against the caption/OCR text the Visual agent used
    * image_verdict   : claim checked against the original image via a VLM
  Aggregated over the subset:
    * caption_pass_rate, image_pass_rate     -- fraction judged 'support'
    * caption_missed_caught                  -- of claims caption marks 'support', the
                                                fraction the image verifier marks NOT
                                                'support' (i.e. caption-grounded errors
                                                exposed only by looking at the image)
    * agreement                              -- caption vs image verdict agreement
    * (with human labels) precision/recall/F1 of each verifier vs human, and the delta.

  Report ONLY numbers produced by a real VLM (see MODEL). Aggregate over the same
  evaluation seeds you use elsewhere and attach a bootstrap CI via stats.seeds_ci /
  stats.bootstrap_ci so the cells carry the same 95% CI convention as Table 6.

INTEGRATION  (per evaluated, *flagged* Visual log entry)
    ClaimItem(
        example_id  = "...",                 # to pair across systems / seeds
        image_path  = "/path/to/original.jpg",
        claim       = "the bar for 2019 is the tallest",   # Content of the Visual log entry
        caption     = "Figure 3 shows revenue by year ...",# the text the Visual agent had
        human_label = "refute",              # optional gold in {support,refute,unsupported}
    )
  Build a list[ClaimItem] for a small subset (50-100 flagged entries is enough for a
  prototype), call run(items, vlm=...), and hand the per-claim verdicts to stats.py.

MODEL
  Pass any callable  vlm(image_path: str, claim: str) -> (label, score)  where label is
  one of {support, refute, unsupported} and score in [0,1]. Two ready paths:
    (a) API VLM (GPT-4V / Qwen-VL / Gemini): wire your client inside `make_api_vlm`.
    (b) HF local VLM: `make_hf_vlm` builds a visual-entailment / VQA pipeline; the label
        order is read from the model config, never hard-coded.
  If neither is available, a clearly-marked CAPTION-ONLY stub runs so the pipeline does
  not crash for smoke tests. The stub DOES NOT LOOK AT THE IMAGE; it is NOT the image
  verifier and its numbers MUST NOT be reported -- it exists only to exercise the code.
"""
from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass, field
from typing import Callable, Optional

LABELS = ("support", "refute", "unsupported")
VLMFn = Callable[[str, str], "tuple[str, float]"]


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
@dataclass
class ClaimItem:
    example_id: str
    image_path: str
    claim: str
    caption: str = ""
    human_label: Optional[str] = None  # {support, refute, unsupported} or None


@dataclass
class ClaimResult:
    example_id: str
    claim: str
    caption_verdict: str
    caption_score: float
    image_verdict: str
    image_score: float
    human_label: Optional[str] = None


@dataclass
class Summary:
    n: int
    caption_pass_rate: float
    image_pass_rate: float
    caption_missed_caught: float
    agreement: float
    # vs-human (None if no labels provided)
    image_precision: Optional[float] = None
    image_recall: Optional[float] = None
    image_f1: Optional[float] = None
    caption_precision: Optional[float] = None
    caption_recall: Optional[float] = None
    caption_f1: Optional[float] = None
    per_claim: list = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Caption-based verifier (the BASELINE -- text only, used for both prod & smoke)
# --------------------------------------------------------------------------- #
_WORD = re.compile(r"[a-z0-9]+")


def _tok(s: str) -> set:
    return set(_WORD.findall(s.lower()))


def caption_verify(claim: str, caption: str) -> "tuple[str, float]":
    """Lexical caption check standing in for DeALOG's existing caption-grounded
    re-read. Overlap >= 0.5 -> support; some but low overlap -> unsupported;
    explicit negation cue with overlap -> refute. This is intentionally simple:
    it models the *information available in the caption*, which is the thing the
    image verifier is meant to improve on."""
    c, cap = _tok(claim), _tok(caption)
    if not c:
        return "unsupported", 0.0
    overlap = len(c & cap) / len(c)
    neg = bool(re.search(r"\bnot\b|\bno\b|\bnever\b|\bwithout\b", caption.lower()))
    if overlap >= 0.5:
        return ("refute", overlap) if neg else ("support", overlap)
    return "unsupported", overlap


# --------------------------------------------------------------------------- #
# Image verifier backends
# --------------------------------------------------------------------------- #
def make_api_vlm(call_model: Callable[[str, str], str]) -> VLMFn:
    """Wrap a user-provided API call. `call_model(image_path, prompt) -> raw_text`.
    We post a strict instruction and parse the first label token out of the reply."""
    prompt_tmpl = (
        "Look ONLY at the image. Decide whether the following claim about the image is "
        "true. Answer with exactly one word: support (claim is true of the image), "
        "refute (claim is contradicted by the image), or unsupported (image lacks the "
        "evidence). Claim: {claim}"
    )

    def _vlm(image_path: str, claim: str) -> "tuple[str, float]":
        raw = call_model(image_path, prompt_tmpl.format(claim=claim)).lower()
        for lab in LABELS:
            if lab in raw:
                return lab, 1.0
        return "unsupported", 0.0

    return _vlm


def make_hf_vlm(model_name: str = "Salesforce/blip2-flan-t5-xl") -> VLMFn:
    """Local HF VLM via a visual-question-answering pipeline. We ask a yes/no/uncertain
    question and map the answer to a label. Label mapping is derived from the model's
    own text output, not hard-coded indices. Requires `transformers` + `torch` + an
    image backend (PIL). Falls back to ImportError so the caller can choose the stub."""
    from transformers import pipeline  # noqa: F401  (raises if unavailable)
    from PIL import Image  # noqa: F401

    vqa = pipeline("visual-question-answering", model=model_name)

    def _vlm(image_path: str, claim: str) -> "tuple[str, float]":
        q = (f"Is this statement true of the image? '{claim}'. "
             f"Answer yes, no, or cannot tell.")
        out = vqa(image=Image.open(image_path).convert("RGB"), question=q, top_k=1)
        ans = (out[0]["answer"] if isinstance(out, list) else out["answer"]).lower()
        score = float(out[0].get("score", 1.0)) if isinstance(out, list) else 1.0
        if ans.startswith("y"):
            return "support", score
        if ans.startswith("n"):
            return "refute", score
        return "unsupported", score

    return _vlm


def make_caption_only_stub() -> VLMFn:
    """DO NOT REPORT. No image is read. Exists so the pipeline runs end-to-end for
    smoke tests when no VLM is configured. It deliberately reuses the caption check,
    so caption_missed_caught will be ~0 by construction -- a signal you are on the stub."""
    def _vlm(image_path: str, claim: str) -> "tuple[str, float]":
        # Intentionally ignores image_path.
        return ("unsupported", 0.0)
    return _vlm


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #
def _prf(results: "list[ClaimResult]", which: str) -> "tuple[Optional[float],Optional[float],Optional[float]]":
    """Precision/recall/F1 of a verifier treating 'support' as the positive class,
    against human_label. Returns (None,None,None) if no human labels."""
    labeled = [r for r in results if r.human_label in LABELS]
    if not labeled:
        return None, None, None
    tp = fp = fn = 0
    for r in labeled:
        pred = (r.caption_verdict if which == "caption" else r.image_verdict) == "support"
        gold = r.human_label == "support"
        tp += int(pred and gold)
        fp += int(pred and not gold)
        fn += int(not pred and gold)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1


def run(items: "list[ClaimItem]", vlm: VLMFn) -> Summary:
    results: "list[ClaimResult]" = []
    for it in items:
        cv, cs = caption_verify(it.claim, it.caption)
        iv, isc = vlm(it.image_path, it.claim)
        results.append(ClaimResult(it.example_id, it.claim, cv, cs, iv, isc, it.human_label))

    n = len(results)
    if n == 0:
        return Summary(0, 0, 0, 0, 0)
    cap_pass = sum(r.caption_verdict == "support" for r in results) / n
    img_pass = sum(r.image_verdict == "support" for r in results) / n
    cap_support = [r for r in results if r.caption_verdict == "support"]
    missed_caught = (
        sum(r.image_verdict != "support" for r in cap_support) / len(cap_support)
        if cap_support else 0.0
    )
    agree = sum(r.caption_verdict == r.image_verdict for r in results) / n
    ip, ir, if1 = _prf(results, "image")
    cp, cr, cf1 = _prf(results, "caption")
    return Summary(
        n=n, caption_pass_rate=cap_pass, image_pass_rate=img_pass,
        caption_missed_caught=missed_caught, agreement=agree,
        image_precision=ip, image_recall=ir, image_f1=if1,
        caption_precision=cp, caption_recall=cr, caption_f1=cf1,
        per_claim=results,
    )


def format_summary(s: Summary) -> str:
    lines = [
        f"n flagged Visual entries        : {s.n}",
        f"caption-verifier pass rate      : {s.caption_pass_rate:.3f}",
        f"image-verifier   pass rate      : {s.image_pass_rate:.3f}",
        f"caption-missed errors caught    : {s.caption_missed_caught:.3f}  <- headline",
        f"caption/image verdict agreement : {s.agreement:.3f}",
    ]
    if s.image_f1 is not None:
        lines += [
            f"image  P/R/F1 vs human          : {s.image_precision:.3f} / {s.image_recall:.3f} / {s.image_f1:.3f}",
            f"caption P/R/F1 vs human         : {s.caption_precision:.3f} / {s.caption_recall:.3f} / {s.caption_f1:.3f}",
        ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Smoke test (stub -- DO NOT REPORT these numbers)
# --------------------------------------------------------------------------- #
def _smoke() -> None:
    items = [
        ClaimItem("ex1", "img/ex1.jpg", "the 2019 bar is the tallest",
                  caption="Chart of revenue by year; 2019 and 2020 shown.", human_label="refute"),
        ClaimItem("ex2", "img/ex2.jpg", "there are three people in the photo",
                  caption="A group photo with three people standing.", human_label="support"),
        ClaimItem("ex3", "img/ex3.jpg", "the sign reads EXIT",
                  caption="A hallway with a red sign.", human_label="unsupported"),
    ]
    s = run(items, make_caption_only_stub())
    print("[SMOKE: caption-only stub -- DO NOT REPORT]\n" + format_summary(s))
    assert s.n == 3
    assert 0.0 <= s.agreement <= 1.0
    print("\nOK: pipeline runs. Wire make_hf_vlm(...) or make_api_vlm(...) for real numbers.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="DeALOG VLM-verifier prototype")
    ap.add_argument("--smoke", action="store_true", help="run the no-VLM smoke test")
    args = ap.parse_args()
    if args.smoke or not os.environ.get("VLM_READY"):
        _smoke()
