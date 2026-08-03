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
    [{"heading":"3つのライセンス種別","body":"WinActorのライセンス種別は、フル機能版・実行版・管理実行版の3つです。フル機能版は記録・編集・実行のすべてが行える開発用です。実行版はシナリオの実行に関連する画面のみが表示され、読み込みと全体実行はできますが、記録・編集はできず、部分実行と「ここから実行」も行えません。監視ルール一覧・イメージ・プロパティ・ブレイクポイント一覧・イベント一覧も利用できません。管理実行版はフローティングライセンスのみで提供され、管理サーバからの指示でシナリオを実行します。"},
     {"heading":"ライセンス方式","body":"ライセンスの割り当て方には、ノードロック方式とフローティング方式があります。ノードロック方式は、ライセンスを登録した特定の端末でのみWinActorを利用できる方式です。フローティング方式は、ライセンスをサーバで管理し、同時に利用できる数の範囲内であれば複数の端末で使い回せる方式で、多人数・多拠点での利用に向きます。ノードロックには管理実行版がありませんが、フル機能版や実行版を管理実行モードに設定すれば同等に機能します。"},
     {"heading":"動作環境と評価ライセンス","body":"WinActorはWindows上で動作します。対応OSはWindows 10 Pro／Windows 11 Pro／Windows Server 2016・2019・2022で、実行環境として.NET Framework 4.8以上が必要です。自動記録・自動操作に対応するブラウザはGoogle Chrome、Mozilla Firefox、Microsoft Edge(Chromium)、外部ファイルはCSVとExcel（xls・xlsx・xlsm）を扱えます。試用期間内にインストールすると評価ライセンスが付き、評価ライセンスで作ったシナリオには試用期限が付きます。期限を外すには、フル機能版の製品ライセンスで保存し直します。"}]),
 SL("l-ov3", "overview", "画面構成と部品", "画面構成と部品", 10,
    "WinActorのメイン画面の各エリアと、シナリオを組み立てる部品（ノード・ライブラリ）を押さえます。",
    ["メイン画面","フローチャート","ノード","ライブラリ","パレット","プロパティ",
     "変数一覧","データ一覧","サブシナリオ","メインウィンドウ","サブルーチン"],
    [{"heading":"基本画面構成","body":"WinActorの基本画面は、メニューバー・ツールバー・パレットエリア・シナリオ編集エリア・プロパティエリア・機能編集エリア・ステータスバーで構成されます。ツールバーは「編集／記録」（フル機能版のみ）と「実行」に分かれ、ステータスバーにはライセンス種類・シナリオの状態・経過時間・エラー数・表示倍率などが表示されます。基本操作は、パレットから部品をシナリオ編集エリアへドラッグ＆ドロップして手順を組み立てることです。"},
     {"heading":"パレットエリアとノードの種類","body":"パレットエリアは、ノード・ライブラリ・サブシナリオ・お気に入り・検索の5つのタブで切り替えます。ノードパレットはフロー（分岐・繰り返し・例外処理など）、アクション（画像マッチング・待機・Excel操作など）、ユーザ（待機ボックス・インプットボックスなど）、変数（変数値設定・四則演算など）の4カテゴリに分かれます。ライブラリパレットにはユーザライブラリが並び、選択したノードやグループを保存して再利用できます。"},
     {"heading":"機能編集エリア","body":"画面下部の機能編集エリアはタブで切り替えます。変数一覧（変数の管理・現在値の確認・変数名インポート・雛形ファイル作成）、データ一覧（ExcelやCSVの投入データ、DB連携）、ログ出力（実行結果とノードIDからのジャンプ）、メール管理、監視ルール一覧、イメージ、ブレイクポイント一覧、サブルーチン、テキスト変換辞書、呼び出し履歴、実行時間、イベント一覧があります。よく使う一連の手順は、サブルーチングループとして部品化し、サブルーチン呼び出しから再利用します。"}]),
 SL("l-ov4", "overview", "起動・終了と起動オプション", "起動・終了と起動オプション", 11,
    "起動と終了の手順、起動オプション、起動パスワード、シナリオファイルの扱いを押さえます。",
    ["起動","終了","起動オプション","起動パスワード","タスクトレイ","シナリオファイル","2重起動"],
    [{"heading":"起動と終了","body":"WinActorを起動すると「ようこそ画面」が表示され、新規作成をクリックするとフローチャート画面が開きます。終了はファイルメニューの終了、画面右上の×、タスクトレイアイコンの終了メニューのいずれかで行います。保存されていないシナリオやデータ一覧がある場合は確認画面が表示されます。WinActorは2重起動できないため、起動アイコンを押しても表示されないときは、すでに起動していてタスクトレイに入っていないかを確認します。"},
     {"heading":"起動オプション","body":"WinActorはコマンドラインから起動でき、起動ショートカット作成機能でショートカットにオプションを設定できます。代表的なものは、-f（開くシナリオファイルの指定）、-r（起動後にシナリオ実行）、-d（データ一覧ファイルの指定）、-w（指定ミリ秒待機）、-x（実行後にデータ一覧を保存）、-e（実行完了後に終了）、-ec（終了ステータス0／1を返して終了）、-t（タスクトレイに収容して起動）、-p（起動パスワードの指定）、-sl（起動時・実行時のダイアログを非表示）、-sa（指定名で保存して終了）です。これらとWindowsのタスクスケジューラを組み合わせると、定期的な無人実行ができます。"},
     {"heading":"起動パスワードとシナリオファイル","body":"起動パスワードはWinActorの起動時に入力を求めるもので、フル機能版でのみ設定・変更・解除ができます。シナリオファイルの拡張子はums7で、フローチャートのほか変数・監視ルール・ウィンドウ識別ルール・イメージ画像などの情報が保存されます。シナリオごとの編集・閲覧・実行を制限したい場合は、起動パスワードではなくシナリオパスワードを使います。"}]),
 # ------- WinActorの機能 -------
 SL("l-ft1", "features", "自動記録と操作の記録方式", "記録モードと自動操作インターフェース", 13,
    "7種類の記録モードと自動切り替え、4つの自動操作インターフェースの仕組みと使い分けを押さえます。",
    ["自動記録","記録方式","画像マッチング","エミュレーション","IEモード","ブラウザ操作",
     "座標指定","ウィンドウ識別","記録モード","値の取得"],
    [{"heading":"記録モードは7種類＋自動切り替え","body":"WinActorの記録モードは、イベント／エミュレーション／IE／Chrome／Firefox／Edge／UIオートメーションの7種類です。加えて、記録中にこれらを自動的に切り替える「自動切り替えモード」があります。記録を始める前に、記録対象アプリケーション選択ボタンで対象ウィンドウをクリックして指定すると、そのアプリに適したモードが自動的に選ばれます。自動選択されたモード以外で記録したい場合は手動で変更できます。"},
     {"heading":"各モードが対象を見分ける方法","body":"イベントモードはWindows純正ライブラリで作られたアプリを対象に、画面上のボタンや入力欄へ通し番号を付けて「何番目の部品か」を記録します。IEモードはEdgeのIEモードが対象で、同じく通し番号で管理します。Chrome・Firefox・Edgeの各モードは要素をXPathで管理します。UIオートメーションモードはアプリのGUI要素として操作を記録します。ここまでがUI識別型です。エミュレーションモードだけが座標指定型で、マウスのクリック位置とキーボード操作の順序をそのまま記録します。"},
     {"heading":"4つの自動操作インターフェースと使い分け","body":"WinActorは、UI識別型（記録モード）、画像識別型（画像マッチングノード）、座標指定型（エミュレーションモード）、ファイル向け（Excel操作ノード）の4つのインターフェースを組み合わせてシナリオを作ります。画像マッチングは記録モードではなくノードである点に注意してください。安定性の面ではUI識別型が有利で、Java・リモートデスクトップ・SBCクライアントのようにイベントやIEで記録できない画面は、エミュレーションと画像マッチングを組み合わせて操作します。なお、管理者権限で起動したアプリや保護モードが有効なアプリは記録できません。"}]),
 SL("l-ft2", "features", "主要ノード", "主要ノード", 12,
    "シナリオの骨組みを作る基本ノード（分岐・繰り返し・待機・変数値設定・グループなど）を押さえます。",
    ["分岐","条件分岐","繰り返し","待機","変数値設定","グループ","コメント","例外処理ノード","付箋",
     "ノードの種類","IF分岐","ウィンドウ状態取得"],
    [{"heading":"分岐と多分岐","body":"分岐（if・else相当）は、条件が成り立つかどうかで処理を2方向に分けるノードです。プロパティでは判定結果が「真」となる条件式だけを設定し、「偽」側は真を満たさない場合に選ばれるため条件式を設定できません。3つ以上の枝から1つを選びたい場合は多分岐（if・else if・else相当）を使い、追加した条件はNoの順に判定されます。"},
     {"heading":"繰り返しと制御","body":"繰り返し（while相当）は処理の前に継続判定を行うため、条件によっては一度も実行されません。後判定繰返（do・while相当）は処理の後に判定するため最低1回は実行されます。判定条件は条件式・回数・範囲・データ数・データ数(DB連携)から選び、カウンタ変数は1から始まり1ずつ加算されます。途中で抜けたいときは繰り返し終了（break相当）、以降を飛ばして条件判定へ進みたいときは次の条件判定（continue相当）を、いずれも繰り返しの中に配置して使います。"},
     {"heading":"まとめる・再利用する・備える","body":"グループは複数のノードを1つに束ね、コピーや移動をまとめて行えるようにするノードです。再利用したい処理はサブルーチングループにまとめ、サブルーチン呼び出しから実行します。引数・返り値・ローカル変数を使え、ローカル変数はサブルーチン開始時に値が保存され終了時に書き戻されます。エラーや特定の画面に備えるのが例外処理（try・catch相当）で、正常系の実行中にエラーが起きると異常系へジャンプします。メモはノードのコメント欄か付箋ノードに残します。"}]),
 SL("l-ft3", "features", "変数・データ一覧・ライブラリ", "変数・データ一覧・ライブラリ", 12,
    "変数とデータ一覧の使い方、ライブラリによるExcel・ブラウザ操作、対応アプリを押さえます。",
    ["変数","データ一覧","ライブラリ","Excel操作","エクセル","ファイル操作","文字列操作",
     "対応アプリケーション","Python実行","CSV読み込み","値の受け渡し"],
    [{"heading":"変数とデータ一覧","body":"変数は値を一時的にしまう箱で、画面から取得した文字列や計算結果を入れて後の処理で使います。データ一覧は、CSVやExcelの表を取り込み、1行ずつ変数に読み込んで繰り返し処理するための表です。『データ一覧の行数だけ繰り返し、各行の値を変数に入れて処理する』という形が、大量データ処理の基本パターンになります。"},
     {"heading":"ライブラリでできること","body":"ライブラリは、細かな具体的操作をまとめた部品群です。Excelの読み書き・シート操作、ファイルやフォルダの操作、文字列の加工（分割・置換・切り出し）、ウィンドウ操作、メール送信など、多くの部品が標準で用意されています。プロパティで対象ファイルや値、格納先の変数を設定して使います。Ver.7.5.0以降ではPython実行ノードも加わり、より柔軟な処理が可能になりました。"},
     {"heading":"対応アプリと値の受け渡し","body":"WinActorは、Excelなどのオフィスソフト、ブラウザ、業務システムなど、人が画面で操作できる幅広いアプリを自動化できます。処理の結果は変数を通じてノード間・ライブラリ間で受け渡します。どのライブラリの出力をどの変数に入れ、次のどの部品で使うかを意識して設計することが、正しく動くシナリオ作りのポイントです。"}]),
 SL("l-ft4", "features", "アクションカテゴリのノード", "アクションカテゴリのノード", 13,
    "画像マッチング・待機系・文字列送信・コマンド／スクリプト実行・Excel操作・クリップボードを押さえます。",
    ["画像マッチング","輪郭マッチング","OCRマッチング","ウィンドウ状態待機","指定時間待機",
     "文字列送信","コマンド実行","スクリプト実行","Python実行","Excel操作","クリップボード"],
    [{"heading":"画像で当てる3つのノード","body":"画像マッチングは、指定ウィンドウと指定した画像を照合し、一致した場所でクリックなどの操作を行うノードです。マッチング画像は赤枠で指定し、検索範囲の絞り込みや、機密部分を黒く塗るマスク（内側／外側）が使えます。画像が見つかったかどうかを変数に格納して分岐に使うこともできます。輪郭マッチングは画像の輪郭を抽出しマルチスケールで照合するノード、OCRマッチングは指定した文字列を画面上から探して操作するノードです。「マッチング画像が存在しません。」というエラーは、待機を入れるかマッチ率を下げて対処します。"},
     {"heading":"待つためのノード","body":"ウィンドウ状態待機は、画面が表示されるまで／手前になるまで／操作可能になるまで／消えるまで／手前でなくなるまで／操作不可能になるまでの6種類の変化を監視します。待機種別は「状態取得のみ」（真偽を即時取得）と「一定時間待つ」（タイムアウトまで待機）の2種類で、結果はtrue／falseで変数に格納されます。指定時間待機は、ミリ秒（0～3,600,000）で待つ、指定時刻まで待つ、指定時間チェック（現在時刻が範囲内かを判定）の3通りで使えます。"},
     {"heading":"外部と連携するノード","body":"文字列送信は文字列を1文字ずつ送るノードで、イベントモードやIEモードで操作できる場合は「文字列設定」の使用が推奨されます。コマンド実行は指定コマンドを実行し、dirのような内部コマンドはコマンドにcmd.exe、オプションに/c dirと指定します。出力を受け取る設定では標準出力の1行目のみが変数に入ります。スクリプト実行はVBScript、Python実行はPythonを実行します。Excel操作は値の取得・値の設定・マクロ実行の3機能を持ち、csv・xls・xlsx・xlsmに対応します。クリップボードは値の設定と取得ができ、取得できるのはテキスト形式のみです。"}]),
 SL("l-ft5", "features", "ユーザ・変数カテゴリのノード", "ユーザ・変数カテゴリのノード", 11,
    "待機ボックスなどユーザとやり取りするノードと、変数を操作するノードを押さえます。",
    ["待機ボックス","インプットボックス","選択ボックス","音","変数値設定","変数値コピー",
     "日時取得","ユーザ名取得","四則演算","カウントアップ","全角化/半角化"],
    [{"heading":"ユーザとやり取りするノード","body":"待機ボックスは処理を一時中断してメッセージを表示するノードで、OKボタンのみの「確認待ち」と、継続・停止を選ばせる「問い合わせ」の2タイプがあります。インプットボックスは入力を受け取って変数に格納し、選択ボックスはあらかじめ登録した選択候補から選ばせて選択結果を変数に格納します。いずれも表示メッセージに%変数名%と書くと、実行時に変数の値へ置き換わります。音はブザーまたはリニアPCM形式のWAVEファイルを鳴らすノードです。"},
     {"heading":"変数を操作するノード","body":"変数値設定は指定した変数へ任意の値を設定し、変数値コピーは変数の値を別の変数へ複製します。日時取得はOSの現在時刻を取得し、フォーマットタイプは日付と時間・日付のみ・時間のみの3種類です。ユーザ名取得はログイン中のWindowsユーザ名を取得します。四則演算は2値の＋－×÷の結果を変数に格納し、整数どうしの割り算は割り切れなければ小数になります。カウントアップは1～999,999の加算値を変数に加えます。全角化/半角化は文字種をそろえますが、結果は対象の変数へ上書きされる点に注意します。"},
     {"heading":"変数を扱うときの決まりごと","body":"変数名は255文字以下で、空白文字を含められず、「$」で始まる名前は特殊変数用のため使えません。変数が保持できるのは既定で1024文字までで、シナリオ情報の「変数値の文字数を制限する」のチェックを外すと解除できます。変数一覧では初期値・コメント・マスク（値を*****で隠す）・「初期化しない」を設定でき、現在値は実行中と一時停止中に確認できます。$LOOP_NUMや$ERROR_MESSAGEなどの特殊変数も、通常の変数と同じようにシナリオ内で利用できます。"}]),
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
    ["デバッグ","例外処理","エラー処理","ログ","トライキャッチ","保守性","ブレークポイント","ブレイクポイント",
     "エラー対応","シナリオの保守","スクリーンショット取得"],
    [{"heading":"デバッグで不具合を切り分ける","body":"思いどおりに動かないときは、ステップ実行で1ノードずつ動かし、どこで止まるか・変数にどんな値が入っているかを確認して原因を切り分けます。特定の位置で処理を止めるブレークポイントや、実行の記録が残るログも役立ちます。エラー発生時に画面のスクリーンショットを残すようにしておくと、後から原因を追いやすくなります。"},
     {"heading":"例外処理でエラーに備える","body":"自動化では、対象アプリの反応が遅い・想定外の画面が出るなど、エラーはつきものです。例外処理は、エラーが起きても処理全体を止めず、あらかじめ決めた対応（再試行・スキップ・通知など）へ流すための仕組みです。待機ノードで表示を待つ、想定外時は分岐で安全に終了する、といった備えを入れておくと安定します。"},
     {"heading":"保守しやすい作り方","body":"シナリオは作って終わりではなく、業務や画面の変化に合わせて直し続けるものです。ノード名を分かりやすく変更し、コメントや付箋で処理の意図を残し、繰り返し使う部分はサブルーチングループに分けて再利用性を高めます。値をシナリオ内に直接書かず変数やデータ一覧で管理する、シナリオ情報の作成者・連絡先・備考を記入する、といった工夫が、後からの修正と引き継ぎを楽にします。"}]),
 SL("l-sc4", "scenario", "実行方式とループ実行", "実行方式とループ実行", 13,
    "全体実行・部分実行・ここから実行の違いと、データ一覧を使ったループ実行を押さえます。",
    ["全体実行","部分実行","ここから実行","実行速度の調整","実行抑止","ループ実行","実行時エラー"],
    [{"heading":"3つの実行方式","body":"全体実行はメインシナリオの「開始」から「終了」までが対象で、実行ボタンまたはF5キーで開始します。開始～終了の外に置かれた浮きフローは対象になりません。部分実行は選択したノードだけを実行する方式で、飛び飛びの選択やノード未選択では選べません。ここから実行は選択したノード以降を実行する方式で、選べるのはノードを1つだけ選択したときです。部分実行とここから実行では、データインポートで読み込んだ値ではなく変数の初期値が使われます。"},
     {"heading":"実行の調整と警告","body":"実行速度は、各ノードの前に待機時間を入れるプルダウンで調整でき、+1ごとに0.1秒増えます。一部のノードを飛ばしたいときは実行抑止を使います。プロパティ未設定の項目や実行されないノードがある状態で実行しようとすると、実行前の警告が表示されます。実行中にエラーが発生するとシナリオは一時停止状態となり、原因を解消してから発生箇所を再開できます。止めたくない場合は例外処理を使います。"},
     {"heading":"ループ実行","body":"ループ実行は、データ一覧に読み込んだ表形式データと連携する実行方式です。1行目にデータ名（変数名と一致させる）、2行目以降に実データを置き、チェックの付いた行の数だけ開始から終了までが繰り返されます。ループのたびに開始箇所でデータ一覧から変数へ値が渡され、終了箇所で変数の値がデータ一覧へ差し戻されます。実行が終わった行はチェックが外れます。Excelファイルを指定した場合はExcelが起動するため、ループ実行が終わる前に閉じると実行エラーになります。CSVはメモリ上で扱われるため、データが大きい場合は読み込む行数を減らします。"}]),
 SL("l-sc5", "scenario", "セキュリティとファイルパス", "セキュリティとファイルパス", 12,
    "シナリオパスワードとセキュリティモード、ファイルパスの扱いを押さえます。",
    ["シナリオパスワード","セキュリティモード","ファイルパス","基準パス","UNCパス","相対パス"],
    [{"heading":"シナリオパスワード","body":"シナリオファイルには、シナリオ編集パスワード・シナリオ閲覧パスワード・シナリオ実行パスワードを設定でき、シナリオ情報画面のパスワードタブから変更します。長さは8文字から64文字までで、3つに同じパスワードを設定することはできません。設定の組み合わせによって、開くときの動作（入力を求めるか、キャンセルしたらどうなるか）が変わります。"},
     {"heading":"セキュリティモード","body":"入力したパスワードに応じてセキュリティモードが切り替わります。シナリオ編集モードは記録・編集・保存・実行のすべてが可能です。シナリオ閲覧モードは記録・編集・保存ができず、内容とプロパティの閲覧と実行のみ可能で、部分実行・ここから実行とブレイクポイント一覧は使えません。シナリオ実行モードは実行のみで、操作できるのは実行に関するボタンと、データ一覧・ログ出力・メール管理のタブに限られます。なお実行版で編集パスワードを入力するとファイルを開けません。"},
     {"heading":"ファイルパスの扱い","body":"WinActorで使えるファイルパスは、ローカルパス・UNCパス・http/httpsスキーマのURIの3種類です。UNCパスは￥￥コンピュータ名￥共有名￥…の形式でネットワーク上の場所を表します。絶対パスは3種類すべてで使えますが、相対パスはローカルパスでのみ使えます。相対パスは基準パスで補完され、優先順位はシナリオパス→WinActorパス→インストールパスの順です。なお、WinActorからファイル保存できないフォルダがある点にも注意します。"}]),
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
 S("s-exception","例外処理","ノード","エラー時も止めず、異常系へ処理を移す（try・catch相当）。","scenario"),
 S("s-subscenario","サブルーチン","シナリオ","一連の手順を部品化し、呼び出して再利用する仕組み。","scenario"),
 # --- 記録モード（7種＋自動切り替え） ---
 S("s-mode-event","イベントモード","記録モード","Windows純正アプリを対象に、部品の通し番号で記録。","features"),
 S("s-mode-ie","IEモード","記録モード","EdgeのIEモードが対象。部品の通し番号で記録。","features"),
 S("s-mode-chrome","Chromeモード","記録モード","Google Chrome専用。要素をXPathで管理する。","features"),
 S("s-mode-firefox","Firefoxモード","記録モード","Mozilla Firefox専用。要素をXPathで管理する。","features"),
 S("s-mode-edge","Edgeモード","記録モード","Edge(Chromium)専用。要素をXPathで管理する。","features"),
 S("s-mode-uia","UIオートメーションモード","記録モード","アプリのGUI要素として操作を記録する。","features"),
 S("s-mode-auto","自動切り替えモード","記録モード","記録中に対象を変えると適切なモードへ自動で切替。","features"),
 # --- フローカテゴリ ---
 S("s-tabunki","多分岐","ノード","3つ以上の枝から1つを選ぶ（if・else if・else相当）。","features"),
 S("s-atohantei","後判定繰返","ノード","処理後に判定するため最低1回は実行される繰り返し。","features"),
 S("s-loopend","繰り返し終了","ノード","繰り返しから抜ける（break相当）。","features"),
 S("s-continue","次の条件判定","ノード","以降を飛ばし条件判定へ進む（continue相当）。","features"),
 S("s-subcall","サブルーチン呼び出し","ノード","サブルーチングループの処理を呼び出して実行する。","features"),
 S("s-subgroup","サブルーチングループ","ノード","再利用する処理のまとまり。ローカル変数を持てる。","features"),
 S("s-callscenario","シナリオファイル呼び出し","ノード","他のシナリオファイルを読み込んで実行する。","scenario"),
 S("s-eventwatch","イベント監視","ノード","登録したトリガーを監視し呼び出し処理を実行する。","features"),
 # --- アクションカテゴリ ---
 S("s-rinkaku","輪郭マッチング","ノード","輪郭を抽出しマルチスケールで照合して操作する。","features"),
 S("s-ocr","OCRマッチング","ノード","画面上の文字列を検索して操作する。","features"),
 S("s-winwait","ウィンドウ状態待機","ノード","画面の状態変化（6種類）を待つ・取得する。","features"),
 S("s-timewait","指定時間待機","ノード","時間（ミリ秒）や時刻まで待つ／時間帯を判定する。","features"),
 S("s-sendstr","文字列送信","ノード","文字列を1文字ずつ送信する。文字列設定が推奨。","features"),
 S("s-command","コマンド実行","ノード","コマンドを実行し、標準出力の1行目を取得できる。","features"),
 S("s-script","スクリプト実行","ノード","VBScriptのコードをシナリオ内で実行する。","features"),
 S("s-python","Python実行","ノード","Pythonのスクリプトを実行する（Ver.7.5.0で追加）。","features"),
 S("s-excel","Excel操作","ノード","値の取得・値の設定・マクロ実行の3機能を持つ。","features"),
 S("s-clipboard","クリップボード","ノード","値の設定と取得。取得はテキスト形式のみ。","features"),
 # --- ユーザ・変数カテゴリ ---
 S("s-waitbox","待機ボックス","ノード","メッセージ表示で中断。確認待ち／問い合わせの2種。","features"),
 S("s-inputbox","インプットボックス","ノード","入力を受け取り変数へ格納する。","features"),
 S("s-selectbox","選択ボックス","ノード","選択候補から選ばせ、結果を変数へ格納する。","features"),
 S("s-copyvar","変数値コピー","ノード","変数の値を別の変数へコピーする。","features"),
 S("s-datetime","日時取得","ノード","現在日時を変数へ格納する。","features"),
 S("s-calc","四則演算","ノード","2値の＋－×÷の結果を変数へ格納する。","features"),
 S("s-countup","カウントアップ","ノード","変数に加算値（1～999,999）を加える。","features"),
 S("s-zenhan","全角化/半角化","ノード","文字種を統一する。結果は対象変数へ上書き。","features"),
 # --- 画面・仕組み ---
 S("s-windowrule","ウィンドウ識別ルール","仕組み","操作対象の画面をタイトルやプロセス名で特定する。","scenario"),
 S("s-kanshi","監視ルール","仕組み","特定画面が出たときの動作を決めておく規則。","scenario"),
 S("s-breakpoint","ブレイクポイント","デバッグ","設定したノードの実行前で一時停止する。","scenario"),
 S("s-yokushi","実行抑止","デバッグ","指定ノードを実行せずスキップする。","scenario"),
 S("s-loopexec","ループ実行","実行","データ一覧の行数だけシナリオを繰り返す実行方式。","scenario"),
 S("s-partial","部分実行","実行","選択したノードだけを実行する（実行版は不可）。","scenario"),
 S("s-fromhere","ここから実行","実行","選択したノード以降を実行する（実行版は不可）。","scenario"),
 S("s-scenariopw","シナリオパスワード","セキュリティ","編集・閲覧・実行を制限する3種のパスワード。","scenario"),
 S("s-bootopt","起動オプション","運用","-fや-r、-ecなどコマンドラインからの起動指定。","overview"),
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
# 1レッスンに載せる確認問題の上限（超過分はランダム問題プールへ）
QUIZ_PER_LESSON = 10


def build_lessons(all_qs):
    from collections import defaultdict
    qmap = {q["id"]: q for q in all_qs}
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

    # 確認問題は1レッスンあたり QUIZ_PER_LESSON 問まで。
    # あふれた分はランダム問題（ドリル）のプールへ回す（問題自体は模試・演習でも使われる）。
    for sl in SUBLESSONS:
        picked = sl["_quiz"]
        if len(picked) <= QUIZ_PER_LESSON:
            continue
        # 難易度の低い順→登場順で選び、確認問題は「学んだ直後の確認」にふさわしい構成にする
        order = sorted(picked, key=lambda qid: (qmap[qid].get("difficulty", 2), picked.index(qid)))
        keep = set(order[:QUIZ_PER_LESSON])
        sl["_quiz"] = [qid for qid in picked if qid in keep]
        sl["_drill"] = [qid for qid in picked if qid not in keep] + sl["_drill"]

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
