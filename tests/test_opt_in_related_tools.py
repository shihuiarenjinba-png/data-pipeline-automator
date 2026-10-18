"""Opt-in product discovery stays completely local with no external tracking."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OptionalToolDiscoveryTests(unittest.TestCase):
    def test_discovers_only_existing_product_names_without_auto_launch(self):
        source = (ROOT / "data_porter_gui.py").read_text(encoding="utf-8")
        self.assertIn("関連する便利なツール", source)
        self.assertIn("command=self.show_related_tools", source)
        for name in ("Spreadsheet Merger", "Excel Formula Auditor",
                     "Document Version Audit"):
            self.assertIn(name, source)
        self.assertIn("messagebox.showinfo(", source)
        self.assertNotIn("webbrowser.open(", source)
        self.assertNotIn("http://", source)
        self.assertNotIn("https://", source)


if __name__ == "__main__":
    unittest.main()
