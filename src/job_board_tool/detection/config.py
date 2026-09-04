from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DetectionConfig:
    threshold: float = 0.45
    min_text_length: int = 8
    weight_overrides: dict[str, float] = field(default_factory=dict)
