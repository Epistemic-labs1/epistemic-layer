# EP-002 — Non-literal Derivation Detection: Experimental Specification

| | |
|---|---|
| Status | **DRAFT — v0.3 written for final review. NOT frozen. No implementation, no dataset, no benchmark run until the specification is explicitly approved and frozen.** |
| Version | 0.3 (2026-10-02) — see Changelog at the end |
| Supersedes | EP-001 (Evidence Independence Baseline) as the active experiment |
| Process | HYPOTHESIS → PRIOR ART → **SPECIFICATION** → REVIEW → EXPERIMENT → RESULTS → KILL / CONTINUE |

Evidence labels used throughout:
**FACT** (verified by running code or reading a primary source), **EVIDENCE** (observed signal, not proof), **INFERENCE** (reasoning from facts), **SPECULATION** (unverified guess). Where a source was seen only as a search-result snippet, this is stated.

This document does not assume the hypothesis is true. Its purpose is to make the hypothesis falsifiable and to fix the success and kill criteria before any result is seen. Constants that do not follow logically from the design are listed, with their status, in §11.

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

At threshold **0.7**: **TP = 15, FP = 0, FN = 35, TN = 385** (precision 1.00, recall 0.30). Results at 0.6 are identical. `pytest` on the EP-001 branch: 12 passed.

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
5. **Document-type confound (identified during EP-002 review).** In EP-001 every dependent document is a *transformed* text and every independent document is an *untransformed* one. A detector can score "this text was transformed" instead of "these two texts share an origin". EP-002 §5 is designed to remove this confound.

### 1.6 Class overlap (FACT — Jaccard to the `original`)
| Relation | Label | Jaccard range |
|---|---|---|
| ai_rewrite | dependent | 0.17 – 0.28 |
| independent | independent | 0.25 – 0.50 |
| summary | dependent | 0.35 – 0.58 |

Independent reports are lexically *closer* to the original than AI rewrites derived from it. No threshold separates the classes.

### 1.7 Conclusion (INFERENCE)
EP-001 measures **near-identical lexical overlap**, not evidence independence. Its result neither supports nor refutes the Epistemic Layer hypothesis; the benchmark could not test it. The code itself correctly describes Jaccard as a "triage signal, not proof of shared provenance". EP-001 is retained as the source of the failure mode EP-002 targets and as baseline B1.

---

## 2. Scope and claims

### 2.1 What EP-002 measures
EP-002 measures **independence of origin with respect to the complete, recorded provenance graph of a synthetic benchmark**. It does **not** measure absolute epistemic independence in the real world.

Formally, the label of a pair is a function of the generation graph only (§3.2). If two documents A and B derive from a source X that is **not a node of the graph**, then A ← X → B is invisible to the benchmark and the pair is labelled INDEPENDENT_ORIGIN even though, in the world, they share an origin. EP-002 does not attempt to solve this problem. It is a declared limitation and it determines what a success may be used for (§2.3).

### 2.2 Closure rule
Every text that is used as input to any generation step must itself be a node of the graph (including auxiliary and later-excluded documents). A document excluded from evaluation (§5.6) keeps its node; only its pairs leave the evaluation. A check (C12, §6) audits generation prompts for undeclared inputs.

### 2.3 What a success authorises
A success on EP-002 authorises **only** EP-003 (real-world data, e.g. an agency copy and its republications, where the common source is observable and the ground-truth protocol is different). It does not authorise an SDK, a product, an API, or any claim about real-world independence.

### 2.4 Out of scope
SDK, product, UI, API, deployment; direction of derivation (who copied whom) and full genealogy beyond the categories of §3.2; real-world data (EP-003); sources not observed in the graph; the full Epistemic Layer architecture. A declaration that the idea is valid because a benchmark can be built is explicitly not a result.

---

## 3. Task definition

### 3.1 Three distinct relations between two texts A and B
| Relation | Meaning | Observable from text alone? |
|---|---|---|
| **Similarity** | A and B say similar things (lexically or semantically) | Yes |
| **Derivation** | B was produced using A (directly or through intermediaries, in whole or in part) | Sometimes |
| **Shared origin / independence** | A and B descend from a common source document, or one from the other, versus no common source document | Only indirectly |

Similarity ≠ derivation ≠ origin-independence:
- A and B can be **highly similar yet independent**: two reporters observe the same event and write nearly the same sentence.
- A and B can be **dissimilar yet dependent**: B is a 100-word summary or an AI rewrite of a 1,000-word A.
- Two derivatives C and D of the same ORIG are **not derived from each other but do not count as two origins**.

### 3.2 Primary task: independence of origin
For each event there is a directed graph over its documents. There is an edge u → v **if and only if the exact text of u, or a deterministic function of it, was in the generation context of v** (prompt, tool input, or any other input). Nothing else creates an edge: not similarity, not shared facts, not the same model, not a shared prompt template, not the world event itself. A **root** is a document produced from an observation set only (no incoming edge). Anc(v) is the set of ancestors of v including v itself.

For a pair (u, v):

| Category | Condition | Primary label |
|---|---|---|
| DIRECT_DERIVATION | edge u → v or v → u | dependent |
| INDIRECT_DERIVATION | u is an ancestor of v (or conversely) through a path of length ≥ 2, no direct edge | dependent |
| SHARED_ORIGIN_NO_DIRECT_FLOW | neither is an ancestor of the other, but Anc(u) ∩ Anc(v) ≠ ∅ | dependent |
| INDEPENDENT_ORIGIN | Anc(u) ∩ Anc(v) = ∅ | independent |

**Primary label:** `dependent` iff Anc(u) ∩ Anc(v) ≠ ∅. The world event (the structured event record) is **not** an origin; only a document is. Sharing facts about the same event does not create dependence.

The relation is **not transitive** (a composed document F built from ORIG and P makes F dependent on both while ORIG and P stay independent). This is intended and is used as a diagnostic (§8.6).

### 3.3 Secondary task: information-flow diagnostic
The same graph yields a second label, `ancestry`: dependent iff the category is DIRECT or INDIRECT. It differs from the primary label only on SHARED_ORIGIN pairs. It is **diagnostic only, with no pass/fail role**: recall of the primary detector is reported per category (§8.6). Direction and genealogy remain out of scope.

### 3.4 Operational definition of "non-literal derivation"
B derives from A iff the graph contains a path A ⇝ B. A derivation is **non-literal** if B is neither an exact copy of A nor a light edit of A (≤ 10% of tokens changed). The graph is the truth; the amount of content that survives is a covariate, never a reason to relabel.

| Situation | Label | Treatment |
|---|---|---|
| B keeps only some facts of A | derived | fraction of A's unique details retained is measured by exact match of fictional tokens; recall is reported per retention bin |
| B adds its own facts | derived | number of invented facts recorded; label unchanged |
| B drops the distinctive details of A | derived | reported as the "zero retention" stratum, the hardest stratum |
| B combines A with another document | derived from both | two incoming edges |
| B passes through several transformations | INDIRECT (path ≥ 2) | maximum depth 2 in EP-002 |
| B is semantically similar but generated without A's text | INDEPENDENT_ORIGIN | similarity creates no edge |
| B uses the same world facts but not the text of A | INDEPENDENT_ORIGIN | facts come from the event record, never from a document |

### 3.5 Ground truth is not detector input
The graph is known to the benchmark and is used **only** to score methods. The relation must be inferred **exclusively from the two document texts**. That a generation process knows A → B does not prove that an outside observer can infer it from A and B; that inference is what is being tested. Consequently a detector receives nothing but the two texts (headline included, being part of the text): no metadata, no generator model, no class label, no provenance, no ID, filename, timestamp or position that encodes any of these (C2, C9, C13).

---

## 4. Hypotheses

**H0.** On the reference dataset, no tested method detects dependent pairs better than the best baseline by at least the minimum effect of interest (0.20 absolute in non-literal recall at equal false-positive rate), without the controlled increase in false positives defined in §9.

**H1.** The primary candidate, selected on the development split and then frozen, meets the success criteria S-a to S-f of §9 on the held-out test split: it detects a substantially larger share of non-literal dependent pairs — summaries, rewrites, paraphrases, compositions, chains and the sibling pairs between them — than **each** baseline including a simple LLM judge, at the same false-positive rate, **without an unacceptable increase in false positives on genuinely independent sources**.

The method is **not** chosen in advance. Candidates are explored on the development split only (§7.2).

---

## 5. Dataset

### 5.1 Why EP-001's construction cannot be reused
If a single author (human or one LLM) writes both the original and the "independent" sources, those sources share model, style and prior knowledge, and a detector can learn style. If dependent documents are always transformed texts and independent documents are always untransformed ones, a detector can learn "was this text transformed" (§1.5.5). The design below addresses both: several generator families, randomized and balanced assignment, and **two parallel lineages per event with the same transformations** so that the label depends on lineage membership and not on document type.

### 5.2 Events
Each event is a structured record of **fictional** facts: a core fact set K, per-reporter unique details U_r, an ordering plan for facts, an event claim string, and a closed list of style identifiers. Fictional = no model has prior knowledge of it. **All entity names, numbers and quotes are ASCII alphanumeric** (the title normalizer of baseline B4 deletes any other character and would split or corrupt names). Fact tokens are exact strings so that fact presence in a text can be determined by exact match, without a model.

Proposed defaults, frozen at stage 1 (§10.2, §15): |K| = 8; |U_r| = 4 unique details per reporter, one of which is an idiosyncratic error (a wrong number); root length 150–250 words; summary length ≤ 30% of its source. These generative parameters set the difficulty of the task and are therefore frozen **before the first dev document is generated**; they may be changed only through the pre-registered knobs of §5.6.

### 5.3 Documents per event: 17, two lineages
- **Roots (6):** ORIG, H, I1, I2, I3, P (P is an auxiliary root used only as the composition partner of F).
- **Lineage X (from ORIG), 7 derived:** A (exact copy), B (light edit), C (summary), D (rewrite), E (sentence-by-sentence paraphrase), F (composition of ORIG and P), G (rewrite of D; chain ORIG → D → G).
- **Lineage Y (from H), 4 derived, same transformations:** C_y (summary of H), D_y (rewrite of H), E_y (paraphrase of H), G_y (rewrite of D_y).

Every document has a headline (first line of the text).

### 5.4 Generation protocol

**Reporter inputs (roots).** A root is written by a reporter that receives **only**: (1) its observation set — facts with IDs, in the order given by its plan; (2) a style identifier from the closed list in the configuration, chosen *a priori* and never extracted from any text; (3) a length target. A reporter never receives the text of any other document, nor any text derived from another document. Few-shot examples, if used, come from a separate pool of events that belongs to neither the dev nor the test split.

| Root | Facts received | Order plan | Style id |
|---|---|---|---|
| ORIG | K ∪ U_ORIG | its own | random |
| H | K ∪ U_H | its own | random |
| I1 (similar wording) | K ∪ **U_ORIG** (same unique details: both reporters were present) | its own | **same id as ORIG** |
| I2 (same facts, different wording) | K ∪ U_I2 | its own | **different id from ORIG** |
| I3 (same facts, same structure) | K ∪ U_I3 | **the order plan assigned to ORIG in the record** (not extracted from ORIG's text) | random |
| P | K ∪ U_P | its own | random |

I1–I3 test that "same facts" or "same register" is not read as "same source". The I1 instruction is artificial and may not mirror real reporters (declared limitation); I2 and I3 are added so that the result does not depend on a single instruction.

**Derived documents.** A derived document is written by a process that receives the **text** of its source(s): A (copy, verbatim including headline), B (deterministic seeded script changing at least one and at most 10% of tokens), C/C_y (LLM summary), D/D_y (LLM rewrite), E/E_y (LLM paraphrase preserving sentence structure), F (LLM composition of ORIG and P), G/G_y (LLM rewrite of D/D_y). Prompts are fixed templates stored in the configuration. Derivation prompts are **not** told to keep or to drop unique details.

**Generators and assignment.** At least three generator model families (open-weight, local in the primary configuration). Each document's generator and style id are assigned by a **blocked, randomized, balanced** algorithm per event, recorded in an assignment table that is checked **before any text is generated** (C14). The rewrite case D is no longer constrained to a "different model": generator choice is randomized for every case so that "same generator" does not predict dependence. Every prompt, raw output, model name, version and parameter set is cached and committed.

**Context audit.** Every generation prompt is logged. A check (C12) scans it for n-grams of at least 8 tokens from any document that is not declared as input, and fails on any match.

### 5.5 Pair classes, cells and roles
The **primary document set S** has 14 documents: all roots except P, and all derived documents except the literal ones A and B (A and B are near-duplicates of ORIG and would pseudo-replicate its pairs). S has 91 pairs. Within S the primary relation is an equivalence relation (P is outside S), with exactly **5 origins** per event: ORIG, H, I1, I2, I3.

R = root, D = derived (non-literal). Counts are per event.

| # | Class | Pairs | Label / category | Role |
|---|---|---|---|---|
| PC1 | R–D, same lineage, direct | 7 | dependent / DIRECT (ORIG–C,D,E,F; H–C_y,D_y,E_y) | **primary positive (cell R–D)** |
| PC2 | R–D, same lineage, indirect | 2 | dependent / INDIRECT (ORIG–G; H–G_y) | **primary positive (cell R–D)** |
| PC3 | D–D, same lineage, direct | 2 | dependent / DIRECT (D–G; D_y–G_y) | **primary positive (cell D–D)** |
| PC4 | D–D, same lineage, siblings | 14 | dependent / SHARED_ORIGIN | **primary positive (cell D–D)** |
| PC5 | R–D, different lineages | 36 | independent | **primary negative (cell R–D)** |
| PC6 | D–D, different lineages | 20 | independent | **primary negative (cell D–D)** |
| PC7 | R–R (ORIG, H, I1, I2, I3) | 10 | independent | guard negatives; no positive exists in this cell |
| PC8 | pairs with A or B, same lineage | 13 | dependent | diagnostic (literal sanity) |
| PC9 | pairs with A or B, different lineage | 16 | independent | diagnostic |
| PC10 | (P, F) | 1 | dependent / DIRECT | diagnostic |
| PC11 | other pairs with P | 15 | independent (incl. (ORIG, P): the bridge case) | diagnostic |
| — | pairs with an excluded document; cross-event pairs | — | — | **excluded** from the primary metrics; cross-event pairs are reported in a separate table |

Total per event: 7+2+2+14+36+20+10+13+16+1+15 = 136 = C(17,2).

**Cells.** Primary metrics are computed **within cells** and then combined with fixed weights, so that a detector cannot gain from knowing whether a text is a root or a derivative:
- Cell R–D: 9 positives (PC1+PC2), 36 negatives (PC5).
- Cell D–D: 16 positives (PC3+PC4), 20 negatives (PC6).
- **Weights** (derived from the design, frozen): w_RD = 9/25 = 0.36, w_DD = 16/25 = 0.64.
- recall_w = 0.36·recall(R–D) + 0.64·recall(D–D); FPR_w = 0.36·FPR(R–D) + 0.64·FPR(D–D). Per-event values are averaged with equal weight over events.

**Named negative sets.** For each case k ∈ {H, I1, I2, I3}: N_k = pairs of the root k with {ORIG, C, D, E, F, G} (6 pairs per event: 1 in PC7, 5 in PC5). These are the hard-negative sets used by S-d.

### 5.6 Exclusions, ledger and regeneration
A pair is excluded (logged and counted) if generation failed, refused or produced off-topic or wrong-language output; if a derived text is identical to its source when the case requires a change; or if the flow log of either document is missing or inconsistent. If more than 10% of an event's documents are excluded, the event is excluded. If more than 10% of events are excluded, the dataset is regenerated with the cause documented; it is not silently patched.

**Generation ledger** (versioned): attempt number, seed, generation-code version, configuration hash, discarded datasets and the reason for each discard.

**No opportunistic regeneration.** At most **one** regeneration of the dev split is allowed, and only for a failure of a pre-registered validity check (C1–C3, C6, C7, C12, C14, C15) — never for the performance of any method on the test split. A second failure ends the experiment (K8). C11 (headroom) failure does **not** permit regeneration: making the dataset more fact-identifiable would be tuning towards the hypothesis; it ends the experiment.

**Pre-registered knobs** (the only parameters a regeneration may change; the change applies to all subsequent events, dev and test):
1. On a C7 (difficulty floor) failure: use the second, pre-written, stronger-rewording prompt template for D/E (template R2), and/or lower the summary length bound from 30% to 15%.
2. On a C6 (confound) or C14 (balance) failure: draw a new assignment seed; no change to content parameters.

Mechanical single-document repairs on the test split (C1–C3, C12, C15) are allowed, logged, and never made after looking at any method's result.

### 5.7 Splits and order of phases
Split **by event** (no event appears in both splits). The order is fixed (§15): the dev split is generated and validated first; the primary candidate and every threshold are then frozen; **only after the freeze is the test split generated**, with the frozen generation configuration and new seeds. The test split does not exist while methods are explored.

---

## 6. Checks

All gating checks run before any method is evaluated. A failure blocks evaluation. "Dev only" means the check is computed on the dev split.

| # | Check | Confounder it removes | Rule |
|---|---|---|---|
| C1 | Label words | label-revealing text | No document contains label-revealing terms (e.g. "independent", "separate", "copy", "summary", "rewrite", "paraphrase", "original", "according to [another document]"); list versioned; matches logged |
| C2 | Opaque identifiers and layout | class leaking through IDs, filenames, file order, timestamps, cache metadata, pair order | Random IDs; no class, lineage or generator name anywhere a method can read; pair order and document order randomized with seeds |
| C3 | Real transformations | no-op or out-of-bound derivations | Every derived case except A differs from its source; B within its edit bounds; C within its length bound |
| C4 | Pair-class reporting | pooling of unlike pairs | Primary metrics use only PC1–PC6; every class of §5.5 is reported separately |
| C5 | Split leakage | dev/test contamination | No event appears in both splits; thresholds, prompts and the primary candidate are frozen and tagged before the test split is generated; the test split is generated only after the freeze (§5.7) |
| C6 | Surface confound classifier (dev only) | stylistic/length signal that alone separates classes | A pair-level classifier on surface features (length, length ratio, TF-IDF of each single text), trained **within each cell** with event-grouped cross-validation, must have recall_w at FPR_w = 10% **below the best of B1, B2, B3, B4-tuned plus 0.20**; otherwise the dataset is confounded |
| C7 | Difficulty floor (dev only) | a dataset too easy to test H1 | If the best of B1, B2, B3, B4-tuned reaches recall_w ≥ 0.8 at FPR_w = 10% on dev, the dataset is invalid |
| C8 | Detector/generator separation | an LLM detector recognising its own style or priors | In the primary configuration the detector model family is **not** among the generator families. If that is impossible, results are stratified by whether the detector family generated a document of the pair and the limitation is stated |
| C9 | Detector isolation | provenance metadata reaching the detector | Methods receive **only the two texts**. The harness strips and withholds metadata, generator, class labels, provenance, and IDs; the information-flow graph is loaded only by the scoring step. A test confirms a method cannot read these fields. An LLM-based method is shown only the two texts and its own fixed prompt |
| C10 | Selection independence | benchmark construction leaking from the baselines | No pair is selected, excluded or stratified using a similarity score computed by any evaluated method or baseline. Strata are defined by generation case only |
| C11 | Headroom (dev only) | a task where success is impossible by construction | headroom = recall_w(O1) − best baseline recall_w, at FPR_w = 10% on dev, with O1 evaluated out-of-sample (§7.4); must be ≥ 0.20. It is a necessary condition, not a sufficient one |
| C12 | Context audit | accidental edges that falsify the graph | No generation prompt contains an n-gram of 8 or more tokens from a document that is not a declared input |
| C13 | Score purity | within-event normalization or corpus statistics exploiting constant event composition and prevalence | The score of a pair depends only on the two texts and on parameters frozen on dev. Test: the score of a pair computed standalone is identical to its score computed inside the full event. Set-level methods must be declared **before** the test; B4-faithful and B4-core are set-level by construction and are the declared exception |
| C14 | Assignment balance (design time) | "same generator" or "same style id" predicting the label | On the assignment table, before generation: within each cell the rate of same-generator and of same-style-id pairs differs between positives and negatives by at most 0.05 (exactly 0 where blocked randomization allows). Both same-generator and cross-generator strata contain at least 30% of the negatives |
| C15 | Boilerplate | format artefacts that reveal the class | No document contains LLM boilerplate ("Here is", "Sure", "As an AI", markdown headings, "Summary:"); offending documents are regenerated mechanically and logged |

**Reported diagnostics (no pass/fail role):**
D1 single-text probe predicting "is derived" (document-type signal, neutralized by the cell design); D2 probe predicting the generator family from a single text; D3 FPR on same-generator versus cross-generator independent pairs; D4 unique-detail masking (§8.6); D5 recall by information-flow category; D6 bridge merge rate; D7 partition metrics and origin-count error; D8 recall by retention bin (fraction of the source's unique details retained, and number of invented facts, by exact match); D9 reference R1 (§7.4).

---

## 7. Methods

### 7.1 Baselines — fixed now, before any result
| ID | Baseline | Definition |
|---|---|---|
| B0 | Surface control | length ratio only; expected to fail; a control, never compared in S |
| B1 | Token Jaccard | EP-001 implementation, unchanged, on the full text including the headline |
| B2 | TF-IDF cosine | word unigrams and bigrams, IDF fitted on the dev split only |
| B3 | Sentence-embedding cosine | one pinned open-source embedding model (name and version in the configuration); document vector = mean of its sentence vectors |
| B4-faithful | corroborate-mcp `assess()`, unmodified | the original function run by Node at commit `1da5f99`, with inputs adapted (§13.3). Native output only: `n_independent_sources` and the cluster-size multiset. Used for the **origin-count** metric (§8.5), never converted into pairwise scores |
| B4-core | corroborate-mcp clustering loop with membership exposed | the original `normTitle`, `jaccard`, `coreTokens` and `relevance` imported from the original `text.js`; the clustering loop of `engine.js` lines 52–58 reproduced verbatim in a harness that returns cluster membership; conformance-tested against B4-faithful (§13.3). Used for co-membership and partition metrics at its native threshold 0.55 |
| B4-tuned | B4-core, relevance gate off, threshold swept | same clustering rule, threshold chosen on dev as the setting with the highest recall_w subject to FPR_w ≤ 10%; the setting sequence is the threshold grid. Reported separately; never presented as corroborate-mcp |
| B5-score | Simple LLM judge, scored | one direct prompt, fixed wording, local open model (§7.3) |
| B5-verdict | Simple LLM judge, raw verdict | the same prompt answered yes / no / uncertain; qualitative kill-test form (§7.3) |

Thresholds for B1, B2, B3, B5-score and the candidate are chosen on the **dev split**: the **lowest cutoff** at which FPR_w ≤ 0.10, then frozen. B4-faithful and B4-core use their original threshold 0.55 and are never tuned.

### 7.2 Candidate methods — explored on dev only, none assumed
Candidates may be: semantic similarity variants; claim overlap; entity/event overlap; unique-detail overlap; structured LLM-based signals; combinations. Rules:

1. **At most K = 10 variants** in total for the candidate family on the dev split, counted jointly across all candidate designs. The same K = 10 applies to every other family that requires tuning (B5: prompt variants). B1, B3 and B4 have no tunable variants; B2 and B3 configurations are fixed in §7.1. A threshold choice is not a variant. The 3 prompt paraphrases of §8.7 are written before exploration and do not count.
2. **Every variant tried is recorded** (design, hash, dev result) in a versioned variant ledger. **After the freeze no further variant is allowed.**
3. A variant that learns parameters from labelled dev pairs is scored by event-grouped cross-validation on dev (K_folds = 5, repeated 10 times, as for O1) and then refit on all dev data; its in-sample dev score is never used for selection.
4. **One primary candidate** is selected on dev: the variant with the highest recall_w at FPR_w = 10% (out-of-fold where applicable); ties go to the cheaper variant. It is frozen — together with its threshold, prompts, features and parameters — with a git tag and a content hash.
5. Other candidates are **secondary**: they may be evaluated once on test and reported, but **cannot declare success**. If a secondary candidate would have succeeded where the primary did not, the consequence is a new pre-registered round, not a success.

### 7.3 B5 in detail
- **Prompt (symmetric).** "Do these two texts originate from a common source text — that is, is one derived from the other, or are both derived from a third text? Answer yes or no." Three pre-written paraphrases of the same question are fixed before exploration. (The earlier "was B produced using A?" question is directional and cannot express the sibling case.)
- **B5-score.** Score = log P("yes") − log P("no") of the first answer token, from the local model. If the runtime does not expose token log-probabilities, the fallback score is the fraction of "yes" over 8 samples at a fixed non-zero temperature; the stage-1 pilot (§10.8) must verify which of the two is available. "uncertain" is not an option in this form.
- **Pair direction.** Each pair is scored in both orders and the two scores are averaged; order is seeded.
- **B5-verdict.** The three-way answer with the same prompt; "uncertain" counts as "not dependent" (conservative for FPR); the opposite mapping is reported alongside. No threshold is applicable; it is a qualitative kill test, not an input of the statistical comparison.
- **Same input as all methods.** The same two texts, with headlines, and the same token limit.
- **Model.** One pinned local open-weight model (name, version, quantization in the configuration). If the candidate is LLM-based it uses the same model, for parity.
- **Tuning budget.** Up to K = 10 prompt variants on dev, logged, as for the candidate.
- **If B5 cannot be turned into a comparable score without giving it an artificial advantage** it is declared so, remains a qualitative kill test, and the comparison S-b is evaluated against the other baselines only.

### 7.4 Oracle O1 and reference R1 (dev only)
**Purpose:** a ceiling for what is identifiable from fact content, so that "no improvement" is not misread as a method failure when the task is not identifiable. The oracle is **never evaluated on the test split, and is never used to select or to evaluate anything on test**.

- **O1 features** (fixed list, computed by exact match of fictional tokens, none using wording): Jaccard of the sets of fact IDs present; number of shared unique details; number of unique details in the union; agreement in the order of shared facts (Kendall tau); number of shared idiosyncratic errors.
- **Model:** logistic regression, L2 regularization with fixed strength, standardized features; a separate model per cell. No hyperparameter search.
- **Validation:** event-grouped cross-validation on dev (5 folds, repeated 10 times with different fold assignments); every pair's score is the mean of its out-of-fold scores, so no prediction is made on an event that contributed to training.
- **Operating point:** on the pooled out-of-fold scores, the lowest cutoff with FPR_w ≤ 0.10. (A single threshold parameter fitted on dev, as for the baselines; the residual optimism is symmetric and, for the baselines, favours them, which makes C11 conservative.)
- **recall_w and FPR_w** as in §5.5, event-macro averaged; the bootstrap CI is over events on the out-of-fold scores (it ignores training variability; stated).
- **C11:** headroom = recall_w(O1) − max over {B1, B2, B3, B4-tuned, B5-score} of recall_w at FPR_w = 10% on dev. Pass if the point estimate is ≥ 0.20 (the effect of interest). A failure ends the experiment (§5.6).
- **Reference R1:** the same procedure with all text features of the pair. R1 is **not** an oracle (it can learn dataset artefacts) and has no gate role; if R1 is far above O1, the signal beyond fact content is flagged for review.

### 7.5 Score purity (C13)
Pairwise methods must produce a pair's score from the two texts and from parameters frozen on dev only. Within-event rank or z-score normalization, corpus statistics fitted on test documents, and any use of other documents of the test event are forbidden. Set-level methods are allowed only if declared before the test; B4-faithful and B4-core are the declared exceptions, and their comparability is limited accordingly (§13.4).

### 7.6 Frontier exception (external-validity control)
A single frontier model is used for one control, on a **fixed subset of the test split**: the first min(10, N_test) test events, in the seeded generation order, **defined before the test is generated**. It runs B5-score and, if the primary candidate is LLM-based, the candidate with the frontier model substituted, without any change of prompt or threshold. It is **reported separately**. It does not enter the statistical test, cannot change any threshold, the candidate, the dataset or any criterion, and **a frontier result cannot turn a failed experiment into a success**. It is required to be reported before a success is used to authorise EP-003.

---

## 8. Metrics and estimators

### 8.1 Primary population
Same-event pairs of the **test** split in the cells of §5.5 (PC1–PC6), with the exclusions of §5.6. Per-event recall_w and FPR_w are computed as in §5.5 and averaged with equal weight over events.

### 8.2 Operating points
- **Primary comparison — equal FPR.** All methods that produce an ordered family of settings (a score or a threshold grid) are compared at the operating point **FPR_w = 10%** on the test split: the setting with the highest recall_w subject to FPR_w ≤ 0.10. This uses the test labels only to place each method at the same false-positive rate, which is an evaluation-time matching symmetric across methods; no parameter of any method is changed.
- **Frozen-threshold analysis — safety guard.** Each method is also evaluated at the threshold frozen on dev. For the candidate this yields the guard of S-c. Recall differences at frozen thresholds are reported as a secondary analysis.
- Sensitivity: results are also reported at FPR_w = 5% and 20%.
- B4-core at its native 0.55, B4-faithful and B5-verdict have no setting sequence; they are reported at their native point and are not part of the equal-FPR comparison.

### 8.3 Reported for every method
Recall_w, FPR_w, precision and F1 (these depend on the constructed prevalence and are not transferable to the real world); recall for every positive class PC1–PC4 and for the categories DIRECT, INDIRECT, SHARED_ORIGIN; FPR for PC5, PC6 and PC7; FPR for each N_k (k = H, I1, I2, I3); the diagnostic classes PC8–PC11; cross-event pairs in a separate table.

### 8.4 Uncertainty and paired bootstrap
- 95% percentile confidence intervals by **paired bootstrap resampling of events** (10,000 resamples, fixed seed). In each replicate the same resampled events are used for both methods of a difference, and **the equal-FPR operating point is recomputed inside every replicate** for each method.
- Non-deterministic methods are run 5 times; the per-pair score is the mean of the 5 runs, and the range of the metrics is reported.

### 8.5 Partition metrics and origin count
Within S the truth is a partition with 5 origins. Reported (D7): the **origin-count error** `n_pred − 5` (signed: positive means missed dependence) and its absolute value; B-cubed precision and recall; adjusted Rand index. B4-faithful provides the count natively. Every other method is reduced to a partition by one fixed rule: connected components of the graph of pairs it predicts dependent at its frozen-threshold operating point. The information lost in that reduction (one false positive can merge two clusters) is stated, and partition metrics are secondary.

### 8.6 Diagnostics
- **Information-flow categories (D5):** recall of the primary detector for DIRECT, INDIRECT and SHARED_ORIGIN pairs; no pass/fail.
- **Bridge (D6):** on the diagnostic classes, how often a method predicts (ORIG, P) dependent although both are ancestors of F.
- **Unique-detail masking (D4):** the frozen primary candidate and the frozen baselines are evaluated on a deterministic masked copy of the test split in which every token of a fact designated as a unique detail (exact fictional string) is replaced by a neutral placeholder. **No pass/fail role.** It shows whether a result depends artificially on the way unique details are built into the dataset. No parameter is re-tuned.
- **Retention (D8):** recall per bin of retained unique details.

### 8.7 Prompt robustness
Every LLM-based method (candidate if LLM-based, and B5) is run with its main prompt and with 3 pre-written paraphrases of it. Thresholds are re-fitted on dev for each paraphrase and frozen. Success criteria are evaluated **separately for each of the four formulations** and success requires all four (§9). Prompts are written before exploration.

---

## 9. Success, kill and inconclusive criteria — fixed before the experiment

All statements refer to the **primary candidate** P and to the baseline set 𝔅 = {B1, B2, B3, B4-tuned, B5-score}. Δ_X = recall_w(P) − recall_w(X) at equal FPR_w = 10% on test, with the paired event bootstrap of §8.4; LB and UB are the 2.5th and 97.5th percentiles.

### 9.1 SUCCESS (H1 supported on synthetic data) — all must hold
- **S-a Validity.** Checks C1–C15 passed (C11 = headroom, on dev).
- **S-b Recall (criterion S1).** For **every** X ∈ 𝔅: Δ̂_X ≥ 0.20 **and** LB(Δ_X) > 0. The value 0.20 is the minimum effect of interest and is frozen before the dataset is generated.
- **S-c FPR guard.** FPR_w(P) at its **dev-frozen threshold** on test is ≤ 0.15 (the operating point plus a 5-point tolerance). This is a safety guard; the scientific comparison is the equal-FPR comparison of S-b.
- **S-d Hard negatives (non-inferiority).** For each k ∈ {I1, I2, I3}, at the equal-FPR operating point, UB of the paired difference FPR_k(P) − FPR_k(R*) is ≤ +0.05, where R* is the baseline with the highest recall_w at equal FPR on dev, designated on dev before the freeze.
- **S-e Robustness.** S-b to S-d hold for each of the four prompt formulations (§8.7), when P or B5 is LLM-based.
- **S-f Cost.** Measured on a fixed random sample of 200 dev pairs: ≤ 2 seconds per pair on a single consumer machine, **or** ≤ USD 0.01 per pair through an API.

### 9.2 KILL — any one is sufficient (and N_test meets the power rule, §10.6)
Each kill criterion is the demonstrated opposite of a success criterion, so that an uncertain result is inconclusive rather than a kill.
- **K1 No margin over a similarity baseline.** For some X ∈ {B1, B2, B3, B4-tuned}: UB(Δ_X) < 0.20.
- **K2 A prompt is enough.** For B5-score: UB(Δ_B5) < 0.20. (The local-model caveat of §14 applies.)
- **K3 False positives.** FPR_w(P) at its frozen threshold has LB(95%) > 0.15, or for some k the LB of FPR_k(P) − FPR_k(R*) is > +0.05.
- **K4 No separation of hard negatives.** The AUC of P separating the positive cell R–D from the negative sets N_{I1}, N_{I2}, N_{I3}, restricted to the cell R–D, has a bootstrap CI that includes 0.5.
- **K5 Fragility.** K1–K4 are met under any of the four prompt formulations (§8.7).
- **K6 Cost.** The cost bounds of S-f cannot be met.
- **K7 Ground truth.** Ground truth cannot be produced reliably (§5.6 exclusion limits exceeded twice).
- **K8 Dataset validity.** The dataset fails C6, C7 or C11 and cannot be fixed within the one allowed regeneration and the time box.

Removed or merged relative to v0.2: the v0.2 criteria "B4 or another open-source system performs within the CI" and "B5 performs within the CI" are now K1 and K2; "within the CI" is operationalized as UB(Δ) < 0.20. See the Changelog.

### 9.3 INCONCLUSIVE
Neither 9.1 nor 9.2 is met within the time box (§15): reported as inconclusive with the reason. No criterion is relaxed, replaced or re-weighted after any result is seen.

### 9.4 INCONCLUSIVE-UNDERPOWERED
If the required N_test of §10.6 exceeds the operational limit, the outcome is labelled INCONCLUSIVE-UNDERPOWERED **whatever the observed statistics are**. Descriptive results may be reported, cannot authorise EP-003, and cannot trigger K1–K5. Criteria K6–K8 do not depend on power and remain in force. **No criterion is modified.**

### 9.5 What cannot change an outcome
The frontier control (§7.6), the unique-detail masking (D4), the information-flow diagnostics (D5), the secondary candidates, the secondary analysis at frozen thresholds, and every diagnostic of §6.

---

## 10. Sample size and power

### 10.1 Principles
N is not chosen "because it seems enough" and is never chosen after any test result. The decision rule S-b to S-d is a **joint** rule: its power is lower than that of each component and is simulated, not multiplied by hand. The observed effect of the candidate on dev is **never** used in a sample-size computation (it is inflated by selection).

### 10.2 Stage 1 — before any dev event is generated
Frozen with a git tag (`ep002-stage1`): the generative parameters of §5.2, α = 0.05 (two-sided CI 95%), target joint power 0.80, minimum effect of interest 0.20, the design alternative for the effect, the FPR tolerance and margin, the grid of §10.5, N_dev, the operational limit N_max, the rules of §10.6, and the constants of §11. The stage-1 planning step also records the planned N_test under each column of the grid and flags if the conservative column would exceed N_max − N_dev.

### 10.3 Stage 2 — after the freeze of the primary candidate, before the test is generated
N_test is computed by the rule of §10.6 using quantities **estimated on dev** and quantities that **stay pre-registered**:

| Estimated from dev at stage 2 | Pre-registered (never taken from dev) |
|---|---|
| σ̂_Δ,X: SD over dev events of the per-event recall_w difference between P and each X ∈ 𝔅, at equal FPR (out-of-fold scores for supervised variants) | α, target power, minimum effect of interest |
| σ̂_f: SD over dev events of the per-event paired FPR difference on N_k | design effect Δ_design = 0.25 (conservative column) |
| ρ̂_crit: mean correlation across events between the per-event statistics of the different criteria | true FPR offset on N_k = +0.02 (conservative column) |
| σ̂_g: SD over dev events of per-event FPR_w at the frozen threshold | the joint decision rule and the bootstrap procedure |

### 10.4 What the simulation does
Simulate N_test events by drawing per-event vectors (one recall difference per X ∈ 𝔅, one FPR difference per k, one frozen-threshold FPR_w) from a multivariate normal with means set to the design alternative, SDs and correlation as in §10.3, then apply the **actual** decision rule (paired bootstrap, S-b to S-d) to the simulated events, 2000 simulation replicates, and report the fraction of replicates in which all criteria hold. The rule has a built-in cap: because S-b requires Δ̂ ≥ 0.20, a true effect of exactly 0.20 gives at most 50% power on that criterion; therefore the design effect is above 0.20.

### 10.5 Sensitivity grid
The values below are **arbitrary assumptions about unknowns** — EP-001 provides no estimate of between-event variance — and are declared as such. The columns are a sensitivity analysis, not a choice of the most convenient N.

| Parameter | Conservative | Moderate | Optimistic |
|---|---|---|---|
| Design effect Δ_design (true recall gain over each baseline) | 0.25 | 0.30 | 0.40 |
| σ_Δ: between-event SD of the per-event recall difference | 0.20 | 0.15 | 0.10 |
| σ_f: between-event SD of the per-event paired FPR difference on N_k | 0.15 | 0.10 | 0.07 |
| True FPR offset of P versus R* on N_k | +0.02 | +0.01 | 0 |
| ρ_crit: correlation between the statistics of different criteria | 0 | 0.3 | 0.6 |

A back-of-envelope check (illustrative only, to be replaced by the simulation): for the non-inferiority criterion S-d alone, n ≈ (1.96·σ_f / (0.05 − offset))². With σ_f = 0.10 and offset 0, about 15 events; with σ_f = 0.15 and offset +0.02, about 96. The criterion on hard negatives is likely to be the one that fixes N, not the recall criterion.

### 10.6 Rule for N, and the operational limit
- **Binding rule.** N_test = the smallest N for which the simulated **joint power is ≥ 0.80** with Δ_design = 0.25, offset = +0.02, σ_Δ,used = max(σ̂_Δ, 0.15), σ_f,used = max(σ̂_f, 0.10), σ_g,used = σ̂_g, ρ_used = min(ρ̂_crit, 0.3).
- **N_dev ≥ 20 events** (minimum), set at stage 1.
- **Operational limit N_max.** A resource limit on the total N_dev + N_test, **provisionally 100 events for planning**; it is **not** a methodological parameter. It is fixed from the timing measured in the pilot (§10.8) and frozen at stage 1. If 100 turns out to be insufficient it is reported as an operational limit.
- **If N_test required > N_max − N_dev:** the outcome is INCONCLUSIVE-UNDERPOWERED (§9.4) and **no criterion is changed**.

### 10.7 Dev size
The dev split must yield enough negatives for threshold calibration: with 56 primary negatives per event, 20 events give 1,120 negatives (an indicative standard error of about one point at FPR 10%, ignoring event clustering). N_dev is not raised after seeing any result.

### 10.8 Pilot
A pilot of 3–5 events, **burned** (they never enter dev or test), is used **only** to verify the pipeline, verify the context audit and the other mechanical checks, measure generation and scoring times, identify mechanical errors, and verify whether the local model exposes token log-probabilities. It is **not** used to estimate the effect of any candidate, and not used to estimate variance.

---

## 11. Register of constants

Source: **MAT** = mathematical or logical consequence of the design; **MET** = methodological choice; **CONV** = statistical convention; **HYP** = empirical assumption about the world; **EXT** = inherited from an external source. "After dev" = may it be changed after seeing dev data.

| Constant | Needed? | Source | Arbitrary? | Frozen | After dev? |
|---|---|---|---|---|---|
| Minimum effect of interest 0.20 | yes | HYP (judgement) | yes | before power analysis and dataset | no |
| Operating point FPR_w = 10% | yes | MET (error-cost judgement) | yes | before dataset | no |
| Sensitivity points 5% and 20% | no | MET | yes | before dataset | reported only |
| FPR guard +5 points (FPR_w ≤ 15%) | yes | MET | yes | before dataset | no |
| Non-inferiority margin +5 points on N_k | yes | MET | yes | before dataset | no |
| α = 0.05; CI 95% | yes | CONV | by convention | before dataset | no |
| Target power 0.80 | yes | CONV | by convention | before dataset | no |
| Bootstrap resamples 10,000, seed | yes | MAT (Monte Carlo precision) | partly | before test | resamples may increase, seed not |
| Simulation replicates 2000 | yes | MAT | partly | stage 1 | may increase |
| K = 10 variants per tuning family | yes | MET | yes | before dev exploration | no |
| 3 prompt paraphrases | yes | MET | yes | before dev exploration | no |
| N_dev ≥ 20 | yes | MET (calibration precision) | partly | stage 1 | no |
| N_test | yes | **MAT** (rule of §10.6) | no, given the inputs | stage 2, before test generation | no |
| N_max (provisional 100) | yes | MET (resources) | yes | stage 1, after timing | no; reported if insufficient |
| Pilot events 3–5 | yes | MET | yes | stage 1 | no |
| Grid values (Δ_design, σ_Δ, σ_f, offset, ρ_crit) | yes | HYP about unknowns | **yes**, declared | stage 1 | no |
| Floors σ_Δ ≥ 0.15, σ_f ≥ 0.10, ρ ≤ 0.3 in the binding rule | yes | MET (conservative direction) | yes | stage 1 | no |
| Cell weights 9/25 and 16/25 | yes | **MAT** (positive counts per cell) | no | with the design | no |
| Headroom threshold 0.20 (C11) | yes | **MAT** (necessary condition derived from the effect of interest) | no | with the design | no |
| C6 rule "below best baseline + 0.20" | yes | MET (reuses the effect of interest) | partly | before dataset | no |
| C7 difficulty floor recall_w ≥ 0.8 | yes | MET (inherited) | yes | before dataset | no |
| C14 balance ≤ 0.05; strata ≥ 30% | yes | MET | yes (0 where exact) | before dataset | no |
| Oracle parameters (5 folds, 10 repeats, L2 strength, feature list) | yes | MET | yes | before dev generation | no |
| Context audit n-gram length 8 | yes | MET | yes | before dataset | no |
| Exclusion limits 10% of documents per event, 10% of events | yes | MET (inherited) | yes | before dataset | no |
| One regeneration of dev | yes | MET | yes | before dataset | no |
| Pre-registered knobs (§5.6) | yes | MET | yes | before dataset | no |
| Cost bounds 2 s or USD 0.01 per pair; timing sample of 200 pairs | yes | MET (judgement) | yes | before dataset | no |
| Generative parameters (|K| = 8, |U_r| = 4, one error per root, length 150–250 words, summary ≤ 30%, light edit ≤ 10%, chain depth 2, style list) | yes | HYP (they set difficulty) | yes | before dev generation | only via §5.6 knobs |
| Frontier subset: first 10 test events | yes | MET | yes | before test generation | no |
| B5 fallback of 8 samples | only if no log-probs | MET | yes | stage 1 | no |
| B4: 100 permutations; majority 50% | yes | MET | yes, harmless (negligible cost) | before dev | no |
| B4 threshold 0.55 | yes | **EXT** (corroborate-mcp `SIM_THRESHOLD`) | no | verified at commit `1da5f99` | no |
| Time box 2 weeks | yes | MET (resources) | yes | at approval | no |

---

## 12. Prior art (as verified on 2026-10-02)

| Work | What it does | Relevance | Label / how verified |
|---|---|---|---|
| **corroborate-mcp** (MIT, JavaScript; `chefcohen/corroborate-mcp`) | Counts "independent story origins" for a claim from news search results | Same stated goal at claim level; method in §13 | **FACT** — source code read at commit `1da5f99` (2026-07-29), §13 |
| **story-origin-check** (Claude skill) | Traces a news story's origin: syndication, rewrite, aggregator pickup; uses metadata and searches | Same question, prompt-based, no measured method | **FACT** that it exists and its description; read its listing page only, not code |
| **"Rewrite the News: Tracing Editorial Reuse across News Agencies"** (SoCon 2026, ACL Anthology) | Sentence-level reuse across agencies in 7 languages | States reuse is *"predominantly non-literal, involving paraphrase and compositional reuse"* and *"simple lexical matching overlooks substantial editorial reuse"* | **FACT** — abstract read |
| **Truth discovery and copying detection** (Dong, Berti-Equille, Srivastava, VLDB 2009–2010; patent US8190546) | Detects which sources copy from others in **structured** data | Conceptual foundation; not free text | **Snippet only** |
| **"From Agent Traces to Trust"** (arXiv 2606.04990, June 2026) | Survey of provenance in LLM agents; includes a *Derive* relation | Taxonomy only; no detection method or code mentioned | **FACT** — abstract/HTML summary read |
| Web-evidence poisoning of deep-research agents (arXiv 2609.06027; DRNOISE 2607.17291) | Agents misled by poisoned or repeated evidence | Motivation, not a solution | **Snippet only** (2609.06027 page returned HTTP 403) |
| Churnalism (2013); "Detecting Textual Reuse in News Stories, At Scale" (IJoC); R `textreuse` | Lexical text-reuse detection | Lexical baselines | **Snippet only** |
| "Revision-Aware Independent Agent Graphs" (arXiv 2610.01249) | Unknown | Unknown | **Not read** — fetch rate-limited |
| EP-001 (this repository) | Lexical lineage detection | Documents the failure mode | **FACT** — §1 |

INFERENCE: the general question ("how many sources are really independent?") is not new. The open question EP-002 tests is narrower: detecting **non-literal** derivation and shared origin in free text at a useful false-positive rate.

---

## 13. corroborate-mcp: verification at the pinned commit

### 13.1 Source read
Repository `chefcohen/corroborate-mcp`, commit `1da5f9933c15119bd8078ecdc25710dfcab7ff93` (2026-07-29, "0.1.3: fix two customer-facing honesty defects…"), checked out locally and read in full: `src/engine.js` (blob `21a99f20ca92b7094925551b1cf916224959b118`), `src/text.js` (blob `af4313efe85ae86e0873ca3b973c8c866676fd3d`), `README.md`. **FACT** (code read).

### 13.2 What `assess()` actually does (FACT)
1. `assess(claim, rawResults, opts)` is a pure function (no network). Each article needs `title`, `domain`, `published_at`, `age_days`, `engine`, `source`/`url`; it also needs a **`claim`** string.
2. **Relevance gate** (`engine.js` lines 40–49): an article is kept only if its normalized title has at least 2 core-token hits **and** at least 35% of the claim's core tokens (prefix-aware match, tokens of length ≥ 3). Discarded articles are not clustered; their count appears only inside a `notes` string.
3. **Clustering** (lines 52–58): articles are processed in input order; each is compared with the **prototype token array of each existing cluster, which is the title tokens of the cluster's first member and is never updated**; it joins the first cluster in creation order with `jaccard(c.toks, toks) ≥ SIM_THRESHOLD`, otherwise it opens a new cluster. `SIM_THRESHOLD = 0.55`. Jaccard is computed on token **sets**; an empty set gives 0. The result therefore depends on **input order**.
4. **Normalization** (`text.js`): lowercase, every character outside `a–z`, `0–9` and space replaced by a space, split on whitespace, stop words removed. Non-ASCII letters are destroyed.
5. `n_independent_sources` is the number of clusters. Domains, the wire list (AP, Reuters, AFP, UPI), publication times, ages and engine agreement affect only notes and confidence; they do **not** affect which cluster an article joins.
6. **`assess()` does not return cluster membership.** It returns the count, a truncated list of cluster representatives (earliest-dated item) and `echoed_by_n_domains` per representative.
7. The pre-clustering deduplication by `domain + first 8 normalized title tokens` is in **`findSources`** (the network path, lines 17–25), **not** in `assess()`.
8. README (FACT): "No LLM in the loop"; "English-language, headline-level"; no stance detection (6/6 distorted claims falsely CONFIRMED); "Independent rewrites of one wire story can occasionally slip clustering; distinct phrasings of one origin can occasionally count as two."

### 13.3 Corrections to the v0.2 description (§10 of v0.2)
- The relevance gate of `assess()` was **omitted**; it requires a claim and can discard documents.
- The pre-dedup by domain and first 8 title tokens was presented as part of the clustering; it belongs to `findSources`, upstream of `assess()`.
- "Joins the first cluster whose headline token set…" is made exact: the comparison is with the **first member's** tokens, never updated.
- A faithful pairwise "reproduction" is **not possible** with the public function, which hides membership. The v0.2 description of B4 as a "faithful reproduction" with a pairwise-style evaluation was an over-statement.

Consequence — three variants, named by what they are:
- **B4-faithful:** the unmodified `assess()`, run by Node. The `claim` is a per-event string generated from the event record's core facts **before any document exists** (ASCII, identical for all documents of the event). Stub metadata: a unique stub domain per document, a constant `published_at`, `age_days` and `engine`. The input regime is adapted (synthetic documents, not search results); the algorithm is not. Output used: `n_independent_sources` and the cluster-size multiset (obtained from `echoed_by_n_domains`, which equals the cluster size when every domain is unique).
- **B4-core:** a harness that imports the original `normTitle`, `jaccard`, `coreTokens`, `relevance` from the original `text.js` and reproduces the loop of lines 52–58 verbatim while returning membership. Conformance test: on a fixed set of at least 1,000 random title lists, for the same order, B4-core gives the same cluster count and the same multiset of cluster sizes as B4-faithful. Until it passes, nothing is claimed about B4-core.
- **B4-tuned:** B4-core with the relevance gate off and a swept threshold. The gate removes documents whose titles do not address the claim; in this regime it handicaps B4, and "beating B4" would then be trivial. Gate-off removes that handicap.

### 13.4 Evaluation of B4 and what is not comparable
- **Input:** the titles of the 14 documents of S (plus the claim for the gate). B4 sees only titles and sees the whole set at once.
- **Order dependence:** 100 seeded random permutations of S per event.
- **From clusters to pairs:** a pair is predicted dependent if both documents are in the same cluster in at least 50% of the permutations; the fraction is kept as a descriptive score. A document discarded by the gate belongs to no cluster and its pairs are predicted independent. **Information lost:** the continuous score (only one operating point remains), the assignment history, and the case of a document similar to two clusters but assigned to the first.
- **Native metrics:** origin-count error, B-cubed, ARI (§8.5). The count is natively comparable to the truth of 5 origins per event on S.
- **Not directly comparable to the pairwise methods:** B4-faithful and B4-core have a single operating point and cannot enter the equal-FPR comparison; B4 sees only titles, not bodies; B4 is a set-level method (the declared C13 exception); the diagnostic pairs with P, where the truth is not a partition, are not comparable.

### 13.5 Verdict
**Not a KILL.** corroborate-mcp addresses claim-level corroboration with a lexical headline rule and no body-level analysis. It does not attempt non-literal derivation detection in body text, which is the EP-002 question. B4-tuned is the strongest form of that rule and enters the comparison S-b.

---

## 14. Limitations (declared)

1. **Provenance not observed.** A ← X → B with X outside the graph is invisible (§2.1). Success says nothing about this case.
2. **Synthetic, one domain.** Fictional news-style events written by LLMs from structured records.
3. **Unique-detail channel.** Unique details are inserted by construction and their retention is a generative parameter. A method exploiting them has an advantage that the real world may not give. D4 (masking) measures the reliance; it does not remove it.
4. **Supervised candidates learn the pipeline.** A candidate with parameters fitted on dev labels can learn artefacts of this generation pipeline, which the test split shares. Mitigations are the cell design, C6, D1, D2 and D4, and the rule that success authorises only EP-003.
5. **Local models.** The primary configuration uses local open-weight models. Rewrites by small models may not resemble rewrites by frontier models, and a weaker local B5 makes the kill K2 less likely to fire than a stronger judge would. The frontier control (§7.6) is reported separately and does not change the outcome.
6. **Error asymmetry.** The operating point (FPR_w = 10%) protects against merging independent sources; missing a dependence (counting two repetitions as two confirmations) is also an error and is visible in recall and in the origin-count error.
7. **Precision and F1** depend on the constructed prevalence.
8. **Hidden dependence between generator models** (overlapping pre-training may produce similar phrasing for the same facts) is addressed only by randomization, strata D3 and D2, not removed.
9. **Direction and genealogy** are not measured.
10. **Chain depth** is at most 2.
11. **I1 instruction** ("same register") is artificial.

---

## 15. Reproducibility, order of execution and time box

**Order of execution**
1. Pilot (3–5 burned events): pipeline, audit, timing, log-probability availability.
2. **Stage-1 freeze** (tag `ep002-stage1`): configuration, constants, grid, rules, N_dev, N_max, prompts and paraphrases, frontier-subset rule, masking rule.
3. Generate the **dev** split; ledger; mechanical checks.
4. Validate dev: C6, C7, C11 and the design checks; at most one regeneration (§5.6).
5. Calibrate baselines and explore candidates on dev, at most K = 10 variants per family, all logged.
6. **Freeze** (tag `ep002-freeze`): primary candidate, thresholds, R*, baselines, paraphrases; compute **N_test** (stage 2, §10.3).
7. Generate the **test** split with the frozen configuration and new seeds; mechanical checks only.
8. Evaluate **once**; produce the report, with the frontier control reported separately.

**Reproducibility**
- All random processes seeded; seeds in a versioned configuration file.
- Generated dataset frozen as versioned JSONL with a content hash; **all LLM outputs and prompts cached and committed**, so evaluation can be re-run without regenerating text.
- Exact model names, versions and generation parameters recorded per document.
- Configuration, prompts (including the 3 paraphrases), thresholds, variant ledger, generation ledger, label-word list and the corroborate-mcp commit and blob hashes are versioned and frozen before the test run.
- Results (raw predictions, metrics, confidence intervals) saved under a results directory.
- **Single command** to reproduce the evaluation from the frozen dataset, documented in the report. Re-running must not depend on any conversation history.
- **Time box: 2 weeks** from approval, covering the order above. If no result in either direction by then: STOP, report as inconclusive with reasons.

---

## 16. Decisions approved and items for the final review

**Approved by the project owner (2026-10-02):** success criterion S1 (not S2); +5-point FPR guard with equal-FPR comparison as the main comparison; K = 10 symmetric with a logged variant ledger; frontier exception as a separate, non-influencing control on a fixed subset; N_max provisional, with INCONCLUSIVE-UNDERPOWERED and no criterion change; two-stage power analysis with pilot limited to mechanics; check C13; unique-detail masking as a diagnostic; primary definition = independence relative to the complete recorded provenance graph, with the closure rule; B4 named by what it is.

**Items for the final review** (introduced while writing v0.3; none changes a threshold):
1. **Kill criteria operationalized** (§9.2): "within the CI" became UB(Δ) < 0.20, and each kill is the demonstrated opposite of a success criterion.
2. **INCONCLUSIVE-UNDERPOWERED** applies whatever the observed statistics (§9.4), and K1–K5 are disabled in that case.
3. **C11 (headroom) failure ends the experiment** without regeneration (§5.6).
4. **B4-tuned runs with the relevance gate off** (§13.3).
5. **B5-score** depends on token log-probabilities, with a sampling fallback (§7.3).
6. **Supervised candidates** learn the pipeline (§14.4).
7. **Generative parameters** (§5.2) are proposed defaults to be frozen at stage 1.

---

## Changelog

**0.3 (2026-10-02)** — specification text only; no code, no dataset, no benchmark run.
1. **Primary task changed from information-flow dependence to independence of origin**, defined on the complete recorded provenance graph, with four categories and a closure rule; information flow kept as a diagnostic (§2, §3).
2. **Dataset redesigned:** 17 documents per event in two parallel lineages (X from ORIG, Y from H), roots H, I1–I3 and an auxiliary P; literal documents A and B and P outside the primary set; cells R–D and D–D with fixed weights; full pair-class table (§5). Removes the document-type confound of EP-001.
3. **Independent reporters made operational** (observation set, a-priori style id, length; no text of other documents); I1 shares ORIG's unique details by construction (§5.4).
4. **Generation protocol:** balanced randomized assignment, "different model" constraint of D removed, context audit, boilerplate check, ledger, one regeneration with pre-registered knobs, test generated after the freeze (§5.4–5.7).
5. **Checks** extended to C1–C15 with the confounder each removes; headroom check C11 with an out-of-sample oracle O1; score purity C13; diagnostics D1–D9 (§6, §7.4).
6. **Baselines:** B4 split into B4-faithful (count only), B4-core (membership, conformance-tested) and B4-tuned; B5 split into B5-score (symmetric prompt, both orders, log-probabilities) and B5-verdict; K = 10 symmetric tuning budget (§7).
7. **Verification of corroborate-mcp at commit `1da5f99`** corrected the v0.2 description (§13.3).
8. **Criteria formalized:** S1 against every baseline at equal FPR_w = 10% with paired event bootstrap; +5-point guard; non-inferiority on hard negatives; robustness over four prompt formulations; kills as the demonstrated opposite of successes; INCONCLUSIVE-UNDERPOWERED (§9).
9. **Power analysis made two-stage** with explicit lists of quantities estimated on dev and quantities pre-registered; grid; binding rule; N_max provisional (§10).
10. **Register of constants** (§11); **frontier control** and **masking diagnostic** defined as non-influencing (§7.6, §8.6).

**0.2 (2026-10-02)** — after review of PR #2: B4 split from B4-tuned; case J removed; ground truth vs detector input made explicit; hard negatives I1–I3; N no longer fixed.

**0.1 (2026-10-02)** — first draft.

---

## Summary for readers of the repository
1. **Why EP-001 was stopped:** it measured near-identical lexical overlap; it detected no summaries or rewrites, and its dataset had a light-edit bug, label leakage, mostly trivial negatives and a document-type confound (§1).
2. **What EP-002 tests:** whether independence of origin — including between two derivatives of the same unseen original — can be detected from the texts substantially better than lexical, semantic and simple-LLM baselines, at the same false-positive rate (§3–4).
3. **What it does not test:** absolute epistemic independence in the real world; sources outside the recorded graph (§2).
4. **Data:** fictional events, several generator families, two parallel lineages per event, controlled information flow, ground truth from the recorded graph (§5).
5. **Baselines:** lexical, TF-IDF, embedding, corroborate-mcp (in three precisely named forms) and a plain LLM prompt (§7, §13).
6. **Criteria:** S1 at equal FPR, +5-point guard, non-inferiority on hard negatives, kills as demonstrated opposites, INCONCLUSIVE-UNDERPOWERED when N cannot be reached (§9–10).
7. **A success** authorises only EP-003 on real data; no SDK, no product (§2.3).
