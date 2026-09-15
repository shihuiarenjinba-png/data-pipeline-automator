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
