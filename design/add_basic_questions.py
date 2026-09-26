# -*- coding: utf-8 -*-
"""
WiAnote：各レッスンの「基礎問題」（確認問題の前に解くやさしい問題）を取り込む。

  python design/add_basic_questions.py <基礎問題JSONのフォルダ> [--apply]

フォルダには <レッスンID>.json（問題の配列）を置く。
--apply なしでは検査だけ行い、Resources は書き換えない。

検査項目（資格学習アプリの標準仕様に合わせる）
  - 必須キー・単一選択・選択肢4つ・誤答解説のキー整合
  - 「一番長い選択肢を選ぶ」だけの正答率（25%前後が目標）
  - 解説が100字未満の問題
  - 設問・ヒント（beginnerNote）に正解の語が入っていないか
  - 正解位置の偏り
  - 既存問題との重複（設問がほぼ同じ）
"""
import json, os, sys, glob, collections, difflib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "Resources")
KEYS = ["id", "question", "choices", "correctAnswers", "explanation",
        "wrongChoiceExplanations", "domain", "service", "difficulty", "tags", "source", "beginnerNote"]


def load(name):
    return json.load(open(os.path.join(RES, f"{name}.json"), encoding="utf-8"))


def leaks(answer, text):
    """正解の語（4文字以上の部分）が text にそのまま入っているか"""
    a = answer.rstrip("。")
    return len(a) >= 4 and a in text


def main():
    folder = sys.argv[1]
    apply = "--apply" in sys.argv
    questions, lessons = load("questions"), load("lessons")
    existing = {q["id"]: q for q in questions if not q["id"].startswith("b-")}
    lesson_by_id = {l["id"]: l for l in lessons}

    new, errors, notes = {}, [], []
    for path in sorted(glob.glob(os.path.join(folder, "l-*.json"))):
        lid = os.path.splitext(os.path.basename(path))[0]
        if lid not in lesson_by_id:
            errors.append(f"{lid}: 該当レッスンが無い")
            continue
        new[lid] = json.load(open(path, encoding="utf-8"))

    all_new = [q for qs in new.values() for q in qs]
    longest_hit = shortest_hit = 0
    pos = collections.Counter()
    ids = collections.Counter(q.get("id") for q in all_new)
    for lid, qs in new.items():
        dom = lesson_by_id[lid]["domain"]
        for q in qs:
            w = q.get("id", "?")
            miss = [k for k in KEYS if k not in q]
            if miss:
                errors.append(f"{w}: キー不足 {miss}")
                continue
            ch, ca = q["choices"], q["correctAnswers"]
            if len(ch) != 4 or len(ca) != 1 or not (0 <= ca[0] < 4):
                errors.append(f"{w}: 選択肢/正解の形が不正")
                continue
            c = ca[0]
            if set(q["wrongChoiceExplanations"]) != {str(i) for i in range(4) if i != c}:
                errors.append(f"{w}: 誤答解説のキーが不整合")
            if q["domain"] != dom:
                errors.append(f"{w}: domain {q['domain']} がレッスンの {dom} と違う")
            if q["difficulty"] != 1 or "基礎" not in q["tags"]:
                errors.append(f"{w}: 難易度1・タグ「基礎」になっていない")
            if len(set(ch)) != 4:
                errors.append(f"{w}: 同じ選択肢がある")
            pos[c] += 1
            lens = [len(x) for x in ch]
            mx, mn = max(lens), min(lens)
            # 同点は按分して数える（同点を正解扱いにすると過大評価になる）
            if lens[c] == mx:
                longest_hit += 1 / lens.count(mx)
            if lens[c] == mn:
                shortest_hit += 1 / lens.count(mn)
            if lens[c] == mx and lens.count(mx) == 1 and mx - sorted(lens)[-2] >= 8:
                notes.append(f"{w}: 正解だけ目で分かるほど長い（{lens}）")
            if len(q["explanation"]) < 100:
                notes.append(f"{w}: 解説が短い（{len(q['explanation'])}字）")
            if leaks(ch[c], q["question"]):
                errors.append(f"{w}: 設問に正解がそのまま入っている")
            if leaks(ch[c], q["beginnerNote"]):
                errors.append(f"{w}: ヒントに正解がそのまま入っている")
            for e in existing.values():
                if difflib.SequenceMatcher(None, q["question"], e["question"]).ratio() > 0.85 \
                        and e["choices"][e["correctAnswers"][0]] == ch[c]:
                    notes.append(f"{w}: 既存 {e['id']} とほぼ同じ")
                    break
    for i, n in ids.items():
        if n > 1:
            errors.append(f"ID重複: {i}")

    n = len(all_new)
    print(f"基礎問題 {n}問（{len(new)}レッスン）")
    for lid, qs in new.items():
        print(f"  {lid:<7} {len(qs)}問")
    if n:
        print(f"一番長い選択肢を選ぶだけの正答率: {longest_hit / n:.1%}（目標25%前後）")
        print(f"一番短い選択肢を選ぶだけの正答率: {shortest_hit / n:.1%}")
        print("正解位置:", dict(sorted(pos.items())))
        print("解説の字数: 最小", min(len(q["explanation"]) for q in all_new),
              "/ 平均", sum(len(q["explanation"]) for q in all_new) // n)
    for x in notes:
        print("  注意", x)
    for x in errors:
        print("  エラー", x)
    if errors:
        sys.exit(1)

    if not apply:
        print("\n検査のみ（--apply で Resources に反映）")
        return

    kept = [q for q in questions if not q["id"].startswith("b-")]   # 再実行しても二重にならない
    kept += all_new
    for l in lessons:
        if l["id"] in new:
            l["basicQuizIds"] = [q["id"] for q in new[l["id"]]]
    json.dump(kept, open(os.path.join(RES, "questions.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(lessons, open(os.path.join(RES, "lessons.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n反映しました：問題 {len(kept)}問")


if __name__ == "__main__":
    main()
