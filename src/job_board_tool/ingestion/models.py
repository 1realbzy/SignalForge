from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class RawPost:
    """Normalized record from a social/source adapter.

    Downstream layers (opportunity detection, extraction, matching) should
    depend on this model, not on Twikit Tweet objects.
    """

    source: str
    source_id: str
    text: str
    author_username: Optional[str] = None
    author_display_name: Optional[str] = None
    created_at: Optional[str] = None
    url: Optional[str] = None
    author_location: Optional[str] = None
    author_bio: Optional[str] = None
    discovered_via: Optional[str] = None
    raw_data: dict[str, Any] = field(default_factory=dict)
