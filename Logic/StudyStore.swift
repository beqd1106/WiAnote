import Foundation
import SwiftData
import SwiftUI

/// アプリの学習状態を司る中央ストア。
/// SwiftData(ModelContext) への読み書きと、進捗統計・今日のタスク生成をまとめる。
/// View からはこのストア経由で操作することで、永続化の詳細を隠蔽する。
@MainActor
final class StudyStore: ObservableObject {
    let context: ModelContext
    private let repo = ContentRepository.shared

    /// 画面更新トリガ（保存のたびに更新）
    @Published private(set) var revision: Int = 0

    init(context: ModelContext) {
        self.context = context
    }

    private func bumpAndSave() {
        try? context.save()
        revision += 1
    }

    // MARK: - プロフィール

    var profile: UserProfile? {
        try? context.fetch(FetchDescriptor<UserProfile>()).first
    }

    var hasCompletedOnboarding: Bool { profile != nil }

    func createProfile(_ p: UserProfile) {
        // 既存があれば一旦削除（やり直し対応）
        if let existing = profile { context.delete(existing) }
        context.insert(p)
        bumpAndSave()
    }

    // MARK: - 回答記録

    /// 演習/模試で1問回答したときに呼ぶ。履歴・復習キュー・学習ログを更新する。
    func recordAnswer(question: QuizQuestion, correct: Bool, isMock: Bool = false) {
        context.insert(AnswerRecord(questionId: question.id, domain: question.domain,
                                    isCorrect: correct, isMockExam: isMock))

        // 復習キューの更新（模試以外）
        if !isMock {
            updateReviewItem(questionId: question.id, correct: correct)
        }

        logStudy(questions: 1, minutes: 0)
        bumpAndSave()
    }

    private func updateReviewItem(questionId: String, correct: Bool) {
        let existing = fetchReviewItem(questionId)
        if let item = existing {
            let r = SpacedRepetition.next(currentLevel: item.reviewLevel, correct: correct)
            item.reviewLevel = r.level
            item.nextReviewDate = r.nextDate
            item.lastResultCorrect = correct
            // 正解を重ねて最終段階に達したら卒業（削除）
            if correct && item.reviewLevel >= SpacedRepetition.intervals.count - 1 {
                context.delete(item)
            }
        } else if !correct {
            // 間違えた問題を新規に復習キューへ
            let r = SpacedRepetition.next(currentLevel: 0, correct: false)
            context.insert(ReviewItem(questionId: questionId, nextReviewDate: r.nextDate,
                                      reviewLevel: 0, lastResultCorrect: false))
        }
    }

    private func fetchReviewItem(_ questionId: String) -> ReviewItem? {
        let d = FetchDescriptor<ReviewItem>(predicate: #Predicate { $0.questionId == questionId })
        return try? context.fetch(d).first
    }

    // MARK: - 復習

    /// 今日が期限の復習問題
    func dueReviewQuestions(limit: Int = 100) -> [QuizQuestion] {
        let items = (try? context.fetch(FetchDescriptor<ReviewItem>())) ?? []
        let dueIds = items.filter { $0.isDue }
            .sorted { $0.nextReviewDate < $1.nextReviewDate }
            .map(\.questionId)
        return dueIds.compactMap { repo.question(id: $0) }.prefix(limit).map { $0 }
    }

    var dueReviewCount: Int {
        let items = (try? context.fetch(FetchDescriptor<ReviewItem>())) ?? []
        return items.filter { $0.isDue }.count
    }

    var totalReviewCount: Int {
        ((try? context.fetch(FetchDescriptor<ReviewItem>())) ?? []).count
    }

    // MARK: - お気に入り・メモ

    func meta(for questionId: String) -> QuestionMeta {
        let d = FetchDescriptor<QuestionMeta>(predicate: #Predicate { $0.questionId == questionId })
        if let m = try? context.fetch(d).first { return m }
        let m = QuestionMeta(questionId: questionId)
        context.insert(m)
        return m
    }

    /// 読み取り専用（描画中に新規メタを生成しないよう fetch のみ）
    func isBookmarked(_ questionId: String) -> Bool {
        let d = FetchDescriptor<QuestionMeta>(predicate: #Predicate { $0.questionId == questionId })
        return ((try? context.fetch(d))?.first)?.isBookmarked ?? false
    }

    func toggleBookmark(_ questionId: String) {
        let m = meta(for: questionId)
        m.isBookmarked.toggle()
        bumpAndSave()
    }

    func setNote(_ note: String, for questionId: String) {
        meta(for: questionId).note = note
        bumpAndSave()
    }

    func note(for questionId: String) -> String {
        let d = FetchDescriptor<QuestionMeta>(predicate: #Predicate { $0.questionId == questionId })
        return ((try? context.fetch(d))?.first)?.note ?? ""
    }

    func bookmarkedQuestions() -> [QuizQuestion] {
        let d = FetchDescriptor<QuestionMeta>(predicate: #Predicate { $0.isBookmarked == true })
        let metas = (try? context.fetch(d)) ?? []
        return metas.compactMap { repo.question(id: $0.questionId) }
    }

    // MARK: - レッスン履修状態

    /// 指定レッスンが履修済みか
    func isLessonCompleted(_ lessonId: String) -> Bool {
        let d = FetchDescriptor<LessonProgress>(predicate: #Predicate { $0.lessonId == lessonId })
        return ((try? context.fetch(d))?.first) != nil
    }

    /// レッスンを履修済みにする（重複挿入しない）
    func markLessonCompleted(_ lessonId: String) {
        guard !isLessonCompleted(lessonId) else { return }
        context.insert(LessonProgress(lessonId: lessonId))
        bumpAndSave()
    }

    /// 履修済みを取り消す
    func unmarkLessonCompleted(_ lessonId: String) {
        let d = FetchDescriptor<LessonProgress>(predicate: #Predicate { $0.lessonId == lessonId })
        if let item = try? context.fetch(d).first {
            context.delete(item)
            bumpAndSave()
        }
    }

    /// 履修済みレッスンの総数
    var completedLessonCount: Int {
        ((try? context.fetch(FetchDescriptor<LessonProgress>())) ?? []).count
    }

    /// 分野別の履修済みレッスン数
    func completedLessonCount(in domain: ExamDomain) -> Int {
        let ids = Set(((try? context.fetch(FetchDescriptor<LessonProgress>())) ?? []).map(\.lessonId))
        return repo.lessons(in: domain).filter { ids.contains($0.id) }.count
    }

    /// カリキュラム順で最初の未履修レッスン（「続きから学習」用）。全て履修済みなら nil。
    func nextUnfinishedLesson() -> Lesson? {
        let ids = Set(((try? context.fetch(FetchDescriptor<LessonProgress>())) ?? []).map(\.lessonId))
        return repo.lessons.first { !ids.contains($0.id) }
    }

    // MARK: - カスタム演習用の集合

    /// これまでに一度でも間違えた問題のID集合
    func mistakenQuestionIds() -> Set<String> {
        Set(allAnswers.filter { !$0.isCorrect }.map(\.questionId))
    }

    /// ブックマーク済み問題のID集合
    func bookmarkedQuestionIds() -> Set<String> {
        let d = FetchDescriptor<QuestionMeta>(predicate: #Predicate { $0.isBookmarked == true })
        return Set(((try? context.fetch(d)) ?? []).map(\.questionId))
    }

    // MARK: - 統計

    private var allAnswers: [AnswerRecord] {
        (try? context.fetch(FetchDescriptor<AnswerRecord>())) ?? []
    }

    var totalAnswered: Int { allAnswers.count }

    /// 分野別の正答率（直近の理解度を反映するため全履歴ベース）
    func correctRateByDomain() -> [ExamDomain: Double] {
        var result: [ExamDomain: Double] = [:]
        let answers = allAnswers
        for domain in ExamDomain.allCases {
            let inDomain = answers.filter { $0.domain == domain }
            if inDomain.isEmpty { result[domain] = 0; continue }
            let correct = inDomain.filter(\.isCorrect).count
            result[domain] = Double(correct) / Double(inDomain.count)
        }
        return result
    }

    func answeredCount(in domain: ExamDomain) -> Int {
        allAnswers.filter { $0.domain == domain }.count
    }

    /// 最も苦手な分野（回答実績があるもののうち正答率が最低）
    func weakestDomain() -> ExamDomain? {
        let rates = correctRateByDomain()
        let answered = ExamDomain.allCases.filter { answeredCount(in: $0) >= 3 }
        return answered.min { (rates[$0] ?? 0) < (rates[$1] ?? 0) }
    }

    /// 苦手克服のおすすめ（最も苦手な分野・その正答率・取り組むべきレッスン）。
    /// 十分な回答実績（3問以上）がある分野が無ければ nil。
    func weakAreaRecommendation() -> (domain: ExamDomain, rate: Double, lesson: Lesson)? {
        guard let domain = weakestDomain() else { return nil }
        let rate = correctRateByDomain()[domain] ?? 0
        // その分野の未履修レッスンを優先、無ければ先頭のレッスン
        let doneIds = Set(((try? context.fetch(FetchDescriptor<LessonProgress>())) ?? []).map(\.lessonId))
        let lessons = repo.lessons(in: domain)
        guard let lesson = lessons.first(where: { !doneIds.contains($0.id) }) ?? lessons.first else { return nil }
        return (domain, rate, lesson)
    }

    // MARK: - 模擬試験結果

    func saveMockResult(_ result: MockExamResult) {
        context.insert(result)
        bumpAndSave()
    }

    func mockResults() -> [MockExamResult] {
        let d = FetchDescriptor<MockExamResult>(sortBy: [SortDescriptor(\.date, order: .reverse)])
        return (try? context.fetch(d)) ?? []
    }

    var latestMockScaledScore: Int? { mockResults().first?.scaledScore }

    // MARK: - 学習ログ・連続日数

    private func logStudy(questions: Int, minutes: Int) {
        let today = Calendar.current.startOfDay(for: .now)
        let d = FetchDescriptor<StudyDayLog>(predicate: #Predicate { $0.day == today })
        if let log = try? context.fetch(d).first {
            log.questionsAnswered += questions
            log.studiedMinutes += minutes
        } else {
            context.insert(StudyDayLog(day: today, studiedMinutes: minutes, questionsAnswered: questions))
        }
    }

    func studyDays() -> Set<Date> {
        let logs = (try? context.fetch(FetchDescriptor<StudyDayLog>())) ?? []
        return Set(logs.map { $0.day })
    }

    /// 今日を含む連続学習日数
    func studyStreak() -> Int {
        let days = studyDays()
        guard !days.isEmpty else { return 0 }
        let cal = Calendar.current
        var streak = 0
        var cursor = cal.startOfDay(for: .now)
        // 今日まだ学習していなければ昨日から数える
        if !days.contains(cursor) {
            cursor = cal.date(byAdding: .day, value: -1, to: cursor)!
        }
        while days.contains(cursor) {
            streak += 1
            cursor = cal.date(byAdding: .day, value: -1, to: cursor)!
        }
        return streak
    }

    // MARK: - 合格可能性スコア

    func passProbabilityScore() -> Int {
        let total = totalReviewCount
        let due = dueReviewCount
        let reviewRate = total == 0 ? 1.0 : Double(total - due) / Double(total)
        let inputs = PassProbability.Inputs(
            correctRateByDomain: correctRateByDomain(),
            latestMockScaledScore: latestMockScaledScore,
            reviewCompletionRate: reviewRate,
            studyStreak: studyStreak(),
            totalAnswered: totalAnswered
        )
        return PassProbability.score(inputs)
    }

    // MARK: - 今日のタスク

    func todayTasks() -> [TodayTask] {
        var tasks: [TodayTask] = []
        let week = currentWeek
        let roadmap = PlanFactory.roadmap(for: profile?.plan ?? .standard8)
        let weekGoal = roadmap.first { $0.week == week } ?? roadmap.first
        let focusDomain = weekGoal?.domains.first ?? .overview

        // 1) 今週テーマのレッスン
        if let lesson = repo.lessons(in: focusDomain).first {
            tasks.append(.init(kind: .lesson, title: "レッスン：\(lesson.title)",
                               subtitle: "今週のテーマ・約\(lesson.estimatedMinutes)分", refId: lesson.id))
        }
        // 2) 用語カード
        tasks.append(.init(kind: .terms, title: "用語カード 5枚",
                           subtitle: "\(focusDomain.shortTitle)の重要用語", refId: focusDomain.rawValue))
        // 3) 今週テーマの確認問題
        tasks.append(.init(kind: .quiz, title: "確認問題 5問",
                           subtitle: "\(focusDomain.title)", refId: focusDomain.rawValue))
        // 4) 復習（期限ありのときだけ）
        if dueReviewCount > 0 {
            tasks.append(.init(kind: .review, title: "復習 \(min(dueReviewCount,10))問",
                               subtitle: "間違えた問題の再挑戦", refId: nil))
        }
        return tasks
    }

    var currentWeek: Int {
        guard let p = profile else { return 1 }
        return PlanFactory.currentWeek(startedAt: p.createdAt, plan: p.plan)
    }
}

struct TodayTask: Identifiable, Hashable {
    enum Kind { case lesson, terms, quiz, review }
    let id = UUID()
    let kind: Kind
    let title: String
    let subtitle: String
    let refId: String?
}
