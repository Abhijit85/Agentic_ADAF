"""Evaluation metrics used by the framework."""


def compute_f1(prediction: str, ground_truth: str) -> float:
    """Compute a simple token-level F1 score."""
    pred_tokens = prediction.lower().split()
    gold_tokens = ground_truth.lower().split()
    if not pred_tokens and not gold_tokens:
        return 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0
    common = set(pred_tokens) & set(gold_tokens)
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(gold_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)
