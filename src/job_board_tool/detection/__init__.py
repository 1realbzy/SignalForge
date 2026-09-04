"""Opportunity detection: RawPost → OpportunityCandidate assessment."""

from job_board_tool.detection.config import DetectionConfig
from job_board_tool.detection.detector import OpportunityDetector
from job_board_tool.detection.models import DetectionSignal, OpportunityCandidate, OpportunityCategory

__all__ = [
    "DetectionConfig",
    "DetectionSignal",
    "OpportunityCandidate",
    "OpportunityCategory",
    "OpportunityDetector",
]
