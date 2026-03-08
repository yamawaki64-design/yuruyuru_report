import base64
import json
import random
import streamlit as st
import streamlit.components.v1 as components
from prompts.bucho_prompt import build_bucho_prompt
from utils.groq_client import call_groq_json

# ---- 背景画像をbase64に変換 ----
with open("assets/doodle_background_1600x900_soft_100kb.jpg", "rb") as _f:
    _bg_b64 = base64.b64encode(_f.read()).decode()

# ---- ハンコ画像をbase64に変換 ----
with open("assets/hanko.png", "rb") as _f:
    _hanko_b64 = base64.b64encode(_f.read()).decode()

# ---- ページ設定 ----
st.set_page_config(
    page_title="部長室 | ゆるゆる報告書",
    page_icon="🐼",
    layout="centered",
)

# ---- スタイル ----
st.markdown("""
<style>
/* Streamlitデフォルトヘッダーを非表示 */
header[data-testid="stHeader"] { display: none; }

/* ── 固定タイトルバー（.stApp疑似要素で実装） ── */
.stApp::before {
    content: "🐼 部長室";
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

/* ── 部長吹き出し（タブ付き） ── */
.speech-bubble {
    position: relative;
    margin-top: 22px;
    background: white;
    border: 2px solid #FFB74D;
    border-radius: 0 12px 12px 12px;
    padding: 16px 20px;
    font-size: 0.95em;
    line-height: 1.75;
    color: #3e2723;
}
.speech-bubble::before {
    content: "🐼 プルプル部長";
    position: absolute;
    top: -22px;
    left: -2px;
    background: #FFB74D;
    color: white;
    font-size: 0.72em;
    font-weight: bold;
    padding: 3px 10px;
    border-radius: 6px 6px 0 0;
    white-space: nowrap;
    letter-spacing: 0.03em;
}
.speech-bubble::after {
    content: "";
    position: absolute;
    left: -15px;
    top: 22px;
    border: 8px solid transparent;
    border-right-color: #FFB74D;
}

/* ── ハンコ ── */
.hanko-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    padding-top: 16px;
}
.hanko {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    border-radius: 50%;
    border: 4px solid rgba(180, 30, 30, 0.78);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: rgba(180, 30, 30, 0.85);
    font-size: 14px;
    font-weight: bold;
    line-height: 1.5;
    text-align: center;
    filter: blur(0.4px);
    opacity: 0.9;
    transform: rotate(-6deg);
    animation: hanko-stamp 0.5s ease-out forwards;
}
@keyframes hanko-stamp {
    0%   { transform: rotate(-6deg) scale(1.3); opacity: 0.3; }
    60%  { transform: rotate(-6deg) scale(0.95); opacity: 1; }
    80%  { transform: rotate(-6deg) scale(1.03); }
    100% { transform: rotate(-6deg) scale(1.0); opacity: 0.9; }
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

/* ── ボタン（戻る） ── */
[data-testid="stBaseButton-secondary"]:not([disabled]) {
    background-color: white !important;
    color: #546e7a !important;
    border-color: #90a4ae !important;
    font-size: 15px !important;
    font-weight: bold !important;
    padding: 10px 24px !important;
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
            val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            if val else ""
        )
        html += f"""
        <div class="result-item">
            <div class="result-label">{display_name}{req}</div>
            <div class="result-value">{safe_val if safe_val else "&nbsp;"}</div>
        </div>"""
    html += "</div>"
    return html


# ---- ハンコHTML生成（PNG画像・ランダム傾き） ----
def build_hanko_html(img_b64: str, rotation_deg: float) -> str:
    return f"""
    <div class="hanko-wrapper">
        <img src="data:image/png;base64,{img_b64}"
             width="163" height="163"
             style="transform: rotate({rotation_deg:.1f}deg);
                    animation: hanko-stamp 0.5s ease-out forwards;
                    display: block;" />
    </div>
    """


# ---- コピーボタンHTML生成 ----
def build_copy_button_html(copy_text: str, label: str = "クリップボードにコピーしとく 📋") -> str:
    js_text = (
        copy_text
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("`", "\\`")
        .replace("\n", "\\n")
    )
    return f"""
    <meta name="color-scheme" content="light">
    <style>body {{ margin: 0; padding: 0; }}</style>
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


# ---- session_state チェック ----
if not st.session_state.get("formatted_result"):
    st.warning("整形結果がありません。メインページに戻って整形してください。")
    if st.button("戻る"):
        st.switch_page("app.py")
    st.stop()

result = st.session_state["formatted_result"]

# ---- テンプレート読み込み ----
with open("data/template_shidan.json", encoding="utf-8") as f:
    template = json.load(f)
fields = template["fields"]

# ---- 部長コメント取得（ページ初回表示時のみ実行） ----
if "bucho_comment" not in st.session_state:
    with st.spinner("部長が確認中…"):
        try:
            system_prompt = build_bucho_prompt()
            report_text = "\n".join(f"{k}：{v}" for k, v in result.items())
            bucho_result = call_groq_json(system_prompt, report_text)
            st.session_state["bucho_comment"] = bucho_result.get("comment", "…うむ、承認だ。")
            st.session_state["bucho_stamp"] = bucho_result.get("stamp", "承認：プルプル部長")
            # ハンコの傾き：左右どちらかにランダムで5〜15度
            sign = random.choice([-1, 1])
            st.session_state["hanko_rotation"] = sign * random.uniform(5, 15)
        except Exception as e:
            st.error(f"部長の呼び出しに失敗しました：{e}")
            st.stop()

# ---- レイアウト：左（吹き出し）、右（ハンコ） ----
col_left, col_right = st.columns([3, 1])

with col_left:
    comment_html = (
        st.session_state["bucho_comment"]
        .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    st.markdown(
        f'<div class="speech-bubble">{comment_html}</div>',
        unsafe_allow_html=True,
    )

with col_right:
    st.markdown(
        build_hanko_html(_hanko_b64, st.session_state["hanko_rotation"]),
        unsafe_allow_html=True,
    )

# ---- 整形済み報告書パネル ----
st.markdown("---")
st.markdown("**整形済み報告書**")
st.markdown(build_result_html(fields, result), unsafe_allow_html=True)

# ---- 戻るボタン ＋ コピーボタン ----
st.markdown("---")
col_back, col_copy = st.columns(2)

with col_back:
    if st.button("← メインページに戻る", use_container_width=True):
        del st.session_state["bucho_comment"]
        del st.session_state["bucho_stamp"]
        st.switch_page("app.py")

with col_copy:
    copy_text = "\n".join(f"{f['name']}：{result.get(f['name'], '')}" for f in fields)
    components.html(build_copy_button_html(copy_text), height=50)
