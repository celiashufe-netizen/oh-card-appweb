import streamlit as st
from openai import OpenAI
import os, random, re

# 1. 界面美化
st.set_page_config(page_title="OH卡私人引导师", layout="wide")
st.markdown("<style>.stApp { background-color: #F7F3F0; color: #3A3A3A; }</style>", unsafe_allow_html=True)

# 2. 初始化 DeepSeek 客户端
client = OpenAI(api_key=st.secrets["API_KEY"], base_url=st.secrets["BASE_URL"])

# 3. 文档与 AI 响应
def get_ai_response(prompt_text):
    try:
        response = client.chat.completions.create(
            model=st.secrets["MODEL_NAME"],
            messages=[{"role": "user", "content": prompt_text}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ 引导师忙线中（请检查 DeepSeek 余额或 Key）"

# --- 状态管理逻辑 (保持你的原版，仅替换调用函数) ---
if 'phase' not in st.session_state: st.session_state.phase = 'input'
if 'messages' not in st.session_state: st.session_state.messages = []

with st.sidebar:
    st.markdown("### 🪞 潜意识镜子")
    user_issue = st.text_area("当下的困惑", height=150)
    if st.button("🔮 推荐牌阵"):
        if user_issue:
            st.session_state.user_issue, st.session_state.phase = user_issue, 'recommend'
        else: st.warning("请输入困惑")
    if st.button("🔄 重新开始"):
        st.session_state.clear(); st.rerun()

st.title("💡 OH卡私人引导师")

# (此处省略其余 UI 逻辑，与你之前的 app.py 保持一致，只需确保调用的是 get_ai_response)
# ... [逻辑同前，调用 DeepSeek 的响应] ...