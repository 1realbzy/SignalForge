# Source Adapters

## 1. Purpose

This document defines how external opportunity sources connect to `job_board_tool`.

The source-adapter layer isolates external platforms, APIs, clients, authentication mechanisms, pagination behavior, rate limits, and source-specific data formats from the rest of the opportunity intelligence pipeline.

The central architectural rule is:

> Downstream business logic should consume the project's internal data contracts, not external provider objects.

---

# 2. Why Source Adapters Exist

Opportunity information may originate from many different sources.

Examples include:

* X/Twitter
* company career pages
* applicant-tracking systems
* newsletters
* professional communities
* university pages
* research organizations
* startup communities
* other public sources

These sources differ in:

* authentication
* APIs
* page structure
* rate limits
* pagination
* data formats
* reliability
* identifiers
* available metadata

The rest of the system should not need to understand these differences.

The adapter layer absorbs that complexity.

---

# 3. Source Boundary

The general architecture is:

```text id="3o0lh8"
External Source
      ↓
Source Adapter
      ↓
Internal Raw Record
      ↓
Shared Opportunity Pipeline
```

For X/Twitter:

```text id="7m3x0d"
X/Twitter
      ↓
TwikitXClient
      ↓
XTwitterSource
      ↓
RawPost
```

The downstream pipeline begins at `RawPost`.

---

# 4. Adapter Responsibilities

A source adapter is responsible for source-specific behavior.

This includes:

### Connection

Communicating with the external source through its supported client, API, or retrieval mechanism.

### Authentication

Handling source authentication using the project's approved configuration mechanisms.

### Pagination

Handling source-specific pagination and continuation behavior.

### Rate Limits

Handling source rate-limit responses appropriately.

### Retries

Handling transient source failures where retrying is appropriate.

### Translation

Converting provider-specific records into internal raw-record models.

### Provenance

Preserving source identifiers, URLs, timestamps, and other useful provenance.

### Source Logging

Providing useful diagnostics about source operations without exposing credentials or sensitive authentication material.

---

# 5. Adapter Non-Responsibilities

Source adapters must not contain downstream product intelligence.

They should not be responsible for:

* opportunity detection
* job extraction
* candidate matching
* eligibility decisions
* ranking
* candidate-specific filtering
* recommendation logic
* UI behavior

For example, the X/Twitter adapter should not decide:

```text
"This tweet is probably an internship."
```

That belongs to opportunity detection.

Likewise, it should not decide:

```text
"This internship is suitable for the candidate."
```

That belongs to eligibility and matching.

---

# 6. Internal Data Contract

The adapter should translate external records into an internal representation.

Conceptually:

```text id="x2gn8j"
Provider Object
      ↓
Adapter Mapping
      ↓
Raw Record
```

For X/Twitter:

```text id="p6r4wq"
Twikit Tweet
      ↓
XTwitterSource
      ↓
RawPost
```

Downstream components should depend on `RawPost` or another stable internal raw-record contract.

They should not depend on:

```python
twikit.Tweet
```

or equivalent provider-specific types.

---

# 7. Raw Record Principles

Raw records represent source evidence.

They should preserve, where available:

* source
* source ID
* original text
* source URL
* source timestamp
* discovery timestamp
* source author/account information where appropriate
* useful source metadata
* provenance

The raw record should remain as close as practical to what the source actually provided.

---

# 8. Evidence Preservation

Adapters should avoid destructive transformation.

Do not unnecessarily:

* remove URLs
* remove meaningful text
* rewrite source content
* lowercase original content
* strip source identifiers
* discard timestamps
* discard provenance

Cleaning or normalization required for downstream processing belongs downstream.

The raw record is evidence.

---

# 9. Current X/Twitter Implementation

The current X/Twitter integration is:

```text id="l9sl2j"
X/Twitter
      ↓
TwikitXClient
      ↓
XTwitterSource
      ↓
RawPost
```

The implementation provides a reusable source boundary around Twikit.

The rest of the application should not need to know how Twikit authentication, pagination, or client behavior works.

---

# 10. Twikit Isolation

Twikit-specific details must remain inside the X/Twitter integration layer.

This includes:

* client initialization
* cookie loading
* environment-based authentication
* authentication health checks
* tweet searching
* pagination
* rate-limit handling
* source-specific retries
* mapping Twikit objects into internal models

A downstream detector should never need to import or understand Twikit.

---

# 11. Authentication

Authentication must be treated as an adapter concern.

Credentials or session material should be supplied through appropriate local configuration mechanisms.

Never:

* hardcode credentials
* commit session cookies
* log passwords
* expose authentication tokens
* copy credentials or authentication material from elsewhere

Authentication should be separate from opportunity processing.

A successful authentication operation should not automatically imply that source discovery has occurred.

---

# 12. Source Discovery

An adapter should expose source discovery through a project-level interface rather than exposing the external client's raw API.

Conceptually:

```python
source.discover(...)
```

rather than requiring downstream code to do:

```python
twikit_client.search_tweet(...)
```

This keeps source-specific implementation behind the adapter.

The exact interface should follow existing repository conventions and actual source requirements.

Do not create an unnecessarily complex universal interface before multiple sources justify it.

---

# 13. Multiple Sources

The long-term architecture should support multiple independent adapters.

Conceptually:

```text id="s7cx1k"
                 ┌── XTwitterSource
                 │
                 ├── CareerPageSource
                 │
                 ├── ATSSource
                 │
                 ├── NewsletterSource
                 │
External Sources ┤
                 └── OtherSource
                         ↓
                    Raw Records
                         ↓
                Shared Pipeline
```

Each adapter can have its own retrieval implementation.

The downstream opportunity pipeline should remain shared.

---

# 14. Source Independence

The opportunity intelligence system must not be designed around assumptions that only apply to X/Twitter.

For example, downstream logic should not require:

* tweets
* handles
* retweet counts
* social-media engagement
* hashtags
* platform-specific terminology

unless those fields are explicitly useful as optional provenance or ranking signals.

The common opportunity pipeline should operate on general source evidence.

---

# 15. Optional Source Metadata

Source-specific metadata may be preserved when it provides useful information.

Examples might include:

* engagement counts
* author information
* source category
* source-specific timestamps
* provider identifiers

However, optional metadata should not become a hidden dependency for downstream processing.

A downstream component should still function when another source does not provide the same metadata.

---

# 16. Source URLs

When a source provides a stable URL, preserve it.

Canonical URLs should be constructed only when sufficient information exists to do so reliably.

Do not invent URLs.

URLs serve several purposes:

* verification
* provenance
* deduplication
* user navigation
* debugging

---

# 17. Source Reliability

External sources should be treated as unreliable dependencies.

Adapters should anticipate:

```text id="c1y3c2"
Authentication failure
Rate limiting
Temporary network failure
Malformed source data
Pagination failure
Unavailable service
Client/API changes
```

The adapter should fail in a way that allows the application to distinguish source failure from a legitimate empty result.

An empty result should not automatically mean:

> "There are no opportunities."

It may mean:

> "The source could not be queried successfully."

---

# 18. Rate Limits and Retries

Rate limits must be respected.

Adapters may retry transient failures when appropriate.

Retry behavior should:

* use bounded attempts where appropriate
* avoid tight retry loops
* use backoff when appropriate
* preserve useful error information
* distinguish retryable from non-retryable failures

Do not implement mechanisms intended to evade platform rate limits or access controls.

---

# 19. Security Boundary

Source adapters are a security-sensitive boundary because they interact with external systems and credentials.

They must not:

* expose credentials in logs
* store secrets in source code
* commit session cookies
* leak authentication material through exceptions
* bypass platform security mechanisms

Authentication artifacts should remain local and protected through the project's configuration and ignore rules.

---

# 20. Testing Strategy

Source adapters should be testable without requiring live external services.

Prefer:

* mocked clients
* fake source responses
* deterministic fixtures
* mapping tests
* pagination tests
* rate-limit tests
* authentication failure tests
* malformed-response tests
* retry behavior tests

Live source integration tests, if eventually required, should be explicitly separated from ordinary unit tests.

They must not be required for normal development or CI unless intentionally configured.

---

# 21. Adapter Contract Testing

As additional source adapters are introduced, the project may establish shared contract tests.

Conceptually:

```text id="7kqjv4"
Source Adapter
      ↓
Must produce valid Raw Record
      ↓
Shared Contract Tests
```

This can verify that every adapter provides the minimum information required by downstream stages.

Do not introduce a heavy abstraction solely for this purpose until multiple adapters justify it.

---

# 22. Source-Specific Failures

Source-specific failures should remain identifiable.

For example:

```text id="v4b9l7"
Authentication failure
    ≠
No opportunities found
```

and:

```text id="g8r1qa"
Rate limit
    ≠
Empty source
```

This distinction becomes important for monitoring source health and evaluating discovery quality.

---

# 24. Current Architecture Boundary

The source-adapter implementation still ends here:

```text id="n3jpxe"
X/Twitter
      ↓
TwikitXClient
      ↓
XTwitterSource
      ↓
RawPost
```

Opportunity detection now consumes that `RawPost` contract:

```text id="g0dbw4"
RawPost
      ↓
OpportunityDetector
      ↓
OpportunityCandidate
```

The opportunity detector must not modify the source adapter to perform its own work.

---

# 25. Future Source Expansion

When adding a new source:

1. Inspect the source and its access method.
2. Determine the minimum information required.
3. Implement the source-specific adapter.
4. Map source records into the internal raw-record contract.
5. Preserve provenance.
6. Add deterministic adapter tests.
7. Verify that downstream components remain source-independent.
8. Add integration testing only when justified.

Do not redesign the entire pipeline every time a new source is added.

---

# 26. Architecture Principle

The source-adapter layer exists to enforce one boundary:

```text id="f7v8f8"
External-world complexity
          ↓
     Source Adapter
          ↓
Internal application contract
```

The rest of the system should care about:

> "What information did we receive?"

not:

> "Which external client produced it, and how does that client work?"

Source complexity belongs at the edge.

Opportunity intelligence belongs in the core.
