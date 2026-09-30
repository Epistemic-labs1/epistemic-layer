# epistemic-layer

An open-source epistemic control layer for AI agents.

## EP-001: Evidence Independence

The first experiment asks a narrow question:

> Can an AI system distinguish many pieces of evidence from many **independent evidence lineages**?

The repository currently contains a deliberately small deterministic baseline:

- an evidence data model;
- explicit provenance through `derived_from`;
- lineage-family grouping;
- tests for copies/summaries versus independent sources.

### What this does **not** claim yet

This baseline does **not** infer independence from text similarity, authorship, web provenance, or semantic analysis. Those are later research questions.

The goal of EP-001 is to establish a reproducible test harness before adding more sophisticated inference.

## Development

Python 3.11+.

Run:

```bash
python -m pytest
```

## Status

Research prototype — not production software.
