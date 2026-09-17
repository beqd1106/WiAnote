# -*- coding: utf-8 -*-
"""
用語カード（terms.json）をマニュアルと突き合わせるための検証パッケージを作る。

各用語について、マニュアル全文から「その用語が説明されていそうな箇所」を
見出し優先で拾い、カード本文と並べて出力する。

  python design/make_term_check.py <op_manual.txt> [出力先ディレクトリ]
"""
import json, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "Resources")
MAX_CHARS = 5000          # 1用語あたりに添えるマニュアル本文の上限


def load_pages(path):
    txt = open(path, encoding="utf-8").read()
    return {int(n): b for n, b in re.findall(r"<<<PAGE (\d+)>>>\n(.*?)(?=<<<PAGE |\Z)", txt, re.S)}


def norm(s):
    """全角/半角スペースや中黒のゆれを吸収して比較用に正規化"""
    return re.sub(r"[\s・／/]", "", s)


def find_pages(term, pages):
    """用語が登場するページを、出現回数の多い順に返す"""
    key = norm(term)
    if len(key) < 2:
        return []
    hits = [(p, norm(b).count(key)) for p, b in pages.items()]
    hits = [(p, n) for p, n in hits if n > 0]
    hits.sort(key=lambda x: (-x[1], x[0]))
    return hits


def main():
    manual = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "design", "term_check")
    os.makedirs(outdir, exist_ok=True)
    pages = load_pages(manual)
    terms = json.load(open(os.path.join(RES, "terms.json"), encoding="utf-8"))

    items, missing = [], []
    for t in terms:
        hits = find_pages(t["term"], pages)
        buf, used = [], []
        for p, _ in hits[:4]:
            body = pages[p].strip()
            if sum(len(x) for x in buf) + len(body) > MAX_CHARS:
                break
            buf.append(f"----- p.{p} -----\n{body}")
            used.append(p)
        if not buf:
            missing.append(t["term"])
        items.append({
            "id": t["id"],
            "term": t["term"],
            "domain": t["domain"],
            "difficulty": t["difficulty"],
            "shortDescription": t["shortDescription"],
            "beginnerExplanation": t["beginnerExplanation"],
            "useCase": t["useCase"],
            "examPoint": t["examPoint"],
            "relatedServices": t["relatedServices"],
            "manualPages": used,
            "manualExcerpt": "\n".join(buf),
        })

    # 4分割して並列で検証できるようにする
    n = 4
    size = (len(items) + n - 1) // n
    for i in range(n):
        part = items[i * size:(i + 1) * size]
        if not part:
            continue
        path = os.path.join(outdir, f"T{i+1}.json")
        json.dump(part, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"  T{i+1}: {len(part)}件  本文 {sum(len(x['manualExcerpt']) for x in part):,}字")

    if missing:
        print(f"\n  マニュアル本文が見つからなかった用語 {len(missing)}件: {', '.join(missing)}")
    print(f"\n合計 {len(items)}件 → {outdir}")


if __name__ == "__main__":
    main()
