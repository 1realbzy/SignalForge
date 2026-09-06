"""Tests for local detection-eval helpers. No live X requests."""

from __future__ import annotations

from pathlib import Path

from job_board_tool.ingestion.models import RawPost

from scripts.detection_eval_support import (
    DedupeIndex,
    append_jsonl,
    format_query_counts,
    label_queue_row,
    load_jsonl,
    load_queries,
    normalize_text,
    per_query_counts,
    raw_post_to_dict,
    score_labels,
)

QUERIES_PATH = Path(__file__).resolve().parents[1] / "evals" / "detection" / "queries.json"


def _post(source_id: str, text: str, query: str = "we're hiring") -> RawPost:
    return RawPost(source="x", source_id=source_id, text=text, discovered_via=query)


def test_normalize_text_collapses_case_and_whitespace() -> None:
    assert normalize_text("  We're   Hiring \n") == normalize_text("we're hiring")


def test_dedupe_skips_same_source_id() -> None:
    index = DedupeIndex()
    first = index.consider(_post("1", "We're hiring engineers."))
    second = index.consider(_post("1", "Different wording that should not matter."))
    assert first.keep is True
    assert second.keep is False
    assert second.reason == "exact_id"


def test_dedupe_skips_same_normalized_text_and_records_duplicate_id() -> None:
    index = DedupeIndex()
    first = index.consider(_post("1", "We're hiring engineers."))
    second = index.consider(_post("2", "we're  hiring engineers."))
    assert first.keep is True
    assert second.keep is False
    assert second.reason == "exact_text"
    assert first.record is not None
    assert first.record["duplicate_source_ids"] == ["2"]


def test_per_query_counts_show_which_query_dominates() -> None:
    rows = [
        {"raw_post": {"discovered_via": "we're hiring"}},
        {"raw_post": {"discovered_via": "we're hiring"}},
        {"raw_post": {"discovered_via": "teacher vacancy"}},
    ]
    counts = per_query_counts(rows, ["we're hiring", "teacher vacancy", "resume tips"])
    assert counts["we're hiring"]["kept"] == 2
    assert counts["teacher vacancy"]["kept"] == 1
    assert counts["resume tips"]["kept"] == 0
    rendered = format_query_counts(counts)
    assert "we're hiring: kept=2" in rendered
    assert "resume tips: kept=0" in rendered


def test_score_labels_excludes_ambiguous_from_primary_metrics() -> None:
    sample = [
        {
            "eval_id": "a",
            "raw_post": {
                "source": "x",
                "source_id": "1",
                "text": "We're hiring software engineers.",
            },
        },
        {
            "eval_id": "b",
            "raw_post": {
                "source": "x",
                "source_id": "2",
                "text": "The weather is nice today and I walked the dog.",
            },
        },
        {
            "eval_id": "c",
            "raw_post": {
                "source": "x",
                "source_id": "3",
                "text": "See the flyer in this photo.",
            },
        },
    ]
    labels = [
        {"eval_id": "a", "label": "opportunity", "rationale": "hiring announcement"},
        {"eval_id": "b", "label": "non_opportunity", "rationale": "unrelated"},
        {"eval_id": "c", "label": "ambiguous", "rationale": "image only"},
    ]
    report = score_labels(sample, labels)
    assert report["clear_support"] == 2
    assert report["ambiguous"] == 1
    assert report["metrics"]["true_positives"] == 1
    assert report["metrics"]["true_negatives"] == 1
    assert report["metrics"]["false_positives"] == 0
    assert report["metrics"]["false_negatives"] == 0


def test_jsonl_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "rows.jsonl"
    append_jsonl(path, {"eval_id": "1"})
    append_jsonl(path, {"eval_id": "2"})
    rows = load_jsonl(path)
    assert [row["eval_id"] for row in rows] == ["1", "2"]


def test_committed_queries_stay_small_and_include_non_tech_domains() -> None:
    queries = load_queries(QUERIES_PATH)
    assert len(queries) == 13
    assert "nurse vacancy" in queries
    assert "teacher vacancy" in queries
    assert "we're hiring" in queries
    assert "resume tips" in queries


def test_label_queue_is_blind() -> None:
    row = label_queue_row(
        {
            "eval_id": "run-001",
            "raw_post": {
                "source_id": "9",
                "text": "We're hiring nurses.",
                "url": "https://example.test/9",
                "discovered_via": "nurse vacancy",
            },
            "opportunity_score": 0.99,
        }
    )
    assert row == {
        "eval_id": "run-001",
        "source_id": "9",
        "text": "We're hiring nurses.",
        "url": "https://example.test/9",
    }
    assert "discovered_via" not in row
    assert "opportunity_score" not in row


def test_raw_post_to_dict_preserves_text_and_provenance() -> None:
    post = _post("99", "Apply here for the opening.")
    payload = raw_post_to_dict(post)
    assert payload["source"] == "x"
    assert payload["source_id"] == "99"
    assert payload["text"] == "Apply here for the opening."
    assert payload["discovered_via"] == "we're hiring"
