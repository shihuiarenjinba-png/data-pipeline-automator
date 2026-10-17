"""Commercial preflight: a preview must never write or claim to have escaped data."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from data_porter import convert


class PorterPreviewAcceptanceTests(unittest.TestCase):
    def test_csv_formula_preview_and_actual_change_are_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = [
                {"id": "001", "note": "=SUM(1,2)"},
                {"id": "002", "note": "+1"},
                {"id": "003", "note": "通常の文字列"},
                {"id": "004", "note": "unchanged"},
                {"id": "005", "note": "a"},
                {"id": "006", "note": "b"},
            ]
            (root / "入力.jsonl").write_text(
                "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in data),
                encoding="utf-8",
            )
            original = (root / "入力.jsonl").read_bytes()
            preview = convert(root, "入力.jsonl", "出力.csv", dry_run=True)
            self.assertFalse((root / "出力.csv").exists())
            self.assertEqual(preview["csv_formula_values_to_escape"], 2)
            self.assertEqual(preview["csv_formula_values_escaped"], 0)
            self.assertEqual(len(preview["preview_input_rows"]), 5)
            self.assertEqual(len(preview["preview_output_rows"]), 5)
            self.assertEqual(preview["preview_input_rows"][0]["note"], "=SUM(1,2)")
            self.assertEqual(preview["preview_output_rows"][0]["note"], "'=SUM(1,2)")
            self.assertEqual(preview["preview_output_rows"][1]["note"], "'+1")
            self.assertEqual(preview["preview_output_rows"][2]["note"], "通常の文字列")
            self.assertEqual((root / "入力.jsonl").read_bytes(), original)
            actual = convert(root, "入力.jsonl", "出力.csv")
            self.assertEqual(actual["csv_formula_values_escaped"], 2)
            self.assertEqual(actual["csv_formula_values_to_escape"], 2)
            with (root / "出力.csv").open(encoding="utf-8", newline="") as handle:
                restored = list(csv.DictReader(handle))
            self.assertEqual(restored[0]["id"], "001")
            self.assertEqual(restored[0]["note"], "'=SUM(1,2)")
            self.assertEqual((root / "入力.jsonl").read_bytes(), original)

    def test_csv_to_jsonl_preview_preserves_leading_zeros(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "data.csv").write_text("id,text\n001,=1+2\n", encoding="utf-8")
            result = convert(root, "data.csv", "data.jsonl", dry_run=True)
            self.assertEqual(result["preview_output_rows"], [{"id": "001", "text": "=1+2"}])
            self.assertEqual(result["csv_formula_values_to_escape"], 0)
            self.assertFalse((root / "data.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
