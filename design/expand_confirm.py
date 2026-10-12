"""確認問題を各レッスン15問（5問×A/B/C）にそろえる。
多い分はランダム問題プールへ戻し、足りない分はそのレッスンのランダム問題プール(drillQuizIds)から移す。
選び方：反復ドリル以外を優先 → 難易度2→3→1 → 既存の確認問題・選んだ問題と論点(service)と設問が似ていないもの。
使い方: python expand_confirm.py <Resourcesフォルダ> [--apply]
"""
import json, sys, os, difflib

TARGET = 15

def main():
    res = sys.argv[1]
    apply = "--apply" in sys.argv
    L = json.load(open(os.path.join(res, "lessons.json"), encoding="utf-8"))
    Q = {q["id"]: q for q in json.load(open(os.path.join(res, "questions.json"), encoding="utf-8"))}
    short = 0
    for l in L:
        quiz = [i for i in l["quizIds"] if i in Q]
        pool = [i for i in (l.get("drillQuizIds") or []) if i in Q and i not in quiz]
        need = TARGET - len(quiz)
        if need < 0:
            # 多すぎる分はランダム問題プールへ戻す（削除はしない）
            l["quizIds"] = quiz[:TARGET]
            l["drillQuizIds"] = quiz[TARGET:] + [i for i in (l.get("drillQuizIds") or []) if i not in quiz]
            continue
        if need == 0:
            continue
        picked = []
        def score(i):
            q = Q[i]
            drill = "ドリル" in q.get("tags", [])
            diff = {2: 0, 3: 1, 1: 2}.get(q.get("difficulty"), 3)
            chosen = [Q[x] for x in quiz + picked]
            sim = max((difflib.SequenceMatcher(None, q["question"], c["question"]).ratio() for c in chosen), default=0)
            same_service = sum(1 for c in chosen if c.get("service") == q.get("service"))
            return (drill, sim > 0.7, diff, same_service, sim)
        for _ in range(min(need, len(pool))):
            best = min((i for i in pool if i not in picked), key=score)
            picked.append(best)
        l["quizIds"] = quiz + picked
        l["drillQuizIds"] = [i for i in (l.get("drillQuizIds") or []) if i not in picked]
        if len(l["quizIds"]) < TARGET:
            short += TARGET - len(l["quizIds"])
            print(f"  不足 {l['id']}: 確認{len(l['quizIds'])}問（あと{TARGET - len(l['quizIds'])}問 新規作成が必要）")
    print("確認問題の数:", sorted({len(l["quizIds"]) for l in L}), "/ 不足合計", short)
    if apply:
        json.dump(L, open(os.path.join(res, "lessons.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("反映しました")

if __name__ == "__main__":
    main()
