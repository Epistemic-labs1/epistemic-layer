from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EvidenceKind(str, Enum):
    ORIGINAL = "original"
    COPY = "copy"
    PARAPHRASE = "paraphrase"
    SUMMARY = "summary"
    DERIVED = "derived"
    INDEPENDENT = "independent"


@dataclass(frozen=True)
class Evidence:
    id: str
    claim_id: str
    kind: EvidenceKind
    source_id: str
    derived_from: tuple[str, ...] = ()
    authority: float = 0.5


@dataclass
class Claim:
    id: str
    text: str
    evidence: list[Evidence] = field(default_factory=list)
