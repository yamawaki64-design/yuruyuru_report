import json
import streamlit as st
from groq import Groq

client = Groq(api_key=st.secrets["GROQ_KEY"])


def call_groq(system_prompt: str, user_message: str, model: str = "llama-3.3-70b-versatile") -> str:
    """Groq APIを呼び出してテキストを返す"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    )
    return response.choices[0].message.content


def call_groq_json(system_prompt: str, user_message: str) -> dict:
    """Groq APIを呼び出してJSONをパースして返す"""
    raw = call_groq(system_prompt, user_message)
    clean = raw.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(clean)
