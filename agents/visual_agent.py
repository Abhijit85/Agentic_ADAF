"""Agent responsible for ingesting visual artefacts such as charts or images."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


class VisualAgent:
    """Produce lightweight textual descriptions from visual inputs."""

    def __init__(self, model: Optional[Any] = None) -> None:  # pragma: no cover - trivial
        self.model = model

    def describe(self, visuals: Optional[Iterable[Dict[str, Any]]]) -> str:
        """Return a textual description of ``visuals``.

        ``visuals`` is expected to be an iterable of dictionaries describing
        figures or images.  The repository's synthetic dataset does not provide
        real visual assets, so this implementation falls back to metadata-based
        descriptions when possible.
        """

        if not visuals:
            return "No visual artefacts provided."

        summaries = []
        for item in visuals:
            title = item.get("title") if isinstance(item, dict) else None
            caption = item.get("caption") if isinstance(item, dict) else None
            if title and caption:
                summaries.append(f"{title}: {caption}")
            elif title:
                summaries.append(f"{title} (no caption available)")
            elif caption:
                summaries.append(caption)

        if not summaries:
            return "Visual metadata present but could not be interpreted."

        return " \n".join(summaries)
