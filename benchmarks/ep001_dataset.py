from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkDocument:
    id: str
    family: str
    relation: str
    text: str


def build_ep001_dataset() -> list[BenchmarkDocument]:
    """Build a deterministic corpus for the first independence experiment.

    Ground-truth family labels are evaluation-only. Production code must not
    use them as observed provenance.
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
        docs.extend(
            [
                BenchmarkDocument(f"{topic_id}-o", topic_id, "original", original),
                BenchmarkDocument(f"{topic_id}-c", topic_id, "exact_copy", original),
                BenchmarkDocument(
                    f"{topic_id}-e",
                    topic_id,
                    "light_edit",
                    original.replace("new", "recent"),
                ),
                BenchmarkDocument(
                    f"{topic_id}-s",
                    topic_id,
                    "summary",
                    summary_text(topic_id),
                ),
                BenchmarkDocument(
                    f"{topic_id}-r",
                    topic_id,
                    "ai_rewrite",
                    rewrite_text(topic_id),
                ),
                BenchmarkDocument(
                    f"{topic_id}-i",
                    f"independent-{topic_id}",
                    "independent",
                    independent_text(topic_id),
                ),
            ]
        )
    return docs


def summary_text(topic_id: str) -> str:
    return {
        "t01": "A port authority confirmed that a weather monitoring sensor was installed at a pier.",
        "t02": "The research ship finished its northern reef survey.",
        "t03": "A museum has opened a temporary display focused on ancient navigation.",
        "t04": "A manufacturing plant replaced an old hydraulic pump as part of planned maintenance.",
        "t05": "The university opened a new laboratory focused on autonomous marine technology.",
    }[topic_id]


def rewrite_text(topic_id: str) -> str:
    return {
        "t01": "Port officials announced that new equipment for monitoring weather conditions is now operating on pier three.",
        "t02": "Scientists said their vessel had finished collecting survey data across the reef in the north.",
        "t03": "A cultural institution is hosting a short-term exhibition examining historical navigation practices.",
        "t04": "Scheduled plant maintenance included removal of an older hydraulic unit and installation of its replacement.",
        "t05": "A university has created a research facility dedicated to autonomous systems used in marine environments.",
    }[topic_id]


def independent_text(topic_id: str) -> str:
    return {
        "t01": "Independent observation recorded calm conditions at a coastal monitoring station.",
        "t02": "A separate expedition reported sediment measurements from a different marine sector.",
        "t03": "Visitors attended a public lecture about maritime archaeology during the same month.",
        "t04": "Maintenance logs from another plant describe a compressor inspection.",
        "t05": "A separate engineering team published results from an unmanned surface vehicle trial.",
    }[topic_id]
