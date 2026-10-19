"""Reject modified input files before committing output; never overwrite source."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import data_porter


class PorterSourceIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "data.csv"
        self.target = self.root / "data.jsonl"
        self.source.write_text("id,value\n001,100\n", encoding="utf-8")

    def test_modification_while_reading_blocks_dryrun_and_output(self):
        reader = data_porter._reader

        def edit_after_read(path, kind, **kwargs):
            result = reader(path, kind, **kwargs)
            self.source.write_text("id,value\n001,900\n", encoding="utf-8")
            return result

        with patch("data_porter._reader", side_effect=edit_after_read):
            with self.assertRaisesRegex(ValueError, "変更"):
                data_porter.convert(self.root, "data.csv", "data.jsonl", dry_run=True)
        self.assertFalse(self.target.exists())

    def test_modification_during_output_write_blocks_commit(self):
        def mutate(_fd):
            self.source.write_text("id,value\n001,900\n", encoding="utf-8")

        with patch("data_porter.os.fsync", side_effect=mutate):
            with self.assertRaisesRegex(ValueError, "変更"):
                data_porter.convert(self.root, "data.csv", "data.jsonl")
        self.assertFalse(self.target.exists())
        self.assertEqual(list(self.root.glob(".data_porter_*")), [])


if __name__ == "__main__":
    unittest.main()
