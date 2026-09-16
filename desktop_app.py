from __future__ import annotations

import contextlib
import io
import json
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from data_pipeline import Pipeline, PipelineError


class DataPipelineDesktop:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Data Pipeline Automator / データ変換")
        self.root.geometry("1000x720")
        self.root.minsize(850, 620)
        self.config_path = tk.StringVar()
        self.status = tk.StringVar(value="Ready / 準備完了")
        self.config: dict | None = None
        self._build()
        default = Path(__file__).resolve().parent / "pipeline.example.json"
        if default.is_file():
            self.config_path.set(str(default))
            self._load_config(False)

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Data Pipeline Automator", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(outer, text="CSVを決められたルールで変換。出力前にDry Runで行数・列・Formula安全性を確認します。").pack(anchor="w", pady=(0, 14))

        cfg = ttk.LabelFrame(outer, text="Configuration / 設定", padding=10)
        cfg.pack(fill="x", pady=(0, 10))
        ttk.Entry(cfg, textvariable=self.config_path).pack(side="left", fill="x", expand=True)
        ttk.Button(cfg, text="Browse / 選択", command=self._browse).pack(side="left", padx=(8, 0))
        ttk.Button(cfg, text="Validate / 検証", command=lambda: self._load_config(True)).pack(side="left", padx=(6, 0))

        summary_box = ttk.LabelFrame(outer, text="Pipeline / パイプライン概要", padding=8)
        summary_box.pack(fill="both", expand=True, pady=(0, 10))
        self.summary = ttk.Treeview(summary_box, columns=("item", "value"), show="headings", height=7)
        self.summary.heading("item", text="Item / 項目")
        self.summary.heading("value", text="Value / 内容")
        self.summary.column("item", width=220, anchor="w")
        self.summary.column("value", width=700, anchor="w")
        self.summary.pack(fill="x")
        ttk.Label(summary_box, text="Operations / 変換手順").pack(anchor="w", pady=(10, 4))
        self.operations = tk.Listbox(summary_box, height=7)
        self.operations.pack(fill="both", expand=True)

        actions = ttk.LabelFrame(outer, text="Preview and Run / 確認と実行", padding=10)
        actions.pack(fill="x", pady=(0, 10))
        self.preview_btn = ttk.Button(actions, text="Preview / Dry Run", command=self._preview)
        self.preview_btn.pack(side="left")
        self.run_btn = ttk.Button(actions, text="Run Pipeline / 変換実行", command=self._run)
        self.run_btn.pack(side="left", padx=6)
        ttk.Label(actions, text="既定formula policyは reject。Excel等で式として評価され得る値を検出すると出力を止めます。", wraplength=560).pack(side="right")

        logbox = ttk.LabelFrame(outer, text="Result / 結果", padding=8)
        logbox.pack(fill="both", expand=True)
        self.log = tk.Text(logbox, wrap="word", height=11, state="disabled", font=("Consolas", 9))
        self.log.pack(fill="both", expand=True)
        ttk.Label(outer, textvariable=self.status).pack(fill="x", pady=(8, 0))

    def _browse(self) -> None:
        path = filedialog.askopenfilename(title="Pipeline JSON", filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if path:
            self.config_path.set(path)
            self._load_config(True)

    def _read(self) -> dict:
        path = Path(self.config_path.get()).expanduser().resolve()
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise PipelineError("config root must be an object")
        return raw

    def _load_config(self, show_error: bool) -> bool:
        try:
            raw = self._read()
            pipeline = Pipeline(raw, dry_run=True)
            self.config = raw
            self._render(pipeline)
            self.status.set("Configuration valid / 設定OK")
            return True
        except Exception as exc:
            self.config = None
            self.status.set(f"Configuration error / 設定エラー: {type(exc).__name__}")
            if show_error:
                messagebox.showerror("Configuration", str(exc))
            return False

    def _render(self, pipeline: Pipeline) -> None:
        for item in self.summary.get_children():
            self.summary.delete(item)
        rows = [
            ("Input CSV / 入力", str(pipeline.input_path)),
            ("Output CSV / 出力", str(pipeline.output_path)),
            ("Encoding", pipeline.encoding),
            ("Overwrite / 上書き", str(pipeline.overwrite)),
            ("Formula policy", pipeline.formula_policy),
            ("Root / ルート", str(pipeline.root)),
        ]
        for row in rows:
            self.summary.insert("", "end", values=row)
        self.operations.delete(0, "end")
        for index, op in enumerate(pipeline.operations, start=1):
            if isinstance(op, dict):
                self.operations.insert("end", f"{index}. {op.get('type', '?')} — {json.dumps(op, ensure_ascii=False)}")
            else:
                self.operations.insert("end", f"{index}. INVALID")

    def _append(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _execute(self, dry_run: bool) -> None:
        if not self._load_config(True):
            return
        assert self.config is not None
        raw = self.config
        self.preview_btn.configure(state="disabled")
        self.run_btn.configure(state="disabled")
        self.status.set("Previewing… / 確認中…" if dry_run else "Running… / 変換中…")
        def worker() -> None:
            buffer = io.StringIO()
            try:
                with contextlib.redirect_stdout(buffer):
                    Pipeline(raw, dry_run=dry_run).run()
                text = buffer.getvalue() or "OK"
                self.root.after(0, lambda: self._finish(True, text, dry_run))
            except Exception as exc:
                text = buffer.getvalue() + f"ERROR: {type(exc).__name__}: {exc}"
                self.root.after(0, lambda: self._finish(False, text, dry_run))
        threading.Thread(target=worker, daemon=True).start()

    def _preview(self) -> None:
        self._execute(True)

    def _run(self) -> None:
        if not messagebox.askyesno("Run Pipeline / 変換実行", "実際に出力ファイルを書き込みます。Previewで内容を確認済みの場合だけ続行してください。"):
            return
        self._execute(False)

    def _finish(self, ok: bool, text: str, dry_run: bool) -> None:
        self._append(text)
        self.preview_btn.configure(state="normal")
        self.run_btn.configure(state="normal")
        self.status.set(("Preview complete / 確認完了" if dry_run else "Pipeline complete / 変換完了") if ok else "Failed / 失敗")
        if not ok:
            messagebox.showerror("Data Pipeline", text[-1500:])


def main() -> None:
    root = tk.Tk()
    DataPipelineDesktop(root)
    root.mainloop()


if __name__ == "__main__":
    main()
