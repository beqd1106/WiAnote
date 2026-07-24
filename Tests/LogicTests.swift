import XCTest
@testable import WiAnote

/// 純粋ロジックのユニットテスト（永続化やバンドルに依存しない部分を検証）。
final class LogicTests: XCTestCase {

    // MARK: - 間隔反復

    func testSpacedRepetitionAdvancesOnCorrect() {
        let r = SpacedRepetition.next(currentLevel: 0, correct: true)
        XCTAssertEqual(r.level, 1)               // 段階が進む
    }

    func testSpacedRepetitionResetsOnWrong() {
        let r = SpacedRepetition.next(currentLevel: 3, correct: false)
        XCTAssertEqual(r.level, 0)               // 間違えたら段階0へ
        let days = SpacedRepetition.interval(forLevel: 0)
        XCTAssertEqual(days, 1)                   // 翌日再出題
    }

    func testSpacedRepetitionIntervalsAreIncreasing() {
        let intervals = (0..<SpacedRepetition.intervals.count).map { SpacedRepetition.interval(forLevel: $0) }
        for i in 1..<intervals.count {
            XCTAssertGreaterThan(intervals[i], intervals[i-1], "間隔は段階とともに広がるべき")
        }
    }

    func testSpacedRepetitionLevelCapped() {
        let r = SpacedRepetition.next(currentLevel: 99, correct: true)
        XCTAssertEqual(r.level, SpacedRepetition.intervals.count - 1)
    }

    // MARK: - 合格可能性スコア

    func testPassProbabilityZeroWhenNoStudy() {
        let input = PassProbability.Inputs(
            correctRateByDomain: [:], latestMockScaledScore: nil,
            reviewCompletionRate: 1.0, studyStreak: 0, totalAnswered: 0)
        XCTAssertEqual(PassProbability.score(input), 0)
    }

    func testPassProbabilityCappedForFewAnswers() {
        // 全分野満点でも学習量が少なければ上限で抑えられる
        let perfect = Dictionary(uniqueKeysWithValues: ExamDomain.allCases.map { ($0, 1.0) })
        let input = PassProbability.Inputs(
            correctRateByDomain: perfect, latestMockScaledScore: 1000,
            reviewCompletionRate: 1.0, studyStreak: 20, totalAnswered: 10)
        XCTAssertLessThanOrEqual(PassProbability.score(input), 35)
    }

    func testPassProbabilityHighWhenWellPrepared() {
        let good = Dictionary(uniqueKeysWithValues: ExamDomain.allCases.map { ($0, 0.85) })
        let input = PassProbability.Inputs(
            correctRateByDomain: good, latestMockScaledScore: 820,
            reviewCompletionRate: 1.0, studyStreak: 14, totalAnswered: 120)
        XCTAssertGreaterThanOrEqual(PassProbability.score(input), 70)
    }

    // MARK: - 配点の整合性

    func testDomainWeightsSumToOne() {
        let sum = ExamDomain.allCases.reduce(0.0) { $0 + $1.weight }
        XCTAssertEqual(sum, 1.0, accuracy: 0.001, "公式配点の合計は100%になるべき")
    }

    // MARK: - 学習プラン

    func testRoadmapMatchesPlanDuration() {
        for plan in StudyPlanType.allCases {
            let roadmap = PlanFactory.roadmap(for: plan)
            XCTAssertEqual(roadmap.count, plan.durationWeeks)
            XCTAssertEqual(roadmap.first?.week, 1)
            XCTAssertEqual(roadmap.last?.week, plan.durationWeeks)
        }
    }

    func testCurrentWeekClampsWithinPlan() {
        let start = Calendar.current.date(byAdding: .day, value: -200, to: .now)!
        let week = PlanFactory.currentWeek(startedAt: start, plan: .standard8)
        XCTAssertLessThanOrEqual(week, 8)
        XCTAssertGreaterThanOrEqual(week, 1)
    }
}
