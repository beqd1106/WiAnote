# -*- coding: utf-8 -*-
"""
ファクトチェック結果（design/term_out/*.json）を Resources/terms.json へ反映する。

  python design/apply_terms.py
"""
import json, os, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "Resources")
FIELDS = ("shortDescription", "beginnerExplanation", "useCase", "examPoint")


def main():
    terms = json.load(open(os.path.join(RES, "terms.json"), encoding="utf-8"))
    by_id = {t["id"]: t for t in terms}

    results = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "design", "term_out", "*.json"))):
        for r in json.load(open(f, encoding="utf-8")):
            results[r["id"]] = r

    verdicts = collections.Counter()
    changed, fixes = 0, []
    for tid, r in results.items():
        t = by_id.get(tid)
        if not t:
            print(f"  ! 未知のID {tid}")
            continue
        verdicts[r.get("verdict", "?")] += 1
        diff = []
        for k in FIELDS:
            v = r.get(k)
            if isinstance(v, str) and v.strip() and v != t[k]:
                diff.append(k)
                t[k] = v.strip()
        if diff:
            changed += 1
            fixes.append((t["term"], ",".join(diff), r.get("reason", "")))

    json.dump(terms, open(os.path.join(RES, "terms.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"検証結果 {len(results)}/{len(terms)}件： " +
          ", ".join(f"{k} {v}件" for k, v in verdicts.most_common()))
    print(f"実際に書き換えた用語: {changed}件\n")
    for term, fields, reason in fixes:
        print(f"  ■ {term}  [{fields}]")
        if reason:
            print(f"     {reason}")
    missing = [t['id'] for t in terms if t['id'] not in results]
    if missing:
        print(f"\n  未検証のまま: {len(missing)}件 {missing[:8]}")


if __name__ == "__main__":
    main()
