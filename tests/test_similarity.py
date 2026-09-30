from epistemic.similarity import cosine_similarity, jaccard_similarity


def test_exact_copy_is_identical():
    text = "The vessel completed the survey in calm weather."
    assert jaccard_similarity(text, text) == 1.0
    assert cosine_similarity(text, text) == 1.0


def test_unrelated_text_has_low_overlap():
    left = "The vessel completed the survey in calm weather."
    right = "The museum opened a temporary exhibition about sculpture."
    assert jaccard_similarity(left, right) < 0.3
