from benchmarks.ep001_dataset import build_ep001_dataset
from epistemic.candidate_detection import similarity_candidates


def test_high_overlap_derivatives_are_flagged():
    docs = {item.id: item.text for item in build_ep001_dataset()}
    candidates = similarity_candidates(docs, threshold=0.7)

    pairs = {(item.left_id, item.right_id) for item in candidates}
    assert ("t01-o", "t01-c") in pairs
    assert ("t01-o", "t01-e") in pairs


def test_lexical_similarity_is_only_a_triage_signal():
    docs = {item.id: item.text for item in build_ep001_dataset()}
    candidates = similarity_candidates(docs, threshold=0.7)

    # AI rewrites and genuinely independent reports may or may not be caught.
    # The detector is a review signal, not a provenance or independence proof.
    assert all(item.left_id != item.right_id for item in candidates)


def test_candidates_have_valid_scores():
    docs = {item.id: item.text for item in build_ep001_dataset()}
    candidates = similarity_candidates(docs, threshold=0.7)

    assert all(0.7 <= item.score <= 1.0 for item in candidates)
