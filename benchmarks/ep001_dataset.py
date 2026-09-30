from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkDocument:
    id: str
    family: str
    relation: str
    text: str


def build_ep001_dataset() -> list[BenchmarkDocument]:
    """Build a deterministic 25-document EP-001 corpus.

    Five source families are represented:
    - original
    - exact copy
    - lightly edited derivative
    - compressed summary
    - independent report

    The family label is ground truth for evaluation only; production code
    must never treat this label as observed provenance.
    """
    topics = [
        ("t01", "A harbor authority installed a new weather sensor on pier three."),
        ("t02", "A research vessel completed a survey of the northern reef."),
        ("t03", "The museum opened a temporary exhibition on ancient navigation."),
        ("t04", "A factory replaced an aging hydraulic pump during scheduled maintenance."),
        ("t05", "The university launched a laboratory for autonomous marine systems."),
    ]

    docs: list[BenchmarkDocument] = []
    for topic_id, original in topics:
        docs.append(BenchmarkDocument(f"{topic_id}-o", topic_id, "original", original))
        docs.append(BenchmarkDocument(f"{topic_id}-c", topic_id, "exact_copy", original))
        docs.append(
            BenchmarkDocument(
                f"{topic_id}-e",
                topic_id,
                "light_edit",
                original.replace("new", "recent").replace("the", "the"),
            )
        )
        docs.append(
            BenchmarkDocument(
                f"{topic_id}-s",
                topic_id,
                "summary",
                "Report: " + original.split(" ", 2)[0] + " confirmed the event.",
            )
        )
        docs.append(
            BenchmarkDocument(
                f"{topic_id}-i",
                f"independent-{topic_id}",
                "independent",
                independent_text(topic_id),
            )
        )
    return docs


def independent_text(topic_id: str) -> str:
    reports = {
        "t01": "Independent observation recorded calm conditions at a coastal monitoring station.",
        "t02": "A separate expedition reported sediment measurements from a different marine sector.",
        "t03": "Visitors attended a public lecture about maritime archaeology during the same month.",
        "t04": "Maintenance logs from another plant describe a compressor inspection.",
        "t05": "A separate engineering team published results from an unmanned surface vehicle trial.",
    }
    return reports[topic_id]
