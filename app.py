import streamlit as st
import google.generativeai as genai
import os
import random
import re

# ==========================================
# 1. 核心：强制本地代理 (针对上海移动/电信环境)
# ==========================================
# 只要你用的是 Clash Verge，且端口是 7897，这几行就是你的“通行证”


# 2. 界面美化
st.set_page_config(page_title="OH卡私人引导师", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #F7F3F0; color: #3A3A3A; }
    .stChatMessage { background-color: rgba(255,255,255,0.6); border-radius: 12px; padding: 15px; margin-bottom: 10px;}
    .stButton>button { border-radius: 20px; border: 1px solid #D1C4E9; width: 100%; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 3. 文档加载
def load_docs():
    sop, spreads_text, names = "你是一位专业OH卡引导师，请温和地引导用户。", "默认牌阵库", ["单卡盲抽"]
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

# 4. 关键：封装响应函数，确保每次调用都带上最新的配置
def get_ai_response(prompt_text):
    if not st.session_state.get('api_key'):
        return "⚠️ 请先在左侧填入 API Key"
    
    # 强制重新配置，确保本地代理生效
    genai.configure(api_key=st.session_state.api_key, transport='rest')
    
    for model_name in ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash']:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt_text)
            return response.text.strip()
        except Exception as e:
            continue
    return "⚠️ 引导师依然无法连接，请确认 Clash Verge 的【系统代理】已开启，且端口为 7897。"

# --- 状态机初始化 ---
if 'phase' not in st.session_state: st.session_state.phase = 'input'
if 'revealed_count' not in st.session_state: st.session_state.revealed_count = 1
if 'messages' not in st.session_state: st.session_state.messages = []

# 5. 侧边栏
with st.sidebar:
    st.markdown("### 🪞 潜意识镜子")
    api_key = st.text_input("Gemini API Key", type="password")
    user_issue = st.text_area("当下的困惑", placeholder="描述你想探索的情境...", height=150)
    
    if st.button("🔮 让引导师推荐牌阵"):
        if api_key and user_issue:
            st.session_state.api_key = api_key.strip()
            st.session_state.user_issue = user_issue
            st.session_state.phase = 'recommend'
            st.session_state.recommendation = None
        else: st.warning("请填入 Key 和 困惑内容")
            
    if st.button("🔄 重新开始"):
        for k in ['phase', 'recommendation', 'drawn_cards', 'messages', 'card_count', 'revealed_count', 'selected_spread']:
            if k in st.session_state: del st.session_state[k]
        st.session_state.phase = 'input'
        st.session_state.revealed_count = 1
        st.session_state.messages = []
        st.rerun()

# 6. 主逻辑
st.title("💡 OH卡私人引导师")

if st.session_state.phase == 'input':
    st.info("👈 请在左侧侧边栏输入困惑。")

elif st.session_state.phase == 'recommend':
    if st.session_state.get('recommendation') is None:
        with st.spinner("引导师查阅牌阵库中..."):
            # 使用三引号，防止语法报错
            prompt = f"""
            用户困惑：{st.session_state.user_issue}
            牌阵库内容：{spreads_content}
            请推荐1个最适合的牌阵并温和说明原因。
            """
            st.session_state.recommendation = get_ai_response(prompt)
    
    st.success(f"🌿 **建议：**\n\n{st.session_state.recommendation}")
    st.markdown("---")
    selected_spread = st.selectbox("确认牌阵：", spread_options)
    if st.button("🎴 确认，准备发牌"):
        st.session_state.selected_spread = selected_spread
        st.session_state.phase = 'prepare_draw'
        st.rerun()

elif st.session_state.phase == 'prepare_draw':
    with st.spinner("计算布局中..."):
        prompt = f"牌阵【{st.session_state.selected_spread}】需要几张牌？只回数字。参考：{spreads_content}"
        count_str = get_ai_response(prompt)
        st.session_state.card_count = int(re.search(r'\d+', count_str).group()) if re.search(r'\d+', count_str) else 1
        st.session_state.phase = 'draw'
        st.rerun()

elif st.session_state.phase == 'draw':
    pic_p, word_p = "OH卡 基础卡图卡", "OH卡基础卡 字卡"
    
    if st.session_state.get('drawn_cards') is None:
        try:
            img_list = [f for f in os.listdir(pic_p) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            word_list = [f for f in os.listdir(word_p) if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists(word_p) else []
            drawn = []
            for _ in range(st.session_state.card_count):
                img_f = random.choice(img_list)
                word_f = random.choice(word_list) if word_list else None
                drawn.append((img_f, word_f))
            st.session_state.drawn_cards = drawn
        except Exception as e: st.error(f"图片加载失败: {e}")

    st.markdown(f"### 🎴 【{st.session_state.selected_spread}】 (进度: {st.session_state.revealed_count}/{st.session_state.card_count})")
    
    for i in range(st.session_state.revealed_count):
        img_f, word_f = st.session_state.drawn_cards[i]
        st.markdown(f"**位置 {i+1}**")
        if word_f:
            c1, c2 = st.columns(2)
            with c1: st.image(os.path.join(pic_p, img_f), use_container_width=True)
            with c2: st.image(os.path.join(word_p, word_f), use_container_width=True)
        else:
            st.image(os.path.join(pic_p, img_f), width=450)
        st.markdown("---")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if not st.session_state.messages:
        with st.spinner("引导师进入状态..."):
            prompt = f"SOP：{sop_content}\n困惑：{st.session_state.user_issue}\n牌阵：{st.session_state.selected_spread}\n当前仅翻开第1张牌：{st.session_state.drawn_cards[0]}。请发起引导。"
            reply = get_ai_response(prompt)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

    if st.session_state.revealed_count < st.session_state.card_count:
        if st.button(f"✨ 揭晓第 {st.session_state.revealed_count + 1} 张牌"):
            st.session_state.revealed_count += 1
            new_card = st.session_state.drawn_cards[st.session_state.revealed_count-1]
            prompt = f"用户翻开第{st.session_state.revealed_count}张牌：{new_card}。请针对新画面引导。"
            reply = get_ai_response(prompt)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

    if user_input := st.chat_input("分享你的感受..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("assistant"):
            with st.spinner("倾听中..."):
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                reply = get_ai_response(f"SOP：{sop_content}\n对话：{history}\n回应并引导。")
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()

    if st.session_state.messages:
        export_text = f"【OH卡日记】\n困惑：{st.session_state.user_issue}\n\n" + "\n\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        st.download_button("📥 导出日记", data=export_text, file_name="OH日记.txt", use_container_width=True)
