import Foundation

/// 8週間標準カリキュラムをベースに、選択プランの週数へスケールして
/// 週ごとの学習テーマ（ロードマップ）を生成する。
struct WeekGoal: Identifiable, Hashable {
    let id = UUID()
    let week: Int
    let title: String
    let detail: String
    let domains: [ExamDomain]
}

enum PlanFactory {

    /// 完全初心者向け 8週間の標準ロードマップ（公式範囲に沿う）
    private static let baseEightWeeks: [WeekGoal] = [
        .init(week: 1, title: "RPAとWinActorの基礎", detail: "RPAとは何か／WinActorの特徴・エディション・動作環境", domains: [.overview]),
        .init(week: 2, title: "画面と基本操作", detail: "メイン画面・フローチャート・アクションライブラリ・記録モード", domains: [.overview, .features]),
        .init(week: 3, title: "主要ノードと機能", detail: "分岐・繰り返し・変数・待機など中心ノードの役割", domains: [.features]),
        .init(week: 4, title: "アプリ連携とライブラリ", detail: "IEモード・エクセル・ライブラリ・ウィンドウ識別", domains: [.features]),
        .init(week: 5, title: "シナリオ作成の基本", detail: "シナリオ設計・データ一覧・変数一覧・実行と停止", domains: [.scenario]),
        .init(week: 6, title: "シナリオの応用とデバッグ", detail: "例外処理・デバッグ・修正・保守しやすい作り方", domains: [.scenario]),
        .init(week: 7, title: "分野別の問題演習", detail: "3分野を横断して演習し、苦手を洗い出す", domains: ExamDomain.allCases),
        .init(week: 8, title: "模試と試験直前対策", detail: "模試→間違い集中復習／頻出用語・ノードの総仕上げ", domains: ExamDomain.allCases),
    ]

    /// プラン週数に合わせてロードマップを生成する。
    /// 8週以外は週数に応じて圧縮/伸長する（テーマの順序は保つ）。
    static func roadmap(for plan: StudyPlanType) -> [WeekGoal] {
        let weeks = plan.durationWeeks
        if weeks == 8 { return baseEightWeeks }

        var result: [WeekGoal] = []
        for w in 1...weeks {
            // 8週カリキュラム上の対応位置を比例で求める
            let srcIndex = min(baseEightWeeks.count - 1,
                               Int((Double(w - 1) / Double(weeks - 1)) * Double(baseEightWeeks.count - 1)))
            let base = baseEightWeeks[srcIndex]
            result.append(.init(week: w, title: base.title, detail: base.detail, domains: base.domains))
        }
        return result
    }

    /// 現在の経過日数から「今が何週目か」を返す（1始まり）。
    static func currentWeek(startedAt: Date, plan: StudyPlanType, now: Date = .now) -> Int {
        let days = Calendar.current.dateComponents([.day],
            from: Calendar.current.startOfDay(for: startedAt),
            to: Calendar.current.startOfDay(for: now)).day ?? 0
        let week = days / 7 + 1
        return min(max(week, 1), plan.durationWeeks)
    }
}
