# Opportunity Detection Task

## 1. Task Context

You are working in the active repository:

`C:\Users\1realbzy\Downloads\job_board_tool`

This is the active codebase for the opportunity intelligence platform.

Do not modify the legacy NLP repository. Treat it as read-only reference material.

Before doing anything, read:

* `AGENTS.md`
* `README.md`
* `docs/product/product-spec.md`
* `docs/product/opportunity-model.md`
* `docs/architecture/system-overview.md`
* `docs/architecture/data-flow.md`
* `docs/architecture/source-adapters.md`

Then inspect the existing source-ingestion implementation, models, tests, and project configuration.

Treat the repository as the source of truth for existing implementation details.

---

# 2. Current Architecture

The currently implemented source boundary is:

```text
X/Twitter
    ↓
TwikitXClient
    ↓
XTwitterSource
    ↓
RawPost
```

The next processing boundary is:

```text
RawPost
    ↓
Opportunity Detection
    ↓
OpportunityCandidate
```

The existing X/Twitter ingestion layer is working and tested.

Do not rewrite it unnecessarily.

---

# 3. Objective

Implement the first opportunity-intelligence layer:

```text
RawPost
    ↓
OpportunityDetector
    ↓
OpportunityCandidate
```

The detector should determine whether a raw source record plausibly represents an **actionable professional opportunity** worth sending to downstream extraction.

The detector is a filtering and classification boundary.

It is not responsible for fully understanding the opportunity.

---

# 4. Definition of an Opportunity

Use the project's opportunity model as the source of truth.

An opportunity is:

> A source-backed, actionable professional opening or program that a person could reasonably take action on.

Potential opportunity types include:

* employment
* internships
* graduate programs
* fellowships
* apprenticeships
* research opportunities
* contracts
* freelance opportunities
* other legitimate professional opportunities

Do not restrict detection to AI, ML, data, or software roles.

Do not assume that the presence of employment-related words automatically makes something an opportunity.

---

# 5. Detection Question

The detector should answer:

> "Does this source record contain enough evidence that it plausibly represents an actionable professional opportunity?"

Examples of likely positive evidence:

* explicit hiring announcements
* invitations to apply
* recruitment announcements
* internship openings
* fellowship applications
* graduate-program applications
* research openings
* contract or freelance openings
* explicit instructions for candidates to apply or contact someone

Examples of likely negative evidence:

* personal career announcements
* "I got hired" posts
* promotions
* generic career advice
* job-market commentary
* discussions about employment
* historical hiring statements
* opinions about recruiting
* vague statements about possibly hiring in the future
* commentary about somebody else's opportunity without actionable information

These are examples, not an exhaustive rule list.

Use realistic context rather than naive keyword presence.

---

# 6. Implementation Strategy

Start with a deterministic, interpretable baseline.

The baseline should use configurable signals rather than hard-coded decision logic scattered throughout the implementation.

Possible signal groups include:

### Positive signals

* hiring intent
* application intent
* explicit opportunity terminology
* internship/graduate/fellowship terminology
* recruitment language
* employment-type signals
* actionable application/contact language

### Negative signals

* personal career announcement
* career advice
* job-market discussion
* historical hiring
* non-actionable commentary
* ambiguous future intent

The final signal groups, weights, and threshold should be determined after inspecting the repository and realistic examples.

Do not blindly copy the example lists above.

---

# 7. Avoid Naive Matching

Do not build the detector as a collection of simplistic substring checks such as:

```python
if "hiring" in text:
    return True
```

This will produce obvious false positives.

The implementation should consider:

* word boundaries
* phrases
* surrounding context
* conflicting positive and negative signals
* punctuation and casing variation
* common language patterns
* multiple opportunity signals occurring together

Keep the logic understandable and testable.

Do not attempt to build a full NLP system for this stage.

---

# 8. Score and Decision

The detector may produce an `opportunity_score`.

The score should represent the strength of the detection evidence.

Do not describe it as:

* a probability
* a confidence percentage
* a calibrated probability

unless actual calibration has been performed.

The decision threshold should be configurable.

The detector should make it possible to inspect which signals contributed to the result.

---

# 9. Explainability

The detector should preserve useful reasons for its decision.

For example:

```text
Decision:
Opportunity

Score:
0.82

Positive signals:
- explicit hiring language
- application instruction
- internship terminology

Negative signals:
None
```

The exact representation should follow repository conventions.

The goal is to make false positives and false negatives understandable during evaluation.

---

# 10. Output Contract

The detector should consume:

```text
RawPost
```

and produce:

```text
OpportunityCandidate
```

The candidate should preserve, directly or through a stable reference:

* original source information
* source ID
* original text
* source URL
* provenance
* detection decision
* opportunity score
* detection signals/reasons
* broad opportunity category where useful

Do not destroy the original source evidence.

Do not prematurely create the complete structured opportunity schema.

---

# 11. Detection vs Extraction

Keep this boundary strict.

The detector determines:

> "This looks like an opportunity."

The extractor will later determine:

> "What exactly is the opportunity?"

Therefore the detector should not be responsible for reliably extracting:

* exact job title
* organization
* salary
* deadline
* complete skills
* education requirements
* work authorization
* full application details

It may use clues from these concepts as detection signals where appropriate, but full extraction belongs to the next pipeline stage.

---

# 12. Detection vs Matching

The detector must not use candidate-specific information.

It should not ask:

> "Is this opportunity good for the candidate?"

It should only ask:

> "Is this an opportunity?"

Candidate matching happens much later.

---

# 13. Detection vs Eligibility

The detector must not determine whether an opportunity is eligible for a particular candidate.

For example:

```text
"This internship is for candidates in the United States."
```

is evidence that the record contains an opportunity.

Whether a particular candidate is eligible is a separate downstream decision.

---

# 14. Configuration

Follow existing repository configuration conventions.

Signal weights, thresholds, and other tunable detection parameters should not be unnecessarily scattered through source code.

If no suitable configuration mechanism exists, implement the smallest clean mechanism necessary.

Do not introduce a large configuration framework.

---

# 15. Evaluation Dataset

Create a small labelled evaluation fixture containing approximately:

**30–50 realistic examples.**

The dataset should include:

* clear opportunities
* clear non-opportunities
* ambiguous cases
* edge cases
* different opportunity types
* different writing styles

Where useful, include an expected broad opportunity category.

The examples should be realistic enough to expose false positives and false negatives.

Do not generate a fixture that makes the implementation trivial by using artificial examples that mirror the detector's exact rules.

---

# 16. Evaluation Metrics

Evaluate the baseline using:

* precision
* recall
* F1
* false positives
* false negatives

Report the results clearly.

If the evaluation set is too small to support strong conclusions, explicitly state that limitation.

The purpose of the dataset is to establish a measurable baseline, not to manufacture a high score.

---

# 17. Testing

Add deterministic automated tests covering at least:

### Positive cases

* clear hiring announcement
* internship opening
* fellowship/program announcement
* application invitation
* contract/freelance opportunity

### Negative cases

* personal hiring success
* promotion
* career advice
* job-market discussion
* historical hiring

### Edge cases

* mixed positive and negative signals
* unusual punctuation
* casing variation
* minimal text
* missing optional fields
* malformed or incomplete raw records
* ambiguous opportunity language

### Detector behavior

* threshold behavior
* score generation
* explainability signals
* category behavior where implemented

Existing ingestion tests must continue to pass.

---

# 18. No Advanced AI Yet

Do not introduce:

* LLM classification
* embeddings
* vector databases
* semantic search infrastructure
* agent frameworks
* databases
* frontend work
* web crawling

for this task.

The purpose of this stage is to establish a deterministic baseline.

If repository inspection reveals an existing dependency or abstraction that genuinely needs to be reused, evaluate it before adding anything new.

---

# 19. No Source-Specific Logic

The detector must operate on the internal raw-record contract.

Do not write logic such as:

```python
if source == "twitter":
    ...
```

for behavior that should apply generally to professional opportunities.

Do not import or depend on Twikit inside the detector.

Source-specific behavior belongs inside the source adapter.

---

# 20. No Legacy NLP Logic

Do not copy from the legacy NLP project:

* Ghanaian Pidgin classification
* Pidgin marker sets
* Ghana/Nigeria heuristics
* corpus-specific scoring
* corpus-specific word limits
* aggressive text cleaning
* corpus-specific deduplication
* corpus persistence behavior

The detector must remain source- and domain-generic.

---

# 21. Plan Mode Requirement

Use Plan Mode first.

Before modifying code:

1. Inspect the repository.
2. Read the required documentation.
3. Inspect existing models and tests.
4. Identify the appropriate implementation location.
5. Determine whether an `OpportunityCandidate` model already exists.
6. Determine whether existing configuration patterns can be reused.
7. Determine how tests and fixtures are currently organized.
8. Identify potential conflicts with the existing architecture.

Then produce a concise implementation plan covering:

* proposed architecture
* files to create or modify
* model changes
* detection strategy
* configuration
* evaluation fixture
* tests
* expected risks
* unresolved questions

**STOP after presenting the plan.**

Do not implement until the plan is approved.

---

# 22. Implementation Phase

After approval:

1. Implement only the approved scope.
2. Reuse existing abstractions where appropriate.
3. Keep the detector independent of external source clients.
4. Keep the implementation small and interpretable.
5. Add tests alongside the implementation.
6. Add the labelled evaluation fixture.
7. Run the existing test suite.
8. Run the detector evaluation.
9. Inspect false positives and false negatives.
10. Make only justified corrections.

Do not expand the task into extraction, normalization, deduplication, eligibility, matching, or UI.

---

# 23. Quality Bar

The implementation should prioritize:

```text
Interpretability
      +
Correct architecture
      +
Measured baseline
      +
Testability
```

over:

```text
Complexity
      +
Large dependency footprint
      +
Unmeasured "AI" sophistication
```

A modest detector with known failure modes is more valuable than a complicated detector whose behavior cannot be evaluated.

---

# 24. Completion Report

After implementation, report:

### Architecture

What component was introduced and where it sits in the pipeline.

### Files

List every file created, modified, or deleted.

### Detection strategy

Explain the signal groups, scoring approach, and threshold.

### Evaluation

Report:

* precision
* recall
* F1
* false positives
* false negatives

### Tests

Report the tests run and their results.

### Failure analysis

Summarize the most important false positives and false negatives.

### Limitations

State what the current baseline does poorly.

### Next step

Recommend the next improvement based on observed evidence.

Do not introduce the next pipeline stage during this task.

Then STOP.
