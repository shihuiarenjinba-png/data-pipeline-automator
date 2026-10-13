"""Tests for the CSV <-> JSONL migration adapter."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from data_porter import convert


class LocalDataPorterTests(unittest.TestCase):
    def test_csv_to_jsonl_preserves_string_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data.csv").write_text("id,text\n00123,こんにちは\n00002,=1+2\n", encoding="utf-8")
            before = (root / "data.csv").read_bytes()
            result = convert(root, "data.csv", "data.jsonl")
            self.assertEqual(result["row_count"], 2)
            rows = [json.loads(x) for x in (root / "data.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[0]["id"], "00123")
            self.assertEqual(rows[1]["text"], "=1+2")
            self.assertEqual((root / "data.csv").read_bytes(), before)

    def test_jsonl_to_csv_defuses_formulas(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.jsonl").write_text(
                json.dumps({"id": "0001", "note": "=HYPERLINK(\"x\")"}) + "\n", encoding="utf-8")
            result = convert(root, "a.jsonl", "b.csv")
            with (root / "b.csv").open(encoding="utf-8") as f:
                got = list(csv.DictReader(f))
            self.assertEqual(result["csv_formula_values_escaped"], 1)
            self.assertEqual(got[0]["note"], "'=HYPERLINK(\"x\")")
            self.assertEqual(got[0]["id"], "0001")

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.csv").write_text("id\n1\n", encoding="utf-8")
            (root / "b.jsonl").write_text("do-not-overwrite", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                convert(root, "a.csv", "b.jsonl")
            self.assertEqual((root / "b.jsonl").read_text(encoding="utf-8"), "do-not-overwrite")

    def test_schema_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.jsonl").write_text('{"id":"1","name":"a"}\n{"id":"2"}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                convert(root, "a.jsonl", "b.csv")
            self.assertFalse((root / "b.csv").exists())

    def test_path_traversal_prohibited(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                convert(root, "../outside.csv", "b.jsonl", dry_run=True)


if __name__ == "__main__":
    unittest.main()
