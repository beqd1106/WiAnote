# -*- coding: utf-8 -*-
"""
WiAnote：新しい問題バンク（マニュアル準拠929問）をアプリへ取り込み、
レッスン14本の quizIds / challengeQuizIds / drillQuizIds を張り替える。

  python design/remap_lessons.py <新questions.json>

やること
  1. 新バンクを読み、各問題を「チャンクID＋テーマ名」でレッスンへ割り当てる
     （1問につき必ず1レッスン。全929問を使い切る）
  2. 各レッスンで
       quizIds      = 確認問題10問（やさしめ中心・テーマが散るように選ぶ）
       challengeQuizIds = 腕試し5問（難易度3から）
       drillQuizIds = 残り全部（ランダム演習のプール）
  3. Resources/questions.json と Resources/lessons.json を書き換える
"""
import json, re, sys, os, collections, random

random.seed(20260917)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "Resources")

# ── レッスン割り当てルール ─────────────────────────────
# (レッスンID, チャンクID, テーマ判定)  テーマ判定は None=そのチャンク全部、
# それ以外は service に対する正規表現（マッチしたものだけ）
RULES = [
    # 概要
    ("l-ov2", "C01", r"ライセンス"),
    ("l-ov1", "C01", None),                       # 残りの C01 全部

    ("l-ov2", "C09", r"ライセンス|バージョン情報"),
    ("l-ov2", "C04", r"評価ライセンス"),

    ("l-ov3", "C05", None),                       # 基本画面構成・メニューバー
    ("l-ov3", "C09", r"ドッキングウィンドウ"),
    ("l-ov3", "C06", r"パレット|ツールバー$|ツールバー（"),

    ("l-ov4", "C09", r"起動ショートカット|起動パスワード|タスクトレイ|オプション画面"),
    ("l-ov4", "C09", None),                       # オンラインシナリオ管理ほか C09 の残り
    ("l-ov4", "C04", None),                       # 起動/終了/制限事項/付録

    # 機能
    ("l-ft1", "C02", None),                       # 記録モード一式
    ("l-ft1", "C09", r"記録操作画面|値の取得画面"),
    ("l-ft1", "C06", r"編集／記録|編集/記録"),
    ("l-ft1", "C12", None),                       # 自動生成ノード/エミュレーション/UIオートメーション

    ("l-sc2", "C10", r"^分岐|多分岐|^繰り返し|後判定繰返|繰り返し終了|次の条件判定"),
    ("l-sc3", "C10", r"例外処理"),
    ("l-ft2", "C10", None),                       # 残りのフローカテゴリ
    ("l-ft2", "C08", r"イベント一覧|監視ルール|サブルーチン"),
    ("l-ft2", "C14", r"監視ルール"),

    ("l-ft3", "C13", None),                       # 変数
    ("l-ft3", "C08", r"変数一覧|データ一覧|メール管理|テキスト変換辞書"),
    ("l-ft3", "C06", r"ライブラリパレット"),
    ("l-ft3", "C03", r"言語非依存化"),

    ("l-ft5", "C11", r"待機ボックス|インプットボックス|選択ボックス|^音$|変数値設定|変数値コピー"
                     r"|日時取得|ユーザ名取得|四則演算|カウントアップ|全角化"),
    ("l-ft4", "C11", None),                       # 残りのアクションカテゴリ
    ("l-ft4", "C08", r"イメージタブ"),

    # シナリオ
    ("l-sc5", "C03", r"パスワード|セキュリティ"),
    ("l-sc1", "C03", None),                       # 作成/保存/雛型/ガイド/生成AI/差分 ほか
    ("l-sc1", "C07", r"^(?!条件式).*"),           # 条件式設定画面だけ l-sc2 へ
    ("l-sc2", "C07", r"条件式"),
    ("l-sc1", "C14", r"ウィンドウ識別ルール"),
    ("l-sc1", "C15", r"値の取得|表の値取得|値の設定"),

    ("l-sc3", "C06", r"ステップ実行"),
    ("l-sc3", "C08", r"ログ出力|ブレイクポイント|呼び出し履歴|実行時間|フォーマットチェック"),
    ("l-sc3", "C14", r"実行時エラー"),

    ("l-sc4", "C06", r"シナリオの実行操作"),
    ("l-sc4", "C14", None),                       # 全体/部分/ここから実行・ループ実行ほか

    ("l-sc5", "C15", None),                       # ファイルパス
]

QUIZ_N, CHALLENGE_N = 10, 5


def assign(questions):
    """各問題をレッスンへ割り当てる。先に書いたルールが優先。"""
    left = {q["id"]: q for q in questions}
    buckets = collections.defaultdict(list)
    for lesson_id, chunk, pattern in RULES:
        rx = re.compile(pattern) if pattern else None
        for qid, q in list(left.items()):
            if q["id"][2:5] != chunk:
                continue
            if rx and not rx.search(q["service"]):
                continue
            buckets[lesson_id].append(q)
            del left[qid]
    return buckets, list(left.values())


def pick(pool):
    """確認問題10・腕試し5・残りドリル に振り分ける。
    確認問題はテーマが偏らないよう、テーマごとに1問ずつ拾っていく。"""
    easy = [q for q in pool if q["difficulty"] <= 2]
    hard = [q for q in pool if q["difficulty"] == 3]

    by_service = collections.defaultdict(list)
    for q in sorted(easy, key=lambda x: (x["difficulty"], x["id"])):
        by_service[q["service"]].append(q)
    order = sorted(by_service, key=lambda s: -len(by_service[s]))

    quiz, i = [], 0
    while len(quiz) < QUIZ_N and any(by_service.values()):
        s = order[i % len(order)]
        if by_service[s]:
            quiz.append(by_service[s].pop(0))
        i += 1
        if i > 4000:
            break
    used = {q["id"] for q in quiz}
    if len(quiz) < QUIZ_N:                       # やさしい問題が足りなければ難問で補う
        quiz += [q for q in hard if q["id"] not in used][:QUIZ_N - len(quiz)]
        used = {q["id"] for q in quiz}

    challenge = [q for q in sorted(hard, key=lambda x: x["id"]) if q["id"] not in used][:CHALLENGE_N]
    used |= {q["id"] for q in challenge}
    drill = [q for q in pool if q["id"] not in used]
    return quiz, challenge, drill


def main():
    src = sys.argv[1]
    questions = json.load(open(src, encoding="utf-8"))
    for q in questions:                          # アプリで使わないキーは落とす
        q.pop("origin", None)

    buckets, leftover = assign(questions)
    if leftover:
        print(f"  ! 未割り当て {len(leftover)}問:")
        for q in leftover[:10]:
            print("     ", q["id"], q["service"])

    lessons = json.load(open(os.path.join(RES, "lessons.json"), encoding="utf-8"))
    total_used = 0
    for lesson in lessons:
        pool = buckets.get(lesson["id"], [])
        if not pool:
            print(f"  ! {lesson['id']} に問題が1問も割り当たっていない")
            continue
        quiz, challenge, drill = pick(pool)
        lesson["quizIds"] = [q["id"] for q in quiz]
        lesson["challengeQuizIds"] = [q["id"] for q in challenge]
        lesson["drillQuizIds"] = [q["id"] for q in drill]
        total_used += len(pool)
        themes = len({q["service"] for q in pool})
        print(f"  {lesson['id']:<7} {lesson['title']:<26} 計{len(pool):>4}問"
              f"（確認{len(quiz)} 腕試し{len(challenge)} ドリル{len(drill)}） {themes}テーマ")

    json.dump(questions, open(os.path.join(RES, "questions.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(lessons, open(os.path.join(RES, "lessons.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # 検証
    qids = {q["id"] for q in questions}
    bad = []
    for lesson in lessons:
        for key in ("quizIds", "challengeQuizIds", "drillQuizIds"):
            for qid in lesson.get(key) or []:
                if qid not in qids:
                    bad.append((lesson["id"], key, qid))
    print(f"\n  問題 {len(questions)}問 / レッスン割り当て {total_used}問 / 参照切れ {len(bad)}件")
    dup = [k for k, v in collections.Counter(
        qid for l in lessons for key in ("quizIds", "challengeQuizIds", "drillQuizIds")
        for qid in (l.get(key) or [])).items() if v > 1]
    print(f"  レッスン間の重複: {len(dup)}件")


if __name__ == "__main__":
    main()
