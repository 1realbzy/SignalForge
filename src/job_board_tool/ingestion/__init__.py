"""Generic X/Twitter ingestion for the job intelligence platform.

Twikit stays behind XTwitterSource. Downstream code consumes RawPost only.
"""

from job_board_tool.ingestion.errors import XAuthError, XRateLimited
from job_board_tool.ingestion.models import RawPost
from job_board_tool.ingestion.x_source import XSourceConfig, XTwitterSource

__all__ = [
    "RawPost",
    "XAuthError",
    "XRateLimited",
    "XSourceConfig",
    "XTwitterSource",
]
