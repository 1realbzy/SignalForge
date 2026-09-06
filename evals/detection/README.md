# Detection evidence-validation

Local workflow for measuring the frozen `OpportunityDetector` on a small real X sample.

This is a diagnostic protocol, not a permanent X-specific intelligence layer. It does not change detection or ingestion. Real post text and labels stay on the operator's machine.

## What this answers

Does this source record contain enough evidence that it plausibly represents an actionable professional opportunity?

That is a detection question. Do not label for extraction completeness, matching, eligibility, location, seniority, or personal fit.

## Files

Committed here:

- `queries.json` — search strings passed to `XTwitterSource.discover()`. Not detector features.
- `label_schema.example.json` — invented placeholder only. Do not paste real X posts into the repo.

Local and gitignored (`data/local/detection_eval/<run_id>/`):

- `run_meta.json`
- `sample.jsonl`
- `label_queue.jsonl`
- `labels.jsonl`
- `scored.jsonl`
- `report.txt`

Do not commit `data/local/`, live `*.jsonl`, cookies, or `.env`.

## Query set

The list is small (~13) and mixed on purpose:

- Opportunity-oriented: `we're hiring`, `applications are now open`, `internship applications`, `fellowship applications`, `nurse vacancy`, `teacher vacancy`
- Negative-leaning: `I just got hired`, `job market is`, `resume tips`, `I was promoted`, `we may be hiring`
- Broader / noisier: `join our team`, `looking for a contractor`

`nurse vacancy` keeps a non-software healthcare phrase. `teacher vacancy` adds a second non-tech, non-healthcare professional phrase so the sample is not only software and healthcare language.

Queries are still a biased convenience sample. `discovered_via` is provenance only. Do not put it into the detector or use it as a label hint.

## Collect

Requires a working local X session (`cookies.json`, `X_COOKIES_PATH`, or `.env`). The collect script does not create that session.

Run from the repository root. The scripts put `src/` on `sys.path`, so an editable install is not required.

```text
python -m scripts.collect_detection_eval_sample
```

Defaults: `count=8`, `max_pages=1`, `product=Latest`, `inter_query_delay_seconds=3.0`. Stop at 80 unique posts or when the query list is exhausted. A partial sample of 60–80 unique posts is enough for this pass.

The script calls existing `authenticate()` and `discover()` only. It does not call `health_check()` unless you pass `--health-check`. It does not bypass auth, rate limits, or adapter backoff.

Exact `(source, source_id)` and exact normalized-text duplicates are collapsed before labeling. Later duplicate ids are stored on the kept row.

`run_meta.json` records per-query `yielded` / `kept` / `skipped_exact_id` / `skipped_exact_text` so one query cannot silently dominate.

## Blind labeling

Label `label_queue.jsonl` only. That file has `eval_id`, `source_id`, `text`, and `url`. It must not include score, signals, reasons, category, or query.

Write `labels.jsonl` with one of:

- `opportunity` — a person could reasonably act (apply, DM for the role, open the stated program). Missing title, salary, or deadline is fine.
- `non_opportunity` — personal career news, promotion, advice, market talk, historical hiring, engagement bait, vague future intent, or commentary with no path to act.
- `ambiguous` — cannot decide from the text (image-only, truncated, unclear whether an opening exists).

Each row needs a one-line `rationale`. See `label_schema.example.json` for the shape, not the content.

Do not open `scored.jsonl` or `report.txt` until labeling is finished.

## Score

```text
python -m scripts.score_detection_eval_sample --run-dir data/local/detection_eval/<run_id>
```

This is the first place detector fields sit next to human labels. Primary precision / recall / F1 exclude `ambiguous` rows. The report also prints per-query contribution counts.

The live sample is diagnostic. It is not representative of X. Do not add a CI floor on live data.

## Change-the-detector rule

Keep the detector frozen through the first scored report. Change it later only for a recurring pattern:

- at least 3 clear errors of the same linguistic type, or
- one pattern that dominates false positives or false negatives

Do not change the detector for a single miss, a single sarcastic “we're hiring”, query-biased leftovers, extraction gaps, eligibility issues, or a desire to raise F1.

Then name the pattern, estimate the false-positive risk of a lexicon change, add a unit test, and consider a small group/phrase edit. Still no LLM or ML.

## Git boundary

Public repo: https://github.com/1realbzy/SignalForge

Allowed in Git: queries, scripts, this protocol, and the invented schema example.

Never in Git: real X text, labels, scores, cookies, or credentials.
