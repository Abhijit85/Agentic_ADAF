"""Data loading utilities."""

from typing import List, Dict


_SAMPLE_DATA = [
    {"question": "What is 1 + 1?", "answer": "2", "table": None, "text": ""},
    {"question": "How many legs on a dog?", "answer": "4", "table": None, "text": ""},
]


def load_benchmark(name: str) -> List[Dict]:
    """Load a small built-in dataset as a placeholder."""
    return list(_SAMPLE_DATA)
