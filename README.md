# Data Pipeline Automator

CSV等のデータを、決められた変換ルールに従ってローカル処理する小型パイプラインです。AI判断は使いません。

## Windows Desktop / デスクトップ

通常利用では `desktop_app.py` / 将来のWindows EXEを使えます。

画面では以下を事前確認できます。
- 入力CSV / 出力CSV
- Encoding
- overwrite
- Spreadsheet formula policy
- `root_dir`
- 変換Operationの順序
- Preview / Dry Run結果

実ファイルへ書き込む **Run Pipeline** は確認ダイアログを通してから実行します。

```powershell
python desktop_app.py
# または
run_desktop.bat
```

## Core MVP

- CSV入力 / CSV出力
- 列選択
- 列名変更
- 完全空行の削除
- 重複行削除
- 指定列でソート
- Dry Run
- `root_dir` 配下だけを読み書き
- 一時ファイル + `fsync` + `os.replace` による安全な出力
- 重複/空ヘッダー拒否
- Spreadsheet formula injection対策

## Spreadsheet formula policy

CSVをExcel等で開いた際に、`=`, `@`, 危険な `+`/`-` から始まる文字列が数式として解釈される事故を避けるため、既定は安全側の `reject` です。

```json
"spreadsheet_formula_policy": "reject"
```

選択肢:
- `reject` — 危険なセルを検出したら出力せず停止（既定）
- `escape` — 先頭に `'` を付けてテキストとして出力
- `preserve` — 入力値をそのまま出力。信頼できるデータだけで明示的に使用

符号付きの通常数値（例 `-12.5`）は数式扱いしません。

## CLI / 開発者向け

```powershell
python data_pipeline.py pipeline.example.json --dry-run
python data_pipeline.py pipeline.example.json
python -m unittest discover -s tests -v
```

Excel対応は後から `openpyxl` Adapterとして分離して追加する予定です。Coreは標準ライブラリだけで動かし、GUIも同じCoreを呼びます。
