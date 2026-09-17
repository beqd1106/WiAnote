# WiAnote（RPA技術者検定 アソシエイト 学習アプリ）

WinActor の「RPA技術者検定 アソシエイト」合格を目指すための iPhone 学習アプリ。
SwiftUI + SwiftData（ローカル完結・オフライン動作）。XcodeGen + GitHub Actions でビルド／配信（Macなし開発フロー）。

## 特徴
- 初回診断 → 学習プラン（4/6/8/12週）自動提案 → 今日のタスク提示
- レッスン14本（確認問題10問＋腕試し5問＋ランダム演習プール）
- 4択の問題演習（即時解説＋不正解選択肢それぞれの理由＋出典ページ）
- 忘却曲線ベースの自動復習
- 苦手分野の可視化・合格可能性スコア（目安）
- 模擬試験（公式配点比率で出題）→分野別スコア
- 試験直前モード・学習カレンダー・連続日数・バッジ

## 出題範囲（公式）
- WinActorの概要 10問 / WinActorの機能に関する知識 20問 / WinActorのシナリオに関する知識 20問
- 全50問・60分・合格は原則正答率7割・対象は Ver.7
- ※範囲・配点は変更され得るため、最新情報は必ず[公式サイト](https://winactor.com/rpa-kentei/associate/)で確認。

## 問題データ
検定の出題範囲である **WinActor Ver.7.6 操作マニュアル（965ページ）** を一次ソースとして作成した
**929問**（概要220／機能424／シナリオ285・218テーマ）。

- 全問にマニュアルの根拠ページを付与（例：`操作マニュアル p.28 (1.7.2 記録モードの種類)`）
- 解説は「結論＋具体的な設定値や既定値＋紛らわしい隣接機能との区別」の3点構成
- 正解位置は①②③④を各25%に均等化（並び順で当てられないように）

問題・解説・用語はすべてオリジナル。公式問題・市販教材の転載なし。非公式の学習支援アプリ。

## 構成
```
App/          アプリ入口・SwiftDataコンテナ・Assets
Models/       ExamDomain / Codableコンテンツ / SwiftData永続化モデル
Logic/        ContentRepository / 間隔反復 / 合格可能性 / プラン生成 / StudyStore
DesignSystem/ Theme（白・ネイビー・ブルー・オレンジ）/ 共通UI部品
Views/        オンボーディング・ホーム・学ぶ・演習・分析・設定 ほか
Resources/    questions/terms/lessons/services/glossary.json（学習コンテンツ）
Tests/        純粋ロジックのユニットテスト
design/       コンテンツ生成・検証スクリプト（アプリには含まれない）
```

## ビルド
```bash
xcodegen generate
open WiAnote.xcodeproj
```
push すると GitHub Actions が署名なしビルド＋ユニットテストを実行します。
TestFlight 配信は `release.yml` を workflow_dispatch で実行。

## コンテンツの更新
```bash
# 問題バンクを差し替え、レッスン14本の問題割り当てを張り替える
python design/remap_lessons.py <新しいquestions.json>

# Swiftのモデル定義どおりにデコードできるか検証（Macが無くても確認できる）
python design/validate_resources.py
```
問題バンク本体の生成は Web版（`Downloads\WinActor教材\quiz\`）と共有。

## 将来拡張
- 他のRPA資格への展開（ExamDomain／コンテンツ差し替えで対応可能な構造）
- CloudKit 同期
