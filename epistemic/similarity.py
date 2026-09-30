from __future__ import annotations

import re
from collections import Counter


def _tokens(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def jaccard_similarity(left: str, right: str) -> float:
    """Token-set Jaccard similarity.

    This is intentionally a simple research baseline, not a semantic
    similarity model and not a provenance proof.
    """
    a, b = set(_tokens(left)), set(_tokens(right))
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cosine_similarity(left: str, right: str) -> float:
    """Cosine similarity over unigram counts using only the standard library."""
    a, b = Counter(_tokens(left)), Counter(_tokens(right))
    if not a or not b:
        return 0.0
    dot = sum(a[token] * b.get(token, 0) for token in a)
    norm_a = sum(value * value for value in a.values()) ** 0.5
    norm_b = sum(value * value for value in b.values()) ** 0.5
    return dot / (norm_a * norm_b)
