from __future__ import annotations

from dataclasses import dataclass

from epistemic.candidate_detection import similarity_candidates
from benchmarks.ep001_dataset import BenchmarkDocument


@dataclass(frozen=True)
class PairLabel:
    left_id: str
    right_id: str
    same_lineage: bool


@dataclass(frozen=True)
class ThresholdMetrics:
    threshold: float
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int

    @property
    def precision(self) -> float:
        denominator = self.true_positives + self.false_positives
        return self.true_positives / denominator if denominator else 0.0

    @property
    def recall(self) -> float:
        denominator = self.true_positives + self.false_negatives
        return self.true_positives / denominator if denominator else 0.0


def pair_labels(documents: list[BenchmarkDocument]) -> list[PairLabel]:
    """Create evaluation-only pair labels from benchmark ground truth."""
    labels: list[PairLabel] = []
    for index, left in enumerate(documents):
        for right in documents[index + 1 :]:
            labels.append(
                PairLabel(
                    left.id,
                    right.id,
                    left.family == right.family,
                )
            )
    return labels


def evaluate_threshold(
    documents: list[BenchmarkDocument], threshold: float
) -> ThresholdMetrics:
    """Evaluate lexical candidate detection against hidden benchmark labels."""
    texts = {item.id: item.text for item in documents}
    predicted = {
        (item.left_id, item.right_id)
        for item in similarity_candidates(texts, threshold=threshold)
    }

    tp = fp = fn = tn = 0
    for pair in pair_labels(documents):
        key = (pair.left_id, pair.right_id)
        if pair.same_lineage and key in predicted:
            tp += 1
        elif pair.same_lineage and key not in predicted:
            fn += 1
        elif not pair.same_lineage and key in predicted:
            fp += 1
        else:
            tn += 1

    return ThresholdMetrics(threshold, tp, fp, fn, tn)
