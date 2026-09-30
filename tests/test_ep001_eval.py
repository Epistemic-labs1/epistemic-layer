from benchmarks.ep001_dataset import build_ep001_dataset
from benchmarks.ep001_eval import evaluate_threshold, pair_labels


def test_pair_labels_use_family_as_ground_truth():
    labels = pair_labels(build_ep001_dataset())

    assert len(labels) == 435
    assert any(
        item.left_id == "t01-o"
        and item.right_id == "t01-c"
        and item.same_lineage
        for item in labels
    )
    assert any(
        item.left_id == "t01-o"
        and item.right_id == "t01-i"
        and not item.same_lineage
        for item in labels
    )


def test_threshold_metrics_are_consistent():
    metrics = evaluate_threshold(build_ep001_dataset(), threshold=0.7)

    assert metrics.true_positives + metrics.false_negatives == 50
    assert (
        metrics.true_positives
        + metrics.false_positives
        + metrics.false_negatives
        + metrics.true_negatives
        == 435
    )
    assert 0.0 <= metrics.precision <= 1.0
    assert 0.0 <= metrics.recall <= 1.0
