import streamlit as st
from openai import OpenAI
import os, random, re

# 1. 界面美化
st.set_page_config(page_title="OH卡私人引导师", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #F7F3F0; color: #3A3A3A; }
    .stChatMessage { background-color: rgba(255,255,255,0.6); border-radius: 12px; padding: 15px; margin-bottom: 10px;}
    .stButton>button { border-radius: 20px; border: 1px solid #D1C4E9; width: 100%; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. 初始化 DeepSeek 客户端 (读取你设置好的 Secrets)
client = OpenAI(
    api_key=st.secrets["API_KEY"],
    base_url=st.secrets["BASE_URL"]
)

# 3. 文档加载
def load_docs():
    sop, spreads_text, names = "你是一位专业OH卡引导师，请温和引导。", "默认库", ["单卡盲抽"]
    try:
        if os.path.exists('ai_sop.md'):
            with open('ai_sop.md', 'r', encoding='utf-8') as f: sop = f.read()
        if os.path.exists('spreads.md'):
            with open('spreads.md', 'r', encoding='utf-8') as f:
                spreads_text = f.read()
                found = re.findall(r'牌阵名称：(.*?)(?:\s|$)', spreads_text)
                if found: names = found
    except: pass
    return sop, spreads_text, names

sop_content, spreads_content, spread_options = load_docs()

def get_ai_response(prompt_text):
    try:
        response = client.chat.completions.create(
            model=st.secrets["MODEL_NAME"],
            messages=[{"role": "user", "content": prompt_text}],
            stream=False
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ 引导师暂时掉线了（报错：{str(e)}）"

# --- 状态管理 ---
if 'phase' not in st.session_state: st.session_state.phase = 'input'
if 'revealed_count' not in st.session_state: st.session_state.revealed_count = 1
if 'messages' not in st.session_state: st.session_state.messages = []

# 4. 侧边栏
with st.sidebar:
    st.markdown("### 🪞 潜意识镜子")
    user_issue = st.text_area("当下的困惑", placeholder="描述你想探索的情境...", height=150)
    
    if st.button("🔮 让引导师推荐牌阵"):
        if user_issue:
            st.session_state.user_issue = user_issue
            st.session_state.phase = 'recommend'
            st.session_state.recommendation = None
            st.rerun() # 强制刷新以进入推荐阶段
        else: st.warning("请输入你的困惑")
            
    if st.button("🔄 重新开始"):
        st.session_state.clear()
        st.session_state.phase = 'input'
        st.rerun()

# 5. 主界面逻辑
st.title("💡 OH卡私人引导师")

if st.session_state.phase == 'input':
    st.info("👈 欢迎，Celia。请在左侧侧边栏输入你当下的困惑。")

elif st.session_state.phase == 'recommend':
    if st.session_state.get('recommendation') is None:
        with st.spinner("引导师思考中..."):
            prompt = f"用户困惑：{st.session_state.user_issue}\n牌阵库：{spreads_content}\n请推荐1个最适合的牌阵。"
            st.session_state.recommendation = get_ai_response(prompt)
    st.success(f"🌿 **建议：**\n\n{st.session_state.recommendation}")
    selected_spread = st.selectbox("确认最终使用的牌阵：", spread_options)
    if st.button("🎴 开始发牌"):
        st.session_state.selected_spread = selected_spread
        st.session_state.phase = 'prepare_draw'
        st.rerun()

elif st.session_state.phase == 'prepare_draw':
    with st.spinner("计算牌阵中..."):
        prompt = f"牌阵【{st.session_state.selected_spread}】需要几张牌？只回数字。参考：{spreads_content}"
        count_str = get_ai_response(prompt)
        st.session_state.card_count = int(re.search(r'\d+', count_str).group()) if re.search(r'\d+', count_str) else 1
        st.session_state.phase = 'draw'
        st.rerun()

elif st.session_state.phase == 'draw':
    pic_p = "OH卡 基础卡图卡"
    if 'drawn_cards' not in st.session_state:
        try:
            img_list = [f for f in os.listdir(pic_p) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            st.session_state.drawn_cards = [(random.choice(img_list), None) for _ in range(st.session_state.card_count)]
        except Exception as e:
            st.error(f"图片加载失败：{e}")

    st.markdown(f"### 🎴 【{st.session_state.selected_spread}】 (第 {st.session_state.revealed_count}/{st.session_state.card_count} 张)")
    for i in range(st.session_state.revealed_count):
        img_f, _ = st.session_state.drawn_cards[i]
        st.image(os.path.join(pic_p, img_f), width=450)
        st.markdown("---")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if not st.session_state.messages:
        with st.spinner("引导师进入状态..."):
            reply = get_ai_response(f"SOP：{sop_content}\n困惑：{st.session_state.user_issue}\n牌阵：{st.session_state.selected_spread}\n第一张图：{st.session_state.drawn_cards[0][0]}。请引导。")
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

    if st.session_state.revealed_count < st.session_state.card_count:
        if st.button(f"✨ 揭晓第 {st.session_state.revealed_count + 1} 张牌"):
            st.session_state.revealed_count += 1
            new_card = st.session_state.drawn_cards[st.session_state.revealed_count-1][0]
            reply = get_ai_response(f"新翻开第{st.session_state.revealed_count}张：{new_card}。继续引导。")
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

    if user_input := st.chat_input("在画面中你看到了什么？"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("assistant"):
            history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            reply = get_ai_response(f"SOP：{sop_content}\n历史记录：{history}\n请回应并引导。")
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()