ゆるゆる報告書　スクリプト案まとめ
Claude Codeへの引継ぎ用　2026年3月
このドキュメントは、設計チャットで検討したPythonスクリプト案をClaude Codeへ引き継ぐためのまとめです。
各スクリプトはあくまで「たたき台」です。実装時にClaude Codeと細部を詰めてください。

1. 想定ファイル構成


ゆるゆる報告書/
├── app.py                  # Streamlitメインアプリ
├── pages/
│   └── bucho.py            # 2ページ目：部長室
├── prompts/
│   ├── prompt_builder.py   # プロンプト自動生成
│   └── bucho_prompt.py     # 部長プロンプト生成
├── data/
│   ├── template_shidan.json  # 項目定義JSON（商談用）
│   └── glossary.json         # 用語辞書JSON
└── utils/
    ├── groq_client.py      # Groq API呼び出し共通
    └── time_context.py     # 時間・曜日判定



2. 項目定義JSON（確定版）
ファイル：data/template_shidan.json


{
  "template_name": "商談レコード",
  "fields": [
    { "name": "会社名",        "required": true },
    { "name": "担当者名",       "required": true },
    { "name": "商談フェーズ",   "required": true,
      "options": ["初回接触", "提案中", "見積提出", "クローズ"] },
    { "name": "予算感",         "required": false },
    { "name": "導入希望時期",   "required": false },
    { "name": "確度",           "required": false,
      "options": ["高", "中", "低"],
      "note": "メモに明記されている場合のみ入力。不明な場合は必ず空文字" },
    { "name": "競合情報",       "required": false },
    { "name": "次のアクション", "required": true },
    { "name": "備考",           "required": false }
  ]
}



3. 用語辞書JSON（空配列スタート）
ファイル：data/glossary.json


{
  "glossary": []
}


// 将来的な追加例：
// { "term": "MM単価", "description": "月単価のこと", "field": "予算感" }
// { "term": "ランク",  "description": "スキルグレード", "field": "備考" }



4. Groq① プロンプト自動生成
ファイル：prompts/prompt_builder.py
項目定義JSONと用語辞書JSONを組み合わせてsystem_promptを自動生成する。



import json


def build_format_prompt(fields: list, glossary: list) -> str:
    """
    整形処理用のsystem_promptを自動生成する
    Args:
        fields   : 項目定義JSONのfields配列
        glossary : 用語辞書JSONのglossary配列
    Returns:
        system_prompt文字列
    """
    output_template = {}
    for field in fields:
        if "note" in field:
            # noteがある項目（確度など）は特別扱い
            hint = field["note"]
        elif "options" in field:
            hint = "、".join(field["options"]) + " のいずれか。不明な場合は空文字"
        else:
            hint = "メモから読み取った値。不明な場合は空文字"
        output_template[field["name"]] = hint


    # 用語辞書があればプロンプトに追加
    glossary_text = ""
    if glossary:
        glossary_text = "\n【用語】\n"
        for g in glossary:
            glossary_text += f'- {g["term"]}：{g["description"]}（{g["field"]}に入れること）\n'


    return f"""
あなたは営業メモを整形するアシスタントです。
以下のJSON形式のみで回答してください。


出力形式：
{json.dumps(output_template, ensure_ascii=False, indent=2)}
{glossary_text}
【重要】
- メモにない情報は補完・推測しないこと
- 出力はJSONのみ。説明文・前置き・\`\`\`は不要
"""



5. Groq② 複数案件判定（ヒソヒソくん用）
prompts/prompt_builder.py に追記
Yes/Noのみ返す。止めない・通す方針。迷ったらfalse。



def build_multiple_check_prompt() -> str:
    """
    複数案件混在チェック用のsystem_prompt
    出力はJSON { is_multiple: true/false } のみ
    """
    return """
あなたは営業メモを分析するアシスタントです。
メモが「1つの案件について書かれているか」
「複数の案件が混在しているか」を判定してください。


以下のJSON形式のみで回答してください：
{"is_multiple": true または false}


【判定基準】
- 会社名が複数登場する → true
- 担当者名が複数の会社に紐づいている → true
- 「あと〜」「別件で〜」などの切り替えワードがある → true
- 上記に当てはまらない → false
- 迷ったら false（止めない方針）


出力はJSONのみ。説明文不要。
"""



6. ヒソヒソくん 判定ロジック
app.py 内に実装
必須項目の空欄チェックはPython側で処理。Groqを呼ばない。



def check_hisohiso(fields: list, result: dict, is_multiple: bool) -> str | None:
    """
    ヒソヒソくんの発言を返す。何も言わない場合はNoneを返す。
    Args:
        fields      : 項目定義JSONのfields配列
        result      : Groq①が返した整形結果dict
        is_multiple : Groq②の複数案件判定結果
    Returns:
        ヒソヒソくんの発言文字列 or None
    """
    # 複数案件混在チェック（Groq②の結果を使う）
    if is_multiple:
        return "たくさんご要望がありますね。。（小声）"


    # 必須項目の空欄チェック（Python側で処理）
    for field in fields:
        if field.get("required") and not result.get(field["name"]):
            name = field["name"]
            return f"…✱の{name}、聞けましたか？（小声）"


    # 何も問題なし
    return None



7. Groq③ プルプル部長プロンプト
ファイル：prompts/bucho_prompt.py



from datetime import datetime


def get_time_context() -> str | None:
    """時間・曜日コンテキストをPython側で判定"""
    now = datetime.now()
    hour = now.hour
    is_weekend = now.weekday() >= 5  # 5=土, 6=日


    if is_weekend:
        return "今日は休日です"
    elif hour >= 18:
        return "今は18時以降です"
    return None




def build_bucho_prompt() -> str:
    """部長のsystem_promptを生成。時間コンテキストを自動付加。"""


    base_prompt = """
あなたは「プルプル部長」です。以下のキャラクターで回答してください。


【キャラクター】
- 58歳、昭和の営業マン気質
- 自分の武勇伝が大好き
- 口癖：「わしの時代はな…」
- メモに人名があれば必ず反応する（知ってるかどうかは一切関係ない）
- 必ずケチをつけるが最終的には承認する
- ケチのネタ：ひらがなが多い・句読点の位置・文字数・改行・カタカナ英語
- 雑談ネタ：ゴルフのスコア・昔の接待文化・バブル時代・最近の若者への愚痴


【返答形式】
以下のJSON形式のみで回答してください：
{
  "stamp": "承認：プルプル部長",
  "comment": "部長の一言（武勇伝・ゴルフ・バブル時代など）"
}


出力はJSONのみ。説明文不要。
"""


    # 時間コンテキストがあれば追記
    time_context = get_time_context()
    if time_context:
        base_prompt += f"""
【追加指示】
{time_context}。
必ず最初にコンプライアンス的な一言を言うこと。
ただしその後は昔話に脱線してよい。
例：「最近の若者は無理させちゃいかん。ちなみにワシの若いころは終電まで…」
"""


    return base_prompt



8. Groq API 共通呼び出し
ファイル：utils/groq_client.py



import json
from groq import Groq


client = Groq()  # GROQ_API_KEYは環境変数から自動取得


def call_groq(system_prompt: str, user_message: str, model: str = 'llama3-70b-8192') -> str:
    """Groq APIを呼び出してテキストを返す"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ]
    )
    return response.choices[0].message.content




def call_groq_json(system_prompt: str, user_message: str) -> dict:
    """Groq APIを呼び出してJSONをパースして返す"""
    raw = call_groq(system_prompt, user_message)
    # ```json〜``` で囲まれて返ってくる場合の除去
    clean = raw.strip().replace('```json', '').replace('```', '').strip()
    return json.loads(clean)



9. app.py メイン処理フロー（骨格）
ファイル：app.py
実際のStreamlit実装はClaude Codeと詰める。骨格のみ記載。



import json
import streamlit as st
from prompts.prompt_builder import build_format_prompt, build_multiple_check_prompt
from utils.groq_client import call_groq_json


# JSONの読み込み
with open('data/template_shidan.json', encoding='utf-8') as f:
    template = json.load(f)
with open('data/glossary.json', encoding='utf-8') as f:
    glossary_data = json.load(f)


fields   = template['fields']
glossary = glossary_data['glossary']


# ---- UI ----
st.title('ゆるゆる報告書')


# 入力欄（プレースホルダー付き）
memo = st.text_area(
    'メモを入力してください',
    placeholder='田中商事の山田さんと面談。予算200万、来月提案予定。競合はA社が入ってるらしい。',
    height=200
)


# 整形結果パネル（整形前から項目名✱を表示）
result_placeholder = st.empty()
hisohiso_placeholder = st.empty()


if st.button('整形して'):
    # Groq①：整形処理
    system_prompt = build_format_prompt(fields, glossary)
    result = call_groq_json(system_prompt, memo)


    # 整形結果表示
    with result_placeholder.container():
        for field in fields:
            name  = field['name']
            required_mark = ' ✱' if field.get('required') else ''
            value = result.get(name, '')
            st.text(f'{name}{required_mark}：{value}')


    # Groq②：複数案件判定
    check_prompt = build_multiple_check_prompt()
    check_result = call_groq_json(check_prompt, memo)
    is_multiple  = check_result.get('is_multiple', False)


    # ヒソヒソくん判定
    from app import check_hisohiso  # 同ファイル内関数
    hisohiso_msg = check_hisohiso(fields, result, is_multiple)
    if hisohiso_msg:
        hisohiso_placeholder.info(f'🤫 {hisohiso_msg}')
    else:
        hisohiso_placeholder.empty()


    # セッションに保存（部長ページへの引き渡し用）
    st.session_state['formatted_result'] = result


# コピーボタン・部長ボタン
st.button('クリップボードにコピー')   # 実装はClaude Codeと詰める
if st.button('プルプル部長に聞いてみよう'):
    st.switch_page('pages/bucho.py')



10. Claude Codeへの申し送り事項
スクリプトはたたき台。細部はClaude Codeと実装しながら調整してください
クリップボードコピーの実装はStreamlitの制約確認が必要（st.code＋手動コピーも選択肢）
session_stateで整形結果を部長ページに引き渡す設計
Groqのモデル名は最新のものに差し替えてください（llama3-70b-8192は例）
用語辞書は空配列スタート。使いながら data/glossary.json に追記していく運用
✱マークの色・サイズはCSS調整でうるさくならないように
