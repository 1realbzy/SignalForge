"""Score a blindly labeled local detection-eval sample.

Uses the frozen OpportunityDetector. Writes local gitignored reports.
Do not commit the output.

Usage:
    python -m scripts.score_detection_eval_sample --run-dir data/local/detection_eval/RUN_ID
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
for _path in (_SRC, _ROOT):
    _text = str(_path)
    if _text not in sys.path:
        sys.path.insert(0, _text)

from job_board_tool.detection.detector import OpportunityDetector

from scripts.detection_eval_support import (
    append_jsonl,
    format_query_counts,
    format_score_report,
    load_jsonl,
    per_query_counts,
    score_labels,
    write_json,
)


def score_run(run_dir: Path) -> int:
    sample_path = run_dir / "sample.jsonl"
    labels_path = run_dir / "labels.jsonl"
    meta_path = run_dir / "run_meta.json"
    if not sample_path.exists():
        print(f"Missing {sample_path}", file=sys.stderr)
        return 2
    if not labels_path.exists():
        print(f"Missing {labels_path}. Label label_queue.jsonl first.", file=sys.stderr)
        return 2

    sample = load_jsonl(sample_path)
    labels = load_jsonl(labels_path)
    meta = {}
    if meta_path.exists():
        import json

        meta = json.loads(meta_path.read_text(encoding="utf-8"))

    payload = score_labels(sample, labels, detector=OpportunityDetector())
    queries = meta.get("queries") or sorted(
        {
            (row.get("raw_post") or {}).get("discovered_via")
            for row in sample
            if (row.get("raw_post") or {}).get("discovered_via")
        }
    )
    query_counts = meta.get("query_counts") or per_query_counts(sample, queries)
    meta["query_counts"] = query_counts

    scored_path = run_dir / "scored.jsonl"
    if scored_path.exists():
        scored_path.unlink()
    for row in payload["scored"]:
        append_jsonl(scored_path, row)

    report = format_score_report(meta, payload)
    (run_dir / "report.txt").write_text(report + "\n", encoding="utf-8")
    write_json(run_dir / "score_summary.json", {k: v for k, v in payload.items() if k != "scored"})
    print(report)
    print(format_query_counts(query_counts))
    print(f"Wrote local report under {run_dir}. Do not commit data/local/.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score a local labeled detection-eval sample.")
    parser.add_argument("--run-dir", required=True, help="Path to data/local/detection_eval/<run_id>")
    args = parser.parse_args(argv)
    return score_run(Path(args.run_dir))


if __name__ == "__main__":
    raise SystemExit(main())
