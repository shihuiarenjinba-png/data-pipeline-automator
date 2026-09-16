# Data Pipeline Automator — 使い方

## 言語

画面右上の **`言語 / Language`** から `日本語` / `English` を選べます。選択内容は次回起動でも引き継がれます。

## 基本操作

1. Pipeline JSONを選ぶ。
2. `検証` で入力・出力・変換手順・Formula policyを確認する。
3. `Preview / Dry Run` で実ファイルを書き込まず結果を確認する。
4. 問題がなければ `変換実行` を押す。

## 安全設計

- 既定の `spreadsheet_formula_policy` は `reject`。
- CSV/XLSXをExcel等で開いた時に式として評価され得る値を検出すると、既定では出力を止めます。
- 重複/空ヘッダーや曖昧な列指定は拒否します。
- 出力は一時ファイルへ書いてから原子的に確定します。
- 元ファイルを上書きする場合は設定で明示する必要があります。

販売前は `SALES_RELEASE_CHECKLIST.md` の未チェック項目を実機で完了してください。
