"""Collect a small real X sample for detection evidence-validation.

Uses existing XTwitterSource.discover() only. Writes local gitignored files.
Does not change the detector or ingestion. Do not commit the output.

Usage:
    python -m scripts.collect_detection_eval_sample
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
for _path in (_SRC, _ROOT):
    _text = str(_path)
    if _text not in sys.path:
        sys.path.insert(0, _text)

from job_board_tool.detection.config import DetectionConfig
from job_board_tool.ingestion.errors import XAuthError, XRateLimited
from job_board_tool.ingestion.x_source import XSourceConfig, XTwitterSource

from scripts.detection_eval_support import (
    DEFAULT_COUNT,
    DEFAULT_INTER_QUERY_DELAY,
    DEFAULT_MAX_PAGES,
    TARGET_UNIQUE,
    DedupeIndex,
    append_jsonl,
    empty_query_counts,
    format_query_counts,
    label_queue_row,
    load_queries,
    utc_now,
    write_json,
)

logger = logging.getLogger(__name__)
ROOT = _ROOT
DEFAULT_QUERIES = ROOT / "evals" / "detection" / "queries.json"


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _run_dir(run_id: str) -> Path:
    return ROOT / "data" / "local" / "detection_eval" / run_id


async def collect(args: argparse.Namespace) -> int:
    queries = load_queries(Path(args.queries))
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out_dir) if args.out_dir else _run_dir(run_id)
    sample_path = out_dir / "sample.jsonl"
    queue_path = out_dir / "label_queue.jsonl"
    meta_path = out_dir / "run_meta.json"

    detection = DetectionConfig()
    config = XSourceConfig(inter_query_delay_seconds=args.inter_query_delay)
    source = XTwitterSource(config=config)
    try:
        await source.authenticate()
    except XAuthError as exc:
        logger.error(
            "Authentication failed: %s. Use local cookies.json, X_COOKIES_PATH, or .env credentials.",
            exc,
        )
        return 2

    if args.health_check:
        healthy = await source.health_check()
        if not healthy:
            logger.error("Optional health_check failed; aborting before collection.")
            return 2

    index = DedupeIndex()
    query_counts = empty_query_counts(queries)
    stop_reason = "queries_exhausted"
    collected_at = utc_now()
    git_sha = _git_sha()

    def dump_meta(reason: str) -> dict:
        meta = {
            "run_id": run_id,
            "collected_at": collected_at,
            "git_sha": git_sha,
            "queries": queries,
            "count": args.count,
            "max_pages": args.max_pages,
            "product": args.product,
            "inter_query_delay_seconds": args.inter_query_delay,
            "target_unique": args.target,
            "kept_unique": len(index.kept_records),
            "skipped_exact_id": index.skipped_exact_id,
            "skipped_exact_text": index.skipped_exact_text,
            "stop_reason": reason,
            "query_counts": query_counts,
            "detector_frozen": True,
            "detection_config": {
                "threshold": detection.threshold,
                "min_text_length": detection.min_text_length,
                "weight_overrides": dict(detection.weight_overrides),
            },
            "note": "Human labels must be written without viewing detector scores.",
        }
        write_json(meta_path, meta)
        return meta

    try:
        async for post in source.discover(
            queries,
            count=args.count,
            max_pages=args.max_pages,
            product=args.product,
        ):
            query = post.discovered_via or ""
            if query not in query_counts:
                query_counts[query] = empty_query_counts([query])[query]
            query_counts[query]["yielded"] += 1
            result = index.consider(post)
            if not result.keep:
                if result.reason == "exact_id":
                    query_counts[query]["skipped_exact_id"] += 1
                elif result.reason == "exact_text":
                    query_counts[query]["skipped_exact_text"] += 1
                logger.info(
                    "Skipped %s duplicate. kept=%s skipped_exact_id=%s skipped_exact_text=%s",
                    result.reason,
                    len(index.kept_records),
                    index.skipped_exact_id,
                    index.skipped_exact_text,
                )
                continue
            record = result.record
            assert record is not None
            record["eval_id"] = f"{run_id}-{record['eval_id']}"
            record["collected_at"] = collected_at
            record["git_sha"] = git_sha
            query_counts[query]["kept"] += 1
            append_jsonl(sample_path, record)
            append_jsonl(queue_path, label_queue_row(record))
            dump_meta(stop_reason)
            logger.info(
                "Kept unique post %s. kept=%s skipped_exact_id=%s skipped_exact_text=%s",
                record["eval_id"],
                len(index.kept_records),
                index.skipped_exact_id,
                index.skipped_exact_text,
            )
            if len(index.kept_records) >= args.target:
                stop_reason = "target_reached"
                break
    except XAuthError as exc:
        logger.error(
            "Authentication failed during discover: %s. Use local cookies.json, X_COOKIES_PATH, or .env credentials.",
            exc,
        )
        stop_reason = "auth_error"
    except XRateLimited:
        logger.error("Collection stopped after an X rate-limit response.")
        stop_reason = "rate_limited"
    except Exception as exc:
        logger.exception("Collection stopped early: %s", type(exc).__name__)
        stop_reason = "error"

    dump_meta(stop_reason)
    print(f"Wrote {len(index.kept_records)} unique posts to {out_dir}")
    print(f"stop_reason={stop_reason}")
    print(format_query_counts(query_counts))
    print("Label only label_queue.jsonl. Do not commit data/local/.")
    return 0 if stop_reason in {"target_reached", "queries_exhausted"} else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect a small local X detection-eval sample.")
    parser.add_argument("--queries", default=str(DEFAULT_QUERIES))
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument("--product", default="Latest")
    parser.add_argument("--inter-query-delay", type=float, default=DEFAULT_INTER_QUERY_DELAY)
    parser.add_argument("--target", type=int, default=TARGET_UNIQUE)
    parser.add_argument("--run-id")
    parser.add_argument("--out-dir")
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Optional live search probe. Off by default because it spends a request.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    return asyncio.run(collect(args))


if __name__ == "__main__":
    raise SystemExit(main())
