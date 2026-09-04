from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from job_board_tool.ingestion.models import RawPost


class OpportunityCategory(Enum):
    EMPLOYMENT = "employment"
    INTERNSHIP = "internship"
    GRADUATE_PROGRAM = "graduate_program"
    FELLOWSHIP = "fellowship"
    APPRENTICESHIP = "apprenticeship"
    RESEARCH = "research"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    OTHER = "other"


@dataclass(frozen=True)
class DetectionSignal:
    name: str
    group: str
    polarity: str
    weight: float
    matched_text: str


@dataclass(frozen=True)
class OpportunityCandidate:
    """Detector assessment of one RawPost. Not a confirmed opportunity."""

    raw_post: RawPost
    is_opportunity: bool
    opportunity_score: float
    category: Optional[OpportunityCategory]
    positive_signals: tuple[DetectionSignal, ...]
    negative_signals: tuple[DetectionSignal, ...]
    decision_reasons: tuple[str, ...]
    threshold: float
