# Local Data Porter — Microsoft Store商品ページ原稿（準備段階）

**状態：Partner Center商品枠・正式Identity確認済み（2026-10-18ユーザー提供画面）。MSIX未生成・アップロード未確認・認証提出禁止・販売HOLD。**

## 正式Store商品名（作成済み）
Local Data Porter

## 短い説明（原稿）
ローカルのCSVとJSON Linesを相互変換し、移行前に内容を確認

## 想定購入者
CSVエクスポートの変換・移行を担当する事務・IT担当者

## 具体的な活用例
取引先から受け取ったCSVを文字列型を維持してJSONLへ移行する。

## 主な機能（実機確認後に掲載可否を判断）
- CSV⇄JSONLの相互変換
- IDの先頭ゼロを文字列として扱う
- 実行前のプレビューと安全な別出力
- CSV数式対策による値の変更件数を表示

## 制約・注意
すべての値を文字列として扱い、階層JSON、型の完全保持、添付ファイル、元サービスとの完全互換は対象外です。CSV数式安全対策によって出力文字列が変化する場合があります。

## 未入力・確認待ち
- 正式Store Product Identity / Package Family Name：登録済み。`store/partner_center_registration.json`を参照。
- 製品名のStore可用性・商標・カテゴリ：未確定
- 価格：未確定。Document Version Auditの既存980円下書きは変更しない。
- 配布地域と言語：所有者判断待ち
- サポートURL、プライバシーポリシーURL：製品に適合する公開ページを確認後入力
- MSIX：パッケージ候補生成/静的チェック/Store Draftアップロード未完了
- スクリーンショット・ロゴ：製品別の承認/実画面撮影待ち
- 公開認証：実機・ライセンス・品質ゲートを終えるまで行わない

## 操作順序（Partner Center）
1. 既存の商品枠を再利用する。正式Store IDは `store/partner_center_registration.json` を参照し、重複作成しない。
2. この製品は既に名前予約・商品枠作成済み。再予約は不要。
3. Product identityをスクリーンショットと登録JSONで突合済み。PublisherとPFNをビルド時に再照合する。
4. 画像の権利と4サイズのロゴを承認して `store/assets/` に配置。
5. Windows上で `store/build-msix.ps1` でパッケージ候補を生成し、`store/verify-upload-inputs.py --msix <実際のファイル>` を実行。
6. Product release → Start submissionで下書き開始。Packagesに指定MSIXをアップロードし、保存。
7. **Submit for certificationは押さない。** 最終実機試験と所有者承認後に判断する。

公式：https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/create-app-submission
公式：https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/upload-app-packages

> この原稿は正確性と非誇張を優先した内部ドラフトであり、実機確認前に機能全体の保証をしない。

## 2026-10-18 商品枠照合結果
- 画面提供による正式Store Identityの確認済み。元コードのEXE名・appIdとPackage/Identity/Nameは**別フィールド**。
- Microsoft Storeの登録表示名とMSIXマニフェスト表示名は `store/product.json` から取得する。
- 画像・スクリーンショット・価格・ライセンス・MSIX実ファイルは別途準備。Storeにアップロード/公開したとは扱わない。
