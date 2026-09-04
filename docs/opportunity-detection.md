# Opportunity detection

Deterministic baseline that assesses whether a `RawPost` plausibly contains an actionable professional opportunity.

```text
RawPost
    ↓
OpportunityDetector
    ↓
OpportunityCandidate
```

`OpportunityCandidate` is an **assessment**, not a confirmed listing. Downstream stages must filter on `is_opportunity`.

## What it does

- Reads `RawPost.text` only.
- Matches named phrase groups with word/phrase boundaries.
- Scores **unique groups**, not overlapping regexes in the same group.
- Compares the clamped score to a configurable threshold (default `0.45`).
- Assigns a broad category only when type language is bound to opening/application language.
- Always returns a candidate, including negative assessments.

It does not extract titles, organizations, salaries, or deadlines. It does not use Twikit, author bios, or `discovered_via`.

## Score

`opportunity_score` is evidence strength, not a probability.

- Strong groups (`hiring_intent`, `application_intent`, `opportunity_terminology`, `research_opening`, `actionable_contact`) weigh `0.50` and can pass alone.
- Supporting groups weigh `0.20` and cannot pass alone.
- Negative groups subtract. There is no hard veto.

## Reason codes

`is_opportunity` stays boolean. Semantics live in `decision_reasons`:

- `no_opportunity_evidence` — no positive or negative groups, or insufficient text
- `confirmed_non_opportunity` — negative groups only
- `insufficient_opportunity_evidence` — positives present but score below threshold
- `opportunity` — score at or above threshold with at least one positive group

## Configuration

```python
from job_board_tool.detection import DetectionConfig, OpportunityDetector
from job_board_tool.ingestion.models import RawPost

detector = OpportunityDetector(DetectionConfig(threshold=0.45))
candidate = detector.detect(post)
```

Weights and phrases live in `src/job_board_tool/detection/signals.py`. Override group weights with `DetectionConfig.weight_overrides`.

## Tests and evaluation

```text
python -m pytest tests/test_opportunity_detection.py tests/test_opportunity_detection_eval.py
python -m job_board_tool.detection.evaluate
```

The labelled fixture is diagnostic. CI only enforces a conservative smoke floor on the clear subset. Do not treat the fixture as a training set.
