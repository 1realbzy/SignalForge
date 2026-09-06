# X/Twitter ingestion source

Generic X search adapter for the job intelligence platform.

The original Ghanaian Pidgin NLP repository was used as **read-only reference**. It was not modified.

## What was extracted

From the older scraper (`collect_gh_pidgin.py` and cookie helpers):

- Twikit client construction (`Client('en-US')`)
- Cookie load / credential login / cookie save
- `search_tweet` plus pagination via `next()`
- Rate-limit handling for `TooManyRequests`
- Exponential backoff on transient errors
- Logging of source-level failures

Those behaviors now live behind `XTwitterSource`. Callers receive `RawPost`, not Twikit objects.

## What was intentionally not extracted

- Ghanaian Pidgin search queries and marker sets
- Nigerian vs Ghanaian classification and quality scoring
- `clean_text()` (it stripped URLs, mentions, and other characters)
- The 5–50 word length filter
- Jaccard near-duplicate detection
- JSON/CSV dataset persistence (`ghanaian_pidgin_dataset.*`)
- tqdm / argparse collector CLI
- Chrome cookie-decryption debug scripts
- Any authentication secrets or `cookies.json`

## Where the source lives

| Piece | Path |
| --- | --- |
| Public API | `src/job_board_tool/ingestion/` |
| Source adapter | `x_source.py` (`XTwitterSource`) |
| Normalized record | `models.py` (`RawPost`) |
| Tweet mapping | `mapping.py` |
| Twikit wrapper | `twikit_adapter.py` (lazy import) |
| Env / cookie path helpers | `auth.py` |
| Manual cookie export | `scripts/export_cookies.py` |
| Manual browser login helper | `scripts/generate_cookies.py` |

## Authentication

Do not commit cookies or `.env`.

1. Copy `.env.example` to `.env` and set `TWITTER_USERNAME`, `TWITTER_EMAIL`, `TWITTER_PASSWORD` locally, **or**
2. Place a Twikit `cookies.json` next to the process (or set `X_COOKIES_PATH`).

`authenticate()` loads cookies if the file exists. Otherwise it logs in with env credentials and saves cookies. It does **not** run a search probe.

Cookie helpers:

```text
python scripts/export_cookies.py
python scripts/generate_cookies.py --browser msedge
```

The browser helper only opens a real browser for a manual login. It does not auto-type passwords or spoof client fingerprints.

## Temporary Twikit compatibility patches

Live X search on `twikit==2.2.2` currently requires two temporary upstream patches applied to the installed package, not to SignalForge source. See [docs/dependencies/twikit-2.2.2-compat.md](dependencies/twikit-2.2.2-compat.md).

```text
python -m scripts.apply_twikit_compat_patches
```

## How queries are supplied

The adapter does not hardcode production queries.

```python
from job_board_tool.ingestion import XTwitterSource

source = XTwitterSource()
await source.authenticate()
async for post in source.discover(
    queries=["example query 1", "example query 2"],
    count=50,
    max_pages=20,
):
    ...
```

Opportunity-specific queries belong in a later discovery layer.

## RawPost

| Field | Meaning |
| --- | --- |
| `source` | Always `"x"` |
| `source_id` | Tweet id |
| `text` | Original post text (URLs kept) |
| `author_username` | `user.screen_name` when present |
| `author_display_name` | `user.name` when present |
| `created_at` | Tweet timestamp string when present |
| `url` | `https://x.com/{screen_name}/status/{id}` only if both exist |
| `author_location` | Profile location when present |
| `author_bio` | Profile description when present |
| `discovered_via` | The search query that found the post |
| `raw_data` | JSON-safe scalars from the tweet/user |

Unavailable fields are `None`. Metadata is not invented.

Twikit fields used (from the 2.x Tweet/User model and the old scraper): `id`, `text`, `created_at`, `lang`, engagement counts when present, `user.screen_name`, `user.name`, `user.location`, `user.description`.

## Pagination

`discover()` requests a search page, maps tweets, then asks the page for `next()` up to `max_pages`. Callers iterate `async for post in source.discover(...)`. Twikit's `tweets.next()` stays inside `TwikitSearchPage`.

## Rate limits and retries

- `XRateLimited` (from Twikit `TooManyRequests`) sleeps `rate_limit_sleep_seconds` (default 900) and retries.
- Other search errors use exponential backoff: `retry_base_seconds * 2^(n-1)`, capped at `retry_max_seconds`.
- After `max_retries` failures the exception is re-raised.
- Optional `inter_query_delay_seconds` / `inter_page_delay_seconds` default to 0.

This is ordinary client backoff, not an attempt to bypass X protections.

## Tests and mocking

Unit tests inject a `FakeClient`. They do not authenticate to X and do not import Twikit.

```text
python -m pytest tests/test_x_ingestion.py
```

Covered: cookie load, credential login, search, pagination, RawPost mapping, multiple queries, rate-limit sleep, retry backoff, missing metadata, URL preservation, provenance, source id.

## Future consumers

```text
X/Twitter
    ↓
XTwitterSource
    ↓
RawPost
    ↓
OpportunityDetector
    ↓
OpportunityCandidate
    ↓
future extraction / normalization / eligibility / matching
```

Detection consumes `RawPost` only. Persistence, deduplication, and extraction belong downstream, not in this adapter.
