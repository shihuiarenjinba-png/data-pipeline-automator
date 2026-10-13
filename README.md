# Data Pipeline Automator

CSV等のデータを、決められた変換ルールに従ってローカル処理する小型パイプラインです。AI判断は使いません。

## MVP

- CSV入力 / CSV出力
- 列選択
- 列名変更
- 完全空行の削除
- 重複行削除
- 指定列でソート
- Dry Run
- `root_dir` 配下だけを読み書き
- 一時ファイル経由の安全な出力

## 実行

```powershell
python data_pipeline.py pipeline.example.json --dry-run
python data_pipeline.py pipeline.example.json
```

Excel対応は後から `openpyxl` Adapterとして分離して追加する予定です。Coreは標準ライブラリだけで動かします。


## 拡張: Local Data Porter（CSV ⇄ JSONL）

既存のルールベースCSVパイプライン `data_pipeline.py` は維持したまま、別エントリーポイントとして安全なデータ移行機能を追加しました。

- Windows GUI: `python data_porter_gui.py`
- CLI例: `python data_porter.py --root C:\\Workspace --input data.csv --output archive.jsonl --dry-run`
- 実変換: 上記から `--dry-run` を外す
- 逆変換: `python data_porter.py --root C:\\Workspace --input archive.jsonl --output restored.csv`
- UTF-8 CSVとJSONLの相互変換（すべて**文字列**として処理、先頭ゼロ保持）
- JSONLは行ごとに共通キーを持つ平坦なオブジェクトのみを許可し、曖昧なデータは拒否
- JSONL→CSVでは、表計算ソフトによる数式実行を防ぐため危険な先頭文字にアポストロフィを追加（値が変化した件数をレポートで表示）
- ファイルは `--root` 配下に限定、既存の出力先は上書きしない
- バックグラウンド処理GUI、最大150MiB/250,000行の試作制限
- テスト: `python -m unittest discover -s tests -p "test_data_porter.py" -v`

**注意**: この移行ツールは元サービスの関係性、添付ファイル、日時型、階層型JSONを自動で復元しません。CSV⇄JSONLの安全な変換に限定したMVPです。

Windows検証ビルド: `powershell -ExecutionPolicy Bypass -File .\\build-windows-validation.ps1`。
`.github/workflows/windows-validation.yml` からも手動テスト可能。
実機動作、署名、AV、販売審査は未完了。生成物は**未署名・販売不可の検証版**。
