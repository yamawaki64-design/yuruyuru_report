import json


def build_format_prompt(fields: list, glossary: list) -> str:
    """
    整形処理用のsystem_promptを自動生成する（Groq①）
    Args:
        fields   : 項目定義JSONのfields配列
        glossary : 用語辞書JSONのglossary配列
    Returns:
        system_prompt文字列
    """
    output_template = {}
    for field in fields:
        if "note" in field:
            hint = field["note"]
        elif "options" in field:
            hint = "、".join(field["options"]) + " のいずれか。不明な場合は空文字"
        else:
            hint = "メモから読み取った値。不明な場合は空文字"
        output_template[field["name"]] = hint

    glossary_text = ""
    if glossary:
        glossary_text = "\n【用語】\n"
        for g in glossary:
            glossary_text += f'- {g["term"]}：{g["description"]}（{g["field"]}に入れること）\n'

    return f"""あなたは営業メモを整形するアシスタントです。
以下のJSON形式のみで回答してください。

出力形式：
{json.dumps(output_template, ensure_ascii=False, indent=2)}
{glossary_text}
【重要】
- メモにない情報は補完・推測しないこと
- 出力はJSONのみ。説明文・前置き・```は不要
"""


def build_multiple_check_prompt() -> str:
    """
    複数案件混在チェック用のsystem_promptを生成する（Groq②）
    出力はJSON {{ is_multiple: true/false }} のみ
    """
    return """あなたは営業メモを分析するアシスタントです。
メモが「1つの案件について書かれているか」「複数の案件が混在しているか」を判定してください。

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
