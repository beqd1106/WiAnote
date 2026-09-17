# 用語カードのファクトチェック仕様（WiAnote）

WiAnote の用語カード（terms.json）は、WinActor 操作マニュアルと照合されないまま
作られており、**事実誤りが混じっている**ことが判明した。

確認済みの実例：用語「記録モード」のカードに「7種類ある」「7種類＋自動切り替え」とあるが、
マニュアル 1.7.2 では「イベント／エミュレーション／IE／Chrome／Firefox／Edge／
UIオートメーション／**画像マッチング**の8つ」＋「自動切り替えモード」が正しい。
画像マッチングモードが抜け落ちている。

この種の誤りを全件洗い出して直す。

## 入力
`design/term_check/<ID>.json` … 配列。各要素：
- `id` / `term` / `domain` / `difficulty`
- `shortDescription`（一言）/ `beginnerExplanation`（初心者向け）/ `useCase`（使いどころ）/ `examPoint`（試験ポイント）
- `relatedServices`（関連語の配列）
- `manualPages` / `manualExcerpt` … **マニュアル本文（唯一の出典）**

## やること
各用語カードの4つの文（shortDescription / beginnerExplanation / useCase / examPoint）を
`manualExcerpt` と突き合わせ、**誤りがあれば直す**。

判定は次の3つのいずれか：
- `ok` … マニュアルと矛盾しない。修正不要。
- `fix` … マニュアルと食い違う記述がある。該当フィールドを直す。
- `unverifiable` … `manualExcerpt` に根拠が無く、正誤を判断できない。

**特に狙って確認すること**
1. **個数・種類の列挙**（「7種類」「3つ」など）→ マニュアルの数と一致するか、抜けが無いか
2. **数値・既定値・上限**（文字数制限、範囲、初期値）
3. **名称の正確さ**（ノード名・メニュー名・画面名・タブ名が実在の表記どおりか）
4. **機能の取り違え**（別の機能の説明になっていないか）

## 絶対のルール
- **`manualExcerpt` に書かれていることだけ**を根拠にする。記憶・推測で補わない。
- 直すときも**元の文体と長さ感を保つ**（shortDescriptionは一言、examPointは1〜2文）。
- 根拠が無い記述は、勝手に「正しい」とみなさない。`unverifiable` として報告する。
  ただし明らかな一般論（「変数は値を入れる箱」等）はokとしてよい。
- 絵文字は使わない。

## 出力
`design/term_out/<ID>.json` に JSON配列（UTF-8）。**修正が必要だったものだけ**ではなく、
**全件**を次の形で出す：
```json
{
  "id": "t-001",
  "verdict": "ok" | "fix" | "unverifiable",
  "shortDescription": "…",
  "beginnerExplanation": "…",
  "useCase": "…",
  "examPoint": "…",
  "reason": "fix のときだけ：何がどう間違っていたか（1行）"
}
```
`ok` / `unverifiable` のときは4つの文を**入力のまま**入れる。

**中断対策**：半分できた時点で一度書き出し、その後追記して完成させること。
