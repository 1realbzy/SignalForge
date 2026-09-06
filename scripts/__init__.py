"""Operator scripts. Not part of the opportunity-detection package."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
for _path in (_SRC, _ROOT):
    _text = str(_path)
    if _text not in sys.path:
        sys.path.insert(0, _text)
