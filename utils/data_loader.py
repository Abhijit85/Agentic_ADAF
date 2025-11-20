"""Utility functions for loading benchmark datasets."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List


def _load_tatqa(split: str = "dev") -> List[Dict[str, Any]]:
    """Return a list of QA examples from the TAT-QA dataset.

    Each example in the returned list is a dictionary with at least the
    following keys:

    ``question`` -- question string
    ``answer`` -- the annotated answer
    ``table`` -- table rows as loaded from the dataset
    ``paragraphs`` -- list of associated context paragraphs
    """

    base_dir = os.path.join(os.path.dirname(__file__), "..", "data", "TATQA")
    file_map = {
        "train": "tatqa_dataset_train.json",
        "dev": "tatqa_dataset_dev.json",
        "test": "tatqa_dataset_test.json",
        "test_gold": "tatqa_dataset_test_gold.json",
    }

    if split not in file_map:
        raise ValueError(f"Unknown TAT-QA split: {split}")

    path = os.path.join(base_dir, file_map[split])
    with open(path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    processed: List[Dict[str, Any]] = []
    for entry in raw_data:
        table = entry.get("table", {}).get("table")
        paragraphs = [p.get("text", "") for p in entry.get("paragraphs", [])]
        for q in entry.get("questions", []):
            processed.append(
                {
                    "question": q.get("question", ""),
                    "answer": q.get("answer"),
                    "table": table,
                    "paragraphs": paragraphs,
                }
            )

    return processed


def _load_flat_dataset(base_dir: str, file_map: Dict[str, str], split: str) -> List[Dict[str, Any]]:
    """Load a dataset stored as a flat list of QA samples (one dict per entry)."""

    if split not in file_map:
        raise ValueError(f"Unknown split '{split}'. Available: {sorted(file_map)}")

    path = os.path.join(base_dir, file_map[split])
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected list of samples in {path}")

    return data


def _load_json_records(base_dir: Path, split: str) -> List[Dict[str, Any]]:
    """Load JSON/JSONL records from ``base_dir``."""

    candidates = [
        base_dir / f"{split}.json",
        base_dir / f"{split}.jsonl",
    ]
    for path in candidates:
        if path.exists():
            if path.suffix == ".jsonl":
                records: List[Dict[str, Any]] = []
                with path.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            records.append(json.loads(line))
                return records
            with path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            if not isinstance(payload, list):
                raise ValueError(f"Expected list in {path}")
            return payload
    raise FileNotFoundError(
        f"Could not locate {split}.json or {split}.jsonl under {base_dir}. "
        "Download/preprocess the dataset and store it there."
    )


def _load_crtqa(split: str = "dev") -> List[Dict[str, Any]]:
    """Load the CRT-QA benchmark."""

    base_dir = os.path.join(os.path.dirname(__file__), "..", "data", "CRTQA")
    file_map = {
        "train": "crtqa_train.json",
        "dev": "crtqa_dev.json",
        "test": "crtqa_test.json",
    }
    return _load_flat_dataset(base_dir, file_map, split)


def _load_multi_hop_synth(split: str = "dev") -> List[Dict[str, Any]]:
    """Load the synthetic multi-hop dataset with 5–8 operator chains."""

    base_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multi_hop_synthetic")
    file_map = {
        "train": "multi_hop_train.json",
        "dev": "multi_hop_dev.json",
        "test": "multi_hop_test.json",
    }
    return _load_flat_dataset(base_dir, file_map, split)


def load_benchmark(name: str, *, split: str = "dev", limit: int | None = None) -> List[Dict[str, Any]]:
    """Load a dataset by name.

    Only the ``tatqa`` benchmark is supported in this example repository.

    Parameters
    ----------
    name:
        The dataset name.  Currently ``"tatqa"`` is the only valid value.
    split:
        Which dataset split to load.  One of ``"train"``, ``"dev"``,
        ``"test"``, or ``"test_gold"``.
    """

    name = name.lower()

    if name == "tatqa":
        data = _load_tatqa(split)
    elif name in {"crtqa", "crt-qa"}:
        data = _load_crtqa(split)
    elif name in {"multi_hop", "multi-hop", "multi_hop_synth", "multi-hop-synth"}:
        data = _load_multi_hop_synth(split)
    elif name == "finqa":
        base = Path(__file__).resolve().parent.parent / "data" / "FinQA"
        data = _load_json_records(base, split)
    elif name == "tat-qa":
        data = _load_tatqa(split)
    elif name in {"mmqa", "mmqa_full"}:
        base = Path(__file__).resolve().parent.parent / "data" / "MMQA"
        folder = base / "full" if name.endswith("full") else base
        data = _load_json_records(folder, split)
    elif name == "mmqa_text_table":
        base = Path(__file__).resolve().parent.parent / "data" / "MMQA_text_table"
        data = _load_json_records(base, split)
    elif name in {"wikitq", "wiki-tq"}:
        base = Path(__file__).resolve().parent.parent / "data" / "WikiTQ"
        data = _load_json_records(base, split)
    elif name in {"fetaqa", "feta-qa"}:
        base = Path(__file__).resolve().parent.parent / "data" / "FeTaQA"
        data = _load_json_records(base, split)
    else:
        raise ValueError(f"Unsupported dataset: {name}")

    if limit is not None and limit > 0:
        return data[:limit]
    return data
