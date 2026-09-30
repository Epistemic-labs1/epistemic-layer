from __future__ import annotations

from collections import defaultdict

from .models import Evidence


def independent_families(evidence: list[Evidence]) -> list[set[str]]:
    """Return evidence families rooted in distinct source lineages.

    This is deliberately conservative and deterministic for EP-001.
    It does not claim semantic independence from text similarity.
    """
    parent = {item.id: item.id for item in evidence}

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    by_id = {item.id: item for item in evidence}

    for item in evidence:
        for parent_id in item.derived_from:
            if parent_id in by_id:
                union(item.id, parent_id)

    families: dict[str, set[str]] = defaultdict(set)
    for item in evidence:
        families[find(item.id)].add(item.id)

    return list(families.values())


def count_independent_families(evidence: list[Evidence]) -> int:
    return len(independent_families(evidence))
