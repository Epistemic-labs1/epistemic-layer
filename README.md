# epistemic-layer

An open-source epistemic control layer for AI agents.

## EP-001: Evidence Independence

The first experiment asks a narrow question:

> Can an AI system distinguish many pieces of evidence from many **independent evidence lineages**?

The current prototype contains:

- a minimal Claim/Evidence data model;
- explicit provenance through `derived_from`;
- deterministic lineage-family grouping;
- a transparent unigram similarity baseline;
- a deterministic 25-document benchmark corpus;
- automated tests and GitHub Actions.

### Benchmark design

Each topic has five documents:

1. original source;
2. exact copy;
3. lightly edited derivative;
4. compressed summary;
5. independent report.

The benchmark's family labels are **ground truth for evaluation only**. They are not presented to the provenance algorithm.

### What this does not claim

This baseline does **not** prove provenance from text similarity. Similarity can identify candidates for further investigation, but it cannot establish that one document caused another.

The research question is therefore:

`Can observable evidence attributes and similarity signals recover hidden provenance well enough to reduce false evidence counts?`

A later benchmark will add paraphrases, AI-generated transformations, citation chains, conflicting claims, and intentionally ambiguous cases.

## Development

Python 3.11+.

Run:

```bash
python -m pytest
```

## Status

Research prototype — not production software.
