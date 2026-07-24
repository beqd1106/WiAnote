import Foundation

/// 忘却曲線を意識した間隔反復のロジック（純粋関数中心でテストしやすい）。
/// 間違えた問題は翌日、以降は正解するたびに 1日→3日→7日→14日→30日 と間隔を広げる。
/// 不正解なら段階を0に戻し、翌日に再出題する。
enum SpacedRepetition {

    /// reviewLevel に対応する次回までの日数
    static let intervals: [Int] = [1, 3, 7, 14, 30]

    static func interval(forLevel level: Int) -> Int {
        let idx = min(max(level, 0), intervals.count - 1)
        return intervals[idx]
    }

    /// 回答結果から次の復習状態を計算する。
    /// - Parameters:
    ///   - currentLevel: 現在の復習段階
    ///   - correct: 今回正解したか
    ///   - now: 基準日時（テスト用に注入可能）
    /// - Returns: (次の段階, 次回復習日)
    static func next(currentLevel: Int, correct: Bool, now: Date = .now)
        -> (level: Int, nextDate: Date) {
        let newLevel: Int
        if correct {
            newLevel = min(currentLevel + 1, intervals.count - 1)
        } else {
            newLevel = 0
        }
        let days = interval(forLevel: newLevel)
        let next = Calendar.current.date(byAdding: .day, value: days,
                                         to: Calendar.current.startOfDay(for: now)) ?? now
        return (newLevel, next)
    }
}
