from __future__ import annotations

import contextlib
import io
import json
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from data_pipeline import Pipeline, PipelineError
from ui_language import load_language, save_language

APP_ID = "data-pipeline-automator"


class DataPipelineDesktop:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.lang = load_language(APP_ID)
        self.root.geometry("1000x740")
        self.root.minsize(850, 640)
        self.config_path = tk.StringVar()
        self.status = tk.StringVar(value="")
        self.config: dict | None = None
        self._build()
        default = Path(__file__).resolve().parent / "pipeline.example.json"
        if default.is_file():
            self.config_path.set(str(default))
            self._load_config(False)
        else:
            self.status.set(self.t("準備完了", "Ready"))

    def t(self, ja: str, en: str) -> str:
        return en if self.lang == "en" else ja

    def _build(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()
        self.root.title(self.t("データ変換", "Data Pipeline Automator"))

        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)

        language = ttk.Frame(outer)
        language.pack(fill="x", pady=(0, 8))
        ttk.Label(language, text="言語 / Language", font=("Segoe UI", 9, "bold")).pack(side="right", padx=(0, 6))
        self.language_var = tk.StringVar(value="日本語" if self.lang == "ja" else "English")
        combo = ttk.Combobox(language, textvariable=self.language_var, values=("日本語", "English"), state="readonly", width=10)
        combo.pack(side="right")
        combo.bind("<<ComboboxSelected>>", self._language_changed)

        ttk.Label(outer, text=self.t("データ変換", "Data Pipeline Automator"), font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text=self.t(
                "CSVを決められたルールで変換します。出力前にPreviewで行数・列・Formula安全性を確認します。",
                "Transforms CSV data using configured rules. Preview row/column/formula safety before writing output.",
            ),
        ).pack(anchor="w", pady=(0, 14))

        cfg = ttk.LabelFrame(outer, text=self.t("設定", "Configuration"), padding=10)
        cfg.pack(fill="x", pady=(0, 10))
        ttk.Entry(cfg, textvariable=self.config_path).pack(side="left", fill="x", expand=True)
        ttk.Button(cfg, text=self.t("選択", "Browse"), command=self._browse).pack(side="left", padx=(8, 0))
        ttk.Button(cfg, text=self.t("検証", "Validate"), command=lambda: self._load_config(True)).pack(side="left", padx=(6, 0))

        summary_box = ttk.LabelFrame(outer, text=self.t("パイプライン概要", "Pipeline"), padding=8)
        summary_box.pack(fill="both", expand=True, pady=(0, 10))
        self.summary = ttk.Treeview(summary_box, columns=("item", "value"), show="headings", height=7)
        self.summary.heading("item", text=self.t("項目", "Item"))
        self.summary.heading("value", text=self.t("内容", "Value"))
        self.summary.column("item", width=220, anchor="w")
        self.summary.column("value", width=700, anchor="w")
        self.summary.pack(fill="x")
        ttk.Label(summary_box, text=self.t("変換手順", "Operations")).pack(anchor="w", pady=(10, 4))
        self.operations = tk.Listbox(summary_box, height=7)
        self.operations.pack(fill="both", expand=True)

        actions = ttk.LabelFrame(outer, text=self.t("確認と実行", "Preview and Run"), padding=10)
        actions.pack(fill="x", pady=(0, 10))
        self.preview_btn = ttk.Button(actions, text=self.t("Preview / Dry Run", "Preview / Dry Run"), command=self._preview)
        self.preview_btn.pack(side="left")
        self.run_btn = ttk.Button(actions, text=self.t("変換実行", "Run Pipeline"), command=self._run)
        self.run_btn.pack(side="left", padx=6)
        ttk.Label(
            actions,
            text=self.t(
                "既定Formula policyは reject。表計算ソフトで式として評価され得る値を検出すると出力を止めます。",
                "Default formula policy is reject. Output stops when values could be evaluated as spreadsheet formulas.",
            ),
            wraplength=560,
        ).pack(side="right")

        logbox = ttk.LabelFrame(outer, text=self.t("結果", "Result"), padding=8)
        logbox.pack(fill="both", expand=True)
        self.log = tk.Text(logbox, wrap="word", height=11, state="disabled", font=("Consolas", 9))
        self.log.pack(fill="both", expand=True)
        ttk.Label(outer, textvariable=self.status).pack(fill="x", pady=(8, 0))

    def _language_changed(self, _event=None) -> None:
        self.lang = "en" if self.language_var.get() == "English" else "ja"
        save_language(APP_ID, self.lang)
        self._build()
        if self.config is not None:
            try:
                self._render(Pipeline(self.config, dry_run=True))
            except Exception:
                pass
        self.status.set(self.t("準備完了", "Ready"))

    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            title=self.t("Pipeline JSONを選択", "Choose Pipeline JSON"),
            filetypes=[("JSON", "*.json"), (self.t("すべてのファイル", "All files"), "*.*")],
        )
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
            self.status.set(self.t("設定OK", "Configuration valid"))
            return True
        except Exception as exc:
            self.config = None
            self.status.set(self.t(f"設定エラー: {type(exc).__name__}", f"Configuration error: {type(exc).__name__}"))
            if show_error:
                messagebox.showerror(self.t("設定エラー", "Configuration error"), str(exc), parent=self.root)
            return False

    def _render(self, pipeline: Pipeline) -> None:
        for item in self.summary.get_children():
            self.summary.delete(item)
        rows = [
            (self.t("入力CSV", "Input CSV"), str(pipeline.input_path)),
            (self.t("出力CSV", "Output CSV"), str(pipeline.output_path)),
            ("Encoding", pipeline.encoding),
            (self.t("上書き", "Overwrite"), str(pipeline.overwrite)),
            ("Formula policy", pipeline.formula_policy),
            (self.t("ルート", "Root"), str(pipeline.root)),
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
        self.status.set(self.t("確認中…", "Previewing…") if dry_run else self.t("変換中…", "Running…"))

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
        if not messagebox.askyesno(
            self.t("変換実行", "Run Pipeline"),
            self.t(
                "実際に出力ファイルを書き込みます。Previewで内容を確認済みの場合だけ続行してください。",
                "This will write the output file. Continue only after reviewing Preview results.",
            ),
            parent=self.root,
        ):
            return
        self._execute(False)

    def _finish(self, ok: bool, text: str, dry_run: bool) -> None:
        self._append(text)
        self.preview_btn.configure(state="normal")
        self.run_btn.configure(state="normal")
        if ok:
            self.status.set(self.t("確認完了", "Preview complete") if dry_run else self.t("変換完了", "Pipeline complete"))
        else:
            self.status.set(self.t("失敗", "Failed"))
            messagebox.showerror(self.t("データ変換", "Data Pipeline"), text[-1500:], parent=self.root)


def main() -> None:
    root = tk.Tk()
    DataPipelineDesktop(root)
    root.mainloop()


if __name__ == "__main__":
    main()
