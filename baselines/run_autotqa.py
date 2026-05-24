#!/usr/bin/env python3
"""Thin wrapper exposing the vendored AutoPrep AutoTQA implementation."""

from __future__ import annotations

import os
from typing import Any, Dict


def _resolve_autotqa_llm(model: str) -> str:
    """Map non-OpenAI identifiers to a valid OpenAI chat model for the vendored AutoTQA stack."""

    override = os.getenv("AUTOTQA_OPENAI_MODEL")
    if override:
        return override
    normalized = (model or "").strip()
    if normalized.startswith(("gpt-", "o1", "o3", "o4", "openai/")):
        return normalized
    return "gpt-4.1-mini"

import pandas as pd

from src.data import TQAData
from src.model.autotqa.autotqa import AutoTQA


def _table_to_dataframe(table: Any) -> pd.DataFrame:
    if isinstance(table, pd.DataFrame):
        return table.copy()
    if not isinstance(table, list) or not table:
        return pd.DataFrame()

    if all(isinstance(row, list) for row in table):
        header = table[0]
        rows = table[1:] if len(table) > 1 else []
        if isinstance(header, list) and header:
            try:
                return pd.DataFrame(rows, columns=[str(x) for x in header])
            except Exception:
                pass
        return pd.DataFrame(table)

    return pd.DataFrame(table)


def _build_tqadata(sample: Dict[str, Any], evidence: Dict[str, Any] | None = None) -> TQAData:
    payload = evidence or sample
    table = _table_to_dataframe(payload.get("table") or sample.get("table") or [])
    question = str(sample.get("question") or payload.get("question") or "")
    label = sample.get("gold_answer")
    if label is None:
        label = sample.get("answer")
    label = "" if label is None else str(label)
    title = (
        payload.get("title")
        or sample.get("title")
        or payload.get("table_title")
        or sample.get("table_title")
        or ""
    )
    caption = payload.get("caption") or sample.get("caption")
    sample_id = sample.get("id") or payload.get("id") or "NO_ID"
    return TQAData(
        dataset_name="mmqa",
        tbl=table,
        question=question,
        label=label,
        task_type="tqa",
        id=str(sample_id),
        title=str(title) if title is not None else None,
        caption=str(caption) if caption is not None else None,
    )


def run_autotqa_on_sample(
    sample: Dict[str, Any],
    evidence: Dict[str, Any] | None,
    model: str,
    temperature_summarizer: float = 0.0,
    temperature_table_context: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    del temperature_summarizer, temperature_table_context, max_tokens
    if not os.getenv("OPENAI_API_KEY") and not os.path.exists("keys.txt"):
        raise RuntimeError("AutoTQA requires OPENAI_API_KEY or a local keys.txt file.")
    data = _build_tqadata(sample, evidence=evidence)
    resolved_model = _resolve_autotqa_llm(model)
    agent = AutoTQA(llm_name=resolved_model)
    result = agent.process(data)
    answer = result.get("final_answer") if isinstance(result, dict) else None
    return "" if answer is None else str(answer)

