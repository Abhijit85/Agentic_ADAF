"""
perturbations.py — evidence corruption for the DeALOG robustness study.

Produces the corrupted inputs behind Table~\ref{tab:robustness_em}:
  * structural/numeric noise  (numeric perturb | row swap | deletion)
  * semantic noise            (paraphrase substitution | entity swap)

KEY INVARIANT (paired comparison):
  Which items are corrupted, with which operation, and to which value is decided
  ONLY by (global_seed, example_id) — never by the system under test. So Planner,
  Plan->Log, AutoTQA, REWoO, and DeALOG all see byte-identical corrupted inputs
  for a given seed. That is what makes the per-row paired bootstrap in stats.py valid.

INTEGRATION (the only thing you adapt):
  Load each example's evidence into a list[EvidenceItem] via your own adapter
  (see `example_to_items` stub at the bottom), then call `corrupt_example(...)`.
  For semantic noise you pass an `llm(prompt:str)->str` callable bound to your backbone.
"""

from __future__ import annotations
import re
import json
import hashlib
import random
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Callable, Optional

# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class EvidenceItem:
    id: str                       # stable per-example id, e.g. "cell:2:3" or "span:0"
    kind: str                     # "cell" | "text"
    text: str                     # surface string the agent reads
    value: Optional[float] = None # numeric value if this is a numeric cell
    table_id: Optional[str] = None
    row: Optional[int] = None
    col: Optional[int] = None
    meta: dict = field(default_factory=dict)


@dataclass
class Change:
    item_id: str
    op: str
    before: str
    after: str


# --------------------------------------------------------------------------- #
# Deterministic, system-agnostic RNG
# --------------------------------------------------------------------------- #
def make_rng(global_seed: int, example_id: str) -> random.Random:
    """Stable across processes/runs (unlike builtin hash()), keyed by seed+example."""
    h = hashlib.sha1(f"{global_seed}:{example_id}".encode()).digest()
    return random.Random(int.from_bytes(h[:8], "big"))


# --------------------------------------------------------------------------- #
# Number helpers
# --------------------------------------------------------------------------- #
_NUM_RE = re.compile(r"-?\$?\d[\d,]*\.?\d*%?")

def _parse_num(s: str) -> Optional[float]:
    s = s.strip().replace(",", "").replace("$", "").replace("%", "")
    try:
        return float(s)
    except ValueError:
        return None

def _fmt_like(original: str, new_val: float) -> str:
    """Re-render new_val with the original token's $/,/% decoration and decimals."""
    dollar = original.strip().startswith("$")
    percent = original.strip().endswith("%")
    dec = len(original.split(".")[1].rstrip("%")) if "." in original else 0
    body = f"{new_val:,.{dec}f}" if "," in original else f"{new_val:.{dec}f}"
    return f"{'$' if dollar else ''}{body}{'%' if percent else ''}"


# --------------------------------------------------------------------------- #
# Structural / numeric operations
# --------------------------------------------------------------------------- #
def numeric_perturb(item: EvidenceItem, rng: random.Random, band: float = 0.10) -> tuple[EvidenceItem, Change]:
    """Replace the (first) number with a draw from a +/- `band` relative window."""
    if item.value is not None:
        factor = 1.0 + rng.uniform(-band, band)
        new_val = item.value * factor
        new_item = replace(item, value=new_val, text=_fmt_like(item.text, new_val))
        return new_item, Change(item.id, "numeric_perturb", item.text, new_item.text)
    m = _NUM_RE.search(item.text)
    if not m:
        return item, Change(item.id, "numeric_perturb_noop", item.text, item.text)
    val = _parse_num(m.group())
    if val is None:
        return item, Change(item.id, "numeric_perturb_noop", item.text, item.text)
    new_tok = _fmt_like(m.group(), val * (1.0 + rng.uniform(-band, band)))
    new_text = item.text[:m.start()] + new_tok + item.text[m.end():]
    return replace(item, text=new_text), Change(item.id, "numeric_perturb", item.text, new_text)


def row_swap(items: list[EvidenceItem], rng: random.Random) -> list[Change]:
    """Swap the *contents* of two random rows within the same table (mutates `items`)."""
    by_table: dict = {}
    for it in items:
        if it.kind == "cell" and it.table_id is not None and it.row is not None:
            by_table.setdefault(it.table_id, {}).setdefault(it.row, []).append(it)
    swappable = [(t, list(rows)) for t, rows in by_table.items() if len(rows) >= 2]
    if not swappable:
        return []
    t, rows = rng.choice(swappable)
    r1, r2 = rng.sample(rows, 2)
    a = {it.col: it for it in by_table[t][r1]}
    b = {it.col: it for it in by_table[t][r2]}
    changes = []
    for col in set(a) | set(b):
        ia, ib = a.get(col), b.get(col)
        if ia is not None and ib is not None:
            changes.append(Change(ia.id, "row_swap", ia.text, ib.text))
            ia.text, ib.text = ib.text, ia.text
            ia.value, ib.value = ib.value, ia.value
    return changes


def delete_item(item: EvidenceItem) -> tuple[EvidenceItem, Change]:
    return replace(item, text="", value=None), Change(item.id, "deletion", item.text, "")


# --------------------------------------------------------------------------- #
# Semantic operations
# --------------------------------------------------------------------------- #
# Light typed-entity extraction. Swap in spaCy NER here if you prefer richer types.
_ENTITY_RES = {
    "PERCENT": re.compile(r"-?\d[\d,]*\.?\d*\s?%"),
    "MONEY":   re.compile(r"\$\s?\d[\d,]*\.?\d*"),
    "YEAR":    re.compile(r"\b(?:19|20)\d{2}\b"),
    "NUMBER":  re.compile(r"\b-?\d[\d,]*\.?\d*\b"),
    "PROPN":   re.compile(r"\b(?:[A-Z][a-z]+)(?:\s+[A-Z][a-z]+){0,3}\b"),
}
_ENTITY_ORDER = ["PERCENT", "MONEY", "YEAR", "PROPN", "NUMBER"]  # specific -> generic

def extract_typed_entities(text: str) -> list[tuple[str, str]]:
    spans, taken = [], []
    for etype in _ENTITY_ORDER:
        for m in _ENTITY_RES[etype].finditer(text):
            if any(not (m.end() <= s or m.start() >= e) for s, e in taken):
                continue
            taken.append((m.start(), m.end()))
            spans.append((etype, m.group()))
    return spans

def build_entity_pools(items: list[EvidenceItem]) -> dict[str, list[str]]:
    pools: dict[str, set] = {}
    for it in items:
        for etype, surface in extract_typed_entities(it.text):
            pools.setdefault(etype, set()).add(surface)
    return {k: sorted(v) for k, v in pools.items()}

def entity_swap(item: EvidenceItem, rng: random.Random, pools: dict[str, list[str]]
                ) -> tuple[EvidenceItem, Change]:
    """Replace one typed entity with a same-type distractor drawn from the example."""
    ents = extract_typed_entities(item.text)
    rng.shuffle(ents)
    for etype, surface in ents:
        cands = [c for c in pools.get(etype, []) if c != surface]
        if cands:
            distractor = rng.choice(cands)
            new_text = item.text.replace(surface, distractor, 1)
            return replace(item, text=new_text, value=None), \
                   Change(item.id, "entity_swap", item.text, new_text)
    # No same-type distractor available -> fall back to numeric perturb (recorded).
    return numeric_perturb(item, rng)


PARAPHRASE_PROMPT = (
    "Rewrite the passage below so it stays fluent and natural but CHANGES one factual "
    "detail (a number, name, date, or relationship) so the meaning is subtly different. "
    "Keep the length and style similar. Output only the rewritten passage.\n\n"
    "Passage: {span}\nRewritten:"
)

def paraphrase_substitute(item: EvidenceItem, rng: random.Random,
                          llm: Callable[[str], str],
                          cache: Optional[dict] = None,
                          cache_key: str = "") -> tuple[EvidenceItem, Change]:
    """Content-altering paraphrase. Cached by key so reruns are deterministic."""
    if cache is not None and cache_key in cache:
        new_text = cache[cache_key]
    else:
        new_text = llm(PARAPHRASE_PROMPT.format(span=item.text)).strip()
        if cache is not None:
            cache[cache_key] = new_text
    return replace(item, text=new_text, value=None), \
           Change(item.id, "paraphrase", item.text, new_text)


# --------------------------------------------------------------------------- #
# Realistic noise (W1): drawn from observed upstream-error modes.
#   ocr_confusion  -- glyph substitutions typical of OCR on scanned tables
#   header_drift   -- column-header labels shift by one position (misalignment)
#   table_crop     -- a contiguous band of rows is lost (cropped scan/screenshot)
# Each op tags Change.op with its name so results can be reported PER ERROR TYPE
# (run one op in isolation via `ops_override` in corrupt_example; see spec).
# --------------------------------------------------------------------------- #
_OCR_MAP = {
    "0": "O", "O": "0", "1": "l", "l": "1", "I": "1", "5": "S", "S": "5",
    "8": "B", "B": "8", "6": "G", "G": "6", "2": "Z", "Z": "2", "9": "g",
}
_OCR_DIGRAPHS = (("rn", "m"), ("cl", "d"), ("vv", "w"), ("m", "rn"))

def ocr_confusion(item: EvidenceItem, rng: random.Random, rate: float = 0.15
                  ) -> tuple[EvidenceItem, Change]:
    """Apply OCR-style glyph substitutions to ~`rate` of characters."""
    s = item.text
    if not s:
        return item, Change(item.id, "ocr_confusion_noop", s, s)
    out = s
    for src, dst in _OCR_DIGRAPHS:
        if src in out and rng.random() < rate * 2:
            out = out.replace(src, dst, 1)
            break
    chars = list(out)
    for i, ch in enumerate(chars):
        if ch in _OCR_MAP and rng.random() < rate:
            chars[i] = _OCR_MAP[ch]
    new_text = "".join(chars)
    return replace(item, text=new_text, value=_parse_num(new_text)), \
           Change(item.id, "ocr_confusion", s, new_text)

def header_drift(items: list[EvidenceItem], rng: random.Random) -> list[Change]:
    """Cyclically shift header-row (row==0) cell texts by one column (mutates items)."""
    headers = sorted([it for it in items if it.kind == "cell" and it.row == 0
                      and it.col is not None], key=lambda it: it.col)
    if len(headers) < 2:
        return []
    texts = [it.text for it in headers]
    shift = 1 if rng.random() < 0.5 else -1
    shifted = texts[-1:] + texts[:-1] if shift > 0 else texts[1:] + texts[:1]
    changes = []
    for it, new in zip(headers, shifted):
        if it.text != new:
            changes.append(Change(it.id, "header_drift", it.text, new))
            it.text = new
    return changes

def table_crop(items: list[EvidenceItem], rng: random.Random, frac: float = 0.25
               ) -> list[Change]:
    """Blank a contiguous band of rows (a cropped scan loses part of the table)."""
    rows = sorted({it.row for it in items if it.kind == "cell" and it.row is not None})
    if len(rows) < 3:
        return []
    k = max(1, int(round(frac * len(rows))))
    start = rng.randint(0, len(rows) - k)
    cropped = set(rows[start:start + k])
    changes = []
    for it in items:
        if it.kind == "cell" and it.row in cropped and it.text:
            changes.append(Change(it.id, "table_crop", it.text, ""))
            it.text, it.value = "", None
    return changes


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
STRUCTURAL = ("numeric_perturb", "row_swap", "deletion")
SEMANTIC   = ("paraphrase", "entity_swap")
REALISTIC  = ("ocr_confusion", "header_drift", "table_crop")

def corrupt_example(items: list[EvidenceItem], rate: float, family: str,
                    global_seed: int, example_id: str,
                    llm: Optional[Callable[[str], str]] = None,
                    para_cache: Optional[dict] = None,
                    ops_override: Optional[tuple] = None
                    ) -> tuple[list[EvidenceItem], list[Change]]:
    """
    Corrupt a `rate` fraction of items under `family` in
    {'structural','semantic','realistic'}. Returns (corrupted_items, changes);
    `changes` feeds fallback_analysis (recoverability) and per-error-type reporting.

    For PER-ERROR-TYPE degradation (W1), pass `ops_override` with a single op,
    e.g. ops_override=("ocr_confusion",), and run each type in its own pass.
    """
    assert family in ("structural", "semantic", "realistic")
    rng = make_rng(global_seed, example_id)
    items = [replace(it) for it in items]                     # copy; never mutate caller's
    n_corrupt = int(round(rate * len(items)))
    if n_corrupt == 0:
        return items, []
    targets = set(rng.sample(range(len(items)), n_corrupt))
    pools = build_entity_pools(items) if family == "semantic" else {}
    by_id = {it.id: i for i, it in enumerate(items)}
    changes: list[Change] = []
    default_ops = {"structural": STRUCTURAL, "semantic": SEMANTIC, "realistic": REALISTIC}[family]
    ops = ops_override or default_ops

    for idx in sorted(targets):
        op = rng.choice(ops)
        it = items[idx]
        if op == "numeric_perturb":
            items[idx], ch = numeric_perturb(it, rng); changes.append(ch)
        elif op == "deletion":
            items[idx], ch = delete_item(it); changes.append(ch)
        elif op == "row_swap":
            changes.extend(row_swap(items, rng))          # may touch several cells
        elif op == "entity_swap":
            items[idx], ch = entity_swap(it, rng, pools); changes.append(ch)
        elif op == "ocr_confusion":
            items[idx], ch = ocr_confusion(it, rng); changes.append(ch)
        elif op == "header_drift":
            changes.extend(header_drift(items, rng))      # whole header row
        elif op == "table_crop":
            changes.extend(table_crop(items, rng))        # contiguous row band
        elif op == "paraphrase":
            if llm is None:
                raise ValueError("semantic family needs an `llm` callable for paraphrase")
            key = f"{global_seed}:{example_id}:{it.id}"
            items[idx], ch = paraphrase_substitute(it, rng, llm, para_cache, key)
            changes.append(ch)
    return items, changes


# --------------------------------------------------------------------------- #
# Persistence helpers for the paraphrase cache (keeps semantic runs reproducible)
# --------------------------------------------------------------------------- #
def load_cache(path: str) -> dict:
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else {}

def save_cache(cache: dict, path: str) -> None:
    Path(path).write_text(json.dumps(cache, ensure_ascii=False, indent=0))


# --------------------------------------------------------------------------- #
# ADAPTER STUB — replace with your loader (this is the only pipeline-specific part)
# --------------------------------------------------------------------------- #
def example_to_items(example: dict) -> list[EvidenceItem]:
    """
    Map ONE dataset example (MMQA / TAT-QA) to list[EvidenceItem].
    Give every cell/span a STABLE id so corruption is reproducible across seeds.
    Below is an illustrative shape — adjust field names to your data.
    """
    items: list[EvidenceItem] = []
    for r, row in enumerate(example.get("table", [])):
        for c, cell in enumerate(row):
            txt = str(cell)
            items.append(EvidenceItem(
                id=f"cell:{r}:{c}", kind="cell", text=txt,
                value=_parse_num(txt), table_id="t0", row=r, col=c))
    for s, span in enumerate(example.get("passages", [])):
        items.append(EvidenceItem(id=f"span:{s}", kind="text", text=str(span)))
    return items
