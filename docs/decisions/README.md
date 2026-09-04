# Architecture Decisions

## 1. Purpose

This directory contains Architecture Decision Records (ADRs) for decisions that materially affect the structure, behavior, dependencies, interfaces, or long-term direction of `job_board_tool`.

An ADR records **why** an important decision was made, not a detailed description of how the entire system works.

General architecture belongs in:

```text
docs/architecture/
```

Product requirements belong in:

```text
docs/product/
```

Task-specific implementation instructions belong in:

```text
docs/prompts/
```

---

# 2. When to Create an ADR

Create an ADR when a decision:

* materially affects system architecture
* introduces or removes an important dependency
* establishes an interface used by multiple components
* changes an established architectural boundary
* selects between meaningful technical alternatives
* introduces a significant security or reliability constraint
* would be expensive or confusing to reconsider later

Do not create an ADR for:

* ordinary bug fixes
* minor refactoring
* formatting decisions
* trivial implementation details
* temporary experiments
* every dependency addition

The goal is to record consequential decisions, not every development action.

---

# 3. ADR Format

Each ADR should normally contain:

```text
# Title

## Status

## Context

## Decision

## Alternatives Considered

## Consequences
```

### Status

Examples:

```text
Proposed
Accepted
Superseded
Rejected
Deprecated
```

### Context

Explain the problem or situation that required a decision.

### Decision

State the chosen approach clearly.

### Alternatives Considered

Record meaningful alternatives that were evaluated and why they were not selected.

### Consequences

Record the important benefits, costs, limitations, and trade-offs created by the decision.

---

# 4. Naming

Use sequential numbering:

```text
0001-short-description.md
0002-short-description.md
0003-short-description.md
```

Use concise filenames.

Examples:

```text
0001-source-adapter-boundary.md
0002-deterministic-opportunity-detection.md
```

---

# 5. Decision Principles

Architecture decisions should be based on:

* actual project requirements
* repository evidence
* measured performance
* reliability considerations
* security considerations
* maintainability
* appropriate complexity

Prefer evidence over speculation.

A technically sophisticated solution is not automatically a better solution.

---

# 6. Relationship to Other Documentation

ADRs should not become duplicate architecture documentation.

For example:

```text
ADR
    ↓
Why was this architectural decision made?

Architecture Documentation
    ↓
What is the resulting architecture?

Task Prompt
    ↓
What are we implementing now?
```

When an accepted decision changes the architecture, update the relevant architecture documentation as necessary.

---

# 7. Changing a Decision

Do not silently rewrite historical decisions.

If an accepted decision is later changed:

1. Create a new ADR describing the new decision.
2. Mark the previous ADR as superseded.
3. Explain why the change was necessary.
4. Update affected architecture documentation.
5. Update implementation where required.

This preserves the reasoning history of the project.

---

# 8. Evidence-Based Decisions

When possible, decisions should reference evidence such as:

* evaluation results
* benchmark results
* production observations
* failure analysis
* reliability data
* security findings
* measured costs

Avoid making major architectural decisions solely because a technology is popular or appears sophisticated.

---

# 9. Current Decision Areas

Potential decisions worth recording as the project develops include:

* source adapter architecture
* raw-record contract
* opportunity detection strategy
* extraction strategy
* normalization approach
* deduplication strategy
* eligibility architecture
* matching methodology
* use of LLMs
* use of embeddings
* persistence architecture
* deployment architecture

Only create ADRs when these decisions become sufficiently consequential.

---

# 10. Current Status

No large ADR collection is required at the beginning of the project.

The project should create decision records organically as meaningful architectural choices are made.

The purpose of this directory is to preserve important reasoning without creating documentation overhead.

---

# 11. Core Principle

> Record decisions that matter. Do not document for the sake of documenting.
