"""Offline CSV<->JSONL migration GUI. Existing pipeline GUI remains unchanged."""
from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from data_porter import convert
from porter_ui_helpers import suggested_output
from ui_preferences import load_preferences, save_preferences


class PorterGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("CSV / JSONL ローカル移行ツール")
        self.geometry("810x450")
        self.rootdir = tk.StringVar()
        self._preferences_warning = ""
        try:
            self.rootdir.set(load_preferences("LocalDataPorter", ("rootdir",)).get("rootdir", ""))
        except (OSError, ValueError) as exc:
            self._preferences_warning = str(exc)
        self.source = tk.StringVar()
        self.destination = tk.StringVar()
        self.status = tk.StringVar(value="フォルダとファイルを選択してください。元データは上書きしません。")
        self.messages = queue.Queue()
        self.running = False
        self._cancel_event: threading.Event | None = None
        body = ttk.Frame(self, padding=20)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        ttk.Label(body, text="ローカルデータ移行（CSV ⇄ JSONL）",
                  font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 18))
        self._line(body, 1, "作業フォルダ", self.rootdir, lambda: filedialog.askdirectory())
        self._line(body, 2, "入力ファイル", self.source, self._pick_source)
        self._line(body, 3, "出力先", self.destination,
                   lambda: filedialog.asksaveasfilename(filetypes=[("CSV / JSON Lines", "*.csv *.jsonl")]))
        ttk.Label(body, text="入力ファイルを選ぶと作業フォルダー・未使用の保存先を自動提案します。\nCSV→JSONLは文字列を保持。JSONL→CSVでは数式実行を避けるため一部の値を変更します。",
                  wraplength=755).grid(row=4, column=0, columnspan=3, sticky="w", pady=(12, 8))
        self.preview = tk.Text(body, width=80, height=5, wrap="word", state="disabled")
        self.preview.grid(row=5, column=0, columnspan=3, sticky="nsew", pady=8)
        row = ttk.Frame(body)
        row.grid(row=6, column=0, columnspan=3, sticky="w", pady=6)
        ttk.Button(row, text="事前確認", command=lambda: self.submit(True)).pack(side="left", padx=(0, 8))
        self.run_button = ttk.Button(row, text="変換する", command=lambda: self.submit(False))
        self.run_button.pack(side="left")
        self.cancel_button = ttk.Button(row, text="中止", command=self.cancel, state="disabled")
        self.cancel_button.pack(side="left", padx=(8, 0))
        ttk.Button(row, text="作業フォルダ設定を保存", command=self.save_user_preferences).pack(side="left", padx=(8, 0))
        self.progress = ttk.Progressbar(body, mode="indeterminate")
        self.progress.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(5, 2))
        ttk.Label(body, textvariable=self.status, wraplength=770).grid(
            row=8, column=0, columnspan=3, sticky="w", pady=10)
        if self._preferences_warning:
            self.status.set("保存設定を読み込めませんでした（元データは変更しません）: " + self._preferences_warning)
        self.after(120, self.poll)

    def _pick_source(self) -> str:
        selected = filedialog.askopenfilename(
            title="CSV / JSONLの入力ファイルを選択",
            filetypes=[("CSV / JSON Lines", "*.csv *.jsonl")],
        )
        if not selected:
            return ""
        source = Path(selected).expanduser().resolve()
        # New users can simply choose one file; its directory becomes the
        # permitted workspace unless an existing saved workspace contains it.
        previous = self.rootdir.get().strip()
        if not previous or not source.is_relative_to(Path(previous).expanduser().resolve()):
            self.rootdir.set(str(source.parent))
        try:
            destination = suggested_output(source)
            self.destination.set(str(destination))
            self.status.set(
                f"入力選択済み: {source.name} → {destination.name}（未保存）"
                "。必要なら保存先を変更し、まず「事前確認」を押してください。"
            )
        except ValueError as exc:
            self.destination.set("")
            self.status.set(str(exc))
        return str(source)

    def save_user_preferences(self) -> None:
        try:
            save_preferences("LocalDataPorter", {"rootdir": self.rootdir.get()}, ("rootdir",))
            self.status.set("作業フォルダ設定をローカルに保存しました。")
        except (OSError, ValueError) as exc:
            self.status.set(f"設定保存エラー: {exc}")
            messagebox.showerror("設定保存失敗", str(exc))

    def _line(self, parent, row, label, variable, choose):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=5)
        def pick():
            new = choose()
            if new:
                variable.set(new)
        ttk.Button(parent, text="参照", command=pick).grid(row=row, column=2, padx=6)

    def submit(self, dry_run: bool) -> None:
        if self.running:
            return
        try:
            root = Path(self.rootdir.get()).expanduser().resolve(strict=True)
            source = Path(self.source.get()).expanduser().resolve(strict=True).relative_to(root)
            destination = Path(self.destination.get()).expanduser().resolve().relative_to(root)
        except (OSError, ValueError) as exc:
            messagebox.showerror("入力エラー", f"入出力は指定の作業フォルダ内にしてください。\n{exc}")
            return
        self.running = True
        self._cancel_event = threading.Event()
        self.run_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.progress.start(15)
        self.status.set("検証中...中止できます。" if dry_run else "変換中...中止できます。")
        def worker():
            try:
                result = convert(root, str(source), str(destination), dry_run=dry_run,
                                 cancel_event=self._cancel_event)
                self.messages.put((True, result))
            except InterruptedError as exc:
                self.messages.put((None, str(exc)))
            except Exception as exc:
                self.messages.put((False, str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def cancel(self) -> None:
        if self.running and self._cancel_event is not None:
            self._cancel_event.set()
            self.cancel_button.configure(state="disabled")
            self.status.set("中止要求を受け付けました。安全に停止しています...")

    def poll(self) -> None:
        try:
            while True:
                ok, value = self.messages.get_nowait()
                self.running = False
                self._cancel_event = None
                self.run_button.configure(state="normal")
                self.cancel_button.configure(state="disabled")
                self.progress.stop()
                if ok is None:
                    self.status.set(str(value))
                elif ok:
                    rendered = json.dumps(value, ensure_ascii=False, indent=2)
                    self.preview.configure(state="normal")
                    self.preview.delete("1.0", "end")
                    self.preview.insert("1.0", rendered)
                    self.preview.configure(state="disabled")
                    self.status.set("事前確認または変換が完了しました。")
                else:
                    self.status.set(f"エラー: {value}")
                    messagebox.showerror("変換エラー", value)
        except queue.Empty:
            pass
        self.after(120, self.poll)



def _validation_smoke() -> None:
    """Noninteractive Tk widget construction smoke; not user-click testing."""
    import json
    import sys
    from pathlib import Path
    if len(sys.argv) != 4 or sys.argv[1] != "--smoke-test" or sys.argv[2] != "--smoke-output":
        raise SystemExit(2)
    app = PorterGUI()
    try:
        app.update_idletasks()
        app.update()
        assert app.winfo_exists() and app.title() and len(app.winfo_children()) > 0
        result = {"status": "GUI_PROCESS_SMOKE_OK", "title": app.title(),
                  "scope": "Tk initialization and event pump only; no simulated clicks"}
        with Path(sys.argv[3]).open("x", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False)
    finally:
        app.destroy()


if __name__ == "__main__":
    import sys
    if "--smoke-test" in sys.argv:
        _validation_smoke()
    elif "--e2e-test" in sys.argv:
        from gui_e2e_harness import run
        run(PorterGUI)
    elif "--preferences-ci" in sys.argv:
        from preferences_ci import run
        run(PorterGUI, "LocalDataPorter", {"rootdir": "C:\\QA\\日本語プロジェクト\\001"})
    else:
        PorterGUI().mainloop()
