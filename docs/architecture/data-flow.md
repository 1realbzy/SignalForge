# Data Flow

## 1. Purpose

This document defines how information moves through `job_board_tool`, how each pipeline stage transforms that information, and what information must be preserved throughout the process.

The goal is to establish clear data boundaries without prematurely defining implementation details that have not yet been validated.

---

# 2. Core Data Flow

The intended end-to-end flow is:

```text
External Sources
       ↓
Source Adapters
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
Hard Eligibility
       ↓
Candidate Profile
       ↓
Candidate Matching
       ↓
Ranking
       ↓
Product / API
       ↓
User
```

The system does not need to implement every stage immediately.

Each stage should be introduced and validated independently.

---

# 3. Data Transformation Principle

Every stage should perform a specific transformation.

Conceptually:

```text
Raw evidence
    ↓
"Is this an opportunity?"
    ↓
"What is the opportunity?"
    ↓
"Can we represent it consistently?"
    ↓
"Is this the same opportunity as another record?"
    ↓
"Is the candidate allowed to pursue it?"
    ↓
"How relevant is it to this candidate?"
    ↓
"How should we rank it?"
```

A stage should not silently perform the responsibilities of another stage.

---

# 4. External Source → Source Adapter

External sources produce provider-specific representations.

Examples:

```text
X/Twitter
Career Page
ATS
Newsletter
Community
Research Organization
```

Each source is handled by its own adapter.

The adapter is responsible for translating provider-specific information into an internal raw-record representation.

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

The rest of the system must not depend on Twikit-specific objects.

---

# 5. Source Adapter → Raw Record

The raw record is the first internal representation.

It represents:

> "This is what the source gave us."

It should preserve useful evidence rather than immediately transforming the content into a presumed job listing.

A raw record should contain, where available:

* source
* source ID
* original text
* source URL
* source timestamp
* discovery timestamp
* source-specific metadata that is useful and safe
* provenance

For X/Twitter, the current internal representation is `RawPost`.

---

# 6. Raw Record Requirements

Raw records should be treated as source evidence.

The ingestion layer should avoid:

* aggressive cleaning
* semantic interpretation
* job classification
* candidate filtering
* candidate matching
* source-specific assumptions outside the adapter

In particular, do not destroy information simply because it is inconvenient for the current processing stage.

Examples of information that should generally be preserved:

```text
Original text
URLs
Source IDs
Timestamps
Author/source information
Provenance
```

Transformations can happen downstream.

---

# 7. Raw Record → Opportunity Candidate

The opportunity detector evaluates whether a raw record plausibly contains an actionable professional opportunity.

```text
RawPost
    ↓
OpportunityDetector
    ↓
OpportunityCandidate
```

The detector answers:

> "Is there enough evidence that this record represents a professional opportunity worth processing further?"

It does not need to know every detail of the opportunity.

A detected candidate may still have unknown:

* title
* organization
* location
* deadline
* skills
* compensation
* eligibility requirements

Those belong to later stages.

---

# 8. Opportunity Candidate

An `OpportunityCandidate` should preserve the connection to the original raw record.

Conceptually it may contain:

```text
Raw record reference
Detection decision
Detection score
Detection category
Detection signals/reasons
Provenance
```

The exact schema should be determined during implementation.

The detector should not replace the original evidence with its interpretation.

---

# 9. Opportunity Candidate → Structured Opportunity

The extraction stage converts a detected candidate into structured opportunity information.

```text
OpportunityCandidate
       ↓
OpportunityExtractor
       ↓
Structured Opportunity
```

Potential fields include:

* title
* organization
* opportunity type
* location
* remote status
* experience requirements
* education requirements
* required skills
* preferred skills
* compensation
* deadline
* start date
* application URL
* work authorization
* other relevant requirements

The extractor should preserve uncertainty.

Each important field should conceptually be capable of representing:

```text
Explicitly stated
Inferred
Unknown
```

The exact implementation may vary.

---

# 10. Extraction Evidence

Structured fields should remain traceable to source evidence where practical.

For example:

```text
Opportunity
    │
    ├── title
    │      ↓
    │   source evidence
    │
    ├── location
    │      ↓
    │   source evidence
    │
    └── deadline
           ↓
        source evidence
```

This becomes important for:

* debugging
* evaluation
* user trust
* correction
* future extraction improvements

The system should not rely solely on a final structured object with no connection to its origin.

---

# 11. Structured Opportunity → Normalized Opportunity

Normalization converts different representations of the same concept into a consistent internal form.

Examples:

```text
"WFH"
"Work from home"
"Fully remote"
"Remote"
```

may be normalized into a common remote-status representation.

Other normalization targets may include:

* locations
* countries
* employment types
* dates
* currencies
* skills
* education levels
* experience expressions

Normalization should improve consistency without changing the underlying source evidence.

---

# 12. Normalization Rules

Normalization must not invent information.

For example:

If the source says:

```text
Remote
```

the system may normalize the representation of remote status.

It must not automatically infer:

```text
Worldwide
```

unless there is sufficient evidence.

Similarly:

```text
Unknown location
```

must not become:

```text
Global
```

simply because the opportunity appears online.

---

# 13. Normalized Opportunity → Deduplication

Multiple source records may represent the same underlying opportunity.

Example:

```text
Company employee post
        ↓
Company career page
        ↓
Community repost
        ↓
Recruiter post
```

These may all refer to one opportunity.

Deduplication determines whether records should be treated as the same underlying opportunity.

---

# 14. Deduplication Evidence

Deduplication should prefer strong evidence before weak similarity.

A conceptual order is:

```text
Exact canonical URL
        ↓
Strong source identifier
        ↓
Matching normalized identifying fields
        ↓
Similarity signals
```

The exact algorithm should be determined through evaluation.

The system must avoid both:

```text
Missed duplicates
```

and:

```text
False merges
```

False merges are especially important because incorrectly combining two different opportunities can destroy useful information.

---

# 15. Deduplicated Opportunity → Eligibility

After an opportunity has been structured and deduplicated, the system can evaluate explicit candidate constraints.

```text
Opportunity
     +
Candidate Constraints
     ↓
Eligibility Engine
     ↓
Eligibility Result
```

Potential constraints include:

* experience
* location
* remote status
* education
* work authorization
* opportunity type
* application deadline

---

# 16. Eligibility States

Eligibility should not be reduced to only:

```text
True / False
```

where important information is unknown.

A more useful conceptual model is:

```text
Eligible
Ineligible
Unknown
```

For example:

```text
Work authorization required
```

cannot safely be evaluated as satisfied if the opportunity provides no information about it.

Unknown information should remain explicit.

The final implementation may use a richer state model where justified.

---

# 17. Candidate Profile

Candidate information enters the pipeline through a separate candidate-profile path.

Conceptually:

```text
Candidate Information
        ↓
Candidate Profile
        ↓
Eligibility
        ↓
Matching
        ↓
Ranking
```

The candidate profile may eventually include:

* skills
* experience
* education
* projects
* certifications
* location
* work authorization
* preferred work mode
* opportunity preferences

Candidate-specific information must not leak into source ingestion or generic opportunity detection.

---

# 18. Eligibility vs Matching

These are separate transformations.

Eligibility asks:

> "Does this opportunity violate an explicit candidate constraint?"

Matching asks:

> "How relevant is this opportunity to this candidate?"

For example:

```text
Opportunity:
Senior Machine Learning Engineer

Candidate:
Strong ML skills
No required experience
```

The opportunity may have:

```text
High skill similarity
+
Failed experience eligibility
```

Therefore:

```text
Relevant ≠ Eligible
```

The system must preserve this distinction.

---

# 19. Candidate Matching

Matching evaluates an eligible or potentially eligible opportunity against the candidate profile.

Potential signals include:

* required skill overlap
* preferred skill overlap
* experience alignment
* education alignment
* role similarity
* location compatibility
* work-mode compatibility
* opportunity-type preference

Matching may eventually use deterministic, statistical, semantic, or hybrid methods.

The method should be selected based on measured performance rather than assumed in advance.

---

# 20. Matching → Ranking

Matching produces candidate-opportunity relevance information.

Ranking combines this with other justified signals.

Conceptually:

```text
Opportunity
     +
Eligibility
     +
Candidate Match
     +
Quality / Freshness / Other Valid Signals
     ↓
Ranking
     ↓
Ranked Opportunity
```

Potential ranking signals include:

* candidate relevance
* skill alignment
* experience fit
* freshness
* opportunity quality
* source reliability
* candidate preferences
* information completeness

The ranking system should retain enough information to explain important decisions.

---

# 21. Ranking → Product

The product layer receives processed opportunity information.

A user-facing result should eventually be able to communicate:

```text
Opportunity
Why it was surfaced
Why it fits the candidate
Eligibility status
Important requirements
Source
Application information
```

The UI should not need to reproduce pipeline logic.

It should consume stable application-level contracts.

---

# 22. Provenance Chain

The system should preserve a provenance chain through the pipeline.

Conceptually:

```text
Ranked Result
      ↓
Candidate Match
      ↓
Eligibility Result
      ↓
Deduplicated Opportunity
      ↓
Normalized Opportunity
      ↓
Structured Opportunity
      ↓
Opportunity Candidate
      ↓
Raw Record
      ↓
External Source
```

Not every intermediate object must necessarily be persisted forever.

However, the architecture should preserve enough linkage to reconstruct why an opportunity exists and where its information originated.

---

# 23. Failure Handling

A pipeline stage should not silently produce valid-looking output when processing has failed.

Preferred behavior:

```text
Failure
   ↓
Record / surface failure
   ↓
Preserve available source evidence
   ↓
Retry when appropriate
   ↓
Continue only when the data contract remains valid
```

Examples include:

* malformed source data
* extraction failure
* normalization failure
* external verification failure
* unexpected schema changes

A failed transformation should not silently become a fabricated fact.

---

# 24. Partial Information

Real opportunity data will often be incomplete.

The pipeline must be able to process partially known opportunities.

For example:

```text
Title: Known
Organization: Known
Location: Unknown
Salary: Unknown
Deadline: Known
Skills: Partially known
```

Missing information should remain missing.

The system should not reject every incomplete opportunity automatically unless the relevant downstream requirement requires that information.

---

# 25. Data Quality States

As the system matures, opportunities may benefit from explicit quality indicators.

Potential concepts include:

* extraction completeness
* source reliability
* freshness
* verification status
* provenance completeness

These should be introduced only when they support an actual product or evaluation need.

Do not create speculative quality scores without a defined purpose.

---

# 26. Current Implemented Flow

Currently implemented:

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

The raw ingestion layer collects and represents source information.

The detector assesses whether that evidence looks like an actionable opportunity. It does not extract structured opportunity fields.

---

# 27. Immediate Next Flow

The next implementation is:

```text
OpportunityCandidate
    ↓
OpportunityExtractor
    ↓
Structured Opportunity
```

The extractor should consume `OpportunityCandidate` records with `is_opportunity=True`.

---

# 28. Data Flow Principle

The pipeline should follow this rule:

> Preserve evidence early, transform deliberately, and never replace unknown information with assumptions.

The architecture should make it possible to answer three questions for any important result:

```text
What did the system conclude?
Why did it conclude it?
What source evidence supports that conclusion?
```

Those questions are fundamental to building a trustworthy opportunity intelligence system.
