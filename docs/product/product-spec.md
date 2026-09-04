# Product Specification

## 1. Product Definition

SignalForge is an opportunity intelligence platform designed to discover, understand, filter, and rank professional opportunities from fragmented sources.

The Python package import path remains `job_board_tool`.

It is not intended to be a conventional job board.

A conventional job board primarily answers:

> "What jobs have been posted here?"

This system aims to answer:

> "What legitimate opportunities exist that are relevant to this candidate, including opportunities they may not have found through conventional job boards?"

The system should eventually combine source discovery, opportunity detection, structured extraction, normalization, deduplication, eligibility reasoning, candidate matching, and explainable ranking.

---

# 2. Problem

Professional opportunities are distributed across many channels.

Potential opportunities may appear in:

* social media posts
* company career pages
* applicant-tracking-system pages
* newsletters
* professional communities
* university pages
* research organizations
* fellowship programs
* startup communities
* other public sources

This creates several problems.

### 2.1 Fragmented discovery

A candidate may need to search many unrelated sources to discover opportunities.

### 2.2 High information noise

Many posts discuss jobs without actually offering one.

Examples include:

* "I just got hired!"
* career advice
* job-market commentary
* reposts without actionable information
* discussions about hiring
* generic "we should hire more..." commentary

A system that simply searches for words such as "hiring" will generate substantial noise.

### 2.3 Duplicate opportunities

The same opportunity can appear:

* on multiple platforms
* through multiple accounts
* as reposts
* through recruitment agencies
* through company employees
* in multiple formats

Candidates should not have to process the same opportunity repeatedly.

### 2.4 Ambiguous eligibility

Listings frequently omit or inconsistently state:

* experience requirements
* geographic restrictions
* remote eligibility
* work authorization
* education requirements
* application deadlines
* employment type

The system therefore needs to distinguish known facts from unknown information.

### 2.5 Poor candidate relevance

A candidate can find a real opportunity and still have little reason to apply.

Discovery alone is not enough.

The system must eventually determine:

> "How relevant is this opportunity to this particular candidate?"

---

# 3. Product Goal

The primary goal is to build a system that produces a **small, high-quality set of actionable opportunities** rather than maximizing the number of records collected.

The system should optimize for:

```text
Useful opportunities
        >
Raw opportunity volume
```

The product should help a candidate move from:

```text
"I have to search everywhere."
```

to:

```text
"Here are the opportunities worth my attention,
why they fit me, and where the evidence came from."
```

---

# 4. Initial Target User

The initial target is an early-career candidate, including:

* students
* recent graduates
* interns
* entry-level professionals
* candidates with approximately internship to one year of relevant experience

The initial product direction is particularly relevant to technology-oriented opportunities such as:

* software engineering
* data
* AI/ML
* analytics
* technical research
* related technology roles

However, the underlying opportunity model and discovery system should remain domain-generic.

The architecture must not permanently assume that every opportunity is an AI, data, or software role.

---

# 5. Geographic and Work-Mode Direction

The initial product should support opportunities with different geographic models, including:

* fully remote
* hybrid
* on-site
* location-specific
* globally accessible opportunities
* opportunities with explicit geographic restrictions

Remote accessibility is an important product concern but should be represented as structured opportunity information rather than hard-coded into source ingestion.

Geographic eligibility should ultimately be handled by the eligibility and matching layers.

---

# 6. Opportunity Types

The system should be capable of representing more than traditional full-time jobs.

Potential opportunity types include:

* full-time employment
* part-time employment
* internships
* graduate programs
* fellowships
* apprenticeships
* research opportunities
* contracts
* freelance opportunities
* temporary roles
* other legitimate professional programs or openings

The system should not treat every mention of these words as an opportunity.

The existence of actionable evidence is what matters.

---

# 7. Core User Journey

The eventual user experience should follow approximately this flow:

```text
Candidate profile
      ↓
System discovers opportunities
      ↓
Opportunity detection
      ↓
Structured extraction
      ↓
Normalization
      ↓
Deduplication
      ↓
Hard eligibility filtering
      ↓
Candidate matching
      ↓
Explainable ranking
      ↓
Candidate reviews opportunity
      ↓
Candidate verifies source
      ↓
Candidate applies / takes action
```

The product should minimize the amount of irrelevant information the candidate needs to process.

---

# 8. Core System Capabilities

## 8.1 Opportunity Discovery

Collect candidate information from multiple sources.

The system should eventually support multiple independent source adapters.

The discovery layer should maximize useful recall without allowing downstream systems to become dependent on one source.

---

## 8.2 Opportunity Detection

Determine whether a raw source record plausibly represents an actionable professional opportunity.

Input:

```text
Raw source record
```

Output:

```text
Opportunity candidate
```

Detection is intentionally separate from extraction.

A record can be identified as an opportunity candidate without yet knowing:

* exact job title
* salary
* deadline
* required skills
* location
* complete application information

---

## 8.3 Opportunity Extraction

Convert an opportunity candidate into structured information.

Potential fields include:

* title
* organization
* opportunity type
* location
* remote status
* experience requirements
* education requirements
* skills
* deadline
* start date
* compensation
* application URL
* work authorization requirements

Extraction should preserve unknown fields rather than inventing information.

---

## 8.4 Normalization

Convert different representations of the same concept into consistent internal representations.

Examples:

```text
"WFH"
"work from home"
"fully remote"
"remote"
```

may eventually map to a common remote representation.

Normalization should not change the underlying evidence or silently create facts that were not present.

---

## 8.5 Deduplication

Identify records that refer to the same underlying opportunity.

The system should eventually combine evidence from multiple sources where appropriate while preserving provenance.

Deduplication should prioritize reliable identifiers and strong evidence before weaker similarity signals.

---

## 8.6 Hard Eligibility

Determine whether an opportunity violates explicit candidate constraints.

Potential constraints include:

* maximum experience
* required location
* remote requirement
* education requirements
* work authorization
* deadline
* opportunity type

Hard eligibility should be distinct from softer relevance scoring.

An opportunity can be highly relevant but still ineligible.

---

## 8.7 Candidate Profile

Represent the candidate using structured information such as:

* skills
* experience
* education
* projects
* certifications
* location
* work authorization
* preferred work mode
* opportunity preferences

The profile should eventually support both deterministic eligibility rules and semantic matching.

---

## 8.8 Candidate Matching

Estimate how relevant an eligible opportunity is to a specific candidate.

Matching may consider:

* skill overlap
* experience fit
* education fit
* role similarity
* opportunity type
* location
* work mode
* candidate preferences

Matching should not simply count keyword overlap.

---

## 8.9 Explainable Ranking

Rank opportunities while exposing meaningful reasons for the ranking.

Possible explanations:

* strong required-skill overlap
* experience alignment
* location compatibility
* remote compatibility
* opportunity freshness
* candidate preference alignment
* missing information
* eligibility status

The system should avoid presenting opaque scores without useful interpretation.

---

# 9. Evidence and Provenance

Every opportunity should remain connected to its source evidence.

Where possible, preserve:

* source
* source ID
* original text
* source URL
* publication timestamp
* discovery timestamp
* relevant supporting evidence

The system should allow a candidate to verify where an opportunity came from.

This is a core trust requirement.

---

# 10. Unknown Information

The system must distinguish:

```text
Known
Unknown
Inferred
```

For example:

If a post does not mention work authorization, the system should not automatically assume:

```text
work authorization required = false
```

It should represent the information as unknown.

Similarly, inferred information should not be presented as if it were explicitly stated.

---

# 11. Product Quality Principles

## Signal over volume

Collecting more opportunities is not automatically better.

A noisy feed can be worse than a smaller, more accurate one.

## Evidence over assumption

Important conclusions should be traceable to source evidence.

## Discovery before intelligence

The system must first reliably find opportunities before increasingly sophisticated matching and ranking layers are justified.

## Deterministic baseline before AI complexity

Use deterministic methods where they establish a strong baseline.

Introduce LLMs, embeddings, or other advanced techniques only when measured failure modes justify them.

## Explainability by default

Important system decisions should have inspectable reasons.

## Replaceable components

Sources, detection strategies, extraction methods, and matching approaches should be replaceable without rewriting the entire system.

## Measure before optimizing

Performance improvements should be based on observed errors rather than intuition alone.

---

# 12. MVP Definition

The first meaningful MVP does not require a polished frontend.

The MVP should prove that the underlying intelligence pipeline works.

Minimum capabilities:

### Source ingestion

At least one reliable source adapter.

### Opportunity detection

A measurable baseline distinguishing opportunities from non-opportunities.

### Opportunity extraction

A structured representation of detected opportunities.

### Normalization

Consistent representation of important fields.

### Deduplication

Basic but measurable duplicate detection.

### Eligibility

Deterministic filtering based on explicit candidate constraints.

### Matching

A baseline candidate-opportunity relevance system.

### Explainability

Reasons for important system decisions.

### Evaluation

A labelled benchmark capable of measuring pipeline quality.

A user interface can be added after these capabilities demonstrate useful performance.

---

# 13. Non-Goals

The initial product is not intended to be:

* a generic job board
* an applicant-tracking system
* a recruitment agency
* an autonomous job-application bot
* a social network
* a general-purpose web crawler
* an enterprise HR platform
* an LLM wrapper with no measurable intelligence advantage

The system should not automatically apply to opportunities on behalf of candidates during the initial stages.

---

# 14. Success Metrics

The product should eventually measure performance at multiple levels.

## Discovery

* precision
* recall
* F1
* false-positive rate
* false-negative rate

## Extraction

* field-level accuracy
* required-field completeness
* extraction failure rate

## Deduplication

* duplicate precision
* duplicate recall
* false merge rate
* missed duplicate rate

## Eligibility

* eligibility accuracy
* false rejection rate
* false acceptance rate

## Matching

* top-k relevance
* useful-opportunity rate
* candidate feedback
* ranking quality

## System

* ingestion success rate
* processing latency
* retry/failure rate
* source reliability

The exact benchmark and metrics should evolve as the system gains real data.

---

# 15. Product Differentiation

The product should not compete primarily on:

> "We have more job listings."

Its intended differentiation is:

> "We find opportunities across fragmented sources, determine which ones are actually actionable, remove noise and duplicates, understand eligibility, and identify which ones are worth your attention."

This makes **opportunity intelligence**, rather than listing volume, the central product capability.

---

# 16. Current Scope

Implemented:

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

Next:

```text
OpportunityCandidate
    ↓
Opportunity Extraction
```

The current development priority is therefore improving the quality of the opportunity pipeline rather than building a user-facing application.

---

# 17. Development Philosophy

The product should be developed in measurable stages:

```text
Build
  ↓
Label
  ↓
Measure
  ↓
Inspect failures
  ↓
Improve
  ↓
Measure again
```

Do not add complexity merely because a more sophisticated technique exists.

The system should earn its complexity through demonstrated limitations of simpler approaches.
