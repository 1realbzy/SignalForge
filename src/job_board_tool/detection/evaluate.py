from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

from job_board_tool.detection.detector import OpportunityDetector
from job_board_tool.detection.models import OpportunityCandidate
from job_board_tool.ingestion.models import RawPost

DEFAULT_FIXTURE = (
    Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "opportunity_detection_eval.json"
)


@dataclass(frozen=True)
class MetricSet:
    support: int
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    precision: float
    recall: float
    f1: float
    false_positive_ids: tuple[str, ...]
    false_negative_ids: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationReport:
    n_examples: int
    n_assessed: int
    full: MetricSet
    clear: MetricSet
    reason_counts: dict[str, int]


def default_fixture_path() -> Path:
    return DEFAULT_FIXTURE


def load_eval_rows(path: Optional[Path] = None) -> list[dict[str, Any]]:
    fixture_path = path or default_fixture_path()
    with fixture_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("Evaluation fixture must be a JSON list.")
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Fixture row {index} must be an object.")
        for required in ("id", "text", "expected_is_opportunity", "ambiguity"):
            if required not in item:
                raise ValueError(f"Fixture row {index} missing {required}.")
        rows.append(item)
    return rows


def row_to_raw_post(row: dict[str, Any]) -> RawPost:
    extras = row.get("raw_post") or {}
    return RawPost(
        source=str(extras.get("source", "eval")),
        source_id=str(extras.get("source_id", row["id"])),
        text=str(row["text"]),
        author_username=extras.get("author_username"),
        author_display_name=extras.get("author_display_name"),
        created_at=extras.get("created_at"),
        url=extras.get("url"),
        author_location=extras.get("author_location"),
        author_bio=extras.get("author_bio"),
        discovered_via=extras.get("discovered_via"),
    )


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _metrics(pairs: Iterable[tuple[dict[str, Any], OpportunityCandidate]]) -> MetricSet:
    tp = fp = fn = tn = 0
    fp_ids: list[str] = []
    fn_ids: list[str] = []
    support = 0
    for row, candidate in pairs:
        support += 1
        expected = bool(row["expected_is_opportunity"])
        predicted = candidate.is_opportunity
        if expected and predicted:
            tp += 1
        elif not expected and predicted:
            fp += 1
            fp_ids.append(str(row["id"]))
        elif expected and not predicted:
            fn += 1
            fn_ids.append(str(row["id"]))
        else:
            tn += 1
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return MetricSet(
        support=support,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        true_negatives=tn,
        precision=precision,
        recall=recall,
        f1=f1,
        false_positive_ids=tuple(fp_ids),
        false_negative_ids=tuple(fn_ids),
    )


def evaluate(
    rows: list[dict[str, Any]],
    detector: Optional[OpportunityDetector] = None,
) -> EvaluationReport:
    detector = detector or OpportunityDetector()
    assessed: list[tuple[dict[str, Any], OpportunityCandidate]] = []
    reason_counts: dict[str, int] = {}
    for row in rows:
        candidate = detector.detect(row_to_raw_post(row))
        assessed.append((row, candidate))
        for reason in candidate.decision_reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
    clear = [(row, candidate) for row, candidate in assessed if row.get("ambiguity") == "clear"]
    return EvaluationReport(
        n_examples=len(rows),
        n_assessed=len(assessed),
        full=_metrics(assessed),
        clear=_metrics(clear),
        reason_counts=reason_counts,
    )


def format_report(report: EvaluationReport) -> str:
    def block(title: str, metrics: MetricSet) -> str:
        return (
            f"{title}\n"
            f"  support={metrics.support} tp={metrics.true_positives} "
            f"fp={metrics.false_positives} fn={metrics.false_negatives} "
            f"tn={metrics.true_negatives}\n"
            f"  precision={metrics.precision:.3f} recall={metrics.recall:.3f} "
            f"f1={metrics.f1:.3f}\n"
            f"  false_positives={list(metrics.false_positive_ids)}\n"
            f"  false_negatives={list(metrics.false_negative_ids)}"
        )

    reasons = ", ".join(f"{name}={count}" for name, count in sorted(report.reason_counts.items()))
    return (
        f"Opportunity detection evaluation ({report.n_assessed}/{report.n_examples} assessed)\n"
        f"{block('Full set', report.full)}\n"
        f"{block('Clear subset', report.clear)}\n"
        f"Reason counts: {reasons}\n"
        "Limitation: this fixture is hand-authored and too small for production claims."
    )


def main(argv: Optional[list[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    path = Path(args[0]) if args else default_fixture_path()
    report = evaluate(load_eval_rows(path))
    print(format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
