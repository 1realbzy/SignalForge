# AGENTS.md

## Project

This repository is the active codebase for SignalForge, an opportunity intelligence platform.

The Python package import path remains `job_board_tool` so existing modules and tests stay stable.

Project root:

`C:\Users\1realbzy\Downloads\job_board_tool`

Treat this directory as the project workspace.

The purpose of this file is to define durable engineering rules for agents working in this repository. It should remain concise and should not contain task-specific implementation instructions.

---

## 1. Source of Truth

When information conflicts, use this order of authority:

1. Explicit user instruction for the current task
2. Existing working code and automated tests
3. This `AGENTS.md`
4. Current product and architecture documentation
5. Task-specific documentation or prompts
6. General assumptions

Do not modify working code merely to make it conform to stale documentation.

If documentation is outdated and the correct behavior is clear from the repository and current task, update the documentation when appropriate.

Never invent requirements simply because they appear useful.

---

## 2. Repository Boundary

Work only within this repository unless explicitly instructed otherwise.

Do not modify unrelated repositories, legacy projects, or reference codebases.

If external code is used as reference material, treat it as read-only.

Never copy:

* passwords
* API keys
* authentication tokens
* session cookies
* browser profiles
* private configuration
* other secrets

from another project.

---

## 3. Inspect Before Implementing

Before making significant changes:

1. Inspect the existing repository structure.
2. Read relevant existing modules and tests.
3. Read relevant documentation.
4. Identify existing abstractions and conventions.
5. Determine whether existing functionality can be reused.
6. Avoid creating duplicate abstractions.
7. Identify the smallest change that satisfies the requirement.

Do not assume an architecture when the repository can provide the answer.

For architectural, multi-file, or potentially destructive changes, plan before implementation.

---

## 4. Planning

For significant changes:

1. Inspect first.
2. Identify the relevant existing architecture.
3. Produce a concise implementation plan.
4. Identify files that will be created or modified.
5. Identify dependencies, risks, and edge cases.
6. In Plan Mode, wait for approval before implementing.
7. After approval, implement only the approved scope.

Do not silently expand the task.

If implementation reveals that the approved plan is insufficient, stop and explain what changed before making a materially larger change.

---

## 5. Requirement Discipline

Do not invent product requirements, infrastructure, integrations, schemas, or user behavior that have not been established.

When an important requirement is ambiguous:

1. Inspect existing project context.
2. Determine whether the repository already establishes an answer.
3. Identify the ambiguity.
4. Make the smallest safe assumption when reasonable.
5. Otherwise ask for clarification.

Do not build speculative infrastructure for hypothetical future requirements.

---

## 6. System Architecture

The intended high-level architecture is:

```text
Sources
   ↓
Raw Records
   ↓
Opportunity Detection
   ↓
Opportunity Extraction
   ↓
Normalization
   ↓
Deduplication
   ↓
Eligibility
   ↓
Candidate Profile
   ↓
Candidate Matching
   ↓
Ranking
   ↓
Product / API / UI
```

Each stage must have a clear responsibility.

Do not put:

* job extraction inside source ingestion
* candidate matching inside extraction
* eligibility logic inside source adapters
* source-specific scraping logic inside downstream business logic
* UI behavior inside data-processing components

Keep pipeline stages replaceable and independently testable.

---

## 7. Data Contracts

Use explicit internal models at the boundaries between major pipeline stages when a stable contract is justified.

A downstream component should depend on the contract of the previous stage, not its implementation details.

For example:

```text
External Source
      ↓
Source Adapter
      ↓
RawPost
      ↓
OpportunityDetector
      ↓
OpportunityCandidate
```

The detector should depend on `RawPost`, not on Twikit objects.

Extraction should depend on the opportunity-detection contract, not on source-client internals.

Do not pass source-specific objects into downstream business logic.

Do not create unnecessarily large schemas before their fields are justified by real requirements.

---

## 8. Source Adapters

External sources must be isolated behind source-specific adapters.

For example:

```text
X/Twitter
    ↓
XTwitterSource
    ↓
RawPost
```

Source adapters are responsible for source-specific concerns such as:

* authentication
* pagination
* rate limits
* retries
* source API/client behavior
* conversion into internal raw models

Source adapters are not responsible for:

* opportunity detection
* job extraction
* candidate matching
* ranking
* UI behavior

The rest of the application must not depend directly on Twikit or another source client's internal object model.

Source implementations should be replaceable.

Do not make the entire system dependent on one external provider.

---

## 9. Preserve Source Evidence

Ingestion must preserve useful source information.

Do not unnecessarily:

* remove URLs
* destroy original text
* discard source IDs
* discard timestamps
* discard provenance
* discard information required for later verification

Raw source content should remain available for downstream processing.

Normalization, extraction, and transformation happen later.

Structured information should remain traceable to its source evidence where practical.

---

## 10. Avoid Premature Complexity

Prefer the smallest implementation that establishes a reliable baseline.

Do not introduce:

* LLMs
* embeddings
* vector databases
* distributed systems
* unnecessary frameworks
* unnecessary services
* databases
* frontend components

unless the current task genuinely requires them.

Do not solve future problems before they exist.

Complexity must have a demonstrated reason to exist.

---

## 11. LLM Usage

LLMs should be introduced only where they provide measurable value.

Before replacing deterministic logic with an LLM:

1. Establish a deterministic baseline.
2. Create an evaluation dataset.
3. Measure performance.
4. Identify the specific failure mode.
5. Determine whether an LLM addresses that failure.
6. Compare the improvement against added complexity, cost, latency, and failure modes.

Do not use an LLM simply because the product is AI-related.

When an LLM is introduced, keep its role bounded and measurable.

---

## 12. Evaluation

Important intelligence components must be measurable.

Where practical, create labelled evaluation data and report:

* precision
* recall
* F1
* false positives
* false negatives

Additional metrics may be introduced when appropriate.

Do not optimize solely for passing a small hand-written test set.

Tests answer:

> Does the implementation behave as intended?

Evaluation answers:

> Is the system actually useful?

These are different questions.

Evaluation datasets should contain realistic positive, negative, and ambiguous examples where appropriate.

Avoid overfitting implementation logic to tiny fixtures.

---

## 13. Explainability and Observability

Important processing decisions should be inspectable.

Where practical, preserve:

* decision scores
* decision reasons
* detected signals
* provenance
* stage outcomes
* useful diagnostic information
* failure information

A downstream user or developer should be able to understand why an important decision occurred.

Do not expose secrets or unnecessarily sensitive information through logs or diagnostics.

---

## 14. Testing

Every meaningful new component should have automated tests.

Prefer:

* deterministic unit tests
* realistic fixtures
* mocks or fakes for external services
* failure-path tests
* edge-case tests
* malformed-input tests
* regression tests for discovered bugs

Do not require live external services for ordinary unit tests.

Never put real credentials into tests.

Existing tests must continue to pass unless a deliberate behavior change is being made.

---

## 15. External Services

Treat external services as unreliable dependencies.

Handle appropriately:

* authentication failures
* rate limits
* transient errors
* malformed responses
* unavailable services
* pagination failures
* API/client behavior changes

Do not attempt to bypass:

* CAPTCHAs
* Cloudflare
* anti-automation systems
* access controls
* platform security mechanisms

Do not implement techniques intended to evade platform restrictions.

---

## 16. Credentials and Secrets

Never commit or hardcode:

* passwords
* API keys
* authentication tokens
* session cookies
* browser profiles
* private keys
* secrets from `.env`

Use environment variables or appropriate local configuration.

Check `.gitignore` when introducing authentication or external services.

Never print secrets in:

* logs
* errors
* test output
* documentation
* source code
* screenshots or generated artifacts

---

## 17. Dependencies

Before adding a dependency:

1. Check whether existing dependencies already solve the problem.
2. Prefer the standard library for simple functionality.
3. Add a dependency only when it provides meaningful value.
4. Consider maintenance, security, size, and complexity.
5. Do not upgrade unrelated dependencies without a reason.

Keep the dependency surface small.

---

## 18. Configuration

Configuration must be separated from business logic.

Avoid scattering:

* thresholds
* URLs
* credentials
* environment-specific paths
* feature flags
* deployment settings
* other environment-dependent values

through implementation files.

Use the repository's established configuration conventions.

Do not hardcode environment-specific credentials or deployment configuration into application logic.

---

## 19. Documentation

Documentation should explain:

* what a component does
* why it exists
* its inputs and outputs
* important design decisions
* important limitations
* how it is tested

Keep documentation concise.

Do not duplicate the entire codebase in documentation.

Architectural decisions that materially affect the system should be recorded.

Task-specific implementation instructions belong in task prompts or relevant documentation, not in this file.

---

## 20. Refactoring

Do not refactor unrelated code while implementing a feature.

If an existing design genuinely blocks the requested work:

1. Identify the problem.
2. Explain why the change is necessary.
3. Make the smallest safe refactor.
4. Run the affected tests.
5. Report the change clearly.

Avoid broad cleanup during feature work.

---

## 21. File Changes

Before completing a task, know exactly which files were created or modified.

Do not silently modify unrelated files.

At the end of significant work, report:

* files created
* files modified
* files deleted
* important behavioral changes
* tests run
* known limitations

---

## 22. Existing Working Code

Do not rewrite functioning components merely to match personal stylistic preferences.

Preserve working behavior unless:

* the task requires a change
* a bug is identified
* a security issue exists
* the existing design prevents the required functionality

Prefer incremental improvement over unnecessary rewrites.

---

# Current Architecture

The current implemented ingestion boundary is:

```text
X/Twitter
    ↓
TwikitXClient
    ↓
XTwitterSource
    ↓
RawPost
```

The X/Twitter implementation uses Twikit behind an adapter.

Twikit-specific details must remain inside the X integration layer.

The current X ingestion layer has automated tests.

Do not unnecessarily rewrite it.

The next major processing boundary is:

```text
RawPost
    ↓
Opportunity Detection
```

---

# Legacy NLP Project

The reusable X/Twitter ingestion code originated from an older NLP project.

That project is not the active codebase.

Treat it as read-only reference material.

Do not modify it.

Do not copy its Ghanaian Pidgin-specific logic into this repository.

Specifically, do not introduce its:

* Ghanaian Pidgin classification
* Pidgin marker sets
* Ghana/Nigeria location heuristics
* corpus-specific scoring
* corpus-specific word limits
* aggressive text cleaning
* corpus-specific deduplication
* dataset persistence logic

The current platform must remain source- and domain-generic.

---

# Product Direction

The long-term goal is an opportunity intelligence system rather than a conventional job board.

The system should eventually help users discover relevant opportunities by combining:

* broad opportunity discovery
* structured opportunity extraction
* normalization
* deduplication
* hard eligibility filtering
* candidate profiling
* semantic candidate matching
* explainable ranking

The system should prioritize useful signal over simply collecting large quantities of data.

The core product question is not:

> How much opportunity data can we collect?

It is:

> Can we reliably discover, understand, filter, and rank opportunities that are genuinely useful to a candidate?

---

# Engineering Principle

When choosing between:

```text
more code
```

and:

```text
better evidence
```

prefer:

```text
better evidence
```

Build a measurable baseline first.

Then improve it based on observed failure modes.

Do not assume complexity equals intelligence.

Do not assume more data equals better results.

Do not assume an AI component is necessary simply because a problem can be described as an AI problem.

**Build. Measure. Inspect failures. Improve.**
