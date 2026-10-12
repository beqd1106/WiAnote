"""今回作った基礎問題・確認問題を検査し、--apply で Resources に反映する。
使い方: python import_new.py <アプリのフォルダ> <作業フォルダ(tasks.json と out/)> [--apply]
- 基礎(b-)は lesson.basicQuizIds の末尾へ、確認(qc-)は lesson.quizIds の末尾へ足す（5問ずつ A/B/C の C 側に入る）。
- basis（作成時の根拠メモ）はアプリに入れない。
"""
import json, os, sys, glob, difflib, collections, re

KEYS = ["id", "question", "choices", "correctAnswers", "explanation",
        "wrongChoiceExplanations", "domain", "service", "difficulty", "tags", "beginnerNote"]

def norm(t):
    return re.sub(r"[\s、。・「」（）()]", "", t)

def leaks(answer, text):
    a = norm(answer)
    return len(a) >= 4 and a in norm(text)

def main():
    app, ws = sys.argv[1], sys.argv[2]
    apply = "--apply" in sys.argv
    res = os.path.join(app, "Resources")
    questions = json.load(open(os.path.join(res, "questions.json"), encoding="utf-8"))
    lessons = json.load(open(os.path.join(res, "lessons.json"), encoding="utf-8"))
    tasks = {t["lesson"]: t for t in json.load(open(os.path.join(ws, "tasks.json"), encoding="utf-8"))}
    byid = {q["id"]: q for q in questions}
    lesson_by_id = {l["id"]: l for l in lessons}

    errors, notes, new = [], [], {}
    for lid, t in tasks.items():
        path = os.path.join(ws, "out", lid + ".json")
        want = t["basic_ids"] + t["confirm_ids"]
        if not want:
            continue
        if not os.path.exists(path):
            errors.append(f"{lid}: 出力なし（{len(want)}問 未作成）")
            continue
        try:
            qs = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            errors.append(f"{lid}: JSONが読めない {e}")
            continue
        got = [q.get("id") for q in qs]
        if sorted(got) != sorted(want):
            errors.append(f"{lid}: id不一致 不足{sorted(set(want)-set(got))} 余分{sorted(set(got)-set(want))}")
        new[lid] = [q for q in qs if q.get("id") in want]

    all_new = [q for qs in new.values() for q in qs]
    pos = collections.Counter()
    longest = shortest = 0.0
    for lid, qs in new.items():
        dom = lesson_by_id[lid]["domain"]
        for q in qs:
            w = q.get("id", "?")
            miss = [k for k in KEYS if k not in q]
            if miss:
                errors.append(f"{w}: キー不足 {miss}"); continue
            ch, ca = q["choices"], q["correctAnswers"]
            if len(ch) != 4 or len(ca) != 1 or not (0 <= ca[0] < 4):
                errors.append(f"{w}: 選択肢/正解の形が不正"); continue
            c = ca[0]
            if set(q["wrongChoiceExplanations"]) != {str(i) for i in range(4) if i != c}:
                errors.append(f"{w}: 誤答解説のキーが不整合")
            if q["domain"] != dom:
                errors.append(f"{w}: domain {q['domain']} != {dom}")
            is_basic = w.startswith("b-")
            if is_basic and (q["difficulty"] != 1 or "基礎" not in q["tags"]):
                errors.append(f"{w}: 基礎なのに難易度1/タグ基礎でない")
            if not is_basic and "基礎" in q["tags"]:
                errors.append(f"{w}: 確認問題にタグ基礎")
            if len(set(ch)) != 4:
                errors.append(f"{w}: 同じ選択肢がある")
            pos[c] += 1
            lens = [len(x) for x in ch]
            mx, mn = max(lens), min(lens)
            if lens[c] == mx: longest += 1 / lens.count(mx)
            if lens[c] == mn: shortest += 1 / lens.count(mn)
            if lens[c] == mx and lens.count(mx) == 1 and mx - sorted(lens)[-2] >= 8:
                notes.append(f"{w}: 正解だけ目立って長い {lens}")
            if len(q["explanation"]) < 100:
                notes.append(f"{w}: 解説が短い（{len(q['explanation'])}字）")
            if leaks(ch[c], q["question"]):
                errors.append(f"{w}: 設問に正解がそのまま入っている")
            if leaks(ch[c], q["beginnerNote"]):
                errors.append(f"{w}: ヒントに正解がそのまま入っている")
    # 重複（既存全問・新規どうし）
    pool = [(q["id"], q) for q in questions] + [(q["id"], q) for q in all_new]
    for q in all_new:
        a = q["choices"][q["correctAnswers"][0]]
        for oid, o in pool:
            if oid == q["id"]:
                continue
            r = difflib.SequenceMatcher(None, q["question"], o["question"]).ratio()
            if r > 0.8 or (r > 0.55 and a in [o["choices"][i] for i in o["correctAnswers"]]):
                notes.append(f"{q['id']}: {oid} と似ている（{r:.2f}）")
                break
    # 字数稼ぎの決まり文句（同じ最後の一文が3問以上）
    last = collections.Counter(re.split(r"(?<=。)", q["explanation"].strip())[-2 if q["explanation"].strip().endswith("。") else -1] for q in all_new if "explanation" in q)
    for sent, k in last.items():
        if k >= 3 and len(sent) < 40:
            notes.append(f"解説の最後が同じ決まり文句 {k}問: {sent}")
    for i, n in collections.Counter(q["id"] for q in all_new).items():
        if n > 1: errors.append(f"ID重複 {i}")
    for q in all_new:
        if q["id"] in byid: errors.append(f"既存IDと衝突 {q['id']}")

    n = len(all_new)
    print(f"新規 {n}問（基礎{sum(q['id'].startswith('b-') for q in all_new)}・確認{sum(q['id'].startswith('qc-') for q in all_new)}） / {len(new)}レッスン")
    if n:
        print(f"一番長い選択肢を選ぶだけ: {longest/n:.1%} / 一番短い: {shortest/n:.1%}（目標25%前後）")
        print("正解位置:", dict(sorted(pos.items())))
        print("解説 最小", min(len(q["explanation"]) for q in all_new), "字 / 平均", sum(len(q["explanation"]) for q in all_new)//n)
    for x in notes: print("  注意", x)
    for x in errors: print("  エラー", x)
    if errors:
        sys.exit(1)
    if not apply:
        print("検査のみ（--apply で反映）"); return

    for q in all_new:
        q.pop("basis", None)
    questions += all_new
    for lid, qs in new.items():
        l = lesson_by_id[lid]
        b = sorted(q["id"] for q in qs if q["id"].startswith("b-"))
        c = sorted(q["id"] for q in qs if q["id"].startswith("qc-"))
        l["basicQuizIds"] = (l.get("basicQuizIds") or []) + b
        l["quizIds"] = l["quizIds"] + c
    json.dump(questions, open(os.path.join(res, "questions.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(lessons, open(os.path.join(res, "lessons.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("反映しました: 問題", len(questions))

if __name__ == "__main__":
    main()
