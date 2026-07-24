# -*- coding: utf-8 -*-
"""
WiAnote（RPA技術者検定 アソシエイト／WinActor Ver.7）学習コンテンツ生成スクリプト。
公式試験情報（3分野・全50問・60分・原則正答率7割合格）に紐づけて
問題(questions)・用語(terms)・レッスン(lessons)・頻出機能一覧(services)・用語集(glossary)を生成する。

方針：
- 合格に必要な各分野の主要キーワードを取りこぼさず問題化する（量も質も）。
- 問題・解説はすべてオリジナル。公式問題・市販教材の転載はしない。
- domain rawValue は ExamDomain と一致：overview / features / scenario
- 問題は design/batch_*.json、用語は terms_extra*.json、用語集は glossary_source*.json、
  反復ドリルは drill_*.json から取り込む。レッスンの quizIds/drillQuizIds は分野で自動割当。
- WinActor は株式会社NTTデータの登録商標。本アプリは非公式の学習支援。
"""
import json, os, glob, random
from collections import Counter

BASE = os.path.join(os.path.dirname(__file__), "..", "Resources")
DESIGN = os.path.dirname(__file__)
random.seed(42)

VALID = {"overview", "features", "scenario"}

def balance_positions(questions):
    """正解位置が①に偏らないよう選択肢をシャッフルして均等化。誤答解説キーも付け替える。"""
    counter = 0
    for q in questions:
        n = len(q["choices"]); correct = list(q["correctAnswers"])
        if len(correct) == 1:
            target = counter % n; counter += 1; src = correct[0]
            others = [i for i in range(n) if i != src]; random.shuffle(others)
            new_order, oi = [], 0
            for pos in range(n):
                if pos == target: new_order.append(src)
                else: new_order.append(others[oi]); oi += 1
        else:
            new_order = list(range(n)); random.shuffle(new_order)
        o2n = {old: pos for pos, old in enumerate(new_order)}
        q["choices"] = [q["choices"][old] for old in new_order]
        q["correctAnswers"] = sorted(o2n[c] for c in correct)
        q["wrongChoiceExplanations"] = {str(o2n[int(k)]): v for k, v in q["wrongChoiceExplanations"].items()}
    return questions

# ============================================================
# レッスン（各分野3小テーマ＝計9本）
# 確認問題とドリルは lessonTheme（新規問題）または service（既存問題）で自動割当。
# ============================================================
def SL(id, domain, theme, title, minutes, summary, services, sections):
    return {"id": id, "domain": domain, "theme": theme, "title": title, "minutes": minutes,
            "summary": summary, "services": services, "sections": sections}

SUBLESSONS = [
 # ------- WinActorの概要 -------
 SL("l-ov1", "overview", "RPAとWinActorの基礎", "RPAとWinActorの基礎", 11,
    "RPAとは何か、WinActorがどんなツールか、どんな業務を自動化できるかを押さえます。",
    ["RPAとは","WinActorとは","WinActorの特徴","純国産","NTTデータ","RPAの適用業務",
     "RPAとマクロの違い","RPAの三段階(クラス)","WinDirector"],
    [{"heading":"RPAとは","body":"RPA（Robotic Process Automation）は、これまで人がパソコン上で行ってきた定型的な操作を、ソフトウェアのロボットに代行させて自動化する仕組みです。キーボード入力・マウス操作・アプリ間のデータ転記など、ルールが決まっていて繰り返し発生する作業を得意とします。RPAの自動化レベルは、定型業務を自動化するRPA（クラス1）、一部にAIを組み合わせて非定型業務も扱うEPA（クラス2）、高度な自律化を目指すCA（クラス3）の3段階で語られます。"},
     {"heading":"WinActorとは","body":"WinActorは、NTTデータが開発・提供する純国産のRPAツールです。メニューや解説がすべて日本語で、プログラミングの知識がなくても操作を記録・編集してシナリオ（自動化の手順書）を作れるのが特徴です。Windows上で動作し、Excelやブラウザ、業務システムなど、人が画面上で操作できるアプリケーションを幅広く自動化できます。多数のロボットを一元管理・実行制御する上位製品としてWinDirectorがあります。"},
     {"heading":"得意なこと・苦手なこと","body":"WinActorは、手順が定まった繰り返し作業（データ入力・転記・集計・帳票作成・定期的なメール送信など）を正確に高速でこなすのが得意です。一方で、その都度人の判断が必要な業務や、画面レイアウトが頻繁に変わる操作は苦手で、シナリオの作り込みや保守が必要になります。Excelのマクロ（VBA）が主にOffice内の自動化に限られるのに対し、RPAは複数の異なるアプリをまたいだ操作を自動化できる点が違いです。"}]),
 SL("l-ov2", "overview", "エディションとライセンス", "エディションとライセンス", 11,
    "フル機能版と実行版の違い、ライセンス方式、動作環境を押さえます。",
    ["フル機能版","実行版","エディション","ノードロックライセンス","フローティングライセンス",
     "動作環境","ライセンス","評価版"],
    [{"heading":"フル機能版と実行版","body":"WinActorには主にフル機能版と実行版があります。フル機能版は、シナリオの作成・編集・実行のすべてが行える開発用のエディションです。実行版は、作成済みのシナリオを読み込んで実行することに特化しており、記録や編集はできず、部分実行（一部のノードだけの実行）もできません。開発担当者はフル機能版、現場で動かすだけの端末は実行版、という使い分けが基本になります。"},
     {"heading":"ライセンス方式","body":"ライセンスの割り当て方には、ノードロック方式とフローティング方式があります。ノードロック方式は、ライセンスをインストールした特定の端末でのみWinActorを利用できる方式です。フローティング方式は、ライセンスをサーバーで管理し、同時に利用できる数の範囲内であれば複数の端末で使い回せる方式で、多人数・多拠点での利用に向きます。"},
     {"heading":"動作環境と評価版","body":"WinActorはWindows上で動作するデスクトップ型のRPAで、対応OSやメモリなどの動作環境が定められています。導入前に試せる評価版（体験版）も用意されており、機能や期間に制限を設けたうえで実際の操作を確認できます。実運用では、ライセンス数や端末構成に応じてフル機能版・実行版とライセンス方式を組み合わせて設計します。"}]),
 SL("l-ov3", "overview", "画面構成と部品", "画面構成と部品", 10,
    "WinActorのメイン画面の各エリアと、シナリオを組み立てる部品（ノード・ライブラリ）を押さえます。",
    ["メイン画面","フローチャート","ノード","ライブラリ","パレット","プロパティ",
     "変数一覧","データ一覧","サブシナリオ","メインウィンドウ"],
    [{"heading":"メイン画面の構成","body":"WinActorのメインウィンドウは、メニューバー・ツールバー（実行や記録のボタン）・パレット（部品置き場）・シナリオ編集エリア（フローチャート）・プロパティ（選択した部品の詳細設定）・変数一覧やデータ一覧・ステータスバーなどで構成されます。基本操作は、パレットから部品をフローチャートへドラッグ＆ドロップして手順を組み立てることです。"},
     {"heading":"ノードとライブラリ","body":"シナリオを構成する部品には、ノードとライブラリがあります。ノードは分岐・繰り返し・待機など、シナリオの骨組みとなる基本的な操作の単位です。ライブラリは、ノードだけでは実現しにくい、より細かく具体的な操作（Excelの読み書き、ウィンドウ操作、文字列処理など）をまとめた部品です。両者を組み合わせて自動化の流れを作ります。"},
     {"heading":"変数一覧・データ一覧・サブシナリオ","body":"変数一覧では、シナリオ内で値を出し入れする箱である変数を管理します。データ一覧は、CSVなどの表形式データを取り込んで1行ずつ処理するのに使います。よく使う一連の手順は、サブシナリオとして部品化し、メインのシナリオから呼び出して再利用できます。これらを使い分けることで、見通しがよく保守しやすいシナリオになります。"}]),
 # ------- WinActorの機能 -------
 SL("l-ft1", "features", "自動記録と操作の記録方式", "自動記録と操作の記録方式", 12,
    "操作を記録する3つの方式（自動記録・画像マッチング・エミュレーション）の仕組みと使い分けを押さえます。",
    ["自動記録","記録方式","画像マッチング","エミュレーション","IEモード","ブラウザ操作",
     "座標指定","ウィンドウ識別","記録モード"],
    [{"heading":"自動記録モード","body":"自動記録は、画面上の部品（ボタンや入力欄）を内部的な情報から識別して操作を記録する方式です。ブラウザやIEではHTMLの構造を読み取って対象を特定するため、ウィンドウの位置が多少ずれても正しく操作できるのが利点です。対象を確実に特定できるため、安定して動くシナリオを作りやすい基本の方式です。"},
     {"heading":"画像マッチング","body":"画像マッチングは、あらかじめ記録しておいた画面の画像と実行時の画面を照合し、一致した場所を操作する方式です。内部情報から部品を識別できないアプリ（特殊な画面やリモート接続先など）でも操作できますが、画面の解像度・拡大率・デザインが変わると一致しなくなり、動作が不安定になりやすい点に注意します。"},
     {"heading":"エミュレーションモード","body":"エミュレーションは、キーボード入力やマウス操作そのもの（座標のクリックやキー送信）を記録・再現する方式です。汎用性は高いものの、画面の配置に依存するため、ウィンドウの位置やサイズが変わるとずれてしまいます。3つの方式は、対象アプリの性質に応じて使い分け、安定性の高い自動記録を優先し、難しい部分だけ画像マッチングやエミュレーションで補うのが定石です。"}]),
 SL("l-ft2", "features", "主要ノード", "主要ノード", 12,
    "シナリオの骨組みを作る基本ノード（分岐・繰り返し・待機・変数値設定・グループなど）を押さえます。",
    ["分岐","条件分岐","繰り返し","待機","変数値設定","グループ","コメント","例外処理ノード",
     "ノードの種類","IF分岐","ウィンドウ状態取得"],
    [{"heading":"分岐と繰り返し","body":"分岐（条件分岐・IF）は、条件が成り立つかどうかで処理の流れを2方向に分けるノードです。繰り返しは、指定した回数や条件が満たされる間、同じ処理を反復するノードで、データ一覧の各行を順番に処理する場合などに使います。これらを組み合わせて、状況に応じた自動化の流れを表現します。"},
     {"heading":"待機と変数の操作","body":"待機ノードは、画面の表示や処理の完了を待つために一定時間・一定条件まで処理を止めるノードです。アプリの反応より先に次の操作へ進んで失敗するのを防ぐ、安定動作の要になります。変数値設定は、変数に値を代入・更新するノードで、計算結果やフラグ、繰り返しの回数などを保持するのに使います。"},
     {"heading":"グループ・コメントで整理","body":"グループノードは、複数のノードを1つのまとまりとして束ね、フローチャートを見やすく整理するのに使います。コメントは処理の意図をメモとして残す部品で、後から見返したり他の人が保守したりするときに役立ちます。ウィンドウの状態を取得・確認するノードなども活用し、読みやすく壊れにくいシナリオを目指します。"}]),
 SL("l-ft3", "features", "変数・データ一覧・ライブラリ", "変数・データ一覧・ライブラリ", 12,
    "変数とデータ一覧の使い方、ライブラリによるExcel・ブラウザ操作、対応アプリを押さえます。",
    ["変数","データ一覧","ライブラリ","Excel操作","エクセル","ファイル操作","文字列操作",
     "対応アプリケーション","Python実行","CSV読み込み","値の受け渡し"],
    [{"heading":"変数とデータ一覧","body":"変数は値を一時的にしまう箱で、画面から取得した文字列や計算結果を入れて後の処理で使います。データ一覧は、CSVやExcelの表を取り込み、1行ずつ変数に読み込んで繰り返し処理するための表です。『データ一覧の行数だけ繰り返し、各行の値を変数に入れて処理する』という形が、大量データ処理の基本パターンになります。"},
     {"heading":"ライブラリでできること","body":"ライブラリは、細かな具体的操作をまとめた部品群です。Excelの読み書き・シート操作、ファイルやフォルダの操作、文字列の加工（分割・置換・切り出し）、ウィンドウ操作、メール送信など、多くの部品が標準で用意されています。プロパティで対象ファイルや値、格納先の変数を設定して使います。Ver.7.5.0以降ではPython実行ノードも加わり、より柔軟な処理が可能になりました。"},
     {"heading":"対応アプリと値の受け渡し","body":"WinActorは、Excelなどのオフィスソフト、ブラウザ、業務システムなど、人が画面で操作できる幅広いアプリを自動化できます。処理の結果は変数を通じてノード間・ライブラリ間で受け渡します。どのライブラリの出力をどの変数に入れ、次のどの部品で使うかを意識して設計することが、正しく動くシナリオ作りのポイントです。"}]),
 # ------- WinActorのシナリオ -------
 SL("l-sc1", "scenario", "シナリオ作成の基本", "シナリオ作成の基本", 12,
    "シナリオの考え方、部品の配置、実行・停止・ステップ実行など基本操作を押さえます。",
    ["シナリオとは","シナリオ作成","シナリオ実行","ステップ実行","一時停止","停止","部分実行",
     "シナリオ設計","フロー設計","保存"],
    [{"heading":"シナリオとは","body":"シナリオは、自動化する作業の手順をフローチャートの形でまとめたものです。人が行う作業を『どのアプリで・何を・どの順番で』行うかに分解し、その一つひとつをノードやライブラリに置き換えて並べていきます。作る前に作業の流れを紙などで整理しておくと、迷わず組み立てられます。"},
     {"heading":"部品を並べて組み立てる","body":"パレットからノードやライブラリをフローチャートへドラッグ＆ドロップし、上から下へ処理の順に並べます。各部品はプロパティで対象や値、格納先の変数を設定します。自動記録で大枠を作ってから、分岐・繰り返し・待機などのノードを足して仕上げていく作り方が効率的です。作成したシナリオはファイルとして保存します。"},
     {"heading":"実行・停止の操作","body":"完成したシナリオは、実行ボタン（三角のボタン）で先頭から動かします。動作を確認しながら1ノードずつ進めるステップ実行、途中で止める一時停止・停止も使えます。フル機能版では特定の範囲だけ動かす部分実行が可能ですが、実行版では部分実行はできません。少しずつ実行して意図どおり動くか確認しながら作るのがコツです。"}]),
 SL("l-sc2", "scenario", "分岐・繰り返しの組み立て", "分岐・繰り返しの組み立て", 13,
    "条件分岐と繰り返しを使った処理の組み立て、データ一覧のループ処理を押さえます。",
    ["条件分岐の組み立て","繰り返しの組み立て","データ一覧ループ","フラグ","カウンタ",
     "ループ条件","分岐条件","繰り返し条件","エラー時分岐"],
    [{"heading":"条件で流れを分ける","body":"条件分岐は、変数の値や画面の状態を条件に、処理を振り分けるときに使います。たとえば『取得した金額が0より大きければ登録処理、そうでなければスキップ』のように、成立時と不成立時で別の流れに進めます。条件の判定には変数を使うことが多く、事前に必要な値を変数へ取り込んでおきます。"},
     {"heading":"繰り返しで大量処理","body":"繰り返しは、同じ処理を何度も行うときに使います。回数を決めて繰り返す方法と、条件が満たされる間だけ繰り返す方法があります。繰り返しの回数を数えるカウンタ変数や、状態を表すフラグ変数を組み合わせると、複雑な制御も表現できます。"},
     {"heading":"データ一覧を1行ずつ処理","body":"実務で多いのが、データ一覧に読み込んだ表を1行ずつ処理するパターンです。『データ一覧の行数だけ繰り返す』ようにして、各回で現在行の値を変数に取り出し、入力や登録を行います。処理が終わったら次の行へ進みます。途中でエラーが起きた行だけ別処理へ分岐させるなど、分岐と繰り返しの組み合わせで実用的なシナリオになります。"}]),
 SL("l-sc3", "scenario", "デバッグ・例外処理・保守", "デバッグ・例外処理・保守", 13,
    "不具合の切り分け、例外処理によるエラー対応、保守しやすいシナリオの作り方を押さえます。",
    ["デバッグ","例外処理","エラー処理","ログ","トライキャッチ","保守性","ブレークポイント",
     "エラー対応","シナリオの保守","スクリーンショット取得"],
    [{"heading":"デバッグで不具合を切り分ける","body":"思いどおりに動かないときは、ステップ実行で1ノードずつ動かし、どこで止まるか・変数にどんな値が入っているかを確認して原因を切り分けます。特定の位置で処理を止めるブレークポイントや、実行の記録が残るログも役立ちます。エラー発生時に画面のスクリーンショットを残すようにしておくと、後から原因を追いやすくなります。"},
     {"heading":"例外処理でエラーに備える","body":"自動化では、対象アプリの反応が遅い・想定外の画面が出るなど、エラーはつきものです。例外処理は、エラーが起きても処理全体を止めず、あらかじめ決めた対応（再試行・スキップ・通知など）へ流すための仕組みです。待機ノードで表示を待つ、想定外時は分岐で安全に終了する、といった備えを入れておくと安定します。"},
     {"heading":"保守しやすい作り方","body":"シナリオは作って終わりではなく、業務や画面の変化に合わせて直し続けるものです。グループやコメントで処理の意図を分かりやすくし、繰り返し使う部分はサブシナリオに分けて再利用性を高めます。変数名を分かりやすく付ける、値をシナリオ内に直接書かず変数やデータ一覧で管理する、といった工夫が、後からの修正を楽にします。"}]),
]

# ============================================================
# 頻出機能・ノード一覧（旧services＝AWSServiceItem を流用）
# ============================================================
def S(id, name, category, oneLiner, domain):
    return {"id": id, "name": name, "category": category, "oneLiner": oneLiner, "domain": domain}

services = [
 S("s-rpa","RPA","概要","定型的なPC操作をソフトのロボットに代行させる自動化の仕組み。","overview"),
 S("s-winactor","WinActor","概要","NTTデータ製の純国産RPAツール。日本語で操作を記録・編集できる。","overview"),
 S("s-windirector","WinDirector","概要","複数のWinActorロボットを一元管理・実行制御する上位製品。","overview"),
 S("s-full","フル機能版","エディション","作成・編集・実行のすべてが行える開発用エディション。","overview"),
 S("s-runtime","実行版","エディション","作成済みシナリオの実行に特化。記録・編集・部分実行は不可。","overview"),
 S("s-nodelock","ノードロックライセンス","ライセンス","インストールした特定端末でのみ利用できる方式。","overview"),
 S("s-floating","フローティングライセンス","ライセンス","同時利用数の範囲で複数端末が使い回せる方式。","overview"),
 S("s-node","ノード","部品","分岐・繰り返し・待機などシナリオの骨組みとなる基本部品。","overview"),
 S("s-library","ライブラリ","部品","Excel操作や文字列処理など細かな操作をまとめた部品。","features"),
 S("s-autorecord","自動記録","記録方式","部品を内部情報で識別して操作を記録。安定して動く基本方式。","features"),
 S("s-imagematch","画像マッチング","記録方式","記録した画像と画面を照合して操作。画面変化に弱い。","features"),
 S("s-emulation","エミュレーション","記録方式","キー・マウス操作そのものを記録。座標依存でずれやすい。","features"),
 S("s-branch","分岐","ノード","条件の成否で処理の流れを2方向に分けるノード。","features"),
 S("s-loop","繰り返し","ノード","回数や条件が満たされる間、同じ処理を反復するノード。","features"),
 S("s-wait","待機","ノード","画面表示や処理完了を待って処理を止める。安定動作の要。","features"),
 S("s-setvar","変数値設定","ノード","変数に値を代入・更新するノード。","features"),
 S("s-variable","変数","データ","値を一時的にしまう箱。ノード間で値を受け渡す。","features"),
 S("s-datalist","データ一覧","データ","CSV等の表を取り込み1行ずつ処理するための表。","features"),
 S("s-scenario","シナリオ","シナリオ","自動化の手順をフローチャートでまとめたもの。","scenario"),
 S("s-stepexec","ステップ実行","実行","1ノードずつ動かして動作や変数を確認する実行方法。","scenario"),
 S("s-exception","例外処理","シナリオ","エラー時も止めず、決めた対応へ流す仕組み。","scenario"),
 S("s-subscenario","サブシナリオ","シナリオ","一連の手順を部品化し呼び出して再利用する仕組み。","scenario"),
]

# ============================================================
# 取り込み・組み立て
# ============================================================
questions = []
for bf in sorted(glob.glob(os.path.join(DESIGN, "batch_*.json"))):
    b = json.load(open(bf, encoding="utf-8")); questions.extend(b)
    print(f"merged {os.path.basename(bf)}: +{len(b)}")

# 反復ドリル（tag「ドリル」・模試除外）
for df in sorted(glob.glob(os.path.join(DESIGN, "drill_*.json"))):
    ds = json.load(open(df, encoding="utf-8"))
    for q in ds:
        if "ドリル" not in q.get("tags", []): q.setdefault("tags", []).append("ドリル")
    questions.extend(ds); print(f"merged {os.path.basename(df)}: +{len(ds)} (ドリル)")

# ------------------------------------------------------------
# レッスン割当：新規問題は lessonTheme、既存問題は service で小レッスンへ。
# 本問が1問でも割当漏れするとエラー（ドリルは同分野内でラウンドロビン）。
# ------------------------------------------------------------
def build_lessons(all_qs):
    from collections import defaultdict
    main = [q for q in all_qs if "ドリル" not in q.get("tags", [])]
    drills = [q for q in all_qs if "ドリル" in q.get("tags", [])]
    dom_subs = defaultdict(list)
    for sl in SUBLESSONS:
        sl["_quiz"], sl["_drill"] = [], []
        dom_subs[sl["domain"]].append(sl)

    def find(q):
        subs = dom_subs.get(q["domain"], [])
        theme = q.get("lessonTheme")
        if theme:
            hit = next((sl for sl in subs if sl["theme"] == theme), None)
            if hit is None:
                raise SystemExit(f'{q["id"]} の lessonTheme「{theme}」が {q["domain"]} に存在しない')
            return hit
        return next((sl for sl in subs if q.get("service") in sl["services"]), None)

    unmapped = []
    for q in main:
        sl = find(q)
        if sl is None:
            unmapped.append((q["id"], q["domain"], q.get("service")))
        else:
            sl["_quiz"].append(q["id"])
    if unmapped:
        print("=== レッスン未割当の本問 ===")
        for u in unmapped[:30]: print("  -", u)
        raise SystemExit(f"未割当 {len(unmapped)}件（SUBLESSONSのservicesに追加が必要）")

    rr = defaultdict(int)
    for dq in drills:
        subs = dom_subs.get(dq["domain"], [])
        if not subs: continue
        target = find(dq)
        if target is None:
            target = subs[rr[dq["domain"]] % len(subs)]; rr[dq["domain"]] += 1
        target["_drill"].append(dq["id"])

    out = []
    for sl in SUBLESSONS:
        out.append({"id": sl["id"], "title": sl["title"], "domain": sl["domain"],
                    "estimatedMinutes": sl["minutes"], "summary": sl["summary"],
                    "sections": sl["sections"], "quizIds": sl["_quiz"],
                    "challengeQuizIds": None,
                    "drillQuizIds": sl["_drill"] if sl["_drill"] else None})
    return out

lessons = build_lessons(questions)
print("レッスン:", len(lessons), "本／quiz計", sum(len(l["quizIds"]) for l in lessons),
      "／drill計", sum(len(l["drillQuizIds"] or []) for l in lessons))
for l in lessons:
    print(f'  {l["id"]:9s} {l["title"]:26s} quiz{len(l["quizIds"]):3d} drill{len(l["drillQuizIds"] or []):3d}')

# 用語カード（全て terms_extra*.json から）
terms = []
for tf in sorted(glob.glob(os.path.join(DESIGN, "terms_extra*.json"))):
    ex = json.load(open(tf, encoding="utf-8")); sid = {t["id"] for t in terms}; strm = {t["term"] for t in terms}
    add = 0
    for t in ex:
        if t["id"] in sid or t["term"] in strm: continue
        terms.append(t); sid.add(t["id"]); strm.add(t["term"]); add += 1
    print(f"merged {os.path.basename(tf)}: +{add} terms")

# 検証
def validate(qs):
    errs, seen = [], set()
    for q in qs:
        i = q.get("id", "?")
        if i in seen: errs.append(f"重複id {i}")
        seen.add(i)
        if q.get("domain") not in VALID: errs.append(f"{i} 不正domain {q.get('domain')}")
        ch = q.get("choices", [])
        if len(ch) != 4: errs.append(f"{i} choices={len(ch)}")
        if len(set(ch)) != 4: errs.append(f"{i} 選択肢重複")
        ca = q.get("correctAnswers", [])
        if len(ca) != 1 or not (0 <= ca[0] < len(ch)): errs.append(f"{i} correct異常 {ca}")
        for k in q.get("wrongChoiceExplanations", {}):
            ki = int(k)
            if not (0 <= ki < len(ch)) or ki in ca: errs.append(f"{i} wrongkey異常 {k}")
        if "ドリル" not in q.get("tags", []):
            for idx in range(len(ch)):
                if idx not in ca and str(idx) not in q.get("wrongChoiceExplanations", {}):
                    errs.append(f"{i} 誤答解説欠落{idx}")
        if not q.get("explanation", "").strip(): errs.append(f"{i} 解説空")
        if q.get("difficulty") not in (1, 2, 3): errs.append(f"{i} difficulty={q.get('difficulty')}")
    return errs

# --- 選択肢の書き換えパッチ（design/fix_choices*.json）---
_fixed = 0
for ff in sorted(glob.glob(os.path.join(DESIGN, "fix_choices*.json"))):
    fixes = {f["id"]: f["choices"] for f in json.load(open(ff, encoding="utf-8"))}
    for q in questions:
        new = fixes.pop(q["id"], None)
        if new is None: continue
        if len(new) != len(q["choices"]):
            raise SystemExit(f"fix適用エラー {q['id']}: 選択肢数が {len(q['choices'])} → {len(new)}")
        q["choices"] = new; _fixed += 1
    if fixes:
        raise SystemExit(f"fix適用エラー: 存在しないid {sorted(fixes)[:5]}")
if _fixed: print(f"選択肢パッチ適用: {_fixed}問")

# 作業用：シャッフル前（元データ順）の問題を書き出す。fix_choices を作る際の参照元。
with open(os.path.join(DESIGN, "_source_questions.json"), "w", encoding="utf-8") as f:
    json.dump(questions, f, ensure_ascii=False, indent=1)

def count_long_tell(qs):
    n = []
    for q in qs:
        ch = q["choices"]; ci = q["correctAnswers"][0]; c = ch[ci]
        mx = max(len(x) for i, x in enumerate(ch) if i != ci)
        if len(c) > mx and len(c) - mx >= 6 and len(c) >= mx * 1.3: n.append(q["id"])
    return n

_errs = validate(questions)
if _errs:
    print("=== 検証エラー ===")
    for e in _errs[:60]: print("  -", e)
    raise SystemExit(f"検証エラー {len(_errs)}件")

_tell = count_long_tell(questions)
print(f"正解だけ明らかに長い問題: {len(_tell)}問 / {len(questions)}")

questions = balance_positions(questions)

# lessonTheme はレッスン割当専用のメタ情報＝アプリ側へは出さない
for q in questions:
    q.pop("lessonTheme", None)

def dump(name, data):
    json.dump(data, open(os.path.join(BASE, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{name}: {len(data)} items")

dump("questions.json", questions)
dump("terms.json", terms)
dump("lessons.json", lessons)
dump("services.json", services)

# 用語集（tooltip）
gsrc = []
for gf in sorted(glob.glob(os.path.join(DESIGN, "glossary_source*.json"))):
    gsrc += json.load(open(gf, encoding="utf-8"))
seen = set(); gout = []
for g in gsrc:
    if g["term"] in seen: continue
    seen.add(g["term"]); gout.append({"term": g["term"], "explanation": g["explanation"]})
gout.sort(key=lambda x: len(x["term"]), reverse=True)
json.dump(gout, open(os.path.join(BASE, "glossary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"glossary.json: {len(gout)} entries")

main = [q for q in questions if "ドリル" not in q.get("tags", [])]
print("本問:", len(main), "総問題:", len(questions),
      "分野別(本問):", dict(Counter(q["domain"] for q in main)))
