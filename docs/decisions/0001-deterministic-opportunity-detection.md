# Deterministic opportunity detection

## Status

Accepted

## Context

The pipeline now ends at `RawPost`. The next boundary must decide whether a raw record is worth sending to extraction. The repository has no NLP stack, no labelled production corpus, and an explicit rule to establish a measurable deterministic baseline before introducing LLMs or embeddings.

## Decision

Implement `OpportunityDetector` as a group-capped phrase/regex scorer that always returns an `OpportunityCandidate` assessment.

- Score unique signal groups, not individual overlapping matches.
- Strong groups weigh 0.50; the default threshold is 0.45 so one unmistakable opening can pass alone.
- Supporting groups weigh 0.20 and cannot pass alone.
- Category assignment is a separate conservative pass and may be `None` on true opportunities.
- Evidence distinctions (`no_opportunity_evidence`, `confirmed_non_opportunity`, `insufficient_opportunity_evidence`) are reason codes, not a pipeline tri-state.

## Alternatives Considered

- Boolean rule cascade: harder to tune and weaker explainability.
- ML / LLM / embeddings: forbidden until this baseline’s measured failures justify them.

## Consequences

- Detection stays source-independent and has no new runtime dependencies.
- Informal openings and sarcastic “we’re hiring” commentary will be wrong until evidence says a richer method is needed.
- Extraction remains a later stage.
