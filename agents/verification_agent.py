"""Agent that verifies candidate answers before finalisation."""

from __future__ import annotations

from typing import Any, Optional


class VerificationAgent:
    """Perform lightweight answer verification against references."""

    def verify(self, candidate: str, reference: Optional[Any]) -> bool:
        """Return ``True`` if ``candidate`` satisfies ``reference``."""

        if reference is None:
            # Without a reference answer we cannot verify automatically.
            return False

        ref_text = str(reference).strip().lower()
        cand_text = str(candidate).strip().lower()
        return cand_text == ref_text
