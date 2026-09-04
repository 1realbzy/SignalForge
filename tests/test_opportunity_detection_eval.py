"""Diagnostic evaluation for opportunity detection. Not a per-example gold test."""

from __future__ import annotations

from job_board_tool.detection.evaluate import (
    default_fixture_path,
    evaluate,
    format_report,
    load_eval_rows,
)
from job_board_tool.detection.models import OpportunityCandidate


def test_eval_fixture_is_sized_and_well_formed() -> None:
    rows = load_eval_rows()
    assert 30 <= len(rows) <= 50
    assert default_fixture_path().is_file()
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids))
    assert any(row["ambiguity"] == "clear" and row["expected_is_opportunity"] for row in rows)
    assert any(row["ambiguity"] == "clear" and not row["expected_is_opportunity"] for row in rows)
    assert any(row.get("expected_category") is None and row["expected_is_opportunity"] for row in rows)


def test_eval_produces_an_assessment_for_every_row() -> None:
    rows = load_eval_rows()
    report = evaluate(rows)
    assert report.n_examples == len(rows)
    assert report.n_assessed == len(rows)


def test_clear_subset_meets_conservative_smoke_floor(capsys) -> None:
    report = evaluate(load_eval_rows())
    print(format_report(report))
    captured = capsys.readouterr()
    assert "precision=" in captured.out
    assert "false_positives=" in captured.out
    assert report.clear.precision >= 0.60
    assert report.clear.recall >= 0.50
    assert report.clear.f1 >= 0.50


def test_evaluate_returns_opportunity_candidate_instances() -> None:
    rows = load_eval_rows()[:1]
    from job_board_tool.detection.detector import OpportunityDetector
    from job_board_tool.detection.evaluate import row_to_raw_post

    candidate = OpportunityDetector().detect(row_to_raw_post(rows[0]))
    assert isinstance(candidate, OpportunityCandidate)
