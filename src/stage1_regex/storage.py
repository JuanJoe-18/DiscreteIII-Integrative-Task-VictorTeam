"""Persistence of Stage 1 results. The data structure is ``ExtractionResult``; this module saves it to,
and loads it from, a JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from src.stage1_regex.models import ExtractionResult

PathLike = Union[str, Path]


def save_result(result: ExtractionResult, path: PathLike) -> Path:
    """Write ``result`` as pretty-printed UTF-8 JSON and return the path."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return target


def load_result(path: PathLike) -> ExtractionResult:
    """Read a JSON file written by ``save_result``."""
    return ExtractionResult.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))