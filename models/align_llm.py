"""Simple aligned language model wrapper."""


class AlignedLanguageModel:
    def __init__(self, name: str = "mistral-7b"):
        self.name = name

    def answer(self, question: str, table=None, text: str | None = None) -> str:
        """Return a dummy answer. Real implementation would query an LLM."""
        return "42"
