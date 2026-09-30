from __future__ import annotations

from dataclasses import dataclass

from .similarity import jaccard_similarity


@dataclass(frozen=True)
class SimilarityCandidate:
    left_id: str
    right_id: str
    score: float


def similarity_candidates(
    texts: dict[str, str], threshold: float = 0.7
) -> list[SimilarityCandidate]:
    """Find pairs whose lexical overlap is high enough to warrant provenance review.

    This is a triage signal, not proof of shared provenance.
    """
    ids = list(texts)
    candidates: list[SimilarityCandidate] = []
    for index, left_id in enumerate(ids):
        for right_id in ids[index + 1 :]:
            score = jaccard_similarity(texts[left_id], texts[right_id])
            if score >= threshold:
                candidates.append(SimilarityCandidate(left_id, right_id, score))
    return sorted(candidates, key=lambda item: (-item.score, item.left_id, item.right_id))
