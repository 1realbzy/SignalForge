# Opportunity Model

## 1. Purpose

This document defines the conceptual model of an opportunity within `job_board_tool`.

It establishes:

* what qualifies as an opportunity
* what does not
* the difference between source evidence and an opportunity
* the lifecycle of an opportunity
* the information the system may eventually extract
* how uncertainty and provenance should be represented

This is a conceptual product and data contract.

It is not a final database schema.

The implementation should evolve as real source data and evaluation results reveal additional requirements.

---

# 2. What Is an Opportunity?

An opportunity is a source-backed, actionable professional opening or program that a person could reasonably take action on.

The key properties are:

```text
Source-backed
+
Professional
+
Actionable
=
Potential Opportunity
```

Examples include:

* a company hiring for a role
* an internship opening
* a graduate program
* a fellowship
* a research position
* an apprenticeship
* a contract opportunity
* a legitimate freelance engagement
* another professional program or opening

The exact opportunity type is secondary to whether there is actionable evidence.

---

# 3. What Is Not an Opportunity?

The system should not treat every employment-related statement as an opportunity.

Examples of non-opportunities include:

### Personal career announcements

```text
"I just started my new role at Company X."
```

### Career advice

```text
"Here are five things you should do to get hired."
```

### Job-market commentary

```text
"The tech job market is terrible right now."
```

### General discussion

```text
"Companies should hire more junior developers."
```

### Historical information

```text
"We hired three engineers last year."
```

### Unactionable engagement bait

```text
"Would you take a job at this company?"
```

### Vague statements without actionable evidence

```text
"We may be hiring soon."
```

These may contain useful context, but they should not automatically become opportunities.

---

# 4. Actionability

Actionability is central to the model.

An opportunity should provide, or reasonably point toward, something a candidate can act upon.

Examples of actionable evidence:

* explicit hiring announcement
* application invitation
* application URL
* stated opening
* named role with instructions to apply
* recruitment announcement
* fellowship application announcement
* research opening with a stated application process

An opportunity does not need to contain every detail.

For example, this may still be a valid opportunity:

```text
"We're hiring software engineering interns.
DM me for the application details."
```

The system can recognize the opportunity while leaving the missing details unknown.

---

# 5. Opportunity Evidence

An opportunity is an interpretation of source evidence.

The source record is the evidence.

The opportunity is the structured representation derived from that evidence.

Therefore:

```text
Source Record
      ↓
Evidence
      ↓
Opportunity Interpretation
```

The system must preserve the relationship between these two.

---

# 6. Source Record vs Opportunity

These concepts must remain separate.

## Source Record

Represents:

> "This is what a source published."

It may contain:

* raw text
* URL
* source ID
* timestamp
* author
* source metadata

## Opportunity Candidate

Represents:

> "This source record appears to contain a professional opportunity."

It may contain:

* detection decision
* detection score
* detected signals
* broad category
* source reference

## Structured Opportunity

Represents:

> "This is the opportunity information extracted from the evidence."

It may contain:

* organization
* title
* opportunity type
* requirements
* location
* deadline
* application information
* compensation
* provenance

The distinctions are:

```text
Raw Record
    ↓
Potential Opportunity
    ↓
Structured Opportunity
```

---

# 7. Opportunity Lifecycle

The intended lifecycle is:

```text
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
Eligibility Assessment
    ↓
Candidate Match
    ↓
Ranked Opportunity
```

Not every raw record reaches every stage.

For example:

```text
Raw Record
    ↓
Not an opportunity
    ↓
Stop
```

A detected opportunity may also fail extraction or contain insufficient information for later stages.

---

# 8. Opportunity Types

The model should support multiple professional opportunity types.

Initial conceptual categories:

```text
Employment
Internship
Graduate Program
Fellowship
Apprenticeship
Research
Contract
Freelance
Other
```

These categories are intentionally broad.

The system should not assume that every opportunity belongs to traditional employment.

---

# 9. Identity

An opportunity should eventually have a stable internal identity independent of any single source.

Conceptually:

```text
Internal Opportunity ID
        ↓
Underlying Opportunity
        ↓
One or more Source Records
```

This is important because the same opportunity may appear across multiple sources.

The source identifier is not necessarily the opportunity identifier.

---

# 10. Conceptual Opportunity Fields

A structured opportunity may eventually contain the following groups.

## 10.1 Identity

* internal opportunity ID
* title
* organization
* opportunity type

## 10.2 Timing

* posted date
* application deadline
* start date
* end date where applicable

## 10.3 Location

* country
* region
* city
* remote status
* geographic restrictions

## 10.4 Requirements

* required skills
* preferred skills
* education requirements
* experience requirements
* language requirements
* work authorization requirements

## 10.5 Compensation

* compensation amount
* currency
* compensation type
* salary/stipend/rate where applicable

## 10.6 Application

* application URL
* application method
* application instructions
* contact information where legitimately published

## 10.7 Provenance

* source
* source ID
* source URL
* original source text
* source timestamp
* discovery timestamp
* supporting evidence

These fields are a conceptual target, not a requirement to implement all of them immediately.

---

# 11. Evidence Status

Important information should distinguish between different levels of certainty.

Conceptually:

```text
Explicit
Inferred
Unknown
```

## Explicit

The source directly states the information.

Example:

```text
"Remote in the United States."
```

Remote status and geographic restriction are explicitly stated.

## Inferred

The system derives information from evidence that strongly supports the conclusion.

Example:

```text
"We are looking for backend engineers to join our fully distributed team."
```

The system may infer a remote work model if the surrounding evidence supports it.

Inferred information must remain distinguishable from explicit information.

## Unknown

The source does not provide sufficient evidence.

Example:

```text
Salary: Unknown
```

Unknown must not be silently converted into a positive or negative assumption.

---

# 12. Evidence Hierarchy

When conflicting information exists, the system should prefer stronger evidence.

A conceptual hierarchy is:

```text
Direct source statement
        ↓
Reliable structured source information
        ↓
Strong contextual inference
        ↓
Weak inference
        ↓
Assumption
```

The system should avoid treating assumptions as facts.

Where evidence conflicts, the conflict should be preserved or surfaced rather than silently resolved without justification.

---

# 13. Provenance

Every structured opportunity should remain traceable to its source evidence.

Conceptually:

```text
Opportunity
    ↓
Source Record(s)
    ↓
Original Source
```

Where practical, important fields should also be traceable to supporting evidence.

For example:

```text
Opportunity
   │
   ├── title
   │      └── source evidence
   │
   ├── location
   │      └── source evidence
   │
   └── deadline
          └── source evidence
```

This supports:

* verification
* debugging
* extraction evaluation
* correction
* deduplication
* user trust

---

# 14. Multiple Sources

One underlying opportunity may have multiple source records.

Example:

```text
Company Career Page
       │
       ├── Opportunity
       │
Employee Announcement
       │
       └── Same Opportunity
       │
Community Repost
       │
       └── Same Opportunity
```

The system should eventually be able to associate these records with one underlying opportunity where evidence supports that conclusion.

It should preserve all relevant provenance rather than arbitrarily choosing one source and discarding the others.

---

# 15. One Source, Multiple Opportunities

A single source record may contain multiple opportunities.

Example:

```text
"We're hiring interns for:
- Data Analytics
- Software Engineering
- Product Design"
```

The system may eventually need to represent these as separate opportunities.

Therefore:

```text
1 Source Record
      ↓
N Opportunities
```

must remain possible.

The exact extraction behavior should be established when the extraction layer is implemented.

---

# 16. Opportunity vs Job

The system should not treat "job" and "opportunity" as interchangeable concepts.

A job is one type of professional opportunity.

Therefore:

```text
Opportunity
├── Employment
├── Internship
├── Fellowship
├── Research
├── Apprenticeship
├── Contract
├── Freelance
└── Other
```

This distinction keeps the product broader than a traditional job board.

---

# 17. Opportunity Quality

An opportunity may eventually have quality-related attributes such as:

* source reliability
* information completeness
* freshness
* verification status
* provenance completeness

These should only become formal scoring systems when they serve a defined product or evaluation purpose.

Do not create arbitrary "quality scores" without a measurable interpretation.

---

# 18. Freshness

Opportunities are time-sensitive.

Important temporal concepts include:

```text
Published
      ↓
Discovered
      ↓
Processed
      ↓
Deadline
      ↓
Expired
```

The system should distinguish the date an opportunity was published from the date the system discovered it.

A recently discovered opportunity may have been published much earlier.

These dates should not be conflated.

---

# 19. Expiration

An opportunity may become invalid because:

* the application deadline passed
* the position was filled
* the source removed it
* the organization closed the opening
* the opportunity was explicitly cancelled

The system should eventually represent expiration or availability status where sufficient evidence exists.

Lack of a known deadline does not automatically mean an opportunity is expired.

---

# 20. Missing Information

Incomplete opportunities are expected.

For example:

```text
Title: Known
Organization: Known
Location: Unknown
Salary: Unknown
Deadline: Known
Skills: Partially known
```

This should still be representable.

The system should not reject an opportunity merely because optional information is missing.

Whether missing information prevents eligibility or ranking is a downstream decision.

---

# 21. Candidate Independence

The core opportunity model must remain candidate-independent.

For example:

```text
Opportunity:
"Machine Learning Intern at Company X"
```

is the same underlying opportunity regardless of whether:

```text
Candidate A
Candidate B
Candidate C
```

views it.

Candidate-specific information belongs in:

* eligibility results
* matching results
* ranking results

not in the core opportunity identity.

---

# 22. Opportunity Identity vs Candidate Result

These should remain separate:

```text
Opportunity
      +
Candidate
      ↓
Eligibility
      ↓
Match
      ↓
Ranking
```

The opportunity itself should not contain:

```text
"90% match for Herbert"
```

That is a candidate-specific result.

---

# 23. Canonical Representation

The system should eventually maintain a canonical representation of an opportunity independent of how the source describes it.

For example:

```text
Source A:
"Remote SWE Intern"

Source B:
"Software Engineering Internship - Remote"

Source C:
"SWE Internship, fully remote"
```

may represent the same underlying opportunity.

Normalization and deduplication are responsible for determining how these representations relate.

The original source representations must still be preserved.

---

# 24. Model Evolution

This document intentionally defines a conceptual model rather than a complete permanent schema.

As the system processes real opportunities, new requirements may emerge.

Model changes should be driven by:

* real source data
* extraction failures
* matching requirements
* eligibility requirements
* evaluation results
* product needs

Avoid adding fields simply because they might be useful someday.

---

# 25. Current Implementation Boundary

Currently:

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

The next stage is extraction of a structured opportunity from a positive assessment.

The detector does not own the complete opportunity schema. `OpportunityCandidate` is an assessment of a raw record, including negative assessments.

---

# 26. Core Definition

For this project:

> An opportunity is a source-backed, actionable professional opening or program that a person could reasonably take action on.

Everything else follows from this definition.

The system should preserve the distinction between:

```text
What the source said
        ↓
What the system detected
        ↓
What the system extracted
        ↓
What the system inferred
        ↓
What the candidate can actually pursue
```

That distinction is fundamental to building a trustworthy opportunity intelligence system.
