"""Additive, offline CSV <-> JSON Lines migration adapter.

Standalone executable alongside data_pipeline.py. The original CSV pipeline
is intentionally unchanged. All cells are strings; leading zeros are preserved.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import tempfile
from pathlib import Path
from threading import Event

MAX_ROWS = 250000
MAX_BYTES = 150 * 1024 * 1024


def confined(root: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute():
        raise ValueError("Specify a non-empty relative path within --root")
    base = root.expanduser().resolve(strict=True)
    path = (base / relative).resolve()
    if not path.is_relative_to(base):
        raise ValueError("Path escapes root")
    return path


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _escape_spreadsheet_formula(s: str) -> str:
    if s.lstrip().startswith(("=", "+", "-", "@")) or s[:1] in ("\t", "\r", "\n"):
        return "'" + s
    return s


def _check_cancel(cancel_event: Event | None) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise InterruptedError("変換がキャンセルされました。出力ファイルは作成されていません。")


def _reader(path: Path, kind: str, *,
            cancel_event: Event | None = None) -> tuple[list[str], list[dict[str, str]]]:
    _check_cancel(cancel_event)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("Input larger than safety limit")
    if kind == "csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            dr = csv.DictReader(f, strict=True)
            columns = dr.fieldnames
            if not columns or not all(columns) or len(columns) != len(set(columns)):
                raise ValueError("Empty or duplicate CSV headers")
            rows: list[dict[str, str]] = []
            for index, rec in enumerate(dr, start=1):
                _check_cancel(cancel_event)
                if index > MAX_ROWS:
                    raise ValueError("Row limit exceeded")
                if None in rec or any(v is None for v in rec.values()):
                    raise ValueError(f"Inconsistent CSV row {index}")
                rows.append({k: str(rec[k]) for k in columns})
        return columns, rows
    if kind == "jsonl":
        rows = []
        columns = None
        with path.open("r", encoding="utf-8-sig") as f:
            for index, line in enumerate(f, start=1):
                _check_cancel(cancel_event)
                if not line.strip():
                    continue
                if len(rows) >= MAX_ROWS:
                    raise ValueError("Row limit exceeded")
                def unique_pairs(pairs):
                    found = {}
                    for k, v in pairs:
                        if k in found:
                            raise ValueError(f"Duplicate JSON key on line {index}: {k}")
                        found[k] = v
                    return found
                try:
                    entry = json.loads(line, object_pairs_hook=unique_pairs)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at line {index}") from exc
                if not isinstance(entry, dict) or not entry or not all(isinstance(k, str) and k for k in entry):
                    raise ValueError(f"JSONL object with non-empty keys required (line {index})")
                if not all(isinstance(v, str) for v in entry.values()):
                    raise ValueError(f"All JSONL values must be strings (line {index})")
                if columns is None:
                    columns = list(entry.keys())
                if set(entry.keys()) != set(columns):
                    raise ValueError(f"Unexpected/missing keys on JSONL line {index}")
                rows.append({c: entry[c] for c in columns})
        if not columns:
            raise ValueError("Empty JSONL")
        return columns, rows
    raise ValueError("Only csv/jsonl formats supported")


def convert(root_dir: str | Path, input_name: str, output_name: str, *,
            dry_run: bool = False, cancel_event: Event | None = None) -> dict:
    _check_cancel(cancel_event)
    root = Path(root_dir)
    src = confined(root, input_name)
    dst = confined(root, output_name)
    if src == dst or not src.is_file():
        raise ValueError("Source missing or source equals destination")
    if dst.exists():
        raise FileExistsError(f"Output already exists: {dst}")
    kind = src.suffix.lower().removeprefix(".")
    out_kind = dst.suffix.lower().removeprefix(".")
    if {kind, out_kind} != {"csv", "jsonl"}:
        raise ValueError("Only CSV <-> JSONL conversion supported")
    columns, rows = _reader(src, kind, cancel_event=cancel_event)
    _check_cancel(cancel_event)
    result: dict = {"input": str(src), "output": str(dst), "row_count": len(rows),
                    "columns": columns, "source_sha256": _sha(src),
                    "dry_run": dry_run, "csv_formula_values_escaped": 0,
                    "source_format": kind, "target_format": out_kind}
    if out_kind == "csv":
        result["csv_formula_values_to_escape"] = sum(
            _escape_spreadsheet_formula(value) != value
            for row in rows for value in row.values()
        )
    else:
        result["csv_formula_values_to_escape"] = 0
    if dry_run:
        sample = rows[:5]
        result["preview_input_rows"] = sample
        result["preview_output_rows"] = [
            {key: _escape_spreadsheet_formula(value) for key, value in row.items()}
            for row in sample
        ] if out_kind == "csv" else sample
        result["preview_note"] = (
            "最大5行の変換予測です。実際の保存や書込みは行っていません。"
            "CSV向けの数式対策では文字列が変更されます。"
        )
        _check_cancel(cancel_event)
        return result
    _check_cancel(cancel_event)
    dst.parent.mkdir(parents=True, exist_ok=True)
    # No overwrites. Stage under the destination folder and claim final filename
    # atomically using a hard link; if it already exists, creation fails.
    fd, temp_name = tempfile.mkstemp(dir=dst.parent, prefix=".data_porter_", suffix=".tmp")
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            if out_kind == "jsonl":
                for row in rows:
                    _check_cancel(cancel_event)
                    f.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
            else:
                writer = csv.DictWriter(f, fieldnames=columns, extrasaction="raise", lineterminator="\n")
                writer.writeheader()
                for row in rows:
                    _check_cancel(cancel_event)
                    guarded = {key: _escape_spreadsheet_formula(value) for key, value in row.items()}
                    result["csv_formula_values_escaped"] += sum(guarded[key] != row[key] for key in row)
                    writer.writerow(guarded)
            f.flush()
            os.fsync(f.fileno())
        _check_cancel(cancel_event)
        os.link(temp, dst)
    finally:
        temp.unlink(missing_ok=True)
    result["output_sha256"] = _sha(dst)
    return result


def main() -> int:
    p = argparse.ArgumentParser(description="Local CSV/JSONL migration, no overwrite")
    p.add_argument("--root", required=True)
    p.add_argument("--input", required=True, help="Relative CSV/JSONL path inside root")
    p.add_argument("--output", required=True, help="Relative JSONL/CSV path inside root")
    p.add_argument("--dry-run", action="store_true")
    options = p.parse_args()
    try:
        print(json.dumps(convert(options.root, options.input, options.output,
                                 dry_run=options.dry_run), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, csv.Error) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
