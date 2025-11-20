"""Agent that verifies candidate answers before finalisation."""

from __future__ import annotations

import re
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
        if cand_text == ref_text:
            return True

        ref_number = self._extract_number(ref_text)
        cand_numbers = self._extract_numbers(cand_text)
        if ref_number is not None and cand_numbers:
            tolerance = max(1e-3, 0.01 * abs(ref_number))
            return any(abs(ref_number - num) <= tolerance for num in cand_numbers)

        return False

    def _extract_number(self, text: str) -> Optional[float]:
        numbers = self._extract_numbers(text)
        return numbers[0] if numbers else None

    def _extract_numbers(self, text: str) -> list[float]:
        matches = re.findall(r"[-+]?\d+(?:\.\d+)?", text.replace(",", ""))
        results = []
        for match in matches:
            try:
                results.append(float(match))
            except ValueError:
                continue
        return results
