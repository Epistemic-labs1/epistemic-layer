from benchmarks.ep001_dataset import build_ep001_dataset
from epistemic.candidate_detection import similarity_candidates


def test_high_overlap_derivatives_are_flagged():
    docs = {item.id: item.text for item in build_ep001_dataset()}
    candidates = similarity_candidates(docs, threshold=0.7)

    pairs = {(item.left_id, item.right_id) for item in candidates}
    assert ("t01-o", "t01-c") in pairs
    assert ("t01-o", "t01-e") in pairs
    assert ("t01-o", "t01-i") not in pairs


def test_candidates_are_triage_not_proof():
    docs = {item.id: item.text for item in build_ep001_dataset()}
    candidates = similarity_candidates(docs, threshold=0.7)

    assert len(candidates) >= 10
    assert all(0.7 <= item.score <= 1.0 for item in candidates)
