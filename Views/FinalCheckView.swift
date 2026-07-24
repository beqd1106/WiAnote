import SwiftUI

/// 試験直前モード：頻出ポイントの総復習＋直前チェックリスト
struct FinalCheckView: View {
    @EnvironmentObject var store: StudyStore
    @State private var checked: Set<String> = []
    @State private var showQuiz = false

    /// 直前チェックリスト項目
    private let checklist: [String] = [
        "RPAとは何か、WinActorがどんなツールかを説明できる",
        "WinActorのエディション（フル版／実行版）の違いを言える",
        "メイン画面・フローチャート・アクションライブラリの役割を理解した",
        "自動記録（IEモード／エミュレーション等）の使い分けを説明できる",
        "分岐・繰り返し・変数・待機など主要ノードの働きを言える",
        "シナリオ・データ一覧・変数一覧の関係を理解した",
        "ライブラリを使った処理（エクセル操作等）の作り方が分かる",
        "例外処理・デバッグ実行で不具合を切り分けられる",
        "受験当日の本人確認書類・CBT会場/オンラインの手順を確認した",
    ]

    /// 頻出の重要用語（直前に見直すカード）
    private var keyTerms: [TermCard] {
        let ids = ["t-rpa", "t-winactor", "t-scenario", "t-node", "t-library", "t-variable"]
        return ids.compactMap { id in ContentRepository.shared.terms.first { $0.id == id } }
    }

    var body: some View {
        ZStack {
            AppBackground()
            ScrollView {
                VStack(alignment: .leading, spacing: Theme.Space.l) {
                    header
                    quickReviewCard
                    keyTermsCard
                    checklistCard
                }
                .padding(Theme.Space.l)
            }
        }
        .navigationTitle("試験直前モード")
        .navigationBarTitleDisplayMode(.inline)
        .navigationDestination(isPresented: $showQuiz) {
            QuizPlayerView(title: "直前総まとめ", questions: finalQuestions)
        }
    }

    private var header: some View {
        Card {
            HStack(spacing: Theme.Space.m) {
                Image(systemName: "bolt.fill").font(.system(size: 24)).foregroundStyle(.white)
                    .frame(width: 48, height: 48).background(Theme.orange).clipShape(Circle())
                VStack(alignment: .leading, spacing: 3) {
                    if let days = store.profile?.daysUntilExam, days >= 0 {
                        Text("試験まで残り\(days)日").font(.system(size: 17, weight: .bold)).foregroundStyle(Theme.navy)
                    } else {
                        Text("ラストスパート").font(.system(size: 17, weight: .bold)).foregroundStyle(Theme.navy)
                    }
                    Text("頻出ポイントを一気に総復習しましょう").captionStyle()
                }
            }
        }
    }

    private var quickReviewCard: some View {
        Card {
            VStack(alignment: .leading, spacing: Theme.Space.m) {
                Text("総まとめ問題").font(.system(size: 16, weight: .bold)).foregroundStyle(Theme.navy)
                Text("苦手分野と間違えた問題を中心に出題します。").captionStyle()
                PrimaryButton(title: "総まとめ問題を解く（\(finalQuestions.count)問）", icon: "checklist") {
                    showQuiz = true
                }
            }
        }
    }

    private var keyTermsCard: some View {
        Card {
            VStack(alignment: .leading, spacing: Theme.Space.m) {
                Text("頻出の重要用語").font(.system(size: 16, weight: .bold)).foregroundStyle(Theme.navy)
                ForEach(keyTerms) { term in
                    VStack(alignment: .leading, spacing: 3) {
                        Text(term.term).font(.system(size: 14, weight: .bold)).foregroundStyle(Theme.blue)
                        Text(term.examPoint).font(.system(size: 13)).foregroundStyle(Theme.ink)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    if term.id != keyTerms.last?.id { Divider() }
                }
            }
        }
    }

    private var checklistCard: some View {
        Card {
            VStack(alignment: .leading, spacing: Theme.Space.m) {
                Text("直前チェックリスト").font(.system(size: 16, weight: .bold)).foregroundStyle(Theme.navy)
                ForEach(checklist, id: \.self) { item in
                    Button {
                        if checked.contains(item) { checked.remove(item) } else { checked.insert(item) }
                    } label: {
                        HStack(alignment: .top, spacing: Theme.Space.s) {
                            Image(systemName: checked.contains(item) ? "checkmark.square.fill" : "square")
                                .foregroundStyle(checked.contains(item) ? Theme.green : Theme.inkSoft)
                            Text(item).font(.system(size: 14))
                                .foregroundStyle(checked.contains(item) ? Theme.inkSoft : Theme.ink)
                                .strikethrough(checked.contains(item))
                                .fixedSize(horizontal: false, vertical: true)
                            Spacer(minLength: 0)
                        }
                    }.buttonStyle(.plain)
                }
                Text("※受験要件・当日ルールは必ず公式サイト・J-Testingでご確認ください。")
                    .font(.system(size: 11)).foregroundStyle(Theme.inkSoft)
            }
        }
    }

    /// 苦手分野＋復習＋足りなければ全体から補充
    private var finalQuestions: [QuizQuestion] {
        var qs: [QuizQuestion] = store.dueReviewQuestions()
        if let weak = store.weakestDomain() {
            qs += ContentRepository.shared.questions(in: weak)
        }
        var seen = Set<String>()
        var unique = qs.filter { seen.insert($0.id).inserted }
        if unique.count < 10 {
            let extra = ContentRepository.shared.questions.shuffled()
                .filter { seen.insert($0.id).inserted }
            unique += extra.prefix(10 - unique.count)
        }
        return Array(unique.prefix(15))
    }
}
