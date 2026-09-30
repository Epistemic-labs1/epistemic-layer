# Epistemic Layer

An open-source research project for an epistemic control layer for AI agents.

## Current research question

Can an agent distinguish genuinely independent evidence from evidence that only appears independent?

EP-001 is deliberately narrow. It is not a production provenance detector and it makes no claim that lexical similarity proves common origin.

### EP-001 baseline

The benchmark contains 25 deterministic documents across five topics:

- original
- exact copy
- lightly edited derivative
- compressed summary
- genuinely independent report

The current implementation has two separate signals:

1. Explicit lineage: when derived_from is available, evidence can be grouped deterministically.
2. Similarity triage: high lexical overlap is surfaced for provenance review when lineage is missing.

The second signal is intentionally weak. A summary can preserve the underlying fact while sharing few words with its source, so lexical similarity alone cannot establish independence.

### Validation rule

We will not claim success because a test passes. The next experiment must measure where the baseline fails, especially:

- hidden paraphrases
- summaries with low lexical overlap
- AI-generated rewrites
- source chains with missing provenance
- genuinely independent reports about the same event

If the system cannot separate these cases with stronger evidence, we will document the failure rather than rename the problem.

## Status

EP-001 is an experiment, not a product.
