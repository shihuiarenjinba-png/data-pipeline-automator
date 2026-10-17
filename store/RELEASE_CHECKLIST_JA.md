# Local Data Porter — Windows有料MSIX検証

このリポジトリの原本・main・既存Windows検証成果物は変更しない。作業対象は独立ブランチ feature/store-local-data-porter-msix-20261017 のみ。

## 実装を確認した用途

CSV→JSONL、JSONL→CSVのローカル文字列保持型移行。先頭ゼロ保持、曖昧なJSONL構造の拒否、元ファイル非上書き、CSV formula injectionの緩和、初期GUIあり。移行エラーの回避と監査可能な変換レポートを主な有料価値とする。

## vNext Store包装

- GUI入口は data_porter_gui.py。store/product.json の entryPoint に固定する。
- store/make-logo-candidates.ps1 は4サイズの候補PNGを作成。既存画像の上書きはしない。
- store/build-msix.ps1 はWindows x64、正式Identity/Publisher、4項目版番号、ロゴ4種の承認、Python回帰テストの合格を要求する。
- PyInstaller→Windows SDK MakeAppxで未署名のMSIX候補を新規フォルダにのみ作成する。

Windowsコード担当の手順：

~~~powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install pyinstaller==6.16.0
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test*.py" -v
powershell -NoProfile -ExecutionPolicy Bypass -File .\store\make-logo-candidates.ps1
~~~

正式なIdentityとロゴの承認がない間はMSIXを生成しない。Partner Centerの正式Name/Publisherを環境変数へ設定し、STORE_VERSION、STORE_IDENTITY_CONFIRMED=YES、STORE_BRAND_APPROVED=YES が揃ってから：

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\store\build-msix.ps1 -PreflightOnly
powershell -NoProfile -ExecutionPolicy Bypass -File .\store\build-msix.ps1
~~~

## 未完了の受入

Windows実機のGUI/大型150MiB付近/不正JSONL/文字コード/空欄/出力衝突/再起動後の結果、MSIX内部manifest、WACK、署名済MSIXのインストール・更新・削除、Store画像・価格・ライセンス・プライバシー表示。

**判定：MSIX構築経路追加済み／Windows全回帰・署名・実機販売QA未実施／有料販売HOLD。**
