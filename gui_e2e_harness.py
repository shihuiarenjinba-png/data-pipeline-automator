"""Compiled Windows GUI end-to-end fixture: real widget invocations + real CSV conversion.

No human-click or screenshot claim. Uses synthetic data and mocked OS dialogs.
"""
from __future__ import annotations

import csv
import json
import sys
import tempfile
import time
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from unittest.mock import patch


def _buttons(window, label):
    found = []
    def visit(node):
        for child in node.winfo_children():
            if isinstance(child, ttk.Button) and child.cget("text") == label:
                found.append(child)
            visit(child)
    visit(window)
    return found


def _run_until_idle(app, seconds=20):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.update()
        if not app.running:
            app.update()
            return
        time.sleep(0.06)
    raise AssertionError("GUI worker timed out")


def run(GUI):
    if len(sys.argv) != 3 or sys.argv[1] != "--e2e-test":
        raise ValueError("Expected --e2e-test <result-path>")
    marker = Path(sys.argv[2]).resolve()
    with tempfile.TemporaryDirectory(prefix="gui_porter_e2e_") as temp:
        root = Path(temp)
        src = root / "source.csv"
        out = root / "converted.jsonl"
        src.write_text("id,amount,note\n00123,100,A\n00002,200,=2+3\n", encoding="utf-8")
        original = src.read_bytes()
        app = GUI()
        errors = []
        try:
            app.withdraw()
            app.update()
            browse = _buttons(app, "参照")
            assert len(browse) == 3, f"Expected 3 chooser buttons, got {len(browse)}"
            with patch.object(filedialog, "askdirectory", return_value=str(root)):
                browse[0].invoke()
            with patch.object(filedialog, "askopenfilename", return_value=str(src)):
                browse[1].invoke()
            with patch.object(filedialog, "asksaveasfilename", return_value=str(out)):
                browse[2].invoke()
            assert app.rootdir.get() == str(root)
            assert app.source.get() == str(src)
            assert app.destination.get() == str(out)
            assert len(_buttons(app, "事前確認")) == 1
            assert len(_buttons(app, "変換する")) == 1
            with patch.object(messagebox, "showerror", side_effect=lambda *args: errors.append(args)):
                _buttons(app, "事前確認")[0].invoke()
                _run_until_idle(app)
                preview = json.loads(app.preview.get("1.0", "end").strip())
                assert preview["dry_run"] is True
                assert preview["row_count"] == 2
                assert not out.exists(), "Dry-run modified destination"
                _buttons(app, "変換する")[0].invoke()
                _run_until_idle(app)
                assert out.is_file(), "GUI did not produce JSONL"
                records = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
                assert records[0]["id"] == "00123"
                assert records[1]["note"] == "=2+3"
                assert src.read_bytes() == original
                assert not errors, f"Unexpected messageboxes: {errors}"
                # The same GUI action must not overwrite a completed output.
                prior = out.read_bytes()
                _buttons(app, "変換する")[0].invoke()
                _run_until_idle(app)
                assert errors, "Second conversion should show safe no-overwrite error"
                assert out.read_bytes() == prior
            proof = {"status": "GUI_E2E_OK", "scenario": "browse -> preview -> convert -> no-overwrite",
                     "actual_output_verified": True, "input_unchanged": True,
                     "negative_case_verified": True, "interactive_human_test": False}
            with marker.open("x", encoding="utf-8") as file:
                json.dump(proof, file, ensure_ascii=False, indent=2)
        finally:
            app.destroy()
