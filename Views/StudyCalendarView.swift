import SwiftUI

/// 学習カレンダー（当月の学習日をハイライト）
struct StudyCalendarView: View {
    @EnvironmentObject var store: StudyStore
    @State private var monthOffset = 0

    private let cal = Calendar.current

    var body: some View {
        ZStack {
            AppBackground()
            ScrollView {
                VStack(spacing: Theme.Space.l) {
                    streakCard
                    calendarCard
                }
                .padding(Theme.Space.l)
            }
        }
        .navigationTitle("学習カレンダー")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var streakCard: some View {
        Card {
            HStack(spacing: Theme.Space.l) {
                VStack {
                    Image(systemName: "flame.fill").font(.system(size: 28)).foregroundStyle(Theme.orange)
                    Text("\(store.studyStreak())日").font(.system(size: 22, weight: .bold)).foregroundStyle(Theme.navy)
                    Text("連続学習").captionStyle()
                }.frame(maxWidth: .infinity)
                Divider().frame(height: 56)
                VStack {
                    Image(systemName: "calendar").font(.system(size: 28)).foregroundStyle(Theme.blue)
                    Text("\(store.studyDays().count)日").font(.system(size: 22, weight: .bold)).foregroundStyle(Theme.navy)
                    Text("累計学習日").captionStyle()
                }.frame(maxWidth: .infinity)
            }
        }
    }

    private var calendarCard: some View {
        let days = store.studyDays()
        let month = displayedMonth
        return Card {
            VStack(spacing: Theme.Space.m) {
                HStack {
                    Button { monthOffset -= 1 } label: { Image(systemName: "chevron.left") }
                    Spacer()
                    Text(monthTitle(month)).font(.system(size: 16, weight: .bold)).foregroundStyle(Theme.navy)
                    Spacer()
                    Button { monthOffset += 1 } label: { Image(systemName: "chevron.right") }
                        .disabled(monthOffset >= 0)
                }
                HStack {
                    ForEach(["日","月","火","水","木","金","土"], id: \.self) { w in
                        Text(w).font(.system(size: 12)).foregroundStyle(Theme.inkSoft).frame(maxWidth: .infinity)
                    }
                }
                let grid = monthGrid(for: month)
                ForEach(Array(grid.enumerated()), id: \.offset) { _, week in
                    HStack {
                        ForEach(Array(week.enumerated()), id: \.offset) { _, date in
                            dayCell(date, studied: date.map { days.contains(cal.startOfDay(for: $0)) } ?? false)
                        }
                    }
                }
            }
        }
    }

    private func dayCell(_ date: Date?, studied: Bool) -> some View {
        Group {
            if let date {
                let isToday = cal.isDateInToday(date)
                Text("\(cal.component(.day, from: date))")
                    .font(.system(size: 13, weight: studied ? .bold : .regular))
                    .foregroundStyle(studied ? .white : Theme.ink)
                    .frame(maxWidth: .infinity, minHeight: 34)
                    .background(
                        Circle().fill(studied ? Theme.orange : .clear)
                            .frame(width: 32, height: 32)
                    )
                    .overlay(
                        Circle().stroke(isToday && !studied ? Theme.blue : .clear, lineWidth: 1.5)
                            .frame(width: 32, height: 32)
                    )
            } else {
                Color.clear.frame(maxWidth: .infinity, minHeight: 34)
            }
        }
    }

    private var displayedMonth: Date {
        cal.date(byAdding: .month, value: monthOffset, to: .now) ?? .now
    }

    private func monthTitle(_ date: Date) -> String {
        let f = DateFormatter(); f.locale = Locale(identifier: "ja_JP"); f.dateFormat = "yyyy年 M月"
        return f.string(from: date)
    }

    /// 当月の日付を週ごとの配列に（前後の空白はnil）
    private func monthGrid(for date: Date) -> [[Date?]] {
        guard let interval = cal.dateInterval(of: .month, for: date),
              let firstWeekday = cal.dateComponents([.weekday], from: interval.start).weekday else { return [] }
        let daysInMonth = cal.range(of: .day, in: .month, for: date)?.count ?? 30
        var cells: [Date?] = Array(repeating: nil, count: firstWeekday - 1)
        for d in 0..<daysInMonth {
            cells.append(cal.date(byAdding: .day, value: d, to: interval.start))
        }
        while cells.count % 7 != 0 { cells.append(nil) }
        return stride(from: 0, to: cells.count, by: 7).map { Array(cells[$0..<$0+7]) }
    }
}
