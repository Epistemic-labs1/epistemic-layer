from epistemic.independence import count_independent_families
from epistemic.models import Evidence, EvidenceKind


def test_copies_and_summaries_share_a_lineage():
    evidence = [
        Evidence("a", "c1", EvidenceKind.ORIGINAL, "source-a"),
        Evidence("b", "c1", EvidenceKind.COPY, "source-b", ("a",)),
        Evidence("c", "c1", EvidenceKind.SUMMARY, "source-c", ("b",)),
        Evidence("d", "c1", EvidenceKind.INDEPENDENT, "source-d"),
    ]

    assert count_independent_families(evidence) == 2


def test_two_unrelated_sources_are_two_families():
    evidence = [
        Evidence("a", "c1", EvidenceKind.ORIGINAL, "source-a"),
        Evidence("b", "c1", EvidenceKind.ORIGINAL, "source-b"),
    ]

    assert count_independent_families(evidence) == 2
