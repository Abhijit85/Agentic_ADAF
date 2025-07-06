class ContextAgent:
    """Retrieve relevant context for a question."""
    def __init__(self, model):
        self.model = model

    def retrieve(self, question, text):
        # In a real system, use the model to select relevant sentences.
        return text
