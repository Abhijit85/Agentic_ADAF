from models.align_llm import AlignedLanguageModel
from .table_agent import TableAgent
from .context_agent import ContextAgent
from .calculation_agent import CalculationAgent


class AdaptiveOrchestrator:
    """Coordinate different agents for answering a question."""

    def __init__(self, model_name: str = "mistral-7b"):
        self.llm = AlignedLanguageModel(model_name)
        self.table_agent = TableAgent(self.llm)
        self.context_agent = ContextAgent(self.llm)
        self.calc_agent = CalculationAgent()

    def run(self, sample: dict) -> dict:
        question = sample.get("question", "")
        table = sample.get("table")
        text = sample.get("text")

        context = self.context_agent.retrieve(question, text)
        # In a full system, operations on tables would be derived from the model
        table = self.table_agent.apply_operation(table, "") if table is not None else None
        answer = self.llm.answer(question, table, context)
        return {"answer": answer}
