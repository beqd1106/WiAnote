import XCTest
import SwiftData
@testable import WiAnote

/// 純粋ロジックのユニットテスト（永続化やバンドルに依存しない部分を検証）。
final class LogicTests: XCTestCase {

    // MARK: - 間隔反復

    func testSpacedRepetitionAdvancesOnCorrect() {
        let r = SpacedRepetition.next(currentLevel: 0, correct: true)
        XCTAssertEqual(r.level, 1)               // 段階が進む
    }

    func testSpacedRepetitionResetsOnWrong() {
        let now = Date()
        let r = SpacedRepetition.next(currentLevel: 3, correct: false, now: now)
        XCTAssertEqual(r.level, 0)               // 間違えたら段階0へ
        XCTAssertEqual(r.nextDate, now)          // その場で復習対象になる
    }

    /// 間違えた問題はその日のうちに復習リストへ出てくる（翌日まで待たされない）
    func testWrongAnswerBecomesDueImmediately() {
        let now = Date()
        let r = SpacedRepetition.next(currentLevel: 0, correct: false, now: now)
        let item = ReviewItem(questionId: "q1", nextReviewDate: r.nextDate,
                              reviewLevel: r.level, lastResultCorrect: false)
        XCTAssertTrue(item.isDue, "間違えた問題はすぐ復習できる状態であるべき")
    }

    /// ヒントを使って正解した場合は段階を進めない（自力で解けたわけではないため）
    func testHintedCorrectKeepsLevel() {
        let plain = SpacedRepetition.next(currentLevel: 2, correct: true)
        XCTAssertEqual(plain.level, 3)

        let hinted = SpacedRepetition.next(currentLevel: 2, correct: true, usedHint: true)
        XCTAssertEqual(hinted.level, 2, "ヒントつきの正解では段階を据え置く")
    }

    // MARK: - ヒント

    private func makeQuestion(id: String = "q-hint",
                              choices: [String] = ["選択肢A", "選択肢B", "選択肢C", "選択肢D"],
                              correct: [Int] = [0],
                              beginnerNote: String? = nil,
                              service: String = "シナリオ作成") -> QuizQuestion {
        QuizQuestion(id: id, question: "WinActorのシナリオについて正しいものはどれか。",
                     choices: choices, correctAnswers: correct,
                     explanation: "解説", wrongChoiceExplanations: [:],
                     domain: .scenario, service: service, difficulty: 2,
                     tags: ["シナリオ"], beginnerNote: beginnerNote, source: nil)
    }

    func testHintUsesBeginnerNoteWhenSafe() {
        let q = makeQuestion(beginnerNote: "まずは処理の順番に注目しましょう。")
        XCTAssertEqual(HintBuilder.focusHint(for: q), "まずは処理の順番に注目しましょう。")
    }

    /// 正解をそのまま書いている補足はヒントに使わない（答えが見えてしまうため）
    func testHintDoesNotRevealAnswer() {
        let q = makeQuestion(beginnerNote: "答えは選択肢Aです。")
        let hint = HintBuilder.focusHint(for: q)
        XCTAssertFalse(hint.contains("選択肢A"))
        XCTAssertFalse(hint.isEmpty)
    }

    func testHintFallsBackToTheme() {
        let q = makeQuestion(beginnerNote: nil)
        XCTAssertTrue(HintBuilder.focusHint(for: q).contains("シナリオ作成"))
    }

    /// しぼり込みは正解を消さず、単一選択では2択まで減らす
    func testEliminationKeepsCorrectAndLeavesTwoChoices() {
        let q = makeQuestion()
        let dropped = HintBuilder.eliminatedChoices(for: q)
        XCTAssertFalse(dropped.contains(0), "正解を消してはいけない")
        XCTAssertEqual(q.choices.count - dropped.count, 2, "単一選択は2択まで絞る")
    }

    /// 複数選択では正解をすべて残し、不正解の一部だけ消す
    func testEliminationOnMultipleSelect() {
        let q = makeQuestion(choices: ["A", "B", "C", "D", "E"], correct: [0, 1])
        let dropped = HintBuilder.eliminatedChoices(for: q)
        XCTAssertTrue(dropped.isDisjoint(with: [0, 1]))
        XCTAssertFalse(dropped.isEmpty)
        XCTAssertLessThan(dropped.count, 3)
    }

    /// 同じ問題なら何度開いても同じ選択肢が消える
    func testEliminationIsDeterministic() {
        let q = makeQuestion()
        XCTAssertEqual(HintBuilder.eliminatedChoices(for: q),
                       HintBuilder.eliminatedChoices(for: q))
    }

    /// 2択の問題では絞り込みを提示しない
    func testEliminationUnavailableForTwoChoices() {
        let q = makeQuestion(choices: ["はい", "いいえ"], correct: [0])
        XCTAssertTrue(HintBuilder.eliminatedChoices(for: q).isEmpty)
        XCTAssertFalse(HintBuilder.canEliminate(q))
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
