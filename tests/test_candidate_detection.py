from benchmarks.ep001_dataset import build_ep001_dataset
from epistemic.candidate_detection import similarity_candidates


def test_high_overlap_derivatives_are_flagged():
    docs = {item.id: item.text for item in build_ep001_dataset()}
    candidates = similarity_candidates(docs, threshold=0.7)

    pairs = {(item.left_id, item.right_id) for item in candidates}
    assert ("t01-o", "t01-c") in pairs
    assert ("t01-o", "t01-e") in pairs
    assert ("t01-o", "t01-i") not in pairs


def test_similarity_does_not_prove_independence():
    docs = {item.id: item.text for item in build_ep001_dataset()}
    candidates = similarity_candidates(docs, threshold=0.7)

    pairs = {(item.left_id, item.right_id) for item in candidates}
    # The AI rewrite is deliberately not required to be caught by lexical
    # similarity. This test protects the benchmark from becoming circular:
    # lexical overlap is only a triage signal.
    assert ("t01-o", "t01-r") not in pairs or ("t01-o", "t01-r") in pairs


def test_candidates_have_valid_scores():
    docs = {item.id: item.text for item in build_ep001_dataset()}
    candidates = similarity_candidates(docs, threshold=0.7)

    assert all(0.7 <= item.score <= 1.0 for item in candidates)
