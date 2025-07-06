class CalculationAgent:
    """Perform simple numeric calculations."""
    def calculate(self, expression: str):
        try:
            return eval(expression, {}, {})
        except Exception:
            return None
