import SwiftUI
import SwiftData

struct SettingsView: View {
    @EnvironmentObject var store: StudyStore
    @AppStorage("aiAssistEnabled") private var aiAssistEnabled = false
    @AppStorage("notificationsEnabled") private var notificationsEnabled = true
    @State private var showResetAlert = false

    var body: some View {
        NavigationStack {
            ZStack {
                AppBackground()
                ScrollView {
                    VStack(spacing: Theme.Space.l) {
                        profileCard
                        planCard
                        aiCard
                        notificationCard
                        nextCertCard
                        legalCard
                        resetButton
                    }
                    .padding(Theme.Space.l)
                }
            }
            .navigationTitle("設定")
        }
    }

    // MARK: - プロフィール

    private var profileCard: some View {
        Card {
            VStack(alignment: .leading, spacing: Theme.Space.m) {
                Text("プロフィール").font(.system(size: 16, weight: .bold)).foregroundStyle(Theme.navy)
                if let p = store.profile {
                    settingRow("ニックネーム", p.name.isEmpty ? "未設定" : p.name)
                    settingRow("経験レベル", p.experience.title)
                    settingRow("1日の学習時間", "約\(p.dailyStudyMinutes)分")
                    if let date = p.targetExamDate {
                        settingRow("試験予定日", date.formatted(date: .long, time: .omitted))
                    } else {
                        settingRow("試験予定日", "未設定")
                    }
                }
            }
        }
    }

    // MARK: - プラン変更

    private var planCard: some View {
        Card {
            VStack(alignment: .leading, spacing: Theme.Space.m) {
                Text("学習プラン").font(.system(size: 16, weight: .bold)).foregroundStyle(Theme.navy)
                ForEach(StudyPlanType.allCases) { plan in
                    Button {
                        store.profile?.plan = plan
                        store.objectWillChange.send()
                        try? store.context.save()
                    } label: {
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(plan.title).font(.system(size: 14, weight: .semibold)).foregroundStyle(Theme.ink)
                                Text(plan.subtitle).captionStyle()
                            }
                            Spacer()
                            Image(systemName: store.profile?.plan == plan ? "checkmark.circle.fill" : "circle")
                                .foregroundStyle(store.profile?.plan == plan ? Theme.orange : Theme.line)
                        }
                    }.buttonStyle(.plain)
                    if plan != StudyPlanType.allCases.last { Divider() }
                }
            }
        }
    }

    // MARK: - AI（将来拡張）

    private var aiCard: some View {
        Card {
            VStack(alignment: .leading, spacing: Theme.Space.s) {
                Toggle(isOn: $aiAssistEnabled) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("AI学習サポート").font(.system(size: 15, weight: .semibold)).foregroundStyle(Theme.ink)
                        Text("用語の言い換え・解説の深掘り（準備中）").captionStyle()
                    }
                }.tint(Theme.blue)
                Text("AI機能はバックエンド経由で安全に呼び出し、利用回数・月額上限・キャッシュを設ける設計です。OFFでもアプリは完全に動作します。")
                    .font(.system(size: 11)).foregroundStyle(Theme.inkSoft)
            }
        }
    }

    private var notificationCard: some View {
        Card {
            Toggle(isOn: $notificationsEnabled) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("学習リマインド").font(.system(size: 15, weight: .semibold)).foregroundStyle(Theme.ink)
                    Text("毎日の学習を通知でお知らせ").captionStyle()
                }
            }.tint(Theme.blue)
        }
    }

    // MARK: - 次の資格

    private var nextCertCard: some View {
        Card {
            VStack(alignment: .leading, spacing: Theme.Space.s) {
                Text("次のステップ").font(.system(size: 16, weight: .bold)).foregroundStyle(Theme.navy)
                certRow("RPA技術者検定 エキスパート", "シナリオ実技・中級者向け", true)
                certRow("RPA技術者検定 プロフェッショナル", "上級者・導入推進向け", true)
                certRow("WinActor実務での自動化", "業務シナリオの内製化", true)
                Text("合格後はこれらのステップへ拡張予定です（現在はアソシエイトに対応）。")
                    .font(.system(size: 11)).foregroundStyle(Theme.inkSoft)
            }
        }
    }

    private func certRow(_ title: String, _ subtitle: String, _ comingSoon: Bool) -> some View {
        HStack {
            Image(systemName: "lock.fill").foregroundStyle(Theme.inkSoft).font(.system(size: 12))
            VStack(alignment: .leading, spacing: 1) {
                Text(title).font(.system(size: 14, weight: .semibold)).foregroundStyle(Theme.ink)
                Text(subtitle).captionStyle()
            }
            Spacer()
            if comingSoon { TagChip(text: "準備中", color: Theme.inkSoft) }
        }
    }

    // MARK: - 法的・免責

    private var legalCard: some View {
        Card {
            VStack(alignment: .leading, spacing: Theme.Space.s) {
                Text("ご利用にあたって").font(.system(size: 16, weight: .bold)).foregroundStyle(Theme.navy)
                bullet("本アプリの問題・解説はすべてオリジナルです。公式問題・市販教材の転載はありません。")
                bullet("試験範囲・配点・受験要件は変更されることがあります。最新情報は必ず公式サイト（J-Testing等）でご確認ください。")
                bullet("合格可能性スコアは学習の目安であり、合否を保証・予測するものではありません。")
                bullet("WinActor は株式会社NTTデータの登録商標です。本アプリはNTTデータおよび関連団体とは無関係の、非公式の学習支援アプリです。")
            }
        }
    }

    private var resetButton: some View {
        Button(role: .destructive) { showResetAlert = true } label: {
            Text("学習データを初期化").font(.system(size: 15, weight: .semibold))
                .frame(maxWidth: .infinity).padding(.vertical, 14)
                .foregroundStyle(Theme.red).background(Theme.red.opacity(0.08))
                .clipShape(RoundedRectangle(cornerRadius: Theme.Radius.button))
        }
        .alert("学習データを初期化しますか？", isPresented: $showResetAlert) {
            Button("キャンセル", role: .cancel) {}
            Button("初期化する", role: .destructive) { resetAll() }
        } message: {
            Text("プロフィール・進捗・履歴がすべて削除され、初回診断からやり直します。")
        }
    }

    // MARK: - 部品

    private func settingRow(_ label: String, _ value: String) -> some View {
        HStack {
            Text(label).font(.system(size: 14)).foregroundStyle(Theme.inkSoft)
            Spacer()
            Text(value).font(.system(size: 14, weight: .semibold)).foregroundStyle(Theme.ink)
        }
    }

    private func bullet(_ text: String) -> some View {
        HStack(alignment: .top, spacing: 6) {
            Text("・").foregroundStyle(Theme.inkSoft)
            Text(text).font(.system(size: 12)).foregroundStyle(Theme.inkSoft)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    private func resetAll() {
        // 全モデルを削除して初回診断へ戻す
        try? store.context.delete(model: UserProfile.self)
        try? store.context.delete(model: AnswerRecord.self)
        try? store.context.delete(model: ReviewItem.self)
        try? store.context.delete(model: QuestionMeta.self)
        try? store.context.delete(model: MockExamResult.self)
        try? store.context.delete(model: StudyDayLog.self)
        try? store.context.save()
        store.objectWillChange.send()
    }
}
