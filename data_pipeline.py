from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


class PipelineError(RuntimeError):
    pass


_NUMERIC_WITH_SIGN = re.compile(r"^[+-](?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def _looks_like_spreadsheet_formula(value: str) -> bool:
    stripped = value.lstrip(" \t\r\n")
    if not stripped:
        return False
    if stripped[0] in {"=", "@"}:
        return True
    if stripped[0] in {"+", "-"} and not _NUMERIC_WITH_SIGN.fullmatch(stripped):
        return True
    return False


class Pipeline:
    def __init__(self, config: dict[str, Any], dry_run: bool = False) -> None:
        self.config = config
        self.dry_run = dry_run
        self.root = Path(config.get("root_dir", ".")).expanduser().resolve()
        self.input_path = self._path(str(config["input_csv"]))
        self.output_path = self._path(str(config["output_csv"]))
        self.encoding = str(config.get("encoding", "utf-8-sig"))
        self.overwrite = bool(config.get("overwrite", False))
        self.formula_policy = str(config.get("spreadsheet_formula_policy", "reject")).lower()
        if self.formula_policy not in {"reject", "escape", "preserve"}:
            raise PipelineError("spreadsheet_formula_policy must be reject, escape, or preserve")
        operations = config.get("operations", [])
        if not isinstance(operations, list):
            raise PipelineError("operations must be a list")
        self.operations = operations

    def _path(self, value: str) -> Path:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = self.root / path
        path = path.resolve()
        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise PipelineError(f"Path is outside root_dir: {path}") from exc
        return path

    def load(self) -> tuple[list[dict[str, str]], list[str]]:
        if not self.input_path.is_file():
            raise PipelineError(f"Input CSV does not exist: {self.input_path}")
        with self.input_path.open("r", encoding=self.encoding, newline="") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames:
                raise PipelineError("CSV header is missing")
            fieldnames = [str(x) for x in reader.fieldnames]
            if any(not field.strip() for field in fieldnames):
                raise PipelineError("CSV header contains an empty column name")
            if len(fieldnames) != len(set(fieldnames)):
                raise PipelineError("CSV header contains duplicate column names")
            rows = [{k: (v or "") for k, v in row.items() if k is not None} for row in reader]
        return rows, fieldnames

    def apply(self, rows: list[dict[str, str]], fields: list[str]) -> tuple[list[dict[str, str]], list[str]]:
        for index, op in enumerate(self.operations, start=1):
            if not isinstance(op, dict):
                raise PipelineError(f"operation {index} must be an object")
            kind = str(op.get("type", ""))

            if kind == "drop_empty_rows":
                rows = [row for row in rows if any(str(row.get(f, "")).strip() for f in fields)]

            elif kind == "select_columns":
                wanted = [str(x) for x in op.get("columns", [])]
                if len(wanted) != len(set(wanted)):
                    raise PipelineError("select_columns contains duplicate column names")
                missing = [x for x in wanted if x not in fields]
                if missing:
                    raise PipelineError(f"select_columns missing fields: {missing}")
                rows = [{f: row.get(f, "") for f in wanted} for row in rows]
                fields = wanted

            elif kind == "rename_columns":
                raw_mapping = op.get("mapping", {})
                if not isinstance(raw_mapping, dict):
                    raise PipelineError("rename_columns mapping must be an object")
                mapping = {str(k): str(v) for k, v in raw_mapping.items()}
                missing = [x for x in mapping if x not in fields]
                if missing:
                    raise PipelineError(f"rename_columns missing fields: {missing}")
                new_fields = [mapping.get(f, f) for f in fields]
                if any(not field.strip() for field in new_fields):
                    raise PipelineError("rename_columns creates an empty column name")
                if len(new_fields) != len(set(new_fields)):
                    raise PipelineError("rename_columns creates duplicate column names")
                rows = [{mapping.get(k, k): v for k, v in row.items()} for row in rows]
                fields = new_fields

            elif kind == "deduplicate":
                on = [str(x) for x in op.get("on", fields)]
                if not on:
                    raise PipelineError("deduplicate requires at least one field")
                missing = [x for x in on if x not in fields]
                if missing:
                    raise PipelineError(f"deduplicate missing fields: {missing}")
                seen: set[tuple[str, ...]] = set()
                unique: list[dict[str, str]] = []
                for row in rows:
                    key = tuple(row.get(f, "") for f in on)
                    if key not in seen:
                        seen.add(key)
                        unique.append(row)
                rows = unique

            elif kind == "sort":
                by = [str(x) for x in op.get("by", [])]
                if not by:
                    raise PipelineError("sort requires at least one field")
                missing = [x for x in by if x not in fields]
                if missing:
                    raise PipelineError(f"sort missing fields: {missing}")
                reverse = bool(op.get("reverse", False))
                rows = sorted(rows, key=lambda row: tuple(row.get(f, "") for f in by), reverse=reverse)

            else:
                raise PipelineError(f"Unsupported operation: {kind}")
        return rows, fields

    def _prepare_output_rows(self, rows: list[dict[str, str]], fields: list[str]) -> list[dict[str, str]]:
        prepared: list[dict[str, str]] = []
        for row_number, row in enumerate(rows, start=2):
            output: dict[str, str] = {}
            for field in fields:
                value = str(row.get(field, ""))
                if _looks_like_spreadsheet_formula(value):
                    if self.formula_policy == "reject":
                        raise PipelineError(
                            f"Potential spreadsheet formula detected at row {row_number}, column '{field}'. "
                            "Set spreadsheet_formula_policy='escape' to export as text or 'preserve' only for trusted data."
                        )
                    if self.formula_policy == "escape":
                        value = "'" + value
                output[field] = value
            prepared.append(output)
        return prepared

    def write(self, rows: list[dict[str, str]], fields: list[str]) -> None:
        if self.output_path.exists() and not self.overwrite:
            raise PipelineError(f"Output already exists and overwrite=false: {self.output_path}")

        safe_rows = self._prepare_output_rows(rows, fields)
        if self.dry_run:
            print(json.dumps({"input": str(self.input_path), "output": str(self.output_path), "rows": len(safe_rows), "columns": fields, "formula_policy": self.formula_policy, "dry_run": True}, ensure_ascii=False))
            return

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.output_path.with_name(self.output_path.name + ".tmp")
        try:
            with temp.open("w", encoding=self.encoding, newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(safe_rows)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(temp, self.output_path)
        finally:
            if temp.exists():
                temp.unlink()
        print(json.dumps({"output": str(self.output_path), "rows": len(safe_rows), "columns": fields, "formula_policy": self.formula_policy}, ensure_ascii=False))

    def run(self) -> None:
        rows, fields = self.load()
        rows, fields = self.apply(rows, fields)
        self.write(rows, fields)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic local CSV pipeline")
    parser.add_argument("config", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        Pipeline(config, dry_run=args.dry_run).run()
        return 0
    except (OSError, csv.Error, json.JSONDecodeError, KeyError, ValueError, PipelineError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
