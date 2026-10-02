# EP-002 — Non-literal Derivation Detection: Experimental Specification

| | |
|---|---|
| Status | **DRAFT — under review. No implementation until explicitly approved.** |
| Version | 0.1 (2026-10-02) |
| Supersedes | EP-001 (Evidence Independence Baseline) as the active experiment |
| Process | HYPOTHESIS → PRIOR ART → **SPECIFICATION** → REVIEW → EXPERIMENT → RESULTS → KILL / CONTINUE |

Evidence labels used throughout:
**FACT** (verified by running code or reading a primary source), **EVIDENCE** (observed signal, not proof), **INFERENCE** (reasoning from facts), **SPECULATION** (unverified guess). Where a source was seen only as a search-result snippet, this is stated.

This document does not assume the hypothesis is true. Its purpose is to make the hypothesis falsifiable and to fix the kill criteria before any result is seen.

---

## 1. Status of EP-001

### 1.1 What EP-001 was meant to measure
Whether pairs of documents that share a provenance lineage ("same family") can be distinguished from pairs that do not, as a first step toward measuring evidence independence.

### 1.2 Dataset (FACT — `benchmarks/ep001_dataset.py`, commit `ba35f73`)
- 5 topics × 6 documents = 30 documents → 435 unordered pairs.
- Per topic: `original`, `exact_copy`, `light_edit`, `summary`, `ai_rewrite` (all one family) and `independent` (its own family).
- Each text is a single hand-written sentence.

### 1.3 Method and result (FACT — re-run locally on 2026-10-02)
Method: token-set Jaccard similarity (`epistemic/similarity.py`), pair flagged as "same lineage" if score ≥ threshold.

At threshold **0.7**: **TP = 15, FP = 0, FN = 35, TN = 385** (precision 1.00, recall 0.30). Results at 0.6 are identical.

| Threshold | TP | FP | FN | TN |
|---|---|---|---|---|
| 0.3 | 30 | 17 | 20 | 368 |
| 0.5 | 18 | 3 | 32 | 382 |
| 0.7 | 15 | 0 | 35 | 385 |
| 0.9 | 13 | 0 | 37 | 385 |

### 1.4 What it actually detected (FACT)
The 15 true positives are exactly the `original` / `exact_copy` / `light_edit` pairs (3 per topic × 5). **No `summary` and no `ai_rewrite` pair was detected.**

### 1.5 Dataset defects (FACT)
1. **`light_edit` bug.** `light_edit = original.replace("new", "recent")`, but the word "new" occurs only in topic t01. In t02–t05 the "light edit" is byte-identical to the original. The benchmark therefore contains one real light edit, not five.
2. **Label leakage in the text.** Every `independent` text begins with a label-revealing phrase ("A separate…", "An independent…").
3. **Trivial negatives dominate.** 360 of 435 pairs compare different topics (max Jaccard 0.25). Only 25 negatives are hard (same topic, independent source). TN = 385 is mostly trivial.
4. **Single author.** All "summaries", "AI rewrites" and "independent reports" were written by the same hand, so "independence" was asserted, not produced by an independent process.

### 1.6 Class overlap (FACT — Jaccard to the `original`)
| Relation | Label | Jaccard range |
|---|---|---|
| ai_rewrite | dependent | 0.17 – 0.28 |
| independent | independent | 0.25 – 0.50 |
| summary | dependent | 0.35 – 0.58 |

Independent reports are lexically *closer* to the original than AI rewrites derived from it. No threshold separates the classes.

### 1.7 Conclusion (INFERENCE)
EP-001 measures **near-identical lexical overlap**, not evidence independence. Its result neither supports nor refutes the Epistemic Layer hypothesis; the benchmark could not test it. The code itself correctly describes Jaccard as a "triage signal, not proof of shared provenance". EP-001 is retained as the source of the failure mode EP-002 targets.

---

## 2. Hypotheses

**H0.** On the reference dataset, a lexical baseline is sufficient to distinguish dependent (derived) from independent source pairs; no tested method improves on it to the degree defined in §8.

**H1.** At least one method that captures non-literal derivation detects a substantially larger share of true dependencies — specifically summaries, rewrites, paraphrases, compositions and chains — than the best lexical baseline, **without an unacceptable increase in false positives on genuinely independent sources**, as defined in §8.

The method is **not** chosen in advance. Candidates (§6.2) are explored on the development split only and evaluated once on the held-out test split.

---

## 3. Problem definition

Three distinct relations between two texts A and B:

| Relation | Meaning | Observable from text alone? |
|---|---|---|
| **Similarity** | A and B say similar things (lexically or semantically) | Yes |
| **Derivation** | B was produced using A (directly, or through intermediaries, in whole or in part) | Sometimes |
| **Independence** | No information flowed from A to B or from B to A, except through the world event both describe | Only indirectly |

Similarity ≠ derivation ≠ independence:
- A and B can be **highly similar yet independent**: two reporters observe the same event and write nearly the same sentence.
- A and B can be **dissimilar yet dependent**: B is a 100-word summary or an AI rewrite of a 1,000-word A.

**Definition used in EP-002.** A pair (A, B) is *dependent* if the generation log (§4.3) records that the text of A was an input, directly or through a chain, to the production of B (or vice versa). Otherwise it is *independent*. Sharing facts about the same event does **not** create dependence.

**Out of scope for EP-002 (declared limitation).** Direction of derivation (who copied whom) and full genealogy (A→B→C vs A→B and A→C) are often not identifiable from text alone. EP-002 measures **pairwise dependent / independent** only.

---

## 4. Dataset

### 4.1 Why EP-001's construction cannot be reused
If a single author (human or one LLM) writes both the original and the "independent" sources, those sources share model, style and prior knowledge. A detector could learn **style**, not **derivation**.

### 4.2 Construction: fictional events with controlled information flow
1. **Event.** Each event is a structured record of fictional facts (actors, actions, place, dates, quantities, quotes). Fictional = no model has prior knowledge of it.
2. **Observations.** Facts are split into a shared core (what any observer would see) and **unique details** assigned to individual reporters (e.g. a witness quote, a specific figure, an idiosyncratic error).
3. **Independent documents** are written by a reporter that receives **only its own observation set**, never the text of another document.
4. **Derived documents** are written by a process that receives **the text** of one or more existing documents.
5. **Generator diversity.** Documents are written by **several different models**, including the independent ones, so that "written by an LLM" or "written by model X" does not predict the label. The model used for each document is recorded.

### 4.3 Ground truth
The ground truth is the **information-flow graph** recorded at generation time: for every document, the list of documents whose text was given as input. Dependence is the transitive closure of this graph.

A pair is **excluded from evaluation** (and the exclusion is logged and counted) if:
- generation failed, refused, or produced off-topic / wrong-language output;
- a derived text is identical to its source when the class requires a change (§4.4);
- the flow log for either document is missing or inconsistent.

If more than 10% of an event's documents are excluded, the whole event is excluded. If more than 10% of events are excluded, the dataset is regenerated with the cause documented; it is not silently patched.

### 4.4 Test cases (per event)

| ID | Case | Generation | Label |
|---|---|---|---|
| A | Exact copy | copy of ORIG | dependent |
| B | Light edit | ≥1 and ≤10% tokens changed, verified non-identical | dependent |
| C | Summary | summary of ORIG (target ≤ 30% of length) | dependent |
| D | AI rewrite | full rewrite of ORIG by a **different** model | dependent |
| E | Paraphrase | sentence-by-sentence paraphrase preserving structure | dependent |
| F | Composition | new text from ORIG + another document's text | dependent on both |
| G | Chain | rewrite of D (ORIG → D → G) | dependent on ORIG and D |
| H | Independent, same event | reporter with its own observation set (shared core, different unique details) | independent |
| I | Independent, similar wording | reporter with an observation set nearly identical to ORIG's, instructed to write in the same register | independent (**hard negative**) |
| J | Dependent, low lexical similarity | not generated separately: the stratum of dependent pairs from C–G whose Jaccard is **below the median Jaccard of the H pairs** | dependent (**hard positive**) |

Plus ORIG itself (the root) per event.

### 4.5 Size (proposal, open for review)
- 40 events: **20 development, 20 test**, split **by event** (no event contributes to both splits).
- About 11 documents per event → about 55 same-event pairs per event.
- Cross-event pairs are generated but reported **separately** and never pooled with same-event pairs in the primary metrics.

---

## 5. Avoiding EP-001's errors: automated checks

All checks run before any method is evaluated. Any failure blocks evaluation.

| # | Check | Rule |
|---|---|---|
| C1 | Label words in text | No document contains label-revealing terms (e.g. "independent", "separate", "copy", "summary", "rewrite", "paraphrase", "original", "according to [another document]") — list versioned in config; matches logged |
| C2 | Opaque identifiers | Document IDs are random; no class, family or generator name in IDs or filenames seen by methods |
| C3 | Real transformations | Every derived class except A differs from its source; B within its edit bounds; C within its length bound |
| C4 | Hard-negative share | Same-event independent pairs (H, I) are reported separately; the primary metrics use **same-event pairs only** |
| C5 | Split leakage | No event appears in both dev and test; thresholds and prompts are frozen before the test split is read |
| C6 | Style confound | A trivial classifier using only surface features (length, length ratio, generator model) must not separate dependent from independent same-event pairs well. If it does, the dataset is confounded and must be regenerated |
| C7 | Difficulty floor | If the best lexical baseline already reaches recall ≥ 0.8 on C–G at the §8 operating point, the dataset is too easy and is invalid for testing H1 |
| C8 | Method/generator separation | Any LLM-based method is evaluated with results stratified by whether its model also generated one of the documents in the pair |

---

## 6. Methods

### 6.1 Baselines — fixed now, before any result
| ID | Baseline | Notes |
|---|---|---|
| B0 | Surface sanity | length-ratio only (expected to fail; it is a control) |
| B1 | Token Jaccard | EP-001 implementation, unchanged |
| B2 | TF-IDF cosine | word unigrams + bigrams, fitted on the dev split only |
| B3 | Sentence-embedding cosine | one pinned open-source embedding model; exact model name and version fixed in config before the run |
| B4 | corroborate-mcp clustering | reproduction of its published `assess()` clustering: Jaccard ≥ 0.55 on normalized **headline** tokens (§10). Each generated document therefore includes a headline |
| B5 | Simple LLM judge | one direct prompt: "Was text B produced using text A? yes / no / uncertain", fixed wording, run with a local open model; a sample with one frontier model if the budget allows |

Thresholds for B1–B4 are chosen on the **dev split** to meet the §8 operating point, then frozen.

**Why B5 is a baseline and not a candidate.** If a single plain prompt already separates the classes, no library is needed. Beating B5 is a requirement for continuing (§8).

### 6.2 Candidate methods — explored on dev only, none assumed
Semantic similarity variants; claim overlap; entity/event overlap; unique-detail overlap (a detail known only to one reporter appearing in another text); structured LLM-based dependency signals; combinations of signals; others.

All candidate design choices (features, prompts, thresholds) are frozen and committed **before** the test split is evaluated. Each candidate is evaluated on test **once**.

---

## 7. Metrics

### 7.1 Primary population
Same-event pairs from the **test** split only.

### 7.2 Reported for every method
- Precision, recall, F1, false-positive rate, false-negative rate — DEPENDENT vs INDEPENDENT.
- **Per-case breakdown:** recall for each of A, B, C, D, E, F, G and J; false-positive rate for H and for I **separately**.
- **Non-literal recall:** pooled recall over C, D, E, F, G.
- Cross-event pairs: reported in a separate table, never pooled.

### 7.3 Uncertainty
- 95% confidence intervals by **bootstrap resampling of events** (10,000 resamples, fixed seed).
- Non-deterministic methods are run 5 times; mean and range are reported.
- **Prompt robustness:** every LLM-based method is run with 3 pre-written paraphrases of its prompt; the **worst** of the three is used for the success test.

---

## 8. Success and kill criteria — fixed before the experiment

### 8.1 Operating point and why
Methods are compared at a fixed **false-positive rate ≤ 10% on independent same-event pairs (H ∪ I)**, with a threshold chosen on dev.
*Rationale:* a false positive merges two genuinely independent sources and **undercounts** corroboration — the exact error the project exists to prevent. 10% is a judgement call, not a derived value; results are also reported at 5% and 20% as a sensitivity check.

### 8.2 SUCCESS (H1 supported on synthetic data) — all must hold
1. Non-literal recall (C–G) of the best candidate exceeds the best of B1–B4 by **≥ 0.20 absolute**, with the bootstrap 95% CI of the difference excluding 0.
   *Rationale for 0.20:* smaller gains on synthetic data are unlikely to survive transfer to real text; judgement call, stated openly.
2. It also exceeds **B5 (simple LLM judge)** on non-literal recall, with the CI of the difference excluding 0.
3. FPR on case **I** (hard negatives) is not higher than the best baseline's FPR on I by more than 5 percentage points.
4. Criteria 1–3 hold under the **worst** prompt paraphrase (§7.3).
5. Cost is practical: runnable on a single consumer machine at ≤ 2 seconds per pair, **or** ≤ USD 0.01 per pair through an API (bounds open for review).
6. Checks C1–C8 all passed.

Success on EP-002 authorises **only** EP-003 (real-world data, e.g. agency copy and its republications). It does not authorise an SDK or a product.

### 8.3 KILL — any one is sufficient
1. No candidate improves non-literal recall by the margin in 8.2(1).
2. Recall improves only at the cost of FPR on H ∪ I above the operating point, or on I beyond the 8.2(3) margin.
3. No method separates case I from cases C/D better than chance (CI of the difference includes 0).
4. The improvement disappears under prompt paraphrase (fragile prompts).
5. The cost bounds in 8.2(5) cannot be met.
6. B4 (corroborate-mcp) or another existing open-source system performs within the CI of the best candidate.
7. **B5 performs within the CI of the best candidate** ("a prompt is enough").
8. Ground truth cannot be produced reliably (§4.3 exclusion limits exceeded twice).
9. The dataset fails C6 or C7 and cannot be fixed within the time box.

### 8.4 INCONCLUSIVE
If neither 8.2 nor 8.3 is met within the time box (§12), the result is reported as inconclusive with the reason. No criterion is relaxed after results are seen.

---

## 9. Prior art (as verified on 2026-10-02)

| Work | What it does | Relevance | Label / how verified |
|---|---|---|---|
| **corroborate-mcp** (MIT, JavaScript) | Counts "independent story origins" for a claim from news search results | Same stated goal at claim level; method in §10 | **FACT** — source code read at commit `1da5f99` (2026-07-29) |
| **story-origin-check** (Claude skill) | Traces a news story's origin: syndication, rewrite, aggregator pickup; uses metadata and searches | Same question, prompt-based, no measured method | **FACT** that it exists and its description; read its listing page only, not code |
| **"Rewrite the News: Tracing Editorial Reuse across News Agencies"** (SoCon 2026, ACL Anthology) | Sentence-level reuse across agencies in 7 languages | States reuse is *"predominantly non-literal, involving paraphrase and compositional reuse"* and *"simple lexical matching overlooks substantial editorial reuse"* | **FACT** — abstract read |
| **Truth discovery and copying detection** (Dong, Berti-Equille, Srivastava, VLDB 2009–2010; patent US8190546) | Detects which sources copy from others in **structured** data | Conceptual foundation; not free text | **Snippet only** |
| **"From Agent Traces to Trust"** (arXiv 2606.04990, June 2026) | Survey of provenance in LLM agents; includes a *Derive* relation | Taxonomy only; no detection method or code mentioned | **FACT** — abstract/HTML summary read |
| Web-evidence poisoning of deep-research agents (arXiv 2609.06027; DRNOISE 2607.17291) | Agents misled by poisoned or repeated evidence | Motivation, not a solution | **Snippet only** (2609.06027 page returned HTTP 403) |
| Churnalism (2013); "Detecting Textual Reuse in News Stories, At Scale" (IJoC); R `textreuse` | Lexical text-reuse detection | Lexical baselines | **Snippet only** |
| "Revision-Aware Independent Agent Graphs" (arXiv 2610.01249) | Unknown | Unknown | **Not read** — fetch rate-limited |
| EP-001 (this repository) | Lexical lineage detection | Documents the failure mode | **FACT** — §1 |

INFERENCE: the general question ("how many sources are really independent?") is not new. The open question EP-002 tests is narrower: detecting **non-literal** derivation in free text at a useful false-positive rate.

---

## 10. corroborate-mcp: direct verification

Source read: `src/engine.js`, `src/text.js`, `src/sources.js`, `README.md` at commit `1da5f99` (latest commit 2026-07-29).

| Question | Answer | Basis |
|---|---|---|
| 1. How it groups sources | Greedy clustering: an article joins the first cluster whose **headline** token set has Jaccard ≥ 0.55 (`SIM_THRESHOLD`), after stop-word removal. Pre-dedup by domain + first 8 normalized title tokens | FACT — `engine.js`, `text.js` |
| 2. Signals used | Headline tokens; domain; a fixed wire-domain list (AP, Reuters, AFP, UPI); publication times (only to add a "cascade" note); agreement across search engines (only for confidence) | FACT — `engine.js` |
| 3. Paraphrase | Not handled beyond lexical overlap of headlines | FACT (code); README: *"Independent rewrites of one wire story can occasionally slip clustering"* |
| 4. Summary | Not handled; body text is never fetched (*"headline-level"*) | FACT — README "Honest limitations" |
| 5. AI rewrite | Not handled; no semantic or LLM component (*"No LLM in the loop"*) | FACT — README, code |
| 6. Compositional reuse | Not handled; each article belongs to exactly one cluster | FACT — `engine.js` |
| 7. Similarity vs derivation | Does not separate them; lexical headline similarity is used as the proxy for shared origin | FACT (code) / INFERENCE (interpretation) |
| 8. Reusable code | Yes: `assess()` is a pure, network-free function over pre-fetched articles; MIT licence | FACT — `engine.js` comment and code |
| 9. Documented limits | No stance detection (6/6 distorted claims falsely CONFIRMED in its own benchmark); English and headline-level only; recency window; possible over/under-clustering of rewrites | FACT — README |

**Verdict: NOT a KILL.** corroborate-mcp addresses claim-level corroboration using headline lexical clustering. It does not attempt non-literal derivation detection in body text, which is the EP-002 question. It is included as baseline **B4** and not reimplemented beyond its published clustering rule.

---

## 11. Scope

In scope: dataset generator, automated checks, baselines, candidate methods, evaluation, report.

Out of scope: SDK, product, UI, API, deployment, genealogy/direction of derivation, real-world data (reserved for EP-003), the full Epistemic Layer architecture.

Pipeline: `dataset → checks → baselines → candidates (dev) → freeze → evaluation (test) → report`.

---

## 12. Reproducibility and time box

- All random processes seeded; seeds in a versioned config file.
- Generated dataset frozen as versioned JSONL with a content hash; **all LLM outputs cached and committed**, so evaluation can be re-run without regenerating text.
- Exact model names, versions and generation parameters recorded per document.
- Config, prompts (including the 3 paraphrases), thresholds and the label-word list are versioned and frozen before the test run.
- Results (raw predictions, metrics, CIs) saved under a results directory.
- **Single command** to reproduce the evaluation from the frozen dataset, documented in the report. Re-running must not depend on any conversation history.
- **Time box: 2 weeks** from approval. If no result in either direction by then: STOP, report as inconclusive with reasons.

---

## 13. Open questions for review

1. **Budget.** Multi-model generation and the frontier sample of B5 need a small API spend. If the budget is strictly zero, everything runs on local open models, with a weaker generator diversity (C8) and no frontier comparison. Decision needed.
2. **Hidden dependence between generator models.** Different models trained on overlapping data may share phrasing for the same facts. Is stratifying by generator (C8) enough, or is an extra control needed?
3. **Margins.** Are 0.20 (recall gain), 10% (FPR operating point), 5 points (case I) and the cost bounds acceptable? They must be agreed **before** the run.
4. **Size.** Is 40 events (20 test) enough for the CI to be informative? A power estimate can be done on dev before freezing.

---

## Summary for readers of the repository
1. **Why EP-001 was stopped:** it measured near-identical lexical overlap; it detected no summaries or rewrites, and its dataset had a light-edit bug, label leakage and mostly trivial negatives (§1).
2. **What EP-002 tests:** whether non-literal derivation can be detected substantially better than lexical baselines without merging genuinely independent sources (§2).
3. **Non-literal derivation:** B was produced using A, but with different wording — summary, rewrite, paraphrase, composition, chain (§3–4).
4. **Prior art:** the general question is not new; corroborate-mcp and others work at the lexical or headline level (§9–10).
5. **Baselines:** fixed in §6.1, including a plain LLM prompt.
6. **Data:** fictional events, multiple generator models, controlled information flow (§4).
7. **Ground truth:** the recorded information-flow graph (§4.3).
8. **Metrics:** per-case recall and per-case false positives on same-event pairs, with event-level bootstrap CIs (§7).
9. **SUCCESS:** §8.2. **KILL:** §8.3.
