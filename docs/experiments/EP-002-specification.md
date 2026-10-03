# EP-002 — Non-literal Derivation Detection: Experimental Specification

| | |
|---|---|
| Status | **DRAFT — v0.8 written for final review. NOT frozen. No implementation, no dataset, no benchmark run until the specification is explicitly approved and frozen.** |
| Version | 0.8 (2026-10-03) — see Changelog at the end |
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

Formally, the label of a pair is a function of the generation graph only (§3). If two documents A and B derive from a document X that is **not a node of the graph**, then A ← X → B is invisible to the benchmark and the pair is labelled independent even though, in the world, they share an origin. EP-002 does not attempt to solve this problem. It is a declared limitation and it determines what a success may be used for (§2.3).

### 2.2 Closure rule
Every text that is used as input to any generation step must itself be a node of the graph (including auxiliary and later-excluded documents). A document excluded from evaluation (§5.6) keeps its node; only its pairs leave the evaluation. A check (C12, §6) audits generation prompts for undeclared inputs.

### 2.3 What a success authorises
A success on EP-002 authorises **only** EP-003 (real-world data, e.g. an agency copy and its republications, where the common source is observable and the ground-truth protocol is different). It does not authorise an SDK, a product, an API, or any claim about real-world independence.

### 2.4 Out of scope
SDK, product, UI, API, deployment; direction of derivation (who copied whom) and full genealogy beyond the diagnostic categories of §3.4; real-world data (EP-003); documents not observed in the graph; the full Epistemic Layer architecture. A declaration that the idea is valid because a benchmark can be built is explicitly not a result.

---

## 3. Task definition

### 3.1 Three distinct relations between two texts A and B
| Relation | Meaning | Observable from text alone? |
|---|---|---|
| **Similarity** | A and B say similar things (lexically or semantically) | Yes |
| **Derivation** | B was produced using A (directly or through intermediaries, in whole or in part) | Sometimes |
| **Shared origin / independence** | A and B descend from the same origin document, versus from different origin documents | Only indirectly |

Similarity ≠ derivation ≠ origin-independence:
- A and B can be **highly similar yet independent**: two reporters observe the same event and write nearly the same sentence.
- A and B can be **dissimilar yet dependent**: B is a 100-word summary or an AI rewrite of a 1,000-word A.
- Two derivatives C and D of the same ORIG are **not derived from each other but do not count as two origins**.

### 3.2 Graph, roots and ancestry (definitions)
For each event there is a directed graph G = (V, E) over its documents. There is an edge u → v **if and only if the exact text of u, or a deterministic function of it, was in the generation context of v** (prompt, tool input, or any other input). Nothing else creates an edge: not similarity, not shared facts, not the same model, not a shared prompt template, not the world event itself. The world event (the structured event record) is **not** an origin; only a document is.

- **Root:** a document with no incoming edge (produced from an observation set only). R ⊆ V is the set of roots.
- **Anc(v):** the set of ancestors of v, including v itself. Roots(v) = Anc(v) ∩ R.
- **Ancestor order:** u ⪯ v iff u ∈ Anc(v). It is a partial order.
- **Ancestor-sharing relation on V:** u ~_G v iff Anc(u) ∩ Anc(v) ≠ ∅. It is reflexive and symmetric and is **not transitive in general** (§3.5). It is a graph-level relation used to label diagnostic pairs outside the primary set; it is **not** the primary relation.

### 3.3 Primary relation: shared-origin equivalence
The **primary evaluation set** S ⊆ V is fixed by design (§5.5). Let R_S = R ∩ S be the origin roots of S.

- **Single-origin condition.** Every v ∈ S has **exactly one** S-root among its ancestors: |Roots(v) ∩ R_S| = 1. This defines the **origin function** o : S → R_S, with o(v) the unique S-root in Anc(v).
- **No-hidden-ancestor condition.** For all u, v ∈ S: u ~_G v ⇔ o(u) = o(v).
- **Shared-origin equivalence** ≈ on S: u ≈ v iff o(u) = o(v). It is the **kernel of the function o**, therefore reflexive, symmetric and transitive: an **equivalence relation**. It partitions S into |R_S| **origin blocks**. There are exactly 5 per event: those of ORIG, H, I1, I2, I3.
- **Primary label:** a pair in S is `dependent` iff u ≈ v, otherwise `independent`. By the no-hidden-ancestor condition this coincides with u ~_G v on S.

Both conditions are guaranteed by the design (§5.5: the auxiliary root P is outside S; the only composition in S has exactly one S-root) **and verified automatically on the recorded graph of every event** (C16). An event that violates either condition is excluded and counted (§5.6).

**Defining statement.** *Shared-origin is the primary equivalence relation; ancestry is a separate diagnostic; the B4 reduction is a separate evaluation transformation.*

### 3.4 Ancestry diagnostic (secondary, no pass/fail role)
For a pair in S with u ≈ v, the **ancestry category** is read from the ancestor order:

| Category | Condition |
|---|---|
| DIRECT_DERIVATION | edge u → v or v → u |
| INDIRECT_DERIVATION | u ≺ v or v ≺ u through a path of length ≥ 2, no direct edge |
| SHARED_ORIGIN_NO_DIRECT_FLOW | u and v incomparable in ⪯, same origin block |

For a pair with u ≉ v the category is INDEPENDENT_ORIGIN. Ancestry is **not** the primary relation and is **not** an equivalence. The ancestry label ("dependent iff DIRECT or INDIRECT") differs from the primary label only on SHARED_ORIGIN_NO_DIRECT_FLOW pairs. Recall of the primary detector is reported per category (D5). Direction and full genealogy remain out of scope.

### 3.5 Bridge diagnostic (outside the primary set)
The composition F = compose(ORIG, P) has Roots(F) = {ORIG, P}. ORIG and P are **independent roots** (ORIG ≁_G P) while F ~_G ORIG and F ~_G P: this is the standard failure of transitivity of ~_G on V.

It does **not** violate the primary partition, for three reasons: (1) P ∉ S, so P is not an origin root of S; (2) within S, F has the single S-root ORIG, so o(F) = ORIG; (3) no other document of S has P among its ancestors, so the no-hidden-ancestor condition holds. The primary relation is defined on S only, where ≈ is an equivalence. The pairs (P, F) and the pairs of P with other documents belong to the diagnostic classes PC10–PC11 (§5.5), labelled by ~_G; they never enter the primary metrics. The **bridge merge rate** (D6) measures how often a method merges ORIG and P through F.

### 3.6 Operational definition of "non-literal derivation"
B derives from A iff the graph contains a path A ⇝ B. A derivation is **non-literal** if B is neither an exact copy of A nor a light edit of A (≤ 10% of tokens changed). The graph is the truth; the amount of content that survives is a covariate, never a reason to relabel.

| Situation | Label | Treatment |
|---|---|---|
| B keeps only some facts of A | derived | fraction of A's unique details retained is measured by exact match of fictional tokens; recall is reported per retention bin |
| B adds its own facts | derived | number of invented facts recorded; label unchanged |
| B drops the distinctive details of A | derived | reported as the "zero retention" stratum, the hardest stratum |
| B combines A with another document | derived from both | two incoming edges |
| B passes through several transformations | INDIRECT (path ≥ 2) | maximum depth 2 in EP-002 |
| B is semantically similar but generated without A's text | independent origin | similarity creates no edge |
| B uses the same world facts but not the text of A | independent origin | facts come from the event record, never from a document |

### 3.7 Ground truth is not detector input
The graph is known to the benchmark and is used **only** to score methods. The relation must be inferred **exclusively from the two document texts**. That a generation process knows A → B does not prove that an outside observer can infer it from A and B; that inference is what is being tested. Consequently a detector receives nothing but the two texts (headline included, being part of the text): no metadata, no generator model, no class label, no provenance, no ID, filename, timestamp or position that encodes any of these (C2, C9, C13).

### 3.8 Terminology
- **Origin:** a root document of S (an element of R_S) and, by extension, the **origin block** it induces in S.
- **Lineage:** the set of all documents of V descended from a root, root included (lineage X from ORIG, lineage Y from H). The origin block of a root is its lineage restricted to S.
- **Ancestry:** the ancestor partial order ⪯ (§3.2). **Ancestor-sharing:** the graph relation ~_G. Neither is the primary relation.
- **Source:** used only in running prose for "independent sources", the project goal. The technical objects are **documents**.

---

## 4. Hypotheses

**H0.** On the reference dataset, no tested method detects dependent pairs better than the best baseline by at least the minimum effect of interest (0.20 absolute in non-literal recall at equal false-positive rate), without the controlled increase in false positives defined in §9.

**H1.** The primary candidate, selected on the development split and then frozen, meets the success criteria S-a to S-f of §9 on the held-out test split: it detects a substantially larger share of non-literal dependent pairs — summaries, rewrites, paraphrases, compositions, chains and the sibling pairs between them — than **each** baseline including a simple LLM judge, at the same false-positive rate, **without an unacceptable increase in false positives on genuinely independent documents**.

The method is **not** chosen in advance. Candidates are explored on the development split only (§7.2).

---

## 5. Dataset

### 5.1 Why EP-001's construction cannot be reused
If a single author (human or one LLM) writes both the original and the "independent" documents, those documents share model, style and prior knowledge, and a detector can learn style. If dependent documents are always transformed texts and independent documents are always untransformed ones, a detector can learn "was this text transformed" (§1.5.5). The design below addresses both: several generator families, randomized and balanced assignment, and **two parallel lineages per event with the same transformations** so that the label depends on origin-block membership and not on document type.

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

I1–I3 test that "same facts" or "same register" is not read as "same origin". **They are artificial hard negatives, built as stress tests; they are not an estimate of the real-world prevalence or of the real-world false-positive rate.** The I1 instruction is artificial and may not mirror real reporters (declared limitation); I2 and I3 are added so that the result does not depend on a single instruction.

**Derived documents.** A derived document is written by a process that receives the **text** of its parent document(s): A (copy, verbatim including headline), B (deterministic seeded script changing at least one and at most 10% of tokens), C/C_y (LLM summary), D/D_y (LLM rewrite), E/E_y (LLM paraphrase preserving sentence structure), F (LLM composition of ORIG and P), G/G_y (LLM rewrite of D/D_y). Prompts are fixed templates stored in the configuration. Derivation prompts are **not** told to keep or to drop unique details.

**Generators and assignment.** At least three generator model families (open-weight, local in the primary configuration). Each document's generator and style id are assigned by a **blocked, randomized, balanced** algorithm per event, recorded in an assignment table that is checked **before any text is generated** (C14). The rewrite case D is not constrained to a "different model": generator choice is randomized for every case so that "same generator" does not predict dependence. Every prompt, raw output, model name, version and parameter set is cached and committed.

**Context audit.** Every generation prompt is logged. A check (C12) scans it for n-grams of at least 8 tokens from any document that is not declared as input, and fails on any match.

### 5.5 Pair classes, cells and roles
The **primary document set S** has 14 documents: all roots except P, and all derived documents except the literal ones A and B (A and B are near-duplicates of ORIG and would pseudo-replicate its pairs):
S = {ORIG, H, I1, I2, I3, C, D, E, F, G, C_y, D_y, E_y, G_y}. S has 91 pairs. The origin function is o(ORIG) = o(C) = o(D) = o(E) = o(F) = o(G) = ORIG; o(H) = o(C_y) = o(D_y) = o(E_y) = o(G_y) = H; o(I1) = I1; o(I2) = I2; o(I3) = I3. The **design constraints** that make §3.3 hold: P ∉ S; every composition in S has exactly one S-root.

R = root, D = derived (non-literal). Counts are per event.

| # | Class | Pairs | Label / ancestry category | Role |
|---|---|---|---|---|
| PC1 | R–D, same origin block, direct | 7 | dependent / DIRECT (ORIG–C,D,E,F; H–C_y,D_y,E_y) | **primary positive (cell R–D)** |
| PC2 | R–D, same origin block, indirect | 2 | dependent / INDIRECT (ORIG–G; H–G_y) | **primary positive (cell R–D)** |
| PC3 | D–D, same origin block, direct | 2 | dependent / DIRECT (D–G; D_y–G_y) | **primary positive (cell D–D)** |
| PC4 | D–D, same origin block, siblings | 14 | dependent / SHARED_ORIGIN_NO_DIRECT_FLOW | **primary positive (cell D–D)** |
| PC5 | R–D, different origin blocks | 36 | independent | **primary negative (cell R–D)** |
| PC6 | D–D, different origin blocks | 20 | independent | **primary negative (cell D–D)** |
| PC7 | R–R (ORIG, H, I1, I2, I3) | 10 | independent | guard negatives; no positive exists in this cell |
| PC8 | pairs with A or B, same lineage | 13 | dependent (~_G) | diagnostic (literal sanity) |
| PC9 | pairs with A or B, different lineage | 16 | independent (~_G) | diagnostic |
| PC10 | (P, F) | 1 | dependent (~_G) / DIRECT | diagnostic (bridge) |
| PC11 | other pairs with P | 15 | independent (~_G), incl. (ORIG, P) | diagnostic (bridge) |
| — | pairs with an excluded document; cross-event pairs | — | — | **excluded** from the primary metrics; cross-event pairs are reported in a separate table |

Total per event: 7+2+2+14+36+20+10+13+16+1+15 = 136 = C(17,2).

**Cells.** Primary metrics are computed **within cells** and then combined with fixed weights, so that a detector cannot gain from knowing whether a text is a root or a derivative:
- Cell R–D: 9 positives (PC1+PC2), 36 negatives (PC5).
- Cell D–D: 16 positives (PC3+PC4), 20 negatives (PC6).
- **Weights** (derived from the design, frozen): w_RD = 9/25 = 0.36, w_DD = 16/25 = 0.64.
- recall_w = 0.36·recall(R–D) + 0.64·recall(D–D); FPR_w = 0.36·FPR(R–D) + 0.64·FPR(D–D). Per-event values are averaged with equal weight over events.

**Named negative sets.** For each case k ∈ {H, I1, I2, I3}: N_k = pairs of the root k with {ORIG, C, D, E, F, G} (6 pairs per event: 1 in PC7, 5 in PC5). These are the hard-negative sets used by S-d.

### 5.6 Exclusions, ledger and regeneration
A pair is excluded (logged and counted) if generation failed, refused or produced off-topic or wrong-language output; if a derived text is identical to its source when the case requires a change; or if the flow log of either document is missing or inconsistent. An event is excluded if it violates C16, or if more than 10% of its documents are excluded. If more than 10% of events are excluded, the dataset is regenerated with the cause documented; it is not silently patched.

**Generation ledger** (versioned): attempt number, seed, generation-code version, configuration hash, discarded datasets and the reason for each discard.

**No opportunistic regeneration.** At most **one** regeneration of the dev split is allowed, and only for a failure of a pre-registered validity check (C1–C3, C6, C7, C12, C14, C15) — never for the performance of any method on the test split. A second failure ends the experiment (K8). C11 (headroom) failure does **not** permit regeneration: making the dataset more fact-identifiable would be tuning towards the hypothesis; it ends the experiment.

**Pre-registered knobs** (the only parameters a regeneration may change; the change applies to all subsequent events, dev and test):
1. On a C7 (difficulty floor) failure: use the second, pre-written, stronger-rewording prompt template for D/E (template R2), and/or lower the summary length bound from 30% to 15%.
2. On a C6 (confound) or C14 (balance) failure: draw a new assignment seed; no change to content parameters.

Mechanical single-document repairs on the test split (C1–C3, C12, C15) are allowed, logged, and never made after looking at any method's result.

### 5.7 Splits and order of phases
Split **by event** (no event appears in both splits). The order is fixed (§15): the dev split is generated and validated first; the baselines, the primary candidate and every threshold are then frozen; **only after the freeze is the test split generated**, with the frozen generation configuration and new seeds. The test split does not exist while methods are explored.

---

## 6. Checks

All gating checks run before any method is evaluated. A failure blocks evaluation. "Dev only" means the check is computed on the dev split.

| # | Check | Confounder it removes | Rule |
|---|---|---|---|
| C1 | Label words | label-revealing text | No document contains label-revealing terms (e.g. "independent", "separate", "copy", "summary", "rewrite", "paraphrase", "original", "according to [another document]"); list versioned; matches logged |
| C2 | Opaque identifiers and layout | class leaking through IDs, filenames, file order, timestamps, cache metadata, pair order | Random IDs; no class, lineage or generator name anywhere a method can read; pair order and document order randomized with seeds |
| C3 | Real transformations | no-op or out-of-bound derivations | Every derived case except A differs from its source; B within its edit bounds; C within its length bound |
| C4 | Pair-class reporting | pooling of unlike pairs | Primary metrics use only PC1–PC6; every class of §5.5 is reported separately |
| C5 | Split leakage | dev/test contamination | No event appears in both splits; baselines, thresholds, prompts and the primary candidate are frozen and tagged before the test split is generated; the test split is generated only after the freeze (§5.7) |
| C6 | Surface confound classifier (dev only) | stylistic/length signal that alone separates classes | A pair-level classifier on surface features (length, length ratio, TF-IDF of each single text), trained **within each cell** with event-grouped cross-validation, must have recall_w at FPR_w = 10% **below the best of B1, B2, B3, B4-tuned plus 0.20**; otherwise the dataset is confounded |
| C7 | Difficulty floor (dev only) | a dataset too easy to test H1 | If the best of B1, B2, B3, B4-tuned reaches recall_w ≥ 0.8 at FPR_w = 10% on dev, the dataset is invalid |
| C8 | Detector/generator separation | an LLM detector recognising its own style or priors | In the primary configuration the detector model family is **not** among the generator families. If that is impossible, results are stratified by whether the detector family generated a document of the pair and the limitation is stated |
| C9 | Detector isolation | provenance metadata reaching the detector | Methods receive **only the two texts**. The harness strips and withholds metadata, generator, class labels, provenance, and IDs; the recorded provenance graph is loaded only by the scoring step. A test confirms a method cannot read these fields. An LLM-based method is shown only the two texts and its own fixed prompt |
| C10 | Selection independence | benchmark construction leaking from the baselines | No pair is selected, excluded or stratified using a similarity score computed by any evaluated method or baseline. Strata are defined by generation case only |
| C11 | Headroom (dev only) | a task where success is impossible by construction | headroom = recall_w(O1) − best frozen-baseline recall_w, at FPR_w = 10% on dev, with O1 evaluated out-of-sample (§7.4); must be ≥ 0.20. It is a necessary condition, not a sufficient one |
| C12 | Context audit | accidental edges that falsify the graph | No generation prompt contains an n-gram of 8 or more tokens from a document that is not a declared input |
| C13 | Score purity | within-event normalization or corpus statistics exploiting constant event composition and prevalence | The score of a pair depends only on the two texts and on parameters frozen on dev. Test: the score of a pair computed standalone is identical to its score computed inside the full event. Set-level methods must be declared **before** the test; B4-faithful and B4-core are set-level by construction and are the declared exception |
| C14 | Assignment balance (design time, **pair level**) | "same generator" or "same style id" predicting the label | Computed on the assignment table **on pairs, not on documents**, before generation, **within each cell and for positives and negatives separately**: the rate of same-generator pairs, and the rate of same-style-id pairs, differ between positives and negatives by at most 0.05 (exactly 0 where blocked randomization allows). Within each cell, both same-generator and cross-generator pairs make up at least 30% of the negatives |
| C15 | Boilerplate | format artefacts that reveal the class | No document contains LLM boilerplate ("Here is", "Sure", "As an AI", markdown headings, "Summary:"); offending documents are regenerated mechanically and logged |
| C16 | Origin-function check (per event, automated) | a recorded graph that contradicts the primary relation | On the recorded graph: (a) every document of S has exactly one S-root among its ancestors; (b) for every pair of S, ancestor-sharing holds iff the two documents have the same S-root (§3.3). An event that violates (a) or (b) is excluded and counted (§5.6) |

**Reported diagnostics (no pass/fail role):**
D1 single-text probe predicting "is derived" (document-type signal, neutralized by the cell design); D2 probe predicting the generator family from a single text; D3 FPR on same-generator versus cross-generator independent pairs; D4 unique-detail masking (§8.6); D5 recall by ancestry category; D6 bridge merge rate; D7 partition metrics and origin-count error; D8 recall by retention bin (fraction of the source's unique details retained, and number of invented facts, by exact match); D9 reference R1 (§7.4).

---

## 7. Methods

### 7.1 Baselines — fixed now, before any result
The baseline set 𝔅 = {B1, B2, B3, B4-tuned, B5-score} is **fixed at stage 1**. No baseline can be added after the stage-1 freeze or after the test; a baseline proposed later belongs to a later experiment and cannot enter criterion S-b.

| ID | Baseline | Definition |
|---|---|---|
| B0 | Surface control | length ratio only; expected to fail; a control, never compared in S |
| B1 | Token Jaccard | EP-001 implementation, unchanged, on the full text including the headline |
| B2 | TF-IDF cosine | word unigrams and bigrams, IDF fitted on the dev split only |
| B3 | Sentence-embedding cosine | one pinned open-source embedding model (name and version in the configuration); document vector = mean of its sentence vectors |
| B4-faithful | corroborate-mcp `assess()`, unmodified | the original function run by Node at commit `1da5f99`, once per permutation (§13.4), with inputs adapted (§13.3). Native output only: `n_independent_sources` and the cluster-size multiset. Used for the **origin-count** metric (§8.5), **never** converted into pairwise scores |
| B4-core | corroborate-mcp clustering loop with membership exposed | the original `normTitle`, `jaccard`, `coreTokens` and `relevance` imported from the original `text.js`; the clustering loop of `engine.js` lines 52–58 reproduced verbatim in a harness that returns cluster membership; conformance-tested against B4-faithful (§13.3). Native threshold 0.55. Pairwise metrics use the **EP-002 evaluation reduction ER-B4** (§13.4), which is not a corroborate-mcp behaviour |
| B4-tuned | B4-core, relevance gate off, threshold swept | same clustering rule, with the Jaccard threshold τ taken from a **pre-registered grid {0.05, 0.10, …, 0.95}**; ER-B4 with θ = 0.50; its frozen setting is the one with the highest recall_w subject to FPR_w ≤ 10% on dev (the equal-FPR comparison uses R_10 of §8.2). Reported separately; never presented as corroborate-mcp |
| B5-score | Simple LLM judge, scored | one direct prompt, one pinned local model, log-odds score (§7.3) |
| B5-verdict | Simple LLM judge, raw verdict | the same prompt answered yes / no / uncertain; qualitative kill-test form (§7.3) |

**Frozen thresholds.** The deployable threshold of B1, B2, B3, B5-score and the candidate is chosen on the **dev split**: the **lowest cutoff** at which FPR_w ≤ 0.10, then frozen. It is a real, deterministic setting; it is used for the guard S-c and for the frozen-threshold analysis. It is **never** defined by randomization. The equal-FPR comparison and every "recall at FPR_w = 10%" in this specification use the evaluation quantity **R_10** of §8.2, which is a separate object. B4-faithful and B4-core use their original threshold 0.55 and are never tuned.

### 7.2 Candidate methods — explored on dev only, none assumed
Candidates may be: semantic similarity variants; claim overlap; entity/event overlap; unique-detail overlap; structured LLM-based signals; combinations. Rules:

1. **At most K = 10 variants** in total for the candidate family on the dev split, counted jointly across all candidate designs. The same K = 10 applies to every other family that requires tuning (B5: prompt variants). B1 has no variants; B2 and B3 configurations are fixed in §7.1; B4-tuned's threshold grid is pre-registered and is not a set of variants. A threshold choice is not a variant. The prompt paraphrases of §8.7 do not count.
2. **Every variant tried is recorded** (design, hash, dev result) in a versioned variant ledger. **After the freeze no further variant is allowed.**
3. A variant that learns parameters from labelled dev pairs is scored by event-grouped cross-validation on dev (5 folds, repeated 10 times, as for O1) and then refit on all dev data; its in-sample dev score is never used for selection.
4. **Selection rule (frozen at stage 1, before any dev event exists).** **One primary candidate** is selected on dev: the variant with the highest R_10 (§8.2) on dev (out-of-fold where applicable); ties go to the cheaper variant. It is frozen — together with its threshold, prompts, features and parameters — with a git tag and a content hash. Selection uses the dev split only.
5. The test split is evaluated **once**. Other candidates are **secondary**: they may be evaluated once on test and reported, but **cannot declare success and can never be promoted to primary after the test has been seen**. If a secondary candidate would have succeeded where the primary did not, the consequence is a new pre-registered round, not a success.
6. The baselines are calibrated on the current dev **before** candidate exploration begins and are frozen (tag `ep002-baselines`); candidates are explored afterwards. No candidate, variant or exploratory design enters any baseline-based quantity (§7.4, C11).

### 7.3 B5 in detail

**Model record (frozen at stage 1).** One open-weight instruction-tuned local model, identified by a record: family, parameter count, checkpoint identifier and content hash, quantization, runtime name and version, tokenizer hash, chat-template hash. The identity cannot be fixed in this document because it depends on the stage-1 pilot (hardware, token log-probability access); it is frozen at stage 1. If the candidate is LLM-based it uses the same record.

**Verbalization V0 (exact template).** One user message, no system message:

```
Text 1:
{TEXT_1}

Text 2:
{TEXT_2}

Question: Do these two texts originate from a common source text — that is, is one of them derived from the other, or are both derived from a third text? Answer with exactly one word: Yes or No.
Answer:
```

The model's answer starts immediately after the chat template's generation prompt. {TEXT_i} is the complete text including the headline.

**Token scoring.**
- Take the logits at the **first generated position**, apply a softmax at temperature 1 with **no** top-k, top-p, repetition penalty or other sampling transformation.
- T_yes = the set of all **single-token** surface forms of "Yes", "yes", "YES", with and without a leading space, in the model's tokenizer; T_no likewise for "No", "no", "NO". Both sets are listed from the tokenizer at stage 1 and frozen. A model for which "Yes" or "No" has no single-token surface form is **ineligible**.
- p_yes = Σ over T_yes of the token probabilities; p_no likewise. **Score s = ln p_yes − ln p_no.** No other normalization is applied; yes and no are single-token events, so no length normalization is needed.
- **Coverage check (dev):** the mean of p_yes + p_no over dev pairs must be ≥ 0.90, otherwise the model is ineligible.
- **Symmetry:** every pair is scored in both orders and s_sym = (s(T1, T2) + s(T2, T1)) / 2. No order seed is needed.
- **Use of the score:** the score is used **only to order pairs**. The comparison is made at equal FPR on each method's own ordering, so no comparability of score scales across models or tokenizations is required or claimed. Ties at a cutoff are included or excluded as a group.

**Tuning budget.** Up to K = 10 prompt variants (wording and delimiters, always keeping the one-word Yes/No answer), logged; the variant with the highest dev R_10 (§8.2.1) is the main prompt (formulation j = 0). The selection uses formulation 0 only; the paraphrases B5_1, B5_2, B5_3 are written once at the baseline freeze, before any candidate is explored, and are not tuned (§8.7).

**B5-verdict.** The same prompt answered in three values yes / no / uncertain (the "uncertain" option added to the instruction); "uncertain" counts as "not dependent" (conservative for FPR); the opposite mapping is reported alongside. No threshold applies. It is a qualitative kill test and not an input of the statistical comparison.

**Same input as all methods.** The same two texts, with headlines, and the same token limit.

**If B5-score is unavailable** — no eligible local model, token log-probabilities not exposed, or the coverage check fails: there is **no sampling-based fallback in the quantitative comparison**. B5-score is declared **unavailable**, B5-verdict remains the qualitative test, and §9.6 applies.

### 7.4 O1 and R1 — dataset-specific diagnostic upper bounds (dev only)
**What they are.** O1 uses exact-match fact tokens, the event schema and features built for this dataset. It is a **dataset-specific diagnostic upper bound** on what can be identified from fact content in this benchmark. It is **not** a universal oracle of identifiability. It is used only as a necessary-condition check (C11) and is **never evaluated on the test split, never used to select or evaluate anything on test, and never given the results of any other method**.

**Fully pre-specified (frozen at stage 1, before the first dev event is generated):**
- **Features** (fixed list, computed by exact match of fictional tokens, none using wording): Jaccard of the sets of fact IDs present; number of shared unique details; number of unique details in the union; agreement in the order of shared facts (Kendall tau); number of shared idiosyncratic errors.
- **Model:** logistic regression, L2 regularization with fixed strength, standardized features; a separate model per cell. No hyperparameter search.
- **Predictions:** all predictions are out-of-fold, from event-grouped cross-validation on dev (5 folds, repeated 10 times with different fold assignments); the score of a pair is the mean of its out-of-fold scores, so no prediction is made on an event that contributed to training.
- **Operating-point rule:** on the pooled out-of-fold scores, the quantity R_10 of §8.2, computed by the same rule as for every other method (the residual optimism of fitting the operating point on dev is symmetric and, for the baselines, favours them, which makes C11 conservative).
- recall_w and FPR_w as in §5.5, event-macro averaged; the bootstrap CI is over events on the out-of-fold scores (it ignores training variability; stated).

**C11.** headroom = recall_w(O1) − max over the **frozen baselines** {B1, B2, B3, B4-tuned, B5-score} of R_10 on dev (§8.2.1; B5-score under formulation 0, §8.7). The maximum is taken **only over baselines that are pre-specified in §7.1, whose tuning budget (K = 10 for B5) was spent and frozen before C11 is computed (tag `ep002-baselines`)**, and never over a candidate, a candidate variant or any design explored after the baselines were frozen. Pass if the point estimate is ≥ 0.20 (the effect of interest). A failure ends the experiment (§5.6).

**Reference R1.** The same procedure with all text features of the pair. R1 is **not** an upper bound on anything (it can learn dataset artefacts) and has no gate role; if R1 is far above O1, the signal beyond fact content is flagged for review.

### 7.5 Score purity (C13)
Pairwise methods must produce a pair's score from the two texts and from parameters frozen on dev only. Within-event rank or z-score normalization, corpus statistics fitted on test documents, and any use of other documents of the test event are forbidden. Set-level methods are allowed only if declared before the test; B4-faithful and B4-core are the declared exceptions, and their comparability is limited accordingly (§13.5).

### 7.6 Frontier exception (external-validity control)
A single frontier model is used for one control, on a **fixed subset of the test split**: the first min(10, N_test) test events, in the seeded generation order, **defined before the test is generated**. It runs B5-score and, if the primary candidate is LLM-based, the candidate with the frontier model substituted, without any change of prompt or threshold. It is **reported separately**. It does not enter the statistical test, cannot change any threshold, the candidate, the dataset or any criterion, and **a frontier result cannot turn a failed experiment into a success**. It is required to be reported before a success is used to authorise EP-003.

---

## 8. Metrics and estimators

### 8.1 Primary population
Same-event pairs of the **test** split in the cells of §5.5 (PC1–PC6), with the exclusions of §5.6. Per-event recall_w and FPR_w are computed as in §5.5 and averaged with equal weight over events.

### 8.2 Operating points
| Quantity | Role | Where used |
|---|---|---|
| **FPR_w = 10%**, equal across methods | **Main operating point**: the scientific comparison is made here | S-b, S-d, K1–K3 |
| **FPR_w ≤ 15%** at the dev-frozen threshold | **Maximum guard** (10% plus a 5-point tolerance); a safety check, not the comparison | S-c, K3 |
| +5 points on N_k, at the equal-FPR point | non-inferiority margin on the hard negatives | S-d, K3 |
| FPR_w = 5% and 20% | descriptive sensitivity | reported only |

- **Primary comparison — equal FPR.** All methods that produce an ordered family of operating points (a score or a threshold grid) are compared at FPR_w = 10% by the single rule below. The rule uses the test labels only to evaluate the (FPR_w, recall_w) of each point of a **pre-registered, frozen family** and to place each method at the same false-positive rate, an evaluation-time matching symmetric across methods, as in any ROC evaluation; no threshold, grid or parameter of any method is chosen or changed with test information.
- **Frozen-threshold analysis — guard.** Each method is also evaluated at the threshold frozen on dev (§7.1). For the candidate this yields the guard of S-c. Recall differences at frozen thresholds are reported as a secondary analysis.
- B4-core at its native 0.55, B4-faithful and B5-verdict have no operating-point family; they are reported at their native point and are not part of the equal-FPR comparison.

#### 8.2.1 The equal-FPR rule (identical for every method)

**Operating-point family.** The family is defined by what is frozen, and the same rule then applies to every method.

*Score-based methods* (B1, B2, B3, B5-score, the primary candidate). What is frozen is the **scoring rule**: a function that maps the two texts of a pair to a real number, with every parameter fixed before the test split exists:
- B1: token-set Jaccard of the full texts, no parameters;
- B2: TF-IDF cosine, with the vocabulary and the IDF weights fitted on dev only and frozen;
- B3: cosine of the mean sentence embeddings of the pinned embedding model;
- B5-score: the symmetric log-odds of §7.3, with the frozen model record and the selected prompt;
- the primary candidate: its scoring function, with all features, prompts and parameters frozen at the freeze (tag and content hash).

The family of operating points is **not** a frozen set of cutoffs. **For score-based methods the family is finite on any realized sample: one operating point is defined for each distinct observed score cutoff, with ties handled as a single cutoff** (a pair is predicted dependent iff its score is at least the cutoff). The cutoffs, and therefore the points, are derived from the scores of the pairs of the sample under evaluation. In each bootstrap replicate the scores are those computed **once** on the test pairs by the frozen scoring rule — nothing is re-scored or re-fitted — and only the events, hence the pairs and their multiplicities, change; the cutoffs and the points are re-derived from the scores of the pairs of the resampled events.

*Trivial classifiers of a score-based family.* The family is the set of threshold classifiers {score ≥ c : c ∈ ℝ ∪ {+∞}}. It therefore contains "predict all pairs dependent" (the cutoff at the smallest observed score, already one of the observed cutoffs) and "predict no pair dependent" (the cutoff +∞, whose inclusion is a **standard mathematical consequence of the definition of a threshold family**, not tuning and not a threshold added after the freeze). Consequently the points (FPR_w, recall_w) = (0, 0) and (1, 1) always belong to the family of a score-based method, and **NO REACHABLE cannot arise from the way the family of a score-based method is defined**.

*Grid-based methods* (B4-tuned; any candidate whose output is a finite set of settings rather than a score). The family is the **pre-registered finite set of settings** — for B4-tuned the threshold grid of §7.1 with ER-B4 at θ = 0.50 (§13.4) — and nothing else; no trivial point is added, because the pre-registered definition of the family does not contain one. A grid that does not bracket FPR_w = 10% yields NO REACHABLE; this is a property of the pre-registered grid, checked on the burned pilot events before the stage-1 freeze (§10.8).

No point or setting is added, removed or modified after the freeze, and the same rule is applied in every bootstrap replicate.

**Statistics of a point.** (FPR_w, recall_w) of §5.5, computed on the events under consideration (the full test split, or a bootstrap resample).

**Empirical frontier.** From the family, keep only the **non-dominated** points: a point j is dominated if another point i has FPR_w(i) ≤ FPR_w(j) and recall_w(i) ≥ recall_w(j) with at least one strict inequality; of identical points keep one. If several points have the same FPR_w, **the one with the highest recall_w is kept**. Sort the remaining points by increasing FPR_w: (F_1, R_1), …, (F_m, R_m), with F and R both strictly increasing. (The non-dominance step makes the rule fair to families whose points are not nested, such as B4-tuned: without it an adjacent point of lower recall could drag the randomized value below a better point already available.)

**Rule.** Let F* = 0.10.
1. **Exact point.** If some F_i = F*: R_10 = R_i, used directly, without randomization.
2. **Randomization between adjacent points.** Otherwise, if there are adjacent points a and b = a + 1 with F_a < F* < F_b, let
   λ = (F* − F_a) / (F_b − F_a) ∈ (0, 1)
   and consider the randomized classifier that uses point b with probability λ and point a with probability 1 − λ. Its **expected** false-positive rate is (1 − λ)·F_a + λ·F_b = F* and its **expected** recall is
   **R_10 = (1 − λ)·R_a + λ·R_b.**
3. **Saturation.** If every F_i < F* and the last frontier point has recall R_m = 1 (recall cannot be higher, and that point is a feasible point with FPR_w < F*), then R_10 = 1. No randomization is used and nothing is extrapolated: the point is a real point of the family. The operating point is that point itself (λ = 0); the other linear statistics are evaluated at it.
4. **No reachable point.** Otherwise, if every F_i < F* (with R_m < 1) or every F_i > F*, the method has **NO REACHABLE 10% OPERATING POINT**. R_10 is undefined; nothing is extrapolated beyond the observed frontier and no recall is assigned.

(Why the saturation case exists: a point with recall 1 and FPR_w < F* dominates the all-positive point (1, 1), which the non-dominance step then removes, so the frontier can end before F*. Without case 3 such a method would be reported as unreachable although it attains the maximum possible recall at FPR_w ≤ F*.)

**Mathematical basis.** FPR_w and recall_w are weighted means (fixed cell weights, equal-weight average over events) of per-pair predicted-positive indicators. They are therefore **linear** in the per-pair prediction probabilities. A classifier that uses point b with probability λ, either as one global Bernoulli draw or independently pair by pair, has per-pair prediction probabilities (1 − λ)·1[a] + λ·1[b], and by linearity its expected statistics are the same convex combinations of the statistics of a and b. The pair (F*, R_10) is therefore an **achievable expected operating point** on the segment between two achievable points; nothing outside the observed frontier is assumed. The relation between R_10 and "the highest recall subject to FPR_w ≤ 0.10" is stated and proved in Proposition 1. The evaluation uses the **expectation**: **no random number is drawn and no seed is involved**; R_10 is a deterministic function of the frozen family and of the events.

**Proposition 1.** Let q = max{ recall_w(p) : p in the family, FPR_w(p) ≤ F* } (defined when at least one point of the family has FPR_w ≤ F*). Whenever R_10 is defined, **R_10 ≥ q; R_10 = q if and only if a frontier point has FPR_w exactly F* or q = 1; and R_10 > q otherwise.**
*Proof.* (i) Let p be a feasible family point with recall q. If p is dominated, some point p′ has FPR_w(p′) ≤ FPR_w(p) ≤ F* and recall_w(p′) ≥ q; p′ is feasible, so by the maximality of q its recall is q, and, the recalls being equal, its FPR_w is strictly smaller. Repeating on the finite family, each step strictly lowering FPR_w among points of recall q, reaches a non-dominated point with FPR_w ≤ F* and recall q. (If p has duplicates, one representative is kept and has the same coordinates.) Hence the best feasible recall among the frontier points is q. (ii) On the frontier F and R both strictly increase, so among the feasible frontier points (those with F_i ≤ F*) the best is the one with the largest index. In case 1 of the rule it is the exact point (F_i = F* is the largest possible feasible FPR_w); in case 2 it is point a, because F_a < F* < F_b; in case 3 it is the last frontier point. So R_i = q in case 1, R_a = q in case 2, R_m = q in case 3. (iii) In case 1, R_10 = R_i = q. In case 2, R_10 = R_a + λ(R_b − R_a) with λ ∈ (0, 1) and R_b > R_a (strict increase), hence R_10 > R_a = q. In case 3, R_10 = 1 = R_m = q. Since R_a < R_b ≤ 1, case 2 never occurs with q = 1. ∎ The proposition says nothing for NO REACHABLE, where R_10 is undefined.
*Edge cases.* **Same FPR_w:** the point with the higher recall dominates the other; with equal recall they are duplicates and one is kept. **(0, 0):** if a point (0, R > 0) exists it dominates (0, 0), and the frontier still has a point with FPR_w = 0; either way the feasible set is non-empty for a score-based family. **(1, 1):** if a point (F < 1, recall 1) exists it dominates (1, 1) and q = 1, which is exactly case 3; otherwise (1, 1) stays on the frontier and provides the upper bracketing point b with F_b = 1 ≥ F*. **Strict monotonicity on the frontier:** two frontier points with F_i < F_j and R_i ≥ R_j would make j dominated, so R is strictly increasing.

**Other statistics at the same point.** Any other statistic that is linear in the predicted-positive indicators — FPR_k on N_k (S-d), recall per class, FPR in each cell, and the per-event values — is evaluated at the **same two points a and b with the same λ** of the pooled FPR_w frontier: (1 − λ)·stat_a + λ·stat_b. For per-event values the λ is the one computed on the pooled sample, so the mean of the per-event values equals R_10.

**λ is determined exclusively by the pooled FPR_w frontier of the method.** It is not recomputed for any N_k, any cell, any class or any other statistic, and a statistic cannot choose its own randomization. Therefore the three hard-negative sets cannot be optimized separately, and S-d compares methods on FPR_k at the operating point already fixed by the pooled FPR_w. The reference baseline R* has its own λ, computed by the same rule from its own pooled FPR_w frontier. Explicitly: λ_P is a function of the pooled FPR_w frontier of P only and λ_R* of the pooled FPR_w frontier of R* only, and
FPR_k(P) = (1 − λ_P)·FPR_k(P, a) + λ_P·FPR_k(P, b), FPR_k(R*) = (1 − λ_R*)·FPR_k(R*, a) + λ_R*·FPR_k(R*, b),
where a and b are the adjacent points of the respective pooled frontier. **Any λ_{N_k}, λ_cell, λ_class, or other separate randomization for a hard-negative set or any other statistic is forbidden.** In a saturated case λ = 0 and the statistics are those of the saturated point.

**Score invariance in the bootstrap (score-based methods).** For a score-based method, the score assigned to an individual original test pair is **invariant across bootstrap replicates**, because the frozen scoring function is not refitted or rescored. Event bootstrap resampling changes only the multiplicity with which that pair contributes to the replicate. If an event is drawn three times, each pair of that event appears three times in the bootstrap multiset, with the **same** score; no three different scores and no three different cutoffs are created, and the multiplicity enters the weights of the FPR_w and recall_w means. What is fixed and what varies:

| Fixed in every replicate | Variable in each replicate |
|---|---|
| scoring function, model, parameters, prompt, embedding model, tokenizer | the multiset of events |
| the score of each individual original test pair | the multiplicity of each pair |
| the family definition (§8.2.1) | the empirical distribution of the scores, hence the set of cutoffs that are observed |
| | the operating points, the frontier, λ and R_10 |

**Where R_10 is used.** Wherever this specification says "recall (or FPR) at FPR_w = 10%": S-b, S-d, K1–K3; C6, C7 and C11 (on dev, applied to the dev events, out-of-fold for supervised scores); the selection of the primary candidate and of the B5 prompt (on dev); and the stage-2 estimates of §10.3. The frozen threshold of §7.1 is **not** defined by this rule.

**Limit cases.**

| Case | Treatment |
|---|---|
| A point with FPR_w exactly 0.10 exists | use it directly, no randomization |
| All frontier points have FPR_w < 0.10 and the last one has recall 1 | R_10 = 1 (saturation, case 3); no randomization, no extrapolation |
| All frontier points have FPR_w < 0.10 and the last one has recall below 1 | NO REACHABLE 10% OPERATING POINT; no extrapolation beyond the observed frontier |
| A point above 0.10 exists but none at or below 0.10 | NO REACHABLE 10% OPERATING POINT; no randomized point is built, because that would assume behaviour outside the grid |
| Several points have the same FPR_w | keep the one with the highest recall_w (the frozen rule), then apply the rule |
| Dominated point (higher FPR_w, not higher recall_w) | removed from the frontier before the rule is applied |
| Any need to choose a threshold, add a grid value or change a grid with test information | **not permitted**; the family is frozen before the test |

**Consequences of NO REACHABLE** are fixed in §9.7.

### 8.3 Reported for every method
Recall_w, FPR_w, precision and F1 (these depend on the constructed prevalence and are not transferable to the real world); recall for every positive class PC1–PC4 and for the ancestry categories; FPR for PC5, PC6 and PC7; FPR for each N_k (k = H, I1, I2, I3); the diagnostic classes PC8–PC11; cross-event pairs in a separate table.

**Equal-FPR results table (mandatory).** One row per method of the equal-FPR comparison (the primary candidate, B1, B2, B3, B4-tuned, B5-score), reporting the quantity of §8.2.1 and how it was obtained:

| Method | FPR operating point (expected) | Recall at FPR = 10% (R_10) | Operating-point type | Adjacent points used (F_a, R_a), (F_b, R_b), λ | Frozen-threshold FPR_w and recall_w |
|---|---:|---:|---|---|---|
| Candidate | … | … | continuous (exact) / continuous (randomized) / continuous (saturated) / discrete (exact) / discrete (randomized) / discrete (saturated) / **NO REACHABLE 10% OPERATING POINT** | … | … |
| B1, B2, B3, B4-tuned, B5-score | … | … | … | … | … |

A method with no reachable point is reported with the text **NO REACHABLE 10% OPERATING POINT** in the recall column; **no interpolated or extrapolated recall is assigned to it.** The number of bootstrap replicates in which a method had no reachable point (§8.4) is reported.

### 8.4 Uncertainty and paired bootstrap
- 95% percentile confidence intervals by **paired bootstrap resampling of events** (10,000 resamples, fixed seed). In each replicate the same resampled events are used for both methods of a difference. **The equal-FPR rule of §8.2.1 is applied separately inside every bootstrap replicate, for each method:** (1) the (FPR_w, recall_w) of every point of the method's frozen family are recomputed on the resampled events; (2) the non-dominated frontier is rebuilt; (3) the points adjacent to FPR_w = 10% are found; (4) λ is computed; (5) R_10 of that replicate is computed; (6) the paired difference of the replicate is taken between the R_10 values. **λ is never computed once on the full test sample and reused across replicates**: the uncertainty about the position of the operating points propagates into the interval.
- **Quantile definition.** For B values v_1 ≤ … ≤ v_B, Q_p = v_(⌈p·B⌉) (nearest rank). The endpoints use p = 0.025 and p = 0.975; with B = 10,000 they are v_(250) and v_(9750).
- **Defined and undefined replicates.** A replicate of a difference (recall difference Δ_X, or an FPR difference on N_k) is **defined** if both methods have a reachable 10% operating point in that replicate, and **undefined** otherwise. If either method is undefined in a replicate, **the whole difference is undefined**; the λ of the other method is not inherited and no value is assigned to the difference. The scores of a score-based method are invariant across replicates (§8.2.1); only the multiplicities change.
- **Conservative partial-identification bootstrap interval (CPI-95).** A recall difference and an FPR difference are each a difference of two quantities in [0, 1], so each lies in [−1, +1]. For the **lower** endpoint every undefined replicate is given the value **−1**; for the **upper** endpoint every undefined replicate is given the value **+1**:
  LB\* = Q_0.025 of { Δ^(b) if replicate b is defined, −1 otherwise },
  UB\* = Q_0.975 of { Δ^(b) if replicate b is defined, +1 otherwise }.
  No replicate is dropped and no favourable value is imputed. **Sufficient conditions** (not necessary ones, because a defined replicate can itself take the value −1 or +1): if at least ⌈0.025·B⌉ replicates are undefined, then LB\* = −1; if at least B − ⌈0.975·B⌉ + 1 replicates are undefined, then UB\* = +1. The definition of CPI-95 does not depend on these consequences.
- **Why it is a bound.** Every quantile is non-decreasing in each of its entries. For **any** assignment of values in [−1, +1] to the undefined replicates, the percentile lower endpoint is at least LB\* and the percentile upper endpoint is at most UB\*. The interval [LB\*, UB\*] therefore contains the percentile interval of every possible completion: it is a worst-case (Manski-type partial-identification) interval, and it is **not** called a percentile bootstrap confidence interval except when no replicate is undefined, in which case it coincides with the ordinary 95% percentile interval. The fraction u of undefined replicates is reported for every comparison and for every method.
- **Use in the criteria.** LB\* and UB\* denote the endpoints of CPI-95. S-b uses LB\*; K1 and K2 use UB\*; S-d uses UB\*; the FPR-difference clause of K3 uses LB\*. Because undefined replicates are counted against the favourable direction in each case, they penalize SUCCESS and they penalize KILL alike. The interval of FPR_w(P) at its frozen threshold (S-c, K3) involves no operating point to reach and is an ordinary percentile interval.
- Non-deterministic methods are run 5 times; the per-pair score is the mean of the 5 runs, and the range of the metrics is reported.

### 8.5 Partition metrics and origin count
Within S the truth is the partition of §3.3 with 5 origin blocks per event. Reported (D7): the **origin-count error** `n_pred − 5` (signed: positive means missed dependence) and its absolute value; B-cubed precision and recall; adjusted Rand index.
- **B4-faithful** gives the count natively, once per permutation; the reported value is the mean over permutations, with the range and the fraction of permutations with the exact count.
- **B4-core:** B-cubed and ARI are computed on **each actual partition** (one per permutation) and averaged; **no reduction is applied**.
- **Every other method** is reduced to a partition by one fixed rule: connected components of the graph of pairs it predicts dependent at its frozen-threshold operating point. The information lost in that reduction (one false positive can merge two clusters) is stated. Partition metrics are secondary.

### 8.6 Diagnostics
- **Ancestry (D5):** recall of the primary detector for DIRECT, INDIRECT and SHARED_ORIGIN_NO_DIRECT_FLOW pairs; no pass/fail.
- **Bridge (D6):** on the diagnostic classes PC10–PC11, how often a method predicts (ORIG, P) dependent although both are ancestors of F and are independent roots.
- **Unique-detail masking (D4):** the frozen primary candidate and the frozen baselines are evaluated on a deterministic masked copy of the test split in which every token of a fact designated as a unique detail (exact fictional string) is replaced by a neutral placeholder. **No pass/fail role.** It shows whether a result depends artificially on the way unique details are built into the dataset. No parameter is re-tuned.
- **Retention (D8):** recall per bin of retained unique details.

### 8.7 Prompt robustness: formulation instances
**Formulations.** j ∈ {0, 1, 2, 3}. j = 0 is the main prompt, selected on dev under §7.2 and §7.3 using formulation 0 only. j = 1, 2, 3 are the three paraphrases, written **once**, as rewordings of the selected prompt's instruction sentence: those of **B5 at the baseline freeze** (§15, step 4), before any candidate is explored, and those of the **candidate at the candidate freeze** (§15, step 7), in both cases before the test split exists. Writing the B5 paraphrases before any candidate result exists prevents them from being shaped by knowledge of how the candidate performs. **All three are used, none is selected, dropped or replaced after being written**, and none is chosen by performance.

**Which methods depend on j.** B5-score, whenever it is available (it is LLM-based), and the primary candidate if it is LLM-based. B1, B2, B3, B4-tuned and a non-LLM candidate are identical in every formulation. J = {0, 1, 2, 3} if the candidate or an available B5-score is LLM-based, otherwise J = {0}.

**Formulation instance.** For each j ∈ J the instance j consists of P_j (the candidate under formulation j, or P itself if it is not LLM-based), B5_j (B5-score under formulation j) and the formulation-independent baselines. Thresholds are re-fitted on dev, mechanically, for each LLM-based method and each j and frozen. **Every criterion of §9 is evaluated within one instance and never mixes formulations: P_j is compared with B5_j, never with B5_j′.** The four instances are not four runs of the candidate: a formulation changes the candidate **and** B5 together.

**The reference baseline R\*.** R* is a baseline **identity**, not an instance. It is designated **once**, at the baseline freeze (§15, step 4), on dev and under formulation 0: the baseline of 𝔅 (as available) with the highest dev R_10, ties broken by the order B1, B2, B3, B4-tuned, B5-score. It does not depend on the candidate, on any test result or on any formulation other than 0, and it is **not re-selected per formulation**. In instance j the reference is R*_j = R* if R* is formulation-independent, and R*_j = B5_j if R* = B5-score. R*_j is used by S-d and by K3 in instance j.

**Common resamples.** The same 10,000 resampled event multisets (same seed, §8.4) are used for every method, every comparison and every instance, so that all differences are paired in the same way.

The decision rule over the instances is fixed in §9.8.

---

## 9. Success, kill and inconclusive criteria — fixed before the experiment

All statements refer to the **primary candidate** P and to the baseline set 𝔅 of §7.1. Δ_X = R_10(P) − R_10(X), the difference of the equal-FPR recalls of §8.2.1 on test, with the paired event bootstrap of §8.4. LB\* and UB\* are the endpoints of the conservative partial-identification bootstrap interval CPI-95 of §8.4 (equal to the ordinary 95% percentile interval when no replicate is undefined).

### 9.0 Statistical status of the intervals
The 95% bootstrap intervals are **descriptive intervals used inside a pre-registered decision rule**. EP-002 does **not** present them as hypothesis tests with control of the family-wise error rate, and no multiplicity-adjusted p-values or simultaneous-inference claims are made. The rule combines many comparisons (up to 5 baselines, 3 hard-negative sets, up to 4 prompt formulations): SUCCESS is an **intersection** of per-comparison conditions and KILL is a **union** (any single demonstrated failure). The operating characteristics of the rule — the probability of SUCCESS, of KILL and of INCONCLUSIVE under stated scenarios — are computed by the simulation of §10 and reported, but are **not** gates.

The decision is fully pre-registered: **one primary candidate**; selection **on dev only** by a rule frozen at stage 1; the test evaluated **once**; secondary candidates never promotable; B5 and B4-tuned with pre-registered tuning budgets; no baseline added after the stage-1 freeze or after the test.

### 9.1 SUCCESS (H1 supported on synthetic data) — all must hold
S-b, S-c and S-d are evaluated **within a formulation instance j** (§8.7); the index j is omitted below. In an instance, P, B5 and R* stand for P_j, B5_j and R*_j.
- **S-a Validity.** Checks C1–C16 passed (C11 = headroom, on dev).
- **S-b Recall (criterion S1).** For **every** X ∈ 𝔅 (𝔅 as available, §9.6): Δ̂_X is defined, Δ̂_X ≥ 0.20 **and** LB\*(Δ_X) > 0. The value 0.20 is the minimum effect of interest and is frozen before the dataset is generated.
- **S-c FPR guard.** FPR_w(P) at its **dev-frozen threshold** on test is ≤ 0.15 (the operating point plus a 5-point tolerance). This is a safety guard; the scientific comparison is the equal-FPR comparison of S-b.
- **S-d Hard negatives (non-inferiority).** For each k ∈ {I1, I2, I3}, at the equal-FPR operating point, UB\* of the paired difference FPR_k(P) − FPR_k(R*) is ≤ +0.05 (both FPR_k evaluated at the operating point fixed by the pooled FPR_w of each method, §8.2.1), where R* is the reference baseline designated once on dev at the baseline freeze (§8.7).
- **S-e Robustness.** S-b, S-c and S-d hold in **every** formulation instance j ∈ J (§8.7); formally, SUCCESS_j holds for all j ∈ J (§9.8).
- **S-f Cost.** Measured on a fixed random sample of 200 dev pairs: ≤ 2 seconds per pair on a single consumer machine, **or** ≤ USD 0.01 per pair through an API.

### 9.2 KILL — any one is sufficient
K1–K3 are evaluated within each formulation instance (§8.7) and K1–K5 apply only when N_test meets the power rule (§10); K6–K8 do not depend on power. Each kill criterion is the demonstrated opposite of a success criterion (K1 and K2 of S-b, K3 of S-c and S-d, K6 of S-f, K7 and K8 of S-a), so that an uncertain result is inconclusive rather than a kill.
- **K1 No margin over a similarity baseline.** For some X ∈ {B1, B2, B3, B4-tuned}: Δ̂_X is defined and UB\*(Δ_X) < 0.20.
- **K2 A prompt is enough.** For B5-score: Δ̂_B5 is defined and UB\*(Δ_B5) < 0.20. (The local-model caveat of §14 applies.)
- **K3 False positives.** FPR_w(P) at its frozen threshold has an ordinary 95% percentile lower endpoint > 0.15, or for some k the LB\* of FPR_k(P) − FPR_k(R*) is > +0.05.
- **K4 — withdrawn in v0.8 (the number is not reused).** The v0.7 criterion declared a kill when the bootstrap interval of an AUC included 0.5. That is not the demonstrated opposite of any success criterion: an interval including 0.5 means uncertainty and not a demonstrated inability to separate, and an AUC significantly below 0.5 would not have fired it. The scientific decision about the hard negatives is carried by S-d (success) and K3 (kill). Nothing replaces K4.
- **K5 Fragility (quantifier over formulations).** K1, K2 and K3 are evaluated in each instance j ∈ J. If **at least one** of K1_j, K2_j, K3_j is demonstrated for **at least one** j ∈ J, the kill is declared. K5 is the clause "for at least one j"; it is not a further condition. The precise rule is §9.8.
- **K6 Cost.** The cost bounds of S-f cannot be met.
- **K7 Ground truth.** Ground truth cannot be produced reliably (§5.6 exclusion limits exceeded twice).
- **K8 Dataset validity.** The dataset fails C6 or C7 and cannot be fixed within the one allowed regeneration and the time box, or fails C11 (which permits no regeneration, §5.6).

Removed or merged relative to v0.2: the v0.2 criteria "B4 or another open-source system performs within the CI" and "B5 performs within the CI" are now K1 and K2; "within the CI" is operationalized as UB(Δ) < 0.20. See the Changelog.

### 9.3 INCONCLUSIVE
The decision rule of §9.8 yields neither SUCCESS nor KILL within the time box (§15): reported as inconclusive with the reason. No criterion is relaxed, replaced or re-weighted after any result is seen.

### 9.4 INCONCLUSIVE-UNDERPOWERED
If the algorithm of §10.5 returns no N_test within the operational limit, the outcome is labelled INCONCLUSIVE-UNDERPOWERED **whatever the observed statistics are**. Descriptive results may be reported, cannot authorise EP-003, and cannot trigger K1–K5. Criteria K6–K8 do not depend on power and remain in force. **No criterion is modified.**

### 9.5 What cannot change an outcome
The frontier control (§7.6), the unique-detail masking (D4), the ancestry diagnostics (D5), the secondary candidates, the secondary analysis at frozen thresholds, the sensitivity analyses of ER-B4 (§13.4) and every diagnostic of §6.

### 9.6 If B5-score is unavailable
(1) S-b is evaluated against the baselines that are available; (2) K2 cannot be evaluated; (3) B5-verdict is reported as a qualitative result; (4) the outcome label carries the suffix "(B5 not quantitatively compared)" and the project owner must review the B5-verdict result before any success is used to authorise EP-003. The fallback is not forced into the quantitative comparison.

### 9.7 If a method has no reachable 10% operating point
1. **On the full test sample.** If R_10 is undefined for P or for some X ∈ 𝔅, then Δ̂_X is undefined (and, if P or R* is the method without a reachable point, the FPR differences of S-d are undefined too): S-b and S-d are **not met**, the comparison is reported as NO REACHABLE 10% OPERATING POINT with no recall assigned, and K1, K2 and the FPR-difference clause of K3 **cannot fire** for that X. The outcome is then at best INCONCLUSIVE unless another kill criterion applies.
2. **In a bootstrap replicate.** A replicate in which P or X has no reachable point is **undefined** and is handled **only** by the conservative partial-identification bootstrap interval CPI-95 of §8.4: the value −1 for the lower endpoint, the value +1 for the upper endpoint, no replicate dropped, no value imputed in a favourable direction. The fraction u of undefined replicates is reported. Consistency with the criteria: S-b (LB\*), K1 and K2 (UB\*), S-d (UB\*) and the FPR-difference clause of K3 (LB\*) all use the endpoint that counts an undefined replicate **against** the conclusion being tested, so undefined replicates penalize SUCCESS and penalize KILL; if u is large enough the endpoint is −1 or +1 and the corresponding criterion cannot be met.
3. **On dev — conservative and symmetric.** Only a grid-based family can lack a reachable point (§8.2.1). A baseline of 𝔅 with no reachable 10% point on dev is **unavailable at the operating point**. It is **not excluded** from the gates, because excluding the strongest baseline would lower the maximum over baselines and make C7 and C11 easier to pass. Instead the gates that use the maximum over baselines — **C6, C7 and C11 — are NOT EVALUABLE and are treated as not passed (INCONCLUSIVE)**; the freeze cannot proceed and the experiment stops with the outcome INCONCLUSIVE (baseline unavailable at the operating point on dev). No grid, setting or baseline is changed after the stage-1 freeze to cure this. The rule is symmetric: a **candidate variant** with no reachable point on dev is **ineligible** for selection. No method can gain by being unreachable. The preventive measure is the pre-flight feasibility check of the pilot (§10.8), which is not a guarantee.

### 9.8 Global decision rule over the formulation instances
Let J ⊆ {0, 1, 2, 3} be the set of formulation instances of §8.7 (J = {0} if neither P nor an available B5-score is LLM-based). For each j ∈ J, using the instance of §8.7 (P_j, B5_j, R*_j, the formulation-independent baselines, 𝔅 as available, §9.6):

- **SUCCESS_j** ⇔ S-b ∧ S-c ∧ S-d, all evaluated in instance j.
- **KILL_j** ⇔ K1 ∨ K2 ∨ K3, all evaluated in instance j.
- **CONTRADICTORY_j** ⇔ SUCCESS_j ∧ KILL_j (possible only through an inconsistency of the bootstrap intervals).
- **INCONCLUSIVE_j** ⇔ ¬SUCCESS_j ∧ ¬KILL_j.

Formulation-independent quantities: A = S-a (C1–C16 passed); F = S-f (cost); KILL_ind = K6 ∨ K7 ∨ K8.

**The outcome is the first of the following that applies, in this order:**
1. **KILL_ind** (K6, K7 or K8) → **KILL**. These do not depend on power.
2. N_test = NONE (§10.5) → **INCONCLUSIVE-UNDERPOWERED** (§9.4): K1–K5 are disabled and SUCCESS is impossible.
3. For at least one j ∈ J, KILL_j ∧ ¬SUCCESS_j → **KILL** (K5: a failure demonstrated in **one** formulation is enough).
4. For at least one j ∈ J, CONTRADICTORY_j → **INCONCLUSIVE** (contradictory evidence; the case is reported).
5. A ∧ F ∧ (SUCCESS_j for **all** j ∈ J) → **SUCCESS**.
6. Otherwise → **INCONCLUSIVE**.

The logic is symmetric between the formulations: **SUCCESS requires every formulation to pass; KILL requires one formulation to give sufficient evidence of failure; INCONCLUSIVE is everything else.** If B5-score is unavailable the suffix of §9.6 is added and the sets of baselines, and hence the criteria that apply, are those available; criteria that cannot be evaluated do not fire. No rule of this subsection may be changed after a result has been seen.

---

## 10. Sample size and power

### 10.1 Principles
N is not chosen "because it seems enough" and is never chosen after any test result. The decision rule S-b to S-d is a **joint** rule: its power is lower than that of each component and is **simulated by a deterministic algorithm (§10.5), not multiplied by hand**. The simulated quantity is a **conditional operating power under the reachable-point regime (u = 0)**: the simulated probability of satisfying S-b, S-c and S-d **conditionally on every needed statistic being identified, that is, on R_10 being reachable and no bootstrap replicate being undefined**. **Algorithm P therefore provides conditional operating power, not unconditional power of the complete decision procedure**: it does not include the probability of NO REACHABLE, the probability of undefined bootstrap replicates, or the widening of CPI-95 that undefined replicates cause. No post-hoc correction of the power is permitted. The observed effect of the candidate on dev is **never** an input of the algorithm.

### 10.2 Pre-registered at stage 1 (before any dev event is generated)
Frozen with a git tag (`ep002-stage1`):
- the generative parameters of §5.2; the selection rule of §7.2.4; the baseline set 𝔅;
- α = 0.05, i.e. two-sided 95% percentile intervals (LB = 2.5th, UB = 97.5th percentile);
- target conditional operating power π* = 0.80 (§10.1); minimum effect of interest 0.20; guard 0.15; non-inferiority margin 0.05;
- the design alternative: Δ_design = 0.25 for every X ∈ 𝔅, FPR offset on N_k of +0.02, mean frozen-threshold FPR_w of 0.10;
- the **grid** of §10.6 (conservative / moderate / optimistic) and the **floors and caps** of the binding rule: σ_Δ ≥ 0.15, σ_f ≥ 0.10, σ_g ≥ 0.05, ρ_crit ∈ [0, 0.30], ρ_form ∈ [0, 0.50];
- N_dev (≥ 20), the operational limit N_max, N_cap = N_max − N_dev;
- the simulation constants: M = 2000 simulated trials, B_sim = 1000 bootstrap resamples per trial, the grid of N (10, 15, 20, … up to N_cap), the seed;
- the binding rule of §10.5.

### 10.3 Estimated from dev, after the freeze of the candidate (stage 2)
Exactly these quantities, and no others, may be estimated from the dev split:
- **σ̂_Δ,X** — the sample standard deviation (n − 1) over dev events of the per-event recall_w difference between P and each X, at the equal-FPR operating point (out-of-fold scores for supervised variants);
- **σ̂_f,k** — the same for the per-event paired FPR difference on N_k, for each k;
- **σ̂_g** — the same for the per-event FPR_w of P at its frozen threshold;
- **ρ̂_crit** — the mean of the off-diagonal sample correlations, across dev events, between statistics of **different** types within the same prompt formulation;
- **ρ̂_form** — the same between **formulations** of the same statistic (only if P or B5 is LLM-based).

**Not usable, ever:** the observed mean effect of P on dev (the mean of any Δ), the observed mean FPR on dev, and any dev-based selection of an assumption for being favourable. The algorithm takes only standard deviations and correlations from dev. If an observed standard deviation is below its floor, **the floor is used**.

### 10.4 Statistics and model
- J = {0} if neither P nor B5 is LLM-based, otherwise J = {0, 1, 2, 3} (the four formulations of §8.7, j = 0 the main prompt). The statistics of Algorithm P are those of one formulation instance each (P_j, B5_j, R*_j), consistently with §9.8. Algorithm P replicates **every** statistic type across j with common mean, standard deviation and correlation ρ_form; for a type that does not actually depend on j (for example a lexical baseline when P is not LLM-based) the replicates are in reality identical, so the simulation requires them to hold separately and is **conservative** for such types.
- Statistic types: d_X for each available X ∈ 𝔅 (recall difference), f_k for k ∈ {I1, I2, I3} (paired FPR difference versus R*), g (FPR_w of P at its frozen threshold). With n_𝔅 = |𝔅 available| the number of types is T = n_𝔅 + 3 + 1, and the number of statistics is m = T·|J|.
- The per-event values of d_X and f_k are the per-event values at the equal-FPR operating point of §8.2.1: for a randomized point, (1 − λ)·value_a + λ·value_b with λ computed on the pooled sample, so that their mean over events is R_10 (or the corresponding mixture). Algorithm P is unchanged.
- **What enters Algorithm P and what does not.** The λ of a sample is derived from the operating points observed **in that sample**: on dev, in the stage-2 estimation of §10.3; on test, only in the final evaluation. This is consistent with §8.2.1: the per-event dev values used for σ̂ and ρ̂ are the mixture values at the dev λ. **Algorithm P is a simulated model of the distribution of the final per-event statistics at the matched operating point, and it yields conditional operating power (§10.1).** It receives neither a test λ nor any test operating point and does not simulate whether operating points are reachable; **no test information enters the choice of N**. Its percentile rule is the nearest-rank definition of §8.4, and when no replicate is undefined CPI-95 coincides with it, so Algorithm P models the case u = 0. If undefined replicates occur in the real evaluation the real power can be lower than the simulated one; this is not hidden, because a sufficiently large u forces LB\* = −1 or UB\* = +1 and the criterion fails.
- Per-event vector z_e ∈ ℝ^m is drawn from **N(μ, Σ)** (a normal approximation, declared as an arbitrary assumption: it ignores the boundedness of the statistics).
- **Means:** μ = Δ_design for every d_X; μ = +0.02 for every f_k; μ = 0.10 for g. These come from §10.2, never from dev.
- **Standard deviations:** the estimates σ̂ of §10.3 are computed in each formulation instance j ∈ J (§8.7), and the maxima below run over X (respectively k) **and over j ∈ J**: σ_Δ,used = max(max_{X,j} σ̂_Δ,X,j, 0.15) for every d_X; σ_f,used = max(max_{k,j} σ̂_f,k,j, 0.10) for every f_k; σ_g,used = max(max_j σ̂_g,j, 0.05).
- **Correlations:** ρ_crit,used = min(max(ρ̂_crit, 0), 0.30); ρ_form,used = min(max(ρ̂_form, 0), 0.50) (if |J| = 1 the formulation factor is absent). Σ = D (C_crit ⊗ C_form) D, with D = diag(σ), C_crit the T×T equicorrelation matrix with ρ_crit,used, C_form the |J|×|J| equicorrelation matrix with ρ_form,used. Both are positive definite for non-negative correlations, hence so is their Kronecker product.

### 10.5 Algorithm P (deterministic)
```
INPUT   pre-registered constants (§10.2); dev-estimated σ̂, ρ̂ (§10.3); N_cap; seed s
STEP 1  compute μ, σ_used, ρ_used, Σ as in §10.4.
STEP 2  for N in the grid {10, 15, 20, ..., N_cap}:
          for t = 1..M:
            draw N per-event vectors z_1..z_N ~ N(μ, Σ) using the pseudo-random stream
            seeded by (s, N, t);
            for b = 1..B_sim: draw N event indices with replacement (stream seeded by
              (s, N, t, b)); the SAME indices are used for every statistic
              (paired); store the mean of each statistic over the resample;
            for each statistic: mean_hat = mean over the N events; LB, UB = 2.5th and
              97.5th percentile (nearest-rank) of the B_sim resample means;
            SUCCESS_t = 1 iff ALL of:
              for every d_X, j:  mean_hat >= 0.20  AND  LB > 0          (S-b)
              for g (every j):   mean_hat <= 0.15                       (S-c)
              for every f_k, j:  UB <= 0.05                             (S-d)
          pi_hat(N) = (1/M) * sum_t SUCCESS_t              (conditional operating power, u = 0)
STEP 3  N_test = the smallest N in the grid such that pi_hat(N) >= 0.80 AND, if N+5 <= N_cap,
        pi_hat(N+5) >= 0.80.
        If no such N exists: N_test = NONE.
STEP 4  if N_test = NONE:  outcome label = INCONCLUSIVE-UNDERPOWERED (§9.4); criteria unchanged.
        else:               generate N_test test events (§5.7, §15).
STEP 5  (reporting, not a gate) at N = N_test, or at N_cap if N_test = NONE, report pi_hat
        and the simulated probabilities of KILL (K1, K2, K3 as defined in §9.2) and of
        INCONCLUSIVE, under (i) the design alternative and (ii) mu_d = 0.20 for every d_X.
OUTPUT  N_test (or NONE) and the reporting table. With the same inputs and seed the output
        is bit-for-bit reproducible.
```
Criteria S-a, S-e (it enters through J), S-f and K5–K8 are not simulated beyond what J implies: validity checks are assumed to pass and cost is deterministic (declared).

### 10.6 Sensitivity grid (planning at stage 1; not binding)
The values below are **arbitrary assumptions about unknowns** — EP-001 provides no estimate of between-event variance — and are declared as such. At stage 1 Algorithm P is run once per column, with the column's values replacing the dev estimates, to record the planned N_test per column and to flag whether the conservative column exceeds N_cap. The columns are a sensitivity analysis, not a choice of the most convenient N. The binding run (stage 2) uses §10.3–10.5.

| Parameter | Conservative | Moderate | Optimistic |
|---|---|---|---|
| Design effect Δ_design (true recall gain over each baseline) | 0.25 | 0.30 | 0.40 |
| σ_Δ: between-event SD of the per-event recall difference | 0.20 | 0.15 | 0.10 |
| σ_f: between-event SD of the per-event paired FPR difference on N_k | 0.15 | 0.10 | 0.07 |
| True FPR offset of P versus R* on N_k | +0.02 | +0.01 | 0 |
| ρ_crit | 0 | 0.3 | 0.6 |

A back-of-envelope check (illustrative only, to be replaced by Algorithm P): for the non-inferiority criterion S-d alone, n ≈ (1.96·σ_f / (0.05 − offset))². With σ_f = 0.10 and offset 0, about 15 events; with σ_f = 0.15 and offset +0.02, about 96. The criterion on hard negatives is likely to be the one that fixes N, not the recall criterion. Because S-b requires Δ̂ ≥ 0.20, a true effect of exactly 0.20 gives at most 50% power on that criterion; the design effect is therefore above 0.20.

### 10.7 N_dev, N_max and the outcome
- **N_dev ≥ 20 events** (minimum), set at stage 1. With 56 primary negatives per event, 20 events give 1,120 negatives (an indicative standard error of about one point at FPR 10%, ignoring event clustering). N_dev is not raised after seeing any result.
- **Operational limit N_max.** A resource limit on the total N_dev + N_test, **provisionally 100 events for planning**; it is **not** a methodological parameter. It is fixed from the timing measured in the pilot (§10.8) and frozen at stage 1. If 100 turns out to be insufficient it is reported as an operational limit.
- **If Algorithm P returns NONE:** the outcome is INCONCLUSIVE-UNDERPOWERED (§9.4) and **no criterion is changed**.

### 10.8 Pilot
A pilot of 3–5 events, **burned** (they never enter dev or test), is used **only** to verify the pipeline, verify the context audit and the other mechanical checks, measure generation and scoring times, identify mechanical errors, verify B5 eligibility (token log-probability access, single-token Yes/No forms, coverage), and verify that every grid-based baseline (B4-tuned) **brackets FPR_w = 10% on the pilot events**; a grid that does not bracket may be corrected **only before the stage-1 freeze**, using the burned pilot events, and never afterwards. This is a **pre-flight feasibility check and not a mathematical guarantee for the test**: it verifies the plausibility of the grid; the grid is then frozen; on the test split the frozen grid may still lack a reachable operating point, some bootstrap replicates may still be undefined (§8.4), and the grid may not be modified after the freeze. It is **not** used to estimate the effect of any candidate, and not used to estimate variance.

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
| Simulation trials M = 2000; B_sim = 1000; N grid step 5 from 10; seed | yes | MAT (Monte Carlo precision) / MET | partly | stage 1 | no |
| K = 10 variants per tuning family | yes | MET | yes | before dev exploration | no |
| 3 prompt paraphrases (written once: B5 at the baseline freeze, the candidate at the candidate freeze) | yes | MET | yes | at the respective freeze, before the test is generated | no |
| N_dev ≥ 20 | yes | MET (calibration precision) | partly | stage 1 | no |
| N_test | yes | **MAT** (output of Algorithm P) | no, given the inputs | stage 2, before test generation | no |
| N_max (provisional 100) | yes | MET (resources) | yes | stage 1, after timing | no; reported if insufficient |
| Pilot events 3–5 | yes | MET | yes | stage 1 | no |
| Grid values (Δ_design, σ_Δ, σ_f, offset, ρ_crit) | yes | HYP about unknowns | **yes**, declared | stage 1 | no |
| Mean frozen-threshold FPR_w in the simulation 0.10 | yes | MAT (the operating point) | no | stage 1 | no |
| Floors σ_Δ ≥ 0.15, σ_f ≥ 0.10, σ_g ≥ 0.05; caps ρ_crit ≤ 0.30, ρ_form ≤ 0.50 | yes | MET (conservative direction) | yes | stage 1 | no |
| Normal approximation of per-event statistics | yes | MET | yes, declared | stage 1 | no |
| Cell weights 9/25 and 16/25 | yes | **MAT** (positive counts per cell) | no | with the design | no |
| R* tie-break order B1, B2, B3, B4-tuned, B5-score; R* designated once under formulation 0 at the baseline freeze | yes | MET | yes (convention) | at the baseline freeze | no |
| Equal-FPR rule: non-dominated frontier and expected randomization between adjacent points, F* = 0.10 (no new numeric constant) | yes | **MAT** (linearity of the statistics) / MET (frontier convention) | no | stage 1 | no |
| Bootstrap quantile rule (nearest rank) and CPI-95 substitution values −1 / +1 | yes | **MAT** (the bounds of the difference of two quantities in [0, 1]) | no | stage 1 | no |
| Trivial classifiers of a score-based family (cutoffs at the smallest observed score and +∞) | yes | **MAT** (definition of a threshold family) | no | stage 1 | no |
| Headroom threshold 0.20 (C11) | yes | **MAT** (necessary condition derived from the effect of interest) | no | with the design | no |
| C6 rule "below best baseline + 0.20" | yes | MET (reuses the effect of interest) | partly | before dataset | no |
| C7 difficulty floor recall_w ≥ 0.8 | yes | MET (inherited) | yes | before dataset | no |
| C14 balance ≤ 0.05; strata ≥ 30% (pair level) | yes | MET | yes (0 where exact) | before dataset | no |
| Oracle parameters (5 folds, 10 repeats, L2 strength, feature list) | yes | MET | yes | stage 1 | no |
| Context audit n-gram length 8 | yes | MET | yes | before dataset | no |
| Exclusion limits 10% of documents per event, 10% of events | yes | MET (inherited) | yes | before dataset | no |
| One regeneration of dev | yes | MET | yes | before dataset | no |
| Pre-registered knobs (§5.6) | yes | MET | yes | before dataset | no |
| Cost bounds 2 s or USD 0.01 per pair; timing sample of 200 pairs | yes | MET (judgement) | yes | before dataset | no |
| Generative parameters (|K| = 8, |U_r| = 4, one error per root, length 150–250 words, summary ≤ 30%, light edit ≤ 10%, chain depth 2, style list) | yes | HYP (they set difficulty) | yes | before dev generation | only via §5.6 knobs |
| Frontier subset: first 10 test events | yes | MET | yes | before test generation | no |
| B5: coverage ≥ 0.90; token sets T_yes / T_no; template V0 | yes | MET | partly | stage 1 | no |
| B4-tuned threshold grid {0.05, …, 0.95} | yes | MET | yes | stage 1 | no |
| ER-B4 reduction θ = 0.50 (sensitivity 0.25 and 0.75 descriptive, dev only) | yes | MET (EP-002 choice, not corroborate-mcp) | yes | stage 1 | no; the sensitivity does not select a value |
| B4: 100 permutations | yes | MET | yes, harmless (negligible cost) | stage 1 | no |
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
6. **`assess()` does not return cluster membership.** It returns the count, a list of cluster representatives (earliest-dated item) truncated to `max_sources`, and `echoed_by_n_domains` per representative.
7. The pre-clustering deduplication by `domain + first 8 normalized title tokens` is in **`findSources`** (the network path, lines 17–25), **not** in `assess()`.
8. README (FACT): "No LLM in the loop"; "English-language, headline-level"; no stance detection (6/6 distorted claims falsely CONFIRMED); "Independent rewrites of one wire story can occasionally slip clustering; distinct phrasings of one origin can occasionally count as two."

**Direct verification of the statement "echoed_by_n_domains = cluster size when every domain is unique" (FACT, from the pinned code).** In `assess()`, after clustering, line 60 sets `c.domains = [...new Set(c.items.map(i => i.domain))]`, and each element of the returned `sources` is built in lines 107–116 from `clusters.slice(0, max_sources)` with the field `echoed_by_n_domains: c.domains.length`. `i.domain` is the `domain` field supplied by the caller. Therefore: **if every document is given a distinct `domain` value and `max_sources` is at least the number of clusters, then `echoed_by_n_domains` of each returned source equals the number of documents in its cluster.** The statement is **not** true without those two conditions: if `max_sources` is smaller than the number of clusters the list is truncated, and if two documents share a `domain` the Set collapses them. The returned list gives the multiset of cluster sizes; it does **not** identify which documents form a cluster. The conformance test of §13.3 also checks the statement empirically.

### 13.3 Corrections to the v0.2 description (§10 of v0.2)
- The relevance gate of `assess()` was **omitted**; it requires a claim and can discard documents.
- The pre-dedup by domain and first 8 title tokens was presented as part of the clustering; it belongs to `findSources`, upstream of `assess()`.
- "Joins the first cluster whose headline token set…" is made exact: the comparison is with the **first member's** tokens, never updated.
- A faithful pairwise "reproduction" is **not possible** with the public function, which hides membership. The v0.2 description of B4 as a "faithful reproduction" with a pairwise-style evaluation was an over-statement.

Consequence — three variants, named by what they are:
- **B4-faithful:** the unmodified `assess()`, run by Node. The `claim` is a per-event string generated from the event record's core facts **before any document exists** (ASCII, identical for all documents of the event). Stub metadata: a **distinct stub domain per document**, a constant `published_at`, `age_days` and `engine`; `max_sources` set to at least the number of documents. The input regime is adapted (synthetic documents, not search results); the algorithm is not. Output used: `n_independent_sources` and the cluster-size multiset (from `echoed_by_n_domains`, under the conditions of §13.2).
- **B4-core:** a harness that imports the original `normTitle`, `jaccard`, `coreTokens`, `relevance` from the original `text.js` and reproduces the loop of lines 52–58 verbatim while returning membership. Conformance test: on a fixed set of at least 1,000 random title lists, for the same order, B4-core gives the same cluster count and the same multiset of cluster sizes as B4-faithful. Until it passes, nothing is claimed about B4-core.
- **B4-tuned:** B4-core with the relevance gate off and a swept threshold. The gate removes documents whose titles do not address the claim; in this regime it handicaps B4, and "beating B4" would then be trivial. Gate-off removes that handicap.

### 13.4 Evaluation of B4: permutations and the EP-002 evaluation reduction
**What belongs to corroborate-mcp and what does not.** Clustering, the threshold 0.55, the relevance gate and the order dependence belong to corroborate-mcp. **Everything in this subsection that turns clusters into pairwise predictions belongs to EP-002 and is not a corroborate-mcp behaviour.**

- **Input:** the titles of the 14 documents of S (plus the event claim for the gate). B4 sees only titles and sees the whole set at once.
- **Permutations:** 100 seeded random permutations π_1..π_100 of S per event. For each, B4-faithful gives a count and a size multiset, and B4-core gives a partition.
- **EP-002 evaluation reduction (ER-B4).** For a pair (u, v), let f(u, v) be the fraction of the 100 permutations in which u and v are in the same B4-core cluster (0 if either is discarded by the gate). **The pair is predicted dependent iff f(u, v) ≥ θ, with θ = 0.50.** θ is a methodological choice of EP-002, frozen at stage 1. **Descriptive sensitivity analysis at θ ∈ {0.25, 0.50, 0.75} on the dev split only; no value is selected from it and no value is chosen on the test split.** The relation induced by ER-B4 is not guaranteed to be transitive.
- **Where ER-B4 is used:** the pairwise metrics of B4-core and B4-tuned. It is **not** used for B4-faithful (count only) or for the partition metrics of B4-core (computed per actual partition, §8.5).
- **Information lost in ER-B4:** the continuous score (only one operating point remains), the assignment history, and the case of a document similar to two clusters but assigned to the first.
- **Native metrics:** origin-count error, B-cubed, ARI (§8.5). The count is natively comparable to the truth of 5 origin blocks per event on S.

### 13.5 What is not directly comparable
B4-faithful and B4-core have a single operating point and cannot enter the equal-FPR comparison; B4 sees only titles, not bodies; B4 is a set-level method (the declared C13 exception); the diagnostic pairs with P, where the graph relation is not a partition, are not comparable.

### 13.6 Verdict
**Not a KILL.** corroborate-mcp addresses claim-level corroboration with a lexical headline rule and no body-level analysis. It does not attempt non-literal derivation detection in body text, which is the EP-002 question. B4-tuned is the strongest form of that rule and enters the comparison S-b.

---

## 14. Limitations (declared)

1. **Provenance not observed.** A ← X → B with X outside the graph is invisible (§2.1). Success says nothing about this case.
2. **Synthetic, one domain.** Fictional news-style events written by LLMs from structured records.
3. **Unique-detail channel.** Unique details are inserted by construction and their retention is a generative parameter. A method exploiting them has an advantage that the real world may not give. D4 (masking) measures the reliance; it does not remove it.
4. **Supervised candidates learn the pipeline.** A candidate with parameters fitted on dev labels can learn artefacts of this generation pipeline, which the test split shares. Mitigations are the cell design, C6, D1, D2 and D4, and the rule that success authorises only EP-003.
5. **Local models.** The primary configuration uses local open-weight models. Rewrites by small models may not resemble rewrites by frontier models, and a weaker local B5 makes the kill K2 less likely to fire than a stronger judge would. The frontier control (§7.6) is reported separately and does not change the outcome.
6. **Error asymmetry.** The operating point (FPR_w = 10%) protects against merging independent documents; missing a dependence (counting two repetitions as two confirmations) is also an error and is visible in recall and in the origin-count error.
7. **Precision and F1** depend on the constructed prevalence.
8. **Hidden dependence between generator models** (overlapping pre-training may produce similar phrasing for the same facts) is addressed only by randomization, strata D3 and D2, not removed.
9. **Direction and genealogy** are not measured.
10. **Chain depth** is at most 2.
11. **Hard negatives are artificial.** I1–I3 are stress tests (§5.4); FPR on N_k is not an estimate of real-world prevalence or of the real-world false-positive rate.
12. **Power analysis** rests on a normal approximation and on assumptions about unknowns (§10.4, §10.6).

---

## 15. Reproducibility, order of execution and time box

**Order of execution**
1. Pilot (3–5 burned events): pipeline, audit, timing, B5 eligibility, bracketing of FPR_w = 10% by every grid-based baseline.
2. **Stage-1 freeze** (tag `ep002-stage1`): configuration, constants, grid, rules, selection rule, baseline set, O1 specification, B5 model record and template, N_dev, N_max, frontier-subset rule, masking rule; planning run of Algorithm P per grid column.
3. Generate the **dev** split; ledger; mechanical checks (C1–C3, C12, C14–C16).
4. Calibrate the **baselines** on dev (B5 prompt variants up to K = 10, thresholds, B4-tuned grid), write the three B5 paraphrases and re-fit their thresholds on dev (§8.7), **designate R\*** (§8.7) and **freeze them** (tag `ep002-baselines`). If the dev split is regenerated (§5.6), the baselines are recalibrated from scratch under the same budget on the new dev, and only the baselines frozen afterwards are used.
5. Validate dev: C6, C7, C11 (using the frozen baselines only); at most one regeneration (§5.6).
6. Explore candidates on dev, at most K = 10 variants, all logged.
7. **Freeze** (tag `ep002-freeze`): primary candidate, thresholds, prompt paraphrases of the candidate, if it is LLM-based (the B5 paraphrases and R* were already frozen at step 4); compute **N_test** by Algorithm P with the dev-estimated quantities of §10.3 (stage 2).
8. Generate the **test** split with the frozen configuration and new seeds; mechanical checks only.
9. Evaluate **once**; produce the report, with the frontier control reported separately.

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

**Approved by the project owner (2026-10-02):** primary task = independence of origin; complete recorded provenance graph and closure rule; two parallel lineages; independent reporters; ground truth invisible to the detector; C13 score purity; test generated after the freeze; one primary candidate; K = 10; S1 (not S2); +0.20 as minimum effect of interest; FPR 10% as main comparison; +5-point guard; frontier control separate; unique-detail masking as a diagnostic; two-stage power analysis; B4-faithful / B4-core / B4-tuned as distinct concepts.

**Closed in v0.4 (the six blocking issues of the review of v0.3):** shared-origin equivalence separated from ancestry and from the bridge diagnostic (§3.3–3.5, C16); B4 reduction named as an EP-002 evaluation reduction with a descriptive sensitivity analysis, and the `echoed_by_n_domains` statement verified with its conditions (§13.2, §13.4); O1 renamed a dataset-specific diagnostic upper bound, fully pre-specified, with C11 restricted to frozen baselines (§7.4); intervals declared descriptive within a pre-registered rule (§9.0); a deterministic power algorithm (§10.5); a rigorous B5-score protocol with no forced fallback (§7.3, §9.6).

**Closed in v0.5 (the remaining blocking issue of the review of v0.4):** the equal-FPR comparison is formalized for families of discrete operating points by randomization between adjacent non-dominated operating points, applied identically to every method and separately inside every bootstrap replicate, with explicit limit cases and a reporting table (§8.2.1, §8.3, §8.4, §9.7). S1, the +0.20, FPR 10%, the +5-point guard and margin, K = 10, candidate selection, test once, Algorithm P, C11 and B4-faithful / B4-core / B4-tuned / ER-B4 are **not** changed.

**Closed in v0.6 (the two blocking issues of the review of v0.5):** undefined bootstrap replicates are handled by a fully specified conservative partial-identification bootstrap interval (§8.4, §9.7); the operating-point family of score-based methods is defined precisely as finite on any realized sample, with its frozen scoring rules and its trivial classifiers (§8.2.1). Also made explicit: Proposition 1 with its proof (R_10 versus the best feasible recall); λ determined only by the pooled FPR_w frontier; the distinction between sample λ and Algorithm P; and a conservative, symmetric rule for baselines without a reachable point on dev. The principle of the equal-FPR rule, S1, the +0.20, FPR 10%, the +5-point guard and margin, K = 10 and the other approved elements are **not** changed.

**Closed in v0.7 (the review of v0.6):** the two false "if and only if" statements on the endpoints of CPI-95 were replaced by sufficient conditions (§8.4); score invariance across bootstrap replicates and the fixed/variable split were made explicit (§8.2.1, §8.4); Algorithm P is qualified as conditional operating power (§10.1); the pilot bracketing check is declared a pre-flight feasibility check (§10.8); λ for P and R* in S-d and K3 is stated formula by formula (§8.2.1); the recheck of Proposition 1 found and closed a saturation case (§8.2.1). Algorithm P, N_test, the target 0.80, S-b to S-d, K1 to K3 and the other approved elements are **not** changed.

**Closed in v0.8 (the review of v0.7):** K4 was withdrawn because it was not the demonstrated opposite of any success criterion (§9.2); K5 was formalized as a quantifier over formulation instances (§9.2, §9.8); the four prompt formulations were formalized as instances in which a formulation changes the candidate and B5 together, with R* a baseline identity designated once on dev under formulation 0 at the baseline freeze (§8.7); a global decision rule with SUCCESS_j, KILL_j, CONTRADICTORY_j and INCONCLUSIVE_j was written (§9.8); the S-d and K3 clauses for undefined comparisons were completed (§9.7). Proposition 1, CPI-95, score invariance, Algorithm P (apart from the relabelling of the formulation index) and the other approved elements are **not** changed.

**Items for the final review** (introduced in v0.3 to v0.8; none changes a threshold):
1. Kill criteria operationalized as UB(Δ) < 0.20, each kill being the demonstrated opposite of a success criterion (§9.2).
2. INCONCLUSIVE-UNDERPOWERED applies whatever the observed statistics (§9.4).
3. C11 (headroom) failure ends the experiment without regeneration (§5.6).
4. B4-tuned runs with the relevance gate off (§13.3).
5. B5-score unavailable → no sampling fallback, success label carries a suffix and requires owner review (§9.6).
6. Supervised candidates learn the pipeline (§14.4).
7. Generative parameters (§5.2) are proposed defaults to be frozen at stage 1.
8. The B5 model identity is frozen at stage 1 from the pilot, not in this document (§7.3).
9. The false-kill probability of the union rule K1–K5 is reported by the simulation but not controlled (§9.0).
10. **Uniform application of R_10.** The equal-FPR rule is applied to continuous-score methods as well, and to the dev quantities of C6, C7, C11 and of selection, so that the rule is identical for all methods; for fine continuous frontiers the difference from "highest recall with FPR_w ≤ 0.10" is at most one frontier step (§8.2.1).
11. **Non-dominated frontier.** "Empirical frontier" is read as the set of non-dominated points; this gives a mild optimism to families with non-nested points (B4-tuned) and is conservative with respect to a continuous candidate (§8.2.1).
12. **Consequences of NO REACHABLE** (§9.7, revised in v0.6): on the full test sample S-b is not met and no kill fires; in bootstrap replicates the conservative partial-identification interval CPI-95 of §8.4 applies; on dev the gates C6, C7 and C11 become NOT EVALUABLE and the experiment stops, with no exclusion of the baseline.
14. **CPI-95** is a worst-case interval, wider than a percentile interval whenever replicates are undefined; it is not presented as a confidence interval in that case (§8.4).
15. **Trivial classifiers** (predict none, predict all) are members of every score-based family as a mathematical consequence of the definition of a threshold family; they are not added to grid-based families (§8.2.1).
16. **Pilot bracketing check:** the grid of B4-tuned may be corrected before the stage-1 freeze, using the burned pilot events, so that it brackets FPR_w = 10% (§10.8). This is the only point at which the grid may change, and the check is a pre-flight feasibility check, not a guarantee for the test.
17. **Saturation case (v0.7).** Rechecking Proposition 1 on the edge cases showed that a point with recall 1 and FPR_w < 0.10 dominates the all-positive point and removes it from the frontier, so that v0.6 would have reported such a method as unreachable. Case 3 of the rule (R_10 = 1) and the corresponding statement of Proposition 1 were added; no threshold, no principle and no criterion changed (§8.2.1).
18. **Algorithm P gives conditional operating power**, not the unconditional power of the full decision procedure (§10.1).
19. **K4 withdrawn** (v0.8). The number is not reused, so K5–K8 keep their numbers (§9.2).
20. **Contradictory evidence** (SUCCESS_j and KILL_j for the same j, possible only through an inconsistency of the bootstrap intervals) is INCONCLUSIVE, unless a clean KILL is demonstrated in another formulation (§9.8).
21. **R\*** is designated at the baseline freeze (step 4) and no longer at the candidate freeze, so that it cannot depend on the candidate (§8.7, §15).
22. **Algorithm P is conservative** for statistic types that do not depend on the formulation (§10.4); its standard deviations are the maxima over X (or k) and over the formulation instances (§10.4).
23. **B5 paraphrases are written at the baseline freeze**, before any candidate is explored, and those of the candidate at the candidate freeze (§8.7, §15), so that no paraphrase of the baseline can be shaped by candidate results.
24. **K8** now states that a C11 failure is immediate, consistently with §5.6 (§9.2).
13. The randomization is a device for defining an achievable **expected** operating point; no random draw is made in evaluation, and the **frozen deployable thresholds are unchanged** (§7.1).

---

## Changelog

**0.8 (2026-10-03)** — specification text only; no code, no dataset, no benchmark run. Corrects only the decision logic identified in the review of v0.7.
1. **K4 withdrawn (§9.2).** The AUC criterion with "the interval includes 0.5" was not the demonstrated opposite of a success criterion, and would not have fired on a systematically reversed ordering. The hard-negative decision stays with S-d and K3. The number K4 is not reused.
2. **K5 formalized (§9.2, §9.8).** K5 is the quantifier "for at least one formulation" over K1–K3; the ambiguous "K1–K4 are met under any of the four formulations" is removed.
3. **Prompt formulations formalized (§8.7).** j ∈ {0, 1, 2, 3}; a formulation instance consists of the candidate and B5 under the same formulation, plus the formulation-independent baselines; nothing mixes formulations; common bootstrap resamples; paraphrases written once at the freeze and all used.
4. **R\* (§8.7, §15).** A baseline identity designated once on dev under formulation 0 at the baseline freeze, with a fixed tie-break order; R*_j is its instance in formulation j (R*_j = B5_j if R* = B5-score); not re-selected per formulation.
5. **Global decision rule (§9.8).** SUCCESS_j, KILL_j, CONTRADICTORY_j, INCONCLUSIVE_j and an ordered rule: K6–K8, underpowered, a clean KILL in one formulation, contradiction, SUCCESS only if every formulation passes, otherwise INCONCLUSIVE.
6. **Found during the audit and corrected (no threshold or principle changed):** (a) the B5 paraphrases are written at the baseline freeze and the candidate's at the candidate freeze (§8.7, §15); (b) K8 stated a regeneration for C11 that §5.6 forbids and now says a C11 failure is immediate (§9.2); (c) the standard deviations of Algorithm P are maxima over X and over formulation instances (§10.4); (d) J counts B5-score only when it is available (§8.7, §9.8).
7. **Consistency edits.** S-d and K3 clauses in §9.7.1; S-b to S-e wording (§9.1); §9.2 heading and the opposites it names; §9.3; C11 under formulation 0 (§7.4); B5 tuning on formulation 0 (§7.3); Algorithm P: formulation index relabelled to {0, 1, 2, 3}, remark that it is conservative for formulation-independent statistics, K4 reference removed (§10.4, §10.5); constants register.

**0.7 (2026-10-03)** — specification text only; no code, no dataset, no benchmark run. Closes the review of v0.6; nothing else is changed.
1. **CPI-95 (§8.4).** The definition is unchanged. The two "if and only if" statements about LB\* = −1 and UB\* = +1 were mathematically false (a defined replicate can itself take the value −1 or +1) and are replaced by sufficient conditions.
2. **Score invariance (§8.2.1, §8.4).** The score of an original test pair is invariant across replicates; resampling changes only multiplicities; fixed and variable quantities listed; if either method is undefined the whole difference is undefined and no λ is inherited.
3. **Conditional operating power (§10.1, §10.2, §10.4, §10.5).** Algorithm P is unchanged; its output is named conditional operating power under the reachable-point regime (u = 0) and is explicitly not the unconditional power of the complete decision procedure; no post-hoc correction is allowed.
4. **Proposition 1 (§8.2.1).** Rechecked on duplicates, equal FPR, (0, 0), (1, 1) and the non-dominated frontier. A saturation case was found and closed (new case 3 of the rule; statement and proof extended). Everything else in the proof is unchanged.
5. **Score-based NO REACHABLE (§8.2.1).** Conclusion kept: for score-based families R_10 is always defined (the feasible set is non-empty and the upper side is either bracketed or saturated); NO REACHABLE can arise only for grid-based families.
6. **Pilot (§10.8, §9.7).** The bracketing check is a pre-flight feasibility check, not a guarantee.
7. **λ and S-d / K3 (§8.2.1).** λ_P and λ_R* stated from their own pooled FPR_w frontiers; any separate randomization for a hard-negative set, a cell or a class is forbidden.

**0.6 (2026-10-02)** — specification text only; no code, no dataset, no benchmark run. Closes the two blocking issues of the review of v0.5; nothing else is changed.
1. **Undefined bootstrap replicates (§8.4, §9.7).** Quantile defined by nearest rank; the conservative partial-identification bootstrap interval CPI-95 (−1 for the lower endpoint, +1 for the upper endpoint, nothing dropped or imputed favourably) with its justification as a worst-case bound; the fraction of undefined replicates is reported; consistency with S-b, K1/K2, S-d, K3 and Algorithm P stated; the interval is no longer called a percentile CI when replicates are undefined.
2. **Operating-point family of score-based methods (§8.2.1).** Frozen scoring rule per method (B1, B2, B3, B5-score, primary candidate); the family is finite on any realized sample, one point per distinct observed cutoff with ties as one cutoff; the trivial classifiers are members as a standard mathematical consequence; the phrase "the points are simply dense" is removed; grid-based families are the pre-registered settings and nothing else.
3. **Proposition 1 (§8.2.1).** Formal statement and proof that R_10 is never below the best feasible recall, with equality only when an exact point exists.
4. **λ for S-d (§8.2.1, §9.1).** λ is determined exclusively by the pooled FPR_w frontier and is not recomputed for any N_k or other statistic.
5. **Algorithm P (§10.4).** Distinction between the λ of a sample and the simulated model; no test information enters N; P models the case with no undefined replicate.
6. **Dev without a reachable point (§9.7.3, §10.8, §15).** Conservative and symmetric rule: the gates C6, C7, C11 become NOT EVALUABLE and the experiment stops; no exclusion of the baseline; an unreachable candidate variant is ineligible; the pilot checks the bracketing of FPR_w = 10% by grid-based baselines before the stage-1 freeze.

**0.5 (2026-10-02)** — specification text only; no code, no dataset, no benchmark run. Formalizes the equal-FPR comparison; nothing else is changed.
1. **Equal-FPR rule (§8.2.1).** Operating-point family, non-dominated empirical frontier, exact point when FPR_w = 0.10 exists, otherwise randomization between the two adjacent points with λ = (0.10 − F_a)/(F_b − F_a) and R_10 = (1 − λ)R_a + λR_b; limit cases; "NO REACHABLE 10% OPERATING POINT" with no extrapolation; the same rule for every method; expectation used, no random draw; other linear statistics evaluated at the same two points and the same λ.
2. **Bootstrap (§8.4).** The rule is applied separately in every replicate: frontier rebuilt, adjacent points found, λ recomputed, R_10 computed, paired difference taken; λ is never reused from the full sample.
3. **Reporting (§8.3).** Mandatory equal-FPR results table with the type of each operating point and the text NO REACHABLE 10% OPERATING POINT where applicable.
4. **Consequences (§9.7).** Behaviour of S-b, K1 and K2, bootstrap replicates and dev baselines when a method has no reachable point.
5. **Consistency edits:** frozen thresholds stay deterministic and separate from R_10 (§7.1); selection, O1, C6, C7, C11 and the stage-2 estimates use R_10 (§7.2, §7.4, §8.2.1, §10.4); the constants register records the rule (§11).

**0.4 (2026-10-02)** — specification text only; no code, no dataset, no benchmark run.
1. **Shared-origin equivalence (§3).** The primary relation is now defined as the kernel of an origin function on the primary set S, which makes it an equivalence with 5 origin blocks per event; ancestor-sharing and the ancestor order are defined separately; ancestry and the bridge case are separate diagnostics; check C16 verifies the single-origin and no-hidden-ancestor conditions on every recorded graph; terminology fixed (§3.8).
2. **B4 (§7.1, §13.2–13.5).** The 50% co-membership rule is named the EP-002 evaluation reduction ER-B4 and is no longer described as corroborate-mcp behaviour; sensitivity at 25/50/75% is descriptive and dev-only; partition metrics for B4-core use the actual partitions; the `echoed_by_n_domains` statement is kept with its two conditions, verified in the pinned code; B4-tuned threshold grid pre-registered.
3. **O1 / C11 (§7.4).** O1 and R1 renamed dataset-specific diagnostic upper bounds; model, features, threshold rule and out-of-fold predictions fully specified; C11 uses only frozen, pre-specified baselines; order of execution changed so that baselines are frozen before C11 and before candidate exploration (§15).
4. **Multiple comparisons (§9.0, §7.2).** Interpretation A: descriptive intervals within a pre-registered decision rule; no FWER claim; one primary candidate; selection rule frozen at stage 1; test once; secondary candidates never promotable; no baseline added after the stage-1 freeze or the test; prompt paraphrases written once at the freeze and all used.
5. **Power analysis (§10).** Deterministic Algorithm P with explicit inputs, statistic vector, multivariate normal model, floors and caps, bootstrap-based decision rule S-b to S-d, joint power, N_test rule, N_cap check and outcome; explicit lists of what is pre-registered, what may be estimated on dev, and what can never be used; I1–I3 enter through the f_k statistics and criterion S-d.
6. **B5-score (§7.3, §9.6).** Model record, exact template, token sets, scoring formula, coverage check, symmetry, use of the score for ordering only, K = 10 budget; the sampling fallback was removed: B5-score is unavailable if log-probabilities are not usable, and §9.6 applies.
7. **Non-blocking:** terminology unified (§3.8); operating point, guard and margin centralized in §8.2; C14 stated at pair level and by cell; I1–I3 declared artificial hard negatives and not a prevalence estimate (§5.4, §14.11).

**0.3 (2026-10-02)** — primary task changed to independence of origin; two-lineage dataset; checks C1–C15; baselines B4-faithful/core/tuned and B5-score/verdict; formal criteria S1 at equal FPR, guard, non-inferiority, kills; two-stage power analysis; register of constants; corroborate-mcp verified at `1da5f99`.

**0.2 (2026-10-02)** — after review of PR #2: B4 split from B4-tuned; case J removed; ground truth vs detector input made explicit; hard negatives I1–I3; N no longer fixed.

**0.1 (2026-10-02)** — first draft.

---

## Summary for readers of the repository
1. **Why EP-001 was stopped:** it measured near-identical lexical overlap; it detected no summaries or rewrites, and its dataset had a light-edit bug, label leakage, mostly trivial negatives and a document-type confound (§1).
2. **What EP-002 tests:** whether independence of origin — including between two derivatives of the same unseen original — can be detected from the texts substantially better than lexical, semantic and simple-LLM baselines, at the same false-positive rate (§3–4).
3. **What it does not test:** absolute epistemic independence in the real world; documents outside the recorded graph (§2).
4. **Data:** fictional events, several generator families, two parallel lineages per event, controlled information flow, ground truth from the recorded graph (§5).
5. **Baselines:** lexical, TF-IDF, embedding, corroborate-mcp (in three precisely named forms) and a plain LLM prompt (§7, §13).
6. **Criteria:** S1 at equal FPR, +5-point guard, non-inferiority on hard negatives, kills as demonstrated opposites, INCONCLUSIVE-UNDERPOWERED when N cannot be reached (§9–10).
7. **A success** authorises only EP-003 on real data; no SDK, no product (§2.3).
