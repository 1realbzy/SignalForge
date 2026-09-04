# System Architecture Overview

## 1. Purpose

This document defines the technical architecture of `job_board_tool`.

The architecture is designed around a modular opportunity intelligence pipeline in which each stage has a distinct responsibility, explicit boundaries, and replaceable implementations.

The system should evolve from a reliable deterministic baseline toward more advanced intelligence only when measured limitations justify the added complexity.

---

# 2. Architectural Goal

The primary architectural goal is:

> Build a pipeline that can ingest fragmented opportunity information, transform it into reliable structured opportunities, determine candidate eligibility and relevance, and produce explainable results without tightly coupling the system to any single source, model, or technology.

The architecture should optimize for:

* correctness
* modularity
* testability
* provenance
* replaceability
* measurable improvement
* controlled complexity

---

# 3. High-Level Architecture

```text
                         EXTERNAL SOURCES
                              │
              ┌───────────────┼────────────────┐
              ↓               ↓                ↓
         X / Twitter     Career Pages      Other Sources
              │               │                │
              └───────────────┼────────────────┘
                              ↓
                       SOURCE ADAPTERS
                              │
                              ↓
                        RAW RECORDS
                              │
                              ↓
                   OPPORTUNITY DETECTION
                              │
                              ↓
                  OPPORTUNITY EXTRACTION
                              │
                              ↓
                       NORMALIZATION
                              │
                              ↓
                      DEDUPLICATION
                              │
                              ↓
                    HARD ELIGIBILITY
                              │
                              ↓
                    CANDIDATE PROFILE
                              │
                              ↓
                    CANDIDATE MATCHING
                              │
                              ↓
                  EXPLAINABLE RANKING
                              │
                              ↓
                       PRODUCT / API
                              │
                              ↓
                           USER
```

The implementation does not need to contain every component immediately.

The architecture describes the intended boundaries, not a requirement to build everything at once.

---

# 4. Architectural Layers

## 4.1 Source Layer

The source layer interacts with external systems where opportunity information originates.

Examples include:

* X/Twitter
* company career pages
* public ATS pages
* newsletters
* professional communities
* research organizations
* university opportunity pages
* other public sources

Each source should be implemented behind an adapter.

The source layer owns source-specific concerns.

It must not own downstream product intelligence.

---

# 5. Source Adapter Layer

Source adapters translate external source representations into internal raw-record models.

Example:

```text
X/Twitter
    ↓
TwikitXClient
    ↓
XTwitterSource
    ↓
RawPost
```

The rest of the application should not depend on Twikit objects.

The same principle must apply to future sources.

For example:

```text
Career Platform
    ↓
CareerPlatformSource
    ↓
RawPost / RawRecord
```

The downstream pipeline should see a common internal representation rather than a provider-specific object.

---

# 6. Raw Record Layer

Raw records represent source evidence before the system interprets it as an opportunity.

Examples include:

* `RawPost`
* future source-specific raw record types where justified

A raw record should preserve useful information such as:

* source
* source ID
* original text
* source URL
* source timestamp
* discovery timestamp
* relevant provenance
* safe source metadata

Raw records should not be aggressively cleaned or transformed for downstream convenience.

The system should retain the original evidence.

---

# 7. Opportunity Detection Layer

The detector determines whether a raw record plausibly represents an actionable professional opportunity.

```text
Raw Record
    ↓
OpportunityDetector
    ↓
OpportunityCandidate
```

The detector should answer:

> "Is this worth sending to the opportunity extraction stage?"

It should not attempt to fully understand the opportunity.

It should not:

* extract every job field
* determine candidate fit
* perform final eligibility
* rank opportunities
* depend on source-specific client objects

The initial implementation should establish a deterministic baseline.

More advanced methods may be introduced later if evaluation demonstrates a meaningful need.

---

# 8. Opportunity Extraction Layer

Extraction converts an opportunity candidate into structured information.

```text
OpportunityCandidate
    ↓
OpportunityExtractor
    ↓
Structured Opportunity
```

Potential information includes:

* title
* organization
* opportunity type
* location
* remote status
* experience requirements
* education requirements
* skills
* compensation
* deadline
* start date
* application information

Extraction should distinguish between:

```text
Explicit
Inferred
Unknown
```

The extractor must not silently turn missing information into assumptions.

---

# 9. Normalization Layer

Normalization converts equivalent representations into consistent internal forms.

Examples include:

```text
"WFH"
"work from home"
"remote"
"fully remote"
```

being represented through a common remote-status model.

Other candidates for normalization include:

* locations
* countries
* employment types
* dates
* currencies
* skills
* education levels
* experience expressions

Normalization should improve consistency without destroying source evidence.

It should not invent facts.

---

# 10. Deduplication Layer

Deduplication determines whether multiple records refer to the same underlying opportunity.

The same opportunity may appear through:

* multiple sources
* reposts
* employees
* recruiters
* communities
* different URLs
* different wording

Deduplication should prefer strong evidence before weaker similarity signals.

Potential evidence hierarchy:

```text
Exact canonical URL
        ↓
Strong source identifier
        ↓
Normalized identifying fields
        ↓
Similarity signals
```

The exact implementation should be driven by measured performance.

Deduplication must avoid both:

* keeping obvious duplicates
* incorrectly merging distinct opportunities

---

# 11. Eligibility Layer

Eligibility determines whether an opportunity satisfies explicit candidate constraints.

Potential constraints include:

* experience
* location
* remote requirements
* education
* work authorization
* opportunity type
* deadline

Eligibility should remain separate from general relevance.

For example:

```text
Highly relevant
+
Geographically ineligible
=
Not eligible
```

Unknown information should remain distinguishable from confirmed eligibility.

---

# 12. Candidate Profile Layer

The candidate profile represents the information required to evaluate opportunities against an individual.

Potential profile information includes:

* skills
* experience
* education
* projects
* certifications
* location
* work authorization
* preferred work mode
* opportunity preferences

The candidate profile should be independent from the source layer.

Source ingestion should never contain candidate-specific assumptions.

---

# 13. Matching Layer

Matching estimates how relevant an opportunity is to a candidate.

Potential signals include:

* required skill overlap
* preferred skill overlap
* experience alignment
* education alignment
* role similarity
* location compatibility
* work-mode compatibility
* opportunity-type preference

Matching should remain separate from hard eligibility.

Eligibility answers:

> "Can this candidate reasonably apply?"

Matching answers:

> "How relevant is this opportunity to this candidate?"

---

# 14. Ranking Layer

Ranking orders eligible opportunities according to justified signals.

Potential ranking factors include:

* candidate relevance
* skill alignment
* experience fit
* freshness
* opportunity quality
* source reliability
* candidate preferences
* completeness of information

Ranking should produce explanations alongside scores where practical.

The ranking system must not become an unexplained numerical black box.

---

# 15. Product / API Layer

The product layer consumes processed opportunity intelligence.

Potential responsibilities include:

* search
* filtering
* opportunity presentation
* candidate profile management
* explanations
* source verification
* user feedback

Business intelligence logic should remain in the underlying pipeline rather than being implemented directly in UI code.

The UI should consume application-level contracts.

---

# 16. Data Flow Boundaries

The primary boundaries are:

```text
External Source
      ↓
Source Adapter
      ↓
Raw Record
      ↓
Opportunity Candidate
      ↓
Structured Opportunity
      ↓
Normalized Opportunity
      ↓
Deduplicated Opportunity
      ↓
Eligibility Result
      ↓
Candidate Match
      ↓
Ranked Result
```

Each boundary should have a clear contract.

A component should depend on the contract of the previous stage rather than its implementation details.

---

# 17. Provenance

Provenance is a first-class architectural concern.

Important information should remain traceable through the pipeline.

Conceptually:

```text
Ranked Result
      ↓
Opportunity
      ↓
Source Evidence
      ↓
Original Source Record
```

This supports:

* user verification
* debugging
* evaluation
* deduplication
* extraction auditing
* trust

Transformations should not sever this chain unnecessarily.

---

# 18. Replaceability

The architecture should make major components replaceable.

For example:

```text
Twikit
   ↓
Another X source implementation
```

should not require rewriting:

* opportunity detection
* extraction
* normalization
* matching
* ranking

Likewise:

```text
Deterministic Detector
        ↓
Improved Detector
```

should not require rewriting the source layer.

The same principle applies to extraction and matching techniques.

---

# 19. Current Implementation

The currently implemented portion is:

```text
X/Twitter
    ↓
TwikitXClient
    ↓
XTwitterSource
    ↓
RawPost
    ↓
OpportunityDetector
    ↓
OpportunityCandidate
```

The X integration is isolated behind an adapter.

Twikit-specific behavior remains inside that integration layer.

Opportunity detection consumes `RawPost` only and does not live in the source adapter.

The current ingestion and detection implementations have automated tests.

They should not be rewritten unnecessarily.

---

# 20. Current Development Boundary

The next implementation boundary is:

```text
OpportunityCandidate
    ↓
Opportunity Extraction
```

The extractor should consume the detection contract rather than source-client internals.

---

# 21. Technology Strategy

Use the simplest technology capable of establishing a reliable baseline.

Do not introduce infrastructure simply because it may eventually be useful.

Potential future technologies such as:

* LLMs
* embeddings
* vector databases
* queues
* distributed workers
* advanced orchestration
* additional databases

must earn their place through demonstrated requirements.

Technology choices should follow measured system needs.

---

# 22. Reliability

External dependencies should be treated as unreliable.

Source adapters should account for:

* authentication failures
* rate limits
* transient failures
* malformed responses
* pagination failures
* service outages
* provider behavior changes

Internal pipeline stages should fail explicitly rather than silently producing misleading data.

---

# 23. Security

Credentials and authentication material must remain outside source code and documentation.

Never store or log:

* passwords
* API keys
* authentication tokens
* session cookies
* private keys
* browser profiles

Use environment variables or appropriate configuration mechanisms.

External-source security mechanisms must not be bypassed.

---

# 24. Testing Strategy

Each meaningful architectural component should have deterministic tests.

Tests should cover:

* normal behavior
* edge cases
* malformed inputs
* failure paths
* boundary conditions
* regression cases

External integrations should use mocks or fakes for ordinary tests.

Live services should not be required to validate basic pipeline behavior.

---

# 25. Evaluation Strategy

Tests alone are insufficient for intelligence components.

Where appropriate, components should have labelled evaluation datasets.

For example:

```text
RawPost
   ↓
Detector
   ↓
Predicted opportunity
   ↓
Compare against labelled truth
   ↓
Precision / Recall / F1
```

This allows architectural improvements to be evaluated rather than assumed to be better.

---

# 26. Observability

Important decisions should be inspectable.

Where appropriate, preserve:

* scores
* signals
* reasons
* stage outcomes
* provenance
* processing failures
* useful diagnostic metadata

Observability should support both development and future product explanations.

Do not expose secrets or unnecessarily sensitive information.

---

# 27. Architecture Evolution

This architecture is intentionally incomplete.

Not every future component should be designed in detail before implementation begins.

The correct process is:

```text
Establish boundary
      ↓
Implement baseline
      ↓
Collect real evidence
      ↓
Measure performance
      ↓
Identify failure modes
      ↓
Improve architecture where justified
```

Future architecture should be based on observed requirements rather than speculation.

---

# 28. Core Architectural Principle

The system should be built as a sequence of understandable, measurable transformations:

```text
Source Evidence
      ↓
Detected Opportunity
      ↓
Structured Opportunity
      ↓
Normalized Opportunity
      ↓
Unique Opportunity
      ↓
Eligible Opportunity
      ↓
Relevant Opportunity
      ↓
Ranked Opportunity
```

Each transformation should have:

* a defined purpose
* an explicit input
* an explicit output
* measurable behavior
* tests
* explainable failure modes where practical

The architecture should remain simple until evidence demonstrates that greater complexity is necessary.
