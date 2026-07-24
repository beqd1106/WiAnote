import SwiftUI

/// RPA技術者検定 アソシエイト（WinActor Ver.7）の3つの試験分野。
/// 出題数は公式試験情報に準拠：
///   WinActorの概要 10問 / WinActorの機能に関する知識 20問 / WinActorのシナリオに関する知識 20問
///   （全50問・60分・合格基準は原則正答率7割以上）
/// ※出題範囲・比率は変更されることがあるため、最新情報は必ず公式サイトで確認すること。
enum ExamDomain: String, CaseIterable, Codable, Identifiable {
    case overview
    case features
    case scenario

    var id: String { rawValue }

    /// 公式の出題比率（合格可能性スコアや模試の出題配分に使用）
    /// 概要10/50=0.20・機能20/50=0.40・シナリオ20/50=0.40
    var weight: Double {
        switch self {
        case .overview: return 0.20
        case .features: return 0.40
        case .scenario: return 0.40
        }
    }

    var title: String {
        switch self {
        case .overview: return "WinActorの概要"
        case .features: return "WinActorの機能"
        case .scenario: return "WinActorのシナリオ"
        }
    }

    var shortTitle: String {
        switch self {
        case .overview: return "概要"
        case .features: return "機能"
        case .scenario: return "シナリオ"
        }
    }

    /// 配点を百分率の整数で（UI表示用）
    var weightPercent: Int { Int((weight * 100).rounded()) }

    var color: Color {
        switch self {
        case .overview: return Theme.blue
        case .features: return Theme.navy
        case .scenario: return Theme.orange
        }
    }

    var systemIcon: String {
        switch self {
        case .overview: return "info.circle.fill"
        case .features: return "square.grid.2x2.fill"
        case .scenario: return "arrow.triangle.branch"
        }
    }
}
