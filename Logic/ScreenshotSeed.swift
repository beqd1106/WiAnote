#if DEBUG
import Foundation
import SwiftData

/// App Store 用スクリーンショット撮影のためのデモデータ投入（DEBUG ビルド専用）。
/// UIテストが起動引数 `-ScreenshotSeed` を付けたときだけ動き、通常の利用では何もしない。
@MainActor
enum ScreenshotSeed {
    static func applyIfRequested(to store: StudyStore) {
        guard ProcessInfo.processInfo.arguments.contains("-ScreenshotSeed"),
              !store.hasCompletedOnboarding else { return }
        let ctx = store.context
        let repo = ContentRepository.shared
        let cal = Calendar.current
        let today = cal.startOfDay(for: .now)

        store.createProfile(UserProfile(name: "",
                                        dailyStudyMinutes: 30,
                                        targetExamDate: cal.date(byAdding: .day, value: 21, to: today),
                                        plan: .standard8,
                                        weakDomains: [.scenario],
                                        createdAt: cal.date(byAdding: .day, value: -14, to: today)!))

        // 分野ごとの正答率に差をつけ、分析画面に「苦手」が見えるようにする
        let rates: [ExamDomain: Double] = [.overview: 0.84, .features: 0.72, .scenario: 0.58]
        var rng = SystemRandomNumberGenerator()
        for (d, rate) in rates {
            for (i, q) in repo.questions(in: d).prefix(70).enumerated() {
                let day = cal.date(byAdding: .day, value: -(i % 12), to: today)!
                let correct = Double.random(in: 0..<1, using: &rng) < rate
                ctx.insert(AnswerRecord(questionId: q.id, domain: d, isCorrect: correct,
                                        answeredAt: day.addingTimeInterval(3600 * 20)))
                if !correct {
                    ctx.insert(ReviewItem(questionId: q.id, nextReviewDate: today))
                }
            }
        }
        for offset in 0..<12 {
            let day = cal.date(byAdding: .day, value: -offset, to: today)!
            ctx.insert(StudyDayLog(day: day, studiedMinutes: 25 + (offset * 7) % 20,
                                   questionsAnswered: 15 + (offset * 5) % 10))
        }
        for lesson in repo.lessons.prefix(6) {
            ctx.insert(LessonProgress(lessonId: lesson.id))
        }
        ctx.insert(MockExamResult(date: cal.date(byAdding: .day, value: -2, to: today)!,
                                  scaledScore: 720, correctCount: 36, totalCount: 50,
                                  domainScores: [
                                    DomainScoreEntry(domainRaw: ExamDomain.overview.rawValue, correct: 9, total: 10),
                                    DomainScoreEntry(domainRaw: ExamDomain.features.rawValue, correct: 15, total: 20),
                                    DomainScoreEntry(domainRaw: ExamDomain.scenario.rawValue, correct: 12, total: 20),
                                  ]))
        try? ctx.save()
    }
}
#endif
