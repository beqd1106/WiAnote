import sys,re
p=sys.argv[1]; s=open(p,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1, a[:60]
    s=s.replace(a,b)

rep('''/// レッスン一覧の補足行（基礎問題があれば併記する）
private func questionSummary(_ lesson: Lesson) -> String {
    let basic = lesson.basicQuizIds?.count ?? 0
    let parts = basic > 0 ? "基礎\(basic)問・確認\(lesson.quizIds.count)問" : "確認問題\(lesson.quizIds.count)問"
    return "約\(lesson.estimatedMinutes)分・\(parts)"
}
''','''/// レッスン一覧の補足行（基礎問題があれば併記する）
private func questionSummary(_ lesson: Lesson) -> String {
    let basic = lesson.basicQuizIds?.count ?? 0
    let quiz = patternCountLabel(lesson.quizIds.count)
    let parts = basic > 0 ? "基礎\(patternCountLabel(basic))・確認\(quiz)" : "確認問題\(quiz)"
    return "約\(lesson.estimatedMinutes)分・\(parts)"
}

// MARK: - 問題パターン（基礎・確認を5問ずつのA/B/Cに分ける）

/// 1パターンの問題数
private let patternSize = 5

/// 問題IDを先頭から5問ずつに区切る（15問ならA/B/Cの3パターン）
private func patterns(_ ids: [String]) -> [[String]] {
    stride(from: 0, to: ids.count, by: patternSize).map { Array(ids[$0..<min($0 + patternSize, ids.count)]) }
}

/// 「5問×3」のような表記。5で割り切れないときは総数で出す
private func patternCountLabel(_ count: Int) -> String {
    count > patternSize && count % patternSize == 0 ? "\(patternSize)問×\(count / patternSize)" : "\(count)問"
}

/// レッスン内で選ばれた問題パターン
private struct PracticeSet: Hashable {
    enum Kind: Hashable { case basic, confirm }
    let kind: Kind
    let index: Int
    let ids: [String]
    /// A, B, C …
    var letter: String { String(UnicodeScalar(UInt8(65 + index))) }
}
''')

rep('''    @State private var showBasic = false
    @State private var showQuiz = false
''','''    /// 基礎・確認のうち選ばれたパターン（A/B/C）
    @State private var activeSet: PracticeSet?
''')

s, n = re.subn(r"                    if !basicIds\.isEmpty \{\n                        // 基礎問題 → 確認問題 の順に解いてもらう[^\n]*\n                        stepsCard\n                    \} else if !lesson\.quizIds\.isEmpty \{\n.*?\n                    \}\n",
    "                    // 基礎問題 → 確認問題 の順に解いてもらう。どちらも5問ずつのパターンA/B/Cから選ぶ\n                    if !basicIds.isEmpty || !lesson.quizIds.isEmpty { stepsCard }\n", s, count=1, flags=re.S)
assert n == 1, "steps block"

rep('''        .navigationDestination(isPresented: $showBasic) {
            QuizPlayerView(title: "基礎問題・\(lesson.title)",
                           questions: basicIds.compactMap { ContentRepository.shared.question(id: $0) },
                           showLessonLink: false)
        }
        .navigationDestination(isPresented: $showQuiz) {
            QuizPlayerView(title: lesson.title,
                           questions: lesson.quizIds.compactMap { ContentRepository.shared.question(id: $0) },
                           showLessonLink: false,
                           onComplete: { store.markLessonCompleted(lesson.id) })
        }
''','''        .navigationDestination(item: $activeSet) { set in
            let questions = set.ids.compactMap { ContentRepository.shared.question(id: $0) }
            switch set.kind {
            case .basic:
                QuizPlayerView(title: "基礎問題\(set.letter)・\(lesson.title)",
                               questions: questions, showLessonLink: false)
            case .confirm:
                // 確認問題のパターンをすべて解き終えたら履修済みにする
                QuizPlayerView(title: "確認問題\(set.letter)・\(lesson.title)",
                               questions: questions, showLessonLink: false,
                               onComplete: {
                                   let answered = store.answeredQuestionIds()
                                   if lesson.quizIds.allSatisfy(answered.contains) {
                                       store.markLessonCompleted(lesson.id)
                                   }
                               })
            }
        }
''')

# replace stepsCard..stepLabel
note = re.search(r'stepLabel\(2, "確認問題", "([^"]*)"\)', s).group(1)
start=s.index('    // 基礎問題（STEP 1）→ 確認問題（STEP 2）の2段構え')
end=s.index('    private func stepLabel(')
s=s[:start]+'''    // 基礎問題（STEP 1）→ 確認問題（STEP 2）の2段構え。どちらも5問ずつのパターンA/B/Cから選ぶ
    private var stepsCard: some View {
        let answered = store.answeredQuestionIds()
        let hasBoth = !basicIds.isEmpty && !lesson.quizIds.isEmpty
        return Card {
            VStack(alignment: .leading, spacing: Theme.Space.l) {
                Text("問題に挑戦").font(.system(size: 16, weight: .bold)).foregroundStyle(Theme.navy)

                if !basicIds.isEmpty {
                    VStack(alignment: .leading, spacing: Theme.Space.m) {
                        stepLabel(1, "基礎問題", "レッスンを読んだら、まずここから。用語と役割を確認します。")
                        patternRow(.basic, ids: basicIds, answered: answered)
                    }
                }

                if !lesson.quizIds.isEmpty {
                    VStack(alignment: .leading, spacing: Theme.Space.m) {
                        stepLabel(hasBoth ? 2 : 1, "確認問題", "'''+note+'''全パターンを解くと履修済みになります。")
                        patternRow(.confirm, ids: lesson.quizIds, answered: answered)
                    }
                }
            }
        }
    }

    /// パターンA/B/Cのタイル（解き終えたパターンにはチェックが付く）
    private func patternRow(_ kind: PracticeSet.Kind, ids: [String], answered: Set<String>) -> some View {
        let tint = kind == .basic ? Theme.orange : Theme.blue
        let soft = kind == .basic ? Theme.orangeSoft : Theme.blueSoft
        return HStack(spacing: Theme.Space.s) {
            ForEach(Array(patterns(ids).enumerated()), id: \.offset) { index, chunk in
                let set = PracticeSet(kind: kind, index: index, ids: chunk)
                let done = chunk.allSatisfy(answered.contains)
                Button {
                    activeSet = set
                } label: {
                    VStack(spacing: 2) {
                        HStack(spacing: 4) {
                            Text(set.letter).font(.system(size: 20, weight: .bold))
                            if done { Image(systemName: "checkmark.circle.fill").font(.system(size: 14)) }
                        }
                        Text(done ? "解答済み" : "\(chunk.count)問").font(.system(size: 12, weight: .semibold))
                    }
                    .foregroundStyle(done ? .white : tint)
                    .frame(maxWidth: .infinity, minHeight: 64)
                    .background(RoundedRectangle(cornerRadius: Theme.Radius.button, style: .continuous)
                        .fill(done ? tint : soft))
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel("\(kind == .basic ? "基礎問題" : "確認問題")パターン\(set.letter)、\(chunk.count)問\(done ? "、解答済み" : "")")
            }
        }
    }

'''+s[end:]
s=s.replace("確認問題・腕試しに載せきれなかった","確認問題・腕試しに載せきれなかった")
open(p,'w',encoding='utf-8').write(s)
