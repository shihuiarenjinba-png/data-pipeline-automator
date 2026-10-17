"""Pure UI path helpers for the local CSV/JSONL converter."""
from __future__ import annotations

from pathlib import Path


def suggested_output(source: str | Path) -> Path:
    """Pick a new opposite-format filename, never proposing an existing path."""
    path = Path(source).expanduser().resolve()
    ext = path.suffix.lower()
    if ext not in {".csv", ".jsonl"}:
        raise ValueError("対応する入力形式はCSVとJSONLのみです。")
    out_ext = ".jsonl" if ext == ".csv" else ".csv"
    stem = path.stem + "_converted"
    candidate = path.with_name(stem + out_ext)
    counter = 2
    while candidate.exists():
        candidate = path.with_name(f"{stem}_{counter}{out_ext}")
        counter += 1
    return candidate
