"""GUI sample for first-time users must never overwrite an existing file."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from data_porter_gui import PorterGUI


class Value:
    def __init__(self): self.value = ""
    def set(self, value): self.value = value


class FakeWindow:
    def __init__(self):
        self.rootdir, self.source, self.destination, self.status = (
            Value(), Value(), Value(), Value()
        )


class SampleCsvTests(unittest.TestCase):
    def test_sample_creates_new_csv_and_suggests_jsonl(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "sample.csv"
            ui = FakeWindow()
            with patch("data_porter_gui.filedialog.asksaveasfilename", return_value=str(target)):
                PorterGUI.make_sample_csv(ui)
            self.assertTrue(target.is_file())
            self.assertIn("001,1200", target.read_text(encoding="utf-8-sig"))
            self.assertEqual(Path(ui.destination.value).suffix, ".jsonl")
            original = target.read_bytes()
            with patch("data_porter_gui.filedialog.asksaveasfilename", return_value=str(target)), \
                 patch("data_porter_gui.messagebox.showerror") as message:
                PorterGUI.make_sample_csv(ui)
            message.assert_called_once()
            self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
