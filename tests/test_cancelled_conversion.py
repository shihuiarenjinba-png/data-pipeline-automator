"""A cancelled conversion must leave its input and final destination untouched."""
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from data_porter import convert


class CancelTests(unittest.TestCase):
    def test_cancel_before_load_writes_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src = root / "data.csv"
            src.write_text("id\n001\n", encoding="utf-8")
            original = src.read_bytes()
            flag = threading.Event()
            flag.set()
            with self.assertRaises(InterruptedError):
                convert(root, "data.csv", "result.jsonl", cancel_event=flag)
            self.assertFalse((root / "result.jsonl").exists())
            self.assertEqual(src.read_bytes(), original)

    def test_cancel_after_temp_staged_cleans_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src = root / "input.csv"
            src.write_text("id,name\n001,abc\n", encoding="utf-8")
            before = src.read_bytes()
            flag = threading.Event()
            import data_porter
            real_fsync = data_porter.os.fsync

            def cancel_after_fsync(fd):
                result = real_fsync(fd)
                flag.set()
                return result

            with patch("data_porter.os.fsync", side_effect=cancel_after_fsync):
                with patch("data_porter.os.link", side_effect=AssertionError("link must not occur")):
                    with self.assertRaises(InterruptedError):
                        convert(root, "input.csv", "result.jsonl", cancel_event=flag)
            self.assertEqual(list(root.glob(".data_porter_*")), [])
            self.assertFalse((root / "result.jsonl").exists())
            self.assertEqual(src.read_bytes(), before)

    def test_previous_output_untouched_on_cancel(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "data.csv").write_text("id\n001\n", encoding="utf-8")
            old = root / "output.jsonl"
            old.write_text("protected", encoding="utf-8")
            flag = threading.Event()
            flag.set()
            with self.assertRaises(InterruptedError):
                convert(root, "data.csv", "output.jsonl", cancel_event=flag)
            self.assertEqual(old.read_text(encoding="utf-8"), "protected")


if __name__ == "__main__":
    unittest.main()
