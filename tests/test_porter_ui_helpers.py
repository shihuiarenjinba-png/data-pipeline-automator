import tempfile
import unittest
from pathlib import Path

from porter_ui_helpers import suggested_output


class PorterPathSuggestionTests(unittest.TestCase):
    def test_csv_destination_and_conflict_avoidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "売上.csv"
            src.write_text("id\n1\n", encoding="utf-8")
            proposed = suggested_output(src)
            self.assertEqual(proposed.name, "売上_converted.jsonl")
            proposed.write_text("not overwritten", encoding="utf-8")
            self.assertEqual(suggested_output(src).name, "売上_converted_2.jsonl")

    def test_jsonl_destination_and_invalid_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "orders.jsonl"
            src.write_text('{"id":"1"}\n', encoding="utf-8")
            self.assertEqual(suggested_output(src).name, "orders_converted.csv")
            with self.assertRaises(ValueError):
                suggested_output(Path(tmp) / "something.exe")


if __name__ == "__main__":
    unittest.main()
