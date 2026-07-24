# AWS合格ナビ（AWS Certified Cloud Practitioner 学習アプリ・MVP）

完全初心者が AWS Certified Cloud Practitioner（CLF-C02）合格を目指すための iPhone 学習アプリ。
SwiftUI + SwiftData（ローカル完結・オフライン動作）。XcodeGen + GitHub Actions でビルド確認（Macなし開発フロー）。

## 特徴
- 初回診断 → 学習プラン（4/6/8/12週）自動提案 → 今日のタスク提示
- レッスン（図解・例え話）／用語カード（一言＋使いどころ＋試験ポイント）
- 4択・複数選択の問題演習（即時解説＋不正解選択肢の理由）
- 忘却曲線ベースの自動復習（1→3→7→14→30日）
- 苦手分野の可視化・合格可能性スコア（目安）
- 模擬試験（公式配点比率で出題）→分野別スコア
- 試験直前モード（頻出総まとめ＋チェックリスト）・学習カレンダー・連続日数・バッジ

## 試験範囲（公式・CLF-C02／配点）
- クラウドの概念 24% / セキュリティとコンプライアンス 30% / クラウドテクノロジーとサービス 34% / 請求・料金・サポート 12%
- 65問・90分・合格700/1000。※範囲・配点は変更され得るため最新情報は必ずAWS公式で確認。

## 著作権
問題・解説・用語はすべてオリジナル。AWS公式問題・市販教材の転載なし。非公式の学習支援アプリ。

## 構成
```
App/          アプリ入口・SwiftDataコンテナ・Assets
Models/       ExamDomain / Codableコンテンツ / SwiftData永続化モデル
Logic/        ContentRepository / 間隔反復 / 合格可能性 / プラン生成 / StudyStore
DesignSystem/ Theme（白・ネイビー・ブルー・オレンジ）/ 共通UI部品
Views/        オンボーディング・ホーム・学ぶ・演習・分析・設定 ほか
Resources/    questions/terms/lessons/services.json（学習コンテンツ）
Tests/        純粋ロジックのユニットテスト
```

## ビルド
```bash
xcodegen generate
open AWSGoukakuNavi.xcodeproj
```
push すると GitHub Actions が署名なしビルド＋ユニットテストを実行します。

## 将来拡張
- AI学習サポート（バックエンド経由・回数/月額上限/キャッシュ前提）
- Solutions Architect / Developer / SysOps Associate への資格拡張（ExamDomain/コンテンツ差し替えで対応可能な構造）
- CloudKit/Supabase 同期
