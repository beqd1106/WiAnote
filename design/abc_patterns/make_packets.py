"""レッスンごとのパケット(pk/<lesson>.md)と作業一覧(tasks.json)を作る。
使い方: python make_packets.py <Resourcesフォルダ> <作業フォルダ>"""
import json, os, sys
res, ws = sys.argv[1], sys.argv[2]
os.makedirs(os.path.join(ws, "pk"), exist_ok=True)
os.makedirs(os.path.join(ws, "out"), exist_ok=True)
Q = {q["id"]: q for q in json.load(open(os.path.join(res, "questions.json"), encoding="utf-8"))}
L = json.load(open(os.path.join(res, "lessons.json"), encoding="utf-8"))
tasks = []
for l in L:
    suf = l["id"][2:]
    basic = [i for i in (l.get("basicQuizIds") or []) if i in Q]
    nb, nc = 15 - len(basic), max(0, 15 - len(l["quizIds"]))
    t = {"lesson": l["id"], "basic": nb, "confirm": nc,
         "basic_ids": [f"b-{suf}-{n:02d}" for n in range(len(basic) + 1, 16)],
         "confirm_ids": [f"qc-{suf}-{n:02d}" for n in range(1, nc + 1)]}
    tasks.append(t)
    out = [f"# パケット {l['id']}「{l['title']}」 domain={l['domain']}",
           f"\n## 今回作る問題",
           f"- 基礎問題 {nb}問: id {', '.join(t['basic_ids']) or 'なし'}",
           f"- 確認問題 {nc}問: id {', '.join(t['confirm_ids']) or 'なし'}",
           "\n## レッスン本文", l["summary"]]
    for s in l["sections"]:
        out += [f"### {s['heading']}", s["body"]]
    out.append("\n## 既存の基礎問題（重複禁止・形式と難易度の手本）")
    for i in basic:
        q = Q[i]
        out.append(f"- {i} [{q.get('service','')}] {q['question']} → {q['choices'][q['correctAnswers'][0]]}")
    out.append("\n## 既存の確認問題（重複禁止・確認問題の難易度の手本）")
    for i in l["quizIds"]:
        q = Q.get(i)
        if q:
            out.append(f"- [{q.get('service','')}] {q['question']} → {' / '.join(q['choices'][c] for c in q['correctAnswers'])}")
    out.append("\n## 既存のランダム問題・腕試し（重複禁止）")
    for i in (l.get("drillQuizIds") or []) + (l.get("challengeQuizIds") or []):
        q = Q.get(i)
        if q:
            out.append(f"- [{q.get('service','')}] {q['question']} → {' / '.join(q['choices'][c] for c in q['correctAnswers'])}")
    open(os.path.join(ws, "pk", l["id"] + ".md"), "w", encoding="utf-8").write("\n".join(out))
json.dump(tasks, open(os.path.join(ws, "tasks.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(tasks), "lessons; basic", sum(t["basic"] for t in tasks), "confirm", sum(t["confirm"] for t in tasks))
