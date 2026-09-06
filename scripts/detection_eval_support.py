"""Helpers for local detection evidence-validation. Not detector logic."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
for _path in (_SRC, _ROOT):
    _text = str(_path)
    if _text not in sys.path:
        sys.path.insert(0, _text)

from job_board_tool.detection.detector import OpportunityDetector
from job_board_tool.ingestion.models import RawPost

TARGET_UNIQUE = 80
MIN_UNIQUE = 60
DEFAULT_COUNT = 8
DEFAULT_MAX_PAGES = 1
DEFAULT_INTER_QUERY_DELAY = 3.0


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_text(text: str) -> str:
    return " ".join((text or "").split()).casefold()


def raw_post_to_dict(post: RawPost) -> dict[str, Any]:
    return {
        "source": post.source,
        "source_id": post.source_id,
        "text": post.text,
        "author_username": post.author_username,
        "author_display_name": post.author_display_name,
        "created_at": post.created_at,
        "url": post.url,
        "author_location": post.author_location,
        "author_bio": post.author_bio,
        "discovered_via": post.discovered_via,
        "raw_data": post.raw_data,
    }


def dict_to_raw_post(payload: dict[str, Any]) -> RawPost:
    return RawPost(
        source=str(payload.get("source", "x")),
        source_id=str(payload.get("source_id", "")),
        text=str(payload.get("text", "")),
        author_username=payload.get("author_username"),
        author_display_name=payload.get("author_display_name"),
        created_at=payload.get("created_at"),
        url=payload.get("url"),
        author_location=payload.get("author_location"),
        author_bio=payload.get("author_bio"),
        discovered_via=payload.get("discovered_via"),
        raw_data=payload.get("raw_data") or {},
    )


@dataclass
class ConsiderResult:
    keep: bool
    reason: Optional[str] = None
    record: Optional[dict[str, Any]] = None


@dataclass
class DedupeIndex:
    seen_ids: set[tuple[str, str]] = field(default_factory=set)
    kept_by_text: dict[str, dict[str, Any]] = field(default_factory=dict)
    skipped_exact_id: int = 0
    skipped_exact_text: int = 0
    kept_records: list[dict[str, Any]] = field(default_factory=list)

    def consider(self, post: RawPost) -> ConsiderResult:
        key = (post.source, post.source_id)
        if key in self.seen_ids:
            self.skipped_exact_id += 1
            return ConsiderResult(keep=False, reason="exact_id")
        self.seen_ids.add(key)
        text_key = normalize_text(post.text)
        existing = self.kept_by_text.get(text_key)
        if existing is not None:
            self.skipped_exact_text += 1
            existing.setdefault("duplicate_source_ids", []).append(post.source_id)
            return ConsiderResult(keep=False, reason="exact_text", record=existing)
        record = {
            "eval_id": f"{len(self.kept_records) + 1:03d}",
            "raw_post": raw_post_to_dict(post),
            "duplicate_source_ids": [],
        }
        self.kept_by_text[text_key] = record
        self.kept_records.append(record)
        return ConsiderResult(keep=True, record=record)


def empty_query_counts(queries: Iterable[str]) -> dict[str, dict[str, int]]:
    return {
        query: {"yielded": 0, "kept": 0, "skipped_exact_id": 0, "skipped_exact_text": 0}
        for query in queries
    }


def per_query_counts(rows: Iterable[dict[str, Any]], queries: Iterable[str]) -> dict[str, dict[str, int]]:
    counts = empty_query_counts(queries)
    for row in rows:
        query = (row.get("raw_post") or {}).get("discovered_via")
        if query not in counts:
            counts[query] = {"yielded": 0, "kept": 0, "skipped_exact_id": 0, "skipped_exact_text": 0}
        counts[query]["kept"] += 1
    return counts


def format_query_counts(counts: dict[str, dict[str, int]]) -> str:
    lines = ["Per-query contribution (kept unique posts):"]
    for query, stats in counts.items():
        lines.append(
            f"  {query}: kept={stats.get('kept', 0)} "
            f"yielded={stats.get('yielded', 0)} "
            f"skipped_exact_id={stats.get('skipped_exact_id', 0)} "
            f"skipped_exact_text={stats.get('skipped_exact_text', 0)}"
        )
    return "\n".join(lines)


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_queries(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    queries = payload.get("queries")
    if not isinstance(queries, list) or not queries:
        raise ValueError("queries.json must contain a non-empty 'queries' list.")
    return [str(item) for item in queries]


def label_queue_row(record: dict[str, Any]) -> dict[str, Any]:
    raw = record.get("raw_post") or {}
    return {
        "eval_id": record["eval_id"],
        "source_id": raw.get("source_id"),
        "text": raw.get("text"),
        "url": raw.get("url"),
    }


def score_labels(
    sample: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    detector: Optional[OpportunityDetector] = None,
) -> dict[str, Any]:
    detector = detector or OpportunityDetector()
    by_id = {row["eval_id"]: row for row in labels}
    scored: list[dict[str, Any]] = []
    pairs: list[tuple[dict[str, Any], Any]] = []
    ambiguous = 0
    missing_labels = 0
    reason_counts: dict[str, int] = {}
    for record in sample:
        eval_id = record["eval_id"]
        label_row = by_id.get(eval_id)
        candidate = detector.detect(dict_to_raw_post(record["raw_post"]))
        for reason in candidate.decision_reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        human_label = None if label_row is None else label_row.get("label")
        if human_label == "ambiguous":
            ambiguous += 1
            error = "ambiguous"
        elif human_label is None:
            missing_labels += 1
            error = "unlabeled"
        else:
            expected = human_label == "opportunity"
            if expected and candidate.is_opportunity:
                error = "tp"
            elif not expected and candidate.is_opportunity:
                error = "fp"
            elif expected and not candidate.is_opportunity:
                error = "fn"
            else:
                error = "tn"
            pairs.append(
                (
                    {
                        "id": eval_id,
                        "expected_is_opportunity": expected,
                    },
                    candidate,
                )
            )
        scored.append(
            {
                "eval_id": eval_id,
                "human_label": human_label,
                "human_rationale": None if label_row is None else label_row.get("rationale"),
                "is_opportunity": candidate.is_opportunity,
                "opportunity_score": candidate.opportunity_score,
                "threshold": candidate.threshold,
                "decision_reasons": list(candidate.decision_reasons),
                "positive_groups": sorted({signal.group for signal in candidate.positive_signals}),
                "negative_groups": sorted({signal.group for signal in candidate.negative_signals}),
                "category": None if candidate.category is None else candidate.category.value,
                "error": error,
                "discovered_via": (record.get("raw_post") or {}).get("discovered_via"),
                "source_id": (record.get("raw_post") or {}).get("source_id"),
                "text": (record.get("raw_post") or {}).get("text"),
                "url": (record.get("raw_post") or {}).get("url"),
            }
        )

    from job_board_tool.detection.evaluate import _metrics

    metrics = _metrics(pairs) if pairs else None
    payload = {
        "clear_support": 0 if metrics is None else metrics.support,
        "ambiguous": ambiguous,
        "missing_labels": missing_labels,
        "reason_counts": reason_counts,
        "scored": scored,
        "metrics": {
            "support": 0 if metrics is None else metrics.support,
            "true_positives": 0 if metrics is None else metrics.true_positives,
            "false_positives": 0 if metrics is None else metrics.false_positives,
            "false_negatives": 0 if metrics is None else metrics.false_negatives,
            "true_negatives": 0 if metrics is None else metrics.true_negatives,
            "precision": 0.0 if metrics is None else metrics.precision,
            "recall": 0.0 if metrics is None else metrics.recall,
            "f1": 0.0 if metrics is None else metrics.f1,
            "false_positive_ids": [] if metrics is None else list(metrics.false_positive_ids),
            "false_negative_ids": [] if metrics is None else list(metrics.false_negative_ids),
        },
    }
    return payload


def format_score_report(
    run_meta: dict[str, Any],
    scored_payload: dict[str, Any],
) -> str:
    metrics = scored_payload["metrics"]
    query_block = format_query_counts(run_meta.get("query_counts", {}))
    return (
        f"Detection evidence-validation report\n"
        f"run_id={run_meta.get('run_id')} git_sha={run_meta.get('git_sha')}\n"
        f"collected={run_meta.get('kept_unique')} labeled_clear={metrics['support']} "
        f"ambiguous={scored_payload['ambiguous']} unlabeled={scored_payload['missing_labels']}\n"
        f"precision={metrics['precision']:.3f} recall={metrics['recall']:.3f} "
        f"f1={metrics['f1']:.3f}\n"
        f"tp={metrics['true_positives']} fp={metrics['false_positives']} "
        f"fn={metrics['false_negatives']} tn={metrics['true_negatives']}\n"
        f"false_positives={metrics['false_positive_ids']}\n"
        f"false_negatives={metrics['false_negative_ids']}\n"
        f"reason_counts={scored_payload['reason_counts']}\n"
        f"{query_block}\n"
        "Limitation: this live sample is diagnostic, not representative of X."
    )
