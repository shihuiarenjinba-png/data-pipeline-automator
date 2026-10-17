"""CSV formula protection must include header names, not just cell values."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from data_porter import convert


class HeaderTests(unittest.TestCase):
    def test_formula_header_escaped_in_preview_and_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src = root / "input.jsonl"
            src.write_text(json.dumps({"=evil": "=1+2", "id": "001"}) + "\n", encoding="utf-8")
            before = src.read_bytes()
            pre = convert(root, "input.jsonl", "out.csv", dry_run=True)
            self.assertEqual(pre["preview_output_columns"], ["'=evil", "id"])
            self.assertEqual(pre["csv_formula_headers_to_escape"], 1)
            self.assertEqual(pre["csv_formula_values_to_escape"], 1)
            self.assertFalse((root / "out.csv").exists())
            result = convert(root, "input.jsonl", "out.csv")
            self.assertEqual(result["csv_formula_headers_escaped"], 1)
            self.assertEqual(result["csv_formula_values_escaped"], 1)
            with (root / "out.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(rows, [["'=evil", "id"], ["'=1+2", "001"]])
            self.assertEqual(src.read_bytes(), before)

    def test_regular_conversion_does_not_change_ids_or_columns(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "a.csv").write_text("id,note\n001,abc\n", encoding="utf-8")
            first = convert(root, "a.csv", "b.jsonl")
            self.assertEqual(first["csv_formula_headers_to_escape"], 0)
            self.assertEqual(
                json.loads((root / "b.jsonl").read_text(encoding="utf-8")),
                {"id": "001", "note": "abc"},
            )
            second = convert(root, "b.jsonl", "c.csv")
            self.assertEqual(second["csv_formula_headers_to_escape"], 0)
            self.assertEqual((root / "c.csv").read_text(encoding="utf-8"), "id,note\n001,abc\n")


if __name__ == "__main__":
    unittest.main()
