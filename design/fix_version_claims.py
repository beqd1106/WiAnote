# -*- coding: utf-8 -*-
"""
用語カードから「裏付けの無いバージョン断定」を取り除く。

WinActor Ver.7.6 操作マニュアル（965ページ）全文を検索したところ、
"Ver.7.5" という表記は1件も存在しない。にもかかわらず用語カードには
「Ver.7.5.0で追加」「Ver.7の新機能」といった断定があり、出典が無い。

検定はVer.7全体が対象で、どの小版で入った機能かは問われない。
教材側の方針（バージョン依存項目は断定しない）にも反するため、
マニュアルに書かれている「その機能が何をするものか」の説明に置き換える。

  python design/fix_version_claims.py
"""
import json, os, re

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Resources")

# 根拠：操作マニュアル p.777(4.4.9 Python実行) / p.862(4.9 UIオートメーションノード)
#       p.768(4.4.7 コマンド実行) / p.28(1.7.2 記録モードの種類)
PATCH = {
    "Python実行": {
        "shortDescription": "Pythonで書いたスクリプトをシナリオの中で実行するノード",
        "examPoint": "プロパティは「設定」「スクリプト」「注釈」の3タブ構成。"
                     "コマンド実行・スクリプト実行との役割の違いが問われる。",
    },
    "UI Automation": {
        "shortDescription": "アプリをGUIの要素レベルで操作する記録方式・ノード",
        "beginnerExplanation": "アプリのボタンや入力欄を「画面上の部品」として認識して操作する方式です。"
                               "記録モードを「UIオートメーション」に切り替えて記録すると、"
                               "クリック(UIA)などのノードが自動で置かれます。",
        "examPoint": "UI識別型の記録モード。座標に依存するエミュレーションモードや画像マッチングモードとの"
                     "違いが問われる。ユーザライブラリの「04_自動記録アクション」からも配置できる。",
    },
    "コマンド実行": {
        "examPoint": "指定したコマンドを実行し、その出力を変数に取得できる。"
                     "ファイル名のみを指定した場合はOSのPATHに従う。"
                     "スクリプト実行・Python実行と並ぶ、外部処理を呼ぶ系のノード。",
    },
    # 根拠：p.423（表3-53 比較演算子）。カードは「がtrue」「がfalse」を落としていた。
    "条件式": {
        "beginnerExplanation": "「この値がこうなら」を決める式です。比較演算子は12種類あり、"
                               "文字列として比べるものと数値として比べるものが分かれています。",
        "examPoint": "比較演算子は12種類。文字列＝「等しい／等しくない」、数値＝「＝≠＞＜≧≦」、"
                     "真偽＝「がtrue／がfalse」（値2は選択不可）、ほかに「等しい（曖昧）」と「正規表現」。",
    },
    # 根拠：p.89-90, p.183-184。拡張子まわりは出題されやすいので周辺事実まで入れる。
    "シナリオファイル（ums7）": {
        "examPoint": "通常のシナリオの拡張子は.ums7。開けるのは.ums7/.uss7/.wsb7/.ums6/.ums5で、"
                     "旧形式（.ums6/.ums5）やStoryboard形式（.wsb7）を編集して保存すると.ums7へ変換される。",
    },
}

FIELDS = ("shortDescription", "beginnerExplanation", "useCase", "examPoint")
VER = re.compile(r"Ver\.?\s?[\d]+(\.\d+)*")


def main():
    path = os.path.join(RES, "terms.json")
    terms = json.load(open(path, encoding="utf-8"))
    changed = 0
    for t in terms:
        p = PATCH.get(t["term"])
        if not p:
            continue
        for k, v in p.items():
            if t[k] != v:
                print(f"  {t['term']} [{k}]")
                print(f"    旧: {t[k]}")
                print(f"    新: {v}")
                t[k] = v
                changed += 1
    json.dump(terms, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    left = [(t["term"], k, t[k]) for t in terms for k in FIELDS if VER.search(t[k])]
    print(f"\n  書き換え {changed}箇所")
    if left:
        print(f"  まだバージョン表記が残っている箇所 {len(left)}件:")
        for term, k, v in left:
            print(f"    {term} [{k}] {v}")
    else:
        print("  裏付けの無いバージョン断定は残っていない")


if __name__ == "__main__":
    main()
