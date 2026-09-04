from __future__ import annotations

from typing import Optional

from job_board_tool.detection.categories import assign_category
from job_board_tool.detection.config import DetectionConfig
from job_board_tool.detection.models import OpportunityCandidate
from job_board_tool.detection.signals import compile_signals, match_signals, matching_view
from job_board_tool.ingestion.models import RawPost


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class OpportunityDetector:
    """Assess whether a RawPost plausibly contains an actionable opportunity."""

    def __init__(self, config: Optional[DetectionConfig] = None) -> None:
        self.config = config or DetectionConfig()
        self._compiled = compile_signals()

    def detect(self, post: RawPost) -> OpportunityCandidate:
        threshold = self.config.threshold
        text = post.text if post.text is not None else ""
        if len(text.strip()) < self.config.min_text_length:
            return OpportunityCandidate(
                raw_post=post,
                is_opportunity=False,
                opportunity_score=0.0,
                category=None,
                positive_signals=(),
                negative_signals=(),
                decision_reasons=("insufficient_text", "no_opportunity_evidence"),
                threshold=threshold,
            )

        view = matching_view(text)
        positive, negative = match_signals(view, self._compiled, self.config.weight_overrides)
        positive_groups = {signal.group: signal.weight for signal in positive}
        negative_groups = {signal.group: signal.weight for signal in negative}
        raw = sum(positive_groups.values()) + sum(negative_groups.values())
        score = _clamp(raw)
        has_positive = bool(positive_groups)
        has_negative = bool(negative_groups)
        is_opportunity = score >= threshold and has_positive

        if is_opportunity:
            reasons = ("opportunity",)
            category = assign_category(view)
        elif not has_positive and not has_negative:
            reasons = ("no_opportunity_evidence",)
            category = None
        elif not has_positive and has_negative:
            reasons = ("confirmed_non_opportunity",)
            category = None
        else:
            reasons = ("insufficient_opportunity_evidence",)
            category = None

        return OpportunityCandidate(
            raw_post=post,
            is_opportunity=is_opportunity,
            opportunity_score=score,
            category=category,
            positive_signals=positive,
            negative_signals=negative,
            decision_reasons=reasons,
            threshold=threshold,
        )
