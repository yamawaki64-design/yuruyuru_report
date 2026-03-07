import base64
import json
import streamlit as st
import streamlit.components.v1 as components
from prompts.prompt_builder import build_format_prompt, build_multiple_check_prompt
from utils.groq_client import call_groq_json

# ---- 背景画像をbase64に変換 ----
with open("assets/doodle_background_1600x900_soft_100kb.jpg", "rb") as _f:
    _bg_b64 = base64.b64encode(_f.read()).decode()

# ---- ページ設定 ----
st.set_page_config(
    page_title="ゆるゆる報告書",
    page_icon="📋",
    layout="centered",
)

# ---- スタイル ----
st.markdown("""
<style>
/* Streamlitデフォルトヘッダーを非表示 */
header[data-testid="stHeader"] { display: none; }

/* ── 固定タイトルバー（.stApp疑似要素で実装：backdrop-filterのcontaining-block問題を回避） ── */
.stApp::before {
    content: "📋 ゆるゆる報告書";
    position: fixed;
    top: 0; left: 0;
    width: 100vw;
    height: 30px;
    background: linear-gradient(90deg, #546e7a, #78909c);
    color: white;
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 0.05em;
    display: flex;
    align-items: center;
    padding: 0 16px;
    box-sizing: border-box;
    z-index: 9999;
}

/* ── ガラスパネル ── */
[data-testid="stMainBlockContainer"] {
    padding-top: 2.5rem;
    background: rgba(255, 255, 255, 0.22);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-radius: 12px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.1);
}
.stApp { background-color: #455a64; }

/* ── ヒソヒソくんヘッダー（入力前案内） ── */
.hisohiso-header {
    position: relative;
    margin-top: 22px;
    background: #fffbf0;
    border: 2px dashed #FFD54F;
    border-radius: 0 12px 12px 12px;
    padding: 10px 16px;
    font-size: 0.88em;
    font-style: italic;
    color: #6d4c41;
    margin-bottom: 6px;
    line-height: 1.8;
}
.hisohiso-header::before {
    content: "🐰 ヒソヒソくん";
    position: absolute;
    top: -22px;
    left: -2px;
    background: #FFD54F;
    color: white;
    font-size: 0.72em;
    font-style: normal;
    font-weight: bold;
    padding: 3px 10px;
    border-radius: 6px 6px 0 0;
    white-space: nowrap;
    letter-spacing: 0.03em;
}

/* ── ルーズリーフ リング ── */
.loose-leaf-rings {
    display: flex;
    justify-content: space-evenly;
    padding: 4px 12px 0;
    margin-bottom: -6px;
    position: relative;
    z-index: 1;
}
.loose-leaf-ring {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    border: 2.5px solid #888;
    background: radial-gradient(circle at 38% 32%, #e0e0e0 0%, #aaa 60%, #888 100%);
    box-shadow:
        inset 0 1px 2px rgba(255,255,255,0.55),
        inset 0 -1px 2px rgba(0,0,0,0.3),
        0 2px 4px rgba(0,0,0,0.22);
}

/* テキストエリア（付箋スタイル） */
.stTextArea textarea {
    background-color: #FFFDE7 !important;
    border: 1.5px solid #FFD54F !important;
    border-radius: 10px !important;
    box-shadow: 2px 4px 10px rgba(0,0,0,0.08) !important;
    font-size: 14px !important;
    color: #333 !important;
    caret-color: #333 !important;
}
.stTextArea textarea::placeholder {
    color: #bbb !important;
    opacity: 1 !important;
}

/* ── ヒソヒソくんメッセージ（条件付き出現） ── */
.hisohiso-box {
    position: relative;
    margin-top: 22px;
    background: #fffbf0;
    border: 2px dashed #FFD54F;
    border-radius: 0 10px 10px 10px;
    padding: 8px 14px;
    font-size: 0.85em;
    font-style: italic;
    color: #795548;
}
.hisohiso-box::before {
    content: "🐰 ヒソヒソくん";
    position: absolute;
    top: -22px;
    left: -2px;
    background: #FFD54F;
    color: white;
    font-size: 0.72em;
    font-style: normal;
    font-weight: bold;
    padding: 3px 10px;
    border-radius: 6px 6px 0 0;
    white-space: nowrap;
    letter-spacing: 0.03em;
}

/* ── 整形結果パネル（バインダー風） ── */
.result-panel {
    position: relative;
    margin-top: 30px;
    background: white;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 10px 16px;
    box-shadow: 2px 4px 10px rgba(0,0,0,0.09);
    margin-bottom: 6px;
}
.result-panel::before {
    content: "";
    position: absolute;
    top: -26px;
    left: 50%;
    transform: translateX(-50%);
    width: 24px;
    height: 12px;
    border: 3px solid #757575;
    border-bottom: none;
    border-radius: 50% 50% 0 0 / 100% 100% 0 0;
    background: transparent;
}
.result-panel::after {
    content: "";
    position: absolute;
    top: -16px;
    left: 50%;
    transform: translateX(-50%);
    width: 52px;
    height: 16px;
    background: linear-gradient(to bottom, #c0c0c0 0%, #888 35%, #aaa 65%, #808080 100%);
    border-radius: 4px 4px 2px 2px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.5), inset 0 -1px 0 rgba(0,0,0,0.2);
}
.result-item {
    padding: 5px 0;
    border-bottom: 1px solid #f3f3f3;
}
.result-item:last-child { border-bottom: none; }
.result-label {
    font-size: 0.72em;
    color: #9e9e9e;
    font-weight: normal;
    margin-bottom: 1px;
}
.result-value {
    font-size: 0.95em;
    color: #2c2c2c;
    font-weight: bold;
    padding-left: 10px;
}

/* ── ボタン ── */
/* 🐰メモをまとめますね → オレンジ */
[data-testid="stBaseButton-primary"] {
    background-color: #e8802a !important;
    border-color: #e8802a !important;
    color: white !important;
    font-size: 15px !important;
    font-weight: bold !important;
    padding: 10px 24px !important;
}
[data-testid="stBaseButton-primary"]:hover {
    background-color: #d4711f !important;
    border-color: #d4711f !important;
}
/* プルプル部長ボタン → 黄色（有効なsecondaryのみ） */
[data-testid="stBaseButton-secondary"]:not([disabled]) {
    background-color: #FFD600 !important;
    color: #333 !important;
    border-color: #FFD600 !important;
    font-size: 15px !important;
    font-weight: bold !important;
    padding: 10px 24px !important;
}
[data-testid="stBaseButton-secondary"]:not([disabled]):hover {
    background-color: #f5cb00 !important;
    border-color: #f5cb00 !important;
}
</style>
""", unsafe_allow_html=True)

# ---- 背景画像を別途注入 ----
st.markdown(f"""
<style>
.stApp {{
    background-image: url('data:image/jpeg;base64,{_bg_b64}');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    background-color: #455a64;
}}
</style>
""", unsafe_allow_html=True)

# ---- JSONの読み込み ----
with open("data/template_shidan.json", encoding="utf-8") as f:
    template = json.load(f)
with open("data/glossary.json", encoding="utf-8") as f:
    glossary_data = json.load(f)

fields = template["fields"]
glossary = glossary_data["glossary"]


# ---- ヒソヒソくん判定 ----
def check_hisohiso(fields: list, result: dict, is_multiple: bool) -> str | None:
    if is_multiple:
        return "たくさんご要望がありますね。。（小声）"
    for field in fields:
        if field.get("required") and not result.get(field["name"]):
            name = field["name"]
            return f"…✱の{name}、聞けましたか？（小声）"
    return None


# ---- 整形結果パネルHTML生成 ----
def build_result_html(fields: list, result: dict) -> str:
    html = '<div class="result-panel">'
    for field in fields:
        name = field["name"]
        display_name = (
            f"{name}（{', '.join(field['options'])}）"
            if "options" in field else name
        )
        req = " ✱" if field.get("required") else ""
        val = result.get(name, "")
        safe_val = (
            val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if val else ""
        )
        html += f"""
        <div class="result-item">
            <div class="result-label">{display_name}{req}</div>
            <div class="result-value">{safe_val if safe_val else "&nbsp;"}</div>
        </div>"""
    html += "</div>"
    return html


# ---- コピー用テキスト生成 ----
def build_copy_text(fields: list, result: dict) -> str:
    return "\n".join(f"{f['name']}：{result.get(f['name'], '')}" for f in fields)


# ---- コピーボタンHTML生成 ----
def build_copy_button_html(copy_text: str, label: str = "クリップボードにコピー 📋") -> str:
    js_text = (
        copy_text
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("`", "\\`")
        .replace("\n", "\\n")
    )
    return f"""
    <meta name="color-scheme" content="light">
    <button onclick="navigator.clipboard.writeText('{js_text}').then(() => {{
            this.textContent = 'コピーしました！ ✅';
            setTimeout(() => this.textContent = '{label}', 2000);
        }})"
        style="
            background:#607d8b; color:white; border:none;
            padding:10px 24px; border-radius:6px;
            font-size:15px; font-weight:bold;
            cursor:pointer; width:100%;
        ">{label}</button>
    """


# ---- session_state 初期化 ----
if "formatted_result" not in st.session_state:
    st.session_state["formatted_result"] = None
if "memo_text" not in st.session_state:
    st.session_state["memo_text"] = ""
if "hisohiso_msg" not in st.session_state:
    st.session_state["hisohiso_msg"] = None

# ---- ヒソヒソくんヘッダー ----
st.markdown("""
<div class="hisohiso-header">
    あの...さっきの会議でメモされてましたよね？<br>
    僕のほうでまとめますので、メモをそのままコピペしてもらっていいですか？
</div>
""", unsafe_allow_html=True)

# ---- ルーズリーフリング ----
st.markdown("""
<div class="loose-leaf-rings">
  <span class="loose-leaf-ring"></span>
  <span class="loose-leaf-ring"></span>
  <span class="loose-leaf-ring"></span>
  <span class="loose-leaf-ring"></span>
  <span class="loose-leaf-ring"></span>
  <span class="loose-leaf-ring"></span>
  <span class="loose-leaf-ring"></span>
  <span class="loose-leaf-ring"></span>
  <span class="loose-leaf-ring"></span>
</div>
""", unsafe_allow_html=True)

# ---- 入力欄 ----
memo = st.text_area(
    label="メモ入力",
    value=st.session_state["memo_text"],
    placeholder="例：田中商事の山田さんと面談。予算200万、来月提案予定。競合はA社が入ってるらしい。次回は見積持参。",
    height=320,
    label_visibility="collapsed",
)
st.session_state["memo_text"] = memo

# ---- 整形ボタン（パネルの上） ----
btn_pressed = st.button("🐰 メモをまとめますね", type="primary", use_container_width=True)

# ---- ヒソヒソくんメッセージ（パネルの上・ボタンの下） ----
hisohiso_placeholder = st.empty()
if st.session_state["hisohiso_msg"]:
    hisohiso_placeholder.markdown(
        f'<div class="hisohiso-box">{st.session_state["hisohiso_msg"]}</div>',
        unsafe_allow_html=True,
    )

# ---- 整形結果パネル ----
result_placeholder = st.empty()
with result_placeholder.container():
    result = st.session_state.get("formatted_result") or {}
    st.markdown(build_result_html(fields, result), unsafe_allow_html=True)

# ---- 整形処理 ----
if btn_pressed:
    if not memo.strip():
        st.warning("メモを入力してください。")
    else:
        with st.spinner("整形中…"):
            try:
                # Groq① 整形処理
                system_prompt = build_format_prompt(fields, glossary)
                result = call_groq_json(system_prompt, memo)
                st.session_state["formatted_result"] = result

                with result_placeholder.container():
                    st.markdown(build_result_html(fields, result), unsafe_allow_html=True)

                # Groq② 複数案件判定
                check_prompt = build_multiple_check_prompt()
                check_result = call_groq_json(check_prompt, memo)
                is_multiple = check_result.get("is_multiple", False)

                # ヒソヒソくん
                hisohiso_msg = check_hisohiso(fields, result, is_multiple)
                st.session_state["hisohiso_msg"] = hisohiso_msg
                if hisohiso_msg:
                    hisohiso_placeholder.markdown(
                        f'<div class="hisohiso-box">{hisohiso_msg}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    hisohiso_placeholder.empty()

            except Exception as e:
                st.error(f"エラーが発生しました：{e}")

# ---- コピー・部長ボタン ----
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.session_state.get("formatted_result"):
        result = st.session_state["formatted_result"]
        copy_html = build_copy_button_html(build_copy_text(fields, result))
        components.html(copy_html, height=50)
    else:
        st.button("クリップボードにコピーしとく", disabled=True, use_container_width=True)

with col2:
    if st.button("プルプル部長に見せてみる🐼", disabled=not st.session_state.get("formatted_result"), use_container_width=True):
        st.switch_page("pages/bucho.py")
