from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from data_pipeline import Pipeline, PipelineError


class DataPipelineTests(unittest.TestCase):
    def test_duplicate_input_headers_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "in.csv").write_text("name,name\na,b\n", encoding="utf-8-sig")
            pipeline = Pipeline({"root_dir": str(root), "input_csv": "in.csv", "output_csv": "out.csv"})
            with self.assertRaisesRegex(PipelineError, "duplicate column names"):
                pipeline.load()

    def test_formula_like_cell_is_rejected_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "in.csv").write_text("name\n=HYPERLINK(\"https://example.com\")\n", encoding="utf-8-sig")
            pipeline = Pipeline({"root_dir": str(root), "input_csv": "in.csv", "output_csv": "out.csv"})
            rows, fields = pipeline.load()
            with self.assertRaisesRegex(PipelineError, "Potential spreadsheet formula"):
                pipeline.write(rows, fields)
            self.assertFalse((root / "out.csv").exists())

    def test_escape_policy_exports_formula_as_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "in.csv").write_text("name\n=1+1\n", encoding="utf-8-sig")
            pipeline = Pipeline({
                "root_dir": str(root),
                "input_csv": "in.csv",
                "output_csv": "out.csv",
                "spreadsheet_formula_policy": "escape",
            })
            pipeline.run()
            with (root / "out.csv").open("r", encoding="utf-8-sig", newline="") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(rows[0]["name"], "'=1+1")

    def test_signed_numeric_value_is_not_treated_as_formula(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "in.csv").write_text("value\n-12.5\n", encoding="utf-8-sig")
            pipeline = Pipeline({"root_dir": str(root), "input_csv": "in.csv", "output_csv": "out.csv"})
            pipeline.run()
            self.assertTrue((root / "out.csv").exists())

    def test_select_columns_duplicate_names_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "in.csv").write_text("a,b\n1,2\n", encoding="utf-8-sig")
            pipeline = Pipeline({
                "root_dir": str(root),
                "input_csv": "in.csv",
                "output_csv": "out.csv",
                "operations": [{"type": "select_columns", "columns": ["a", "a"]}],
            })
            rows, fields = pipeline.load()
            with self.assertRaisesRegex(PipelineError, "duplicate column names"):
                pipeline.apply(rows, fields)


if __name__ == "__main__":
    unittest.main()
