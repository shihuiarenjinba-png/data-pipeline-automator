from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any


class PipelineError(RuntimeError):
    pass


class Pipeline:
    def __init__(self, config: dict[str, Any], dry_run: bool = False) -> None:
        self.config = config
        self.dry_run = dry_run
        self.root = Path(config.get("root_dir", ".")).expanduser().resolve()
        self.input_path = self._path(str(config["input_csv"]))
        self.output_path = self._path(str(config["output_csv"]))
        self.encoding = str(config.get("encoding", "utf-8-sig"))
        self.overwrite = bool(config.get("overwrite", False))
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
                missing = [x for x in wanted if x not in fields]
                if missing:
                    raise PipelineError(f"select_columns missing fields: {missing}")
                rows = [{f: row.get(f, "") for f in wanted} for row in rows]
                fields = wanted

            elif kind == "rename_columns":
                mapping = {str(k): str(v) for k, v in op.get("mapping", {}).items()}
                missing = [x for x in mapping if x not in fields]
                if missing:
                    raise PipelineError(f"rename_columns missing fields: {missing}")
                new_fields = [mapping.get(f, f) for f in fields]
                if len(new_fields) != len(set(new_fields)):
                    raise PipelineError("rename_columns creates duplicate column names")
                rows = [{mapping.get(k, k): v for k, v in row.items()} for row in rows]
                fields = new_fields

            elif kind == "deduplicate":
                on = [str(x) for x in op.get("on", fields)]
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
                missing = [x for x in by if x not in fields]
                if missing:
                    raise PipelineError(f"sort missing fields: {missing}")
                reverse = bool(op.get("reverse", False))
                rows = sorted(rows, key=lambda row: tuple(row.get(f, "") for f in by), reverse=reverse)

            else:
                raise PipelineError(f"Unsupported operation: {kind}")
        return rows, fields

    def write(self, rows: list[dict[str, str]], fields: list[str]) -> None:
        if self.output_path.exists() and not self.overwrite:
            raise PipelineError(f"Output already exists and overwrite=false: {self.output_path}")
        if self.dry_run:
            print(json.dumps({"input": str(self.input_path), "output": str(self.output_path), "rows": len(rows), "columns": fields, "dry_run": True}, ensure_ascii=False))
            return

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.output_path.with_name(self.output_path.name + ".tmp")
        try:
            with temp.open("w", encoding=self.encoding, newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)
            os.replace(temp, self.output_path)
        finally:
            if temp.exists():
                temp.unlink()
        print(json.dumps({"output": str(self.output_path), "rows": len(rows), "columns": fields}, ensure_ascii=False))

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
