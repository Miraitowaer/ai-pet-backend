import streamlit as st
from llm_chat import KaoyanRAGChatbot

# ================= 1. 页面全局配置 =================
st.set_page_config(
    page_title="考研择校AI系统",
    page_icon="🎓",
    layout="centered" # 居中布局，类似 ChatGPT
)

st.title("🎓 面向高校知识库的考研择校系统")
st.caption("基于 RAG 架构 (BM25 + ChromaDB + BGE-Reranker) 的智能问答引擎")

# ================= 2. 初始化核心系统与状态 =================
# st.session_state 是 Streamlit 的状态保持机制
# 确保每次用户提问刷新页面时，我们的 AI 大脑不会失忆

if "chatbot" not in st.session_state:
    # ⚠️ 请在这里填入你的真实 API Key
    YOUR_API_KEY = "sk-tkqtgoblxblenofevcpovkirzziuhsptbxbvjzadsvcgtldu" 
    
    with st.spinner("正在初始化检索大脑与知识库..."):
        st.session_state.chatbot = KaoyanRAGChatbot(api_key=YOUR_API_KEY)

if "ui_messages" not in st.session_state:
    # UI 界面的初始欢迎语
    st.session_state.ui_messages = [
        {"role": "assistant", "content": "你好！我是考研择校AI专家。我的大脑中装载了多所高校的最新招生简章。请问你想了解哪个学校的具体信息？"}
    ]

# ================= 3. 渲染历史对话气泡 =================
for msg in st.session_state.ui_messages:
    # st.chat_message 会自动生成漂亮的用户头像和 AI 头像
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ================= 4. 处理用户输入与交互 =================
# st.chat_input 会在页面底部生成一个固定输入框
if prompt := st.chat_input("例如：哈尔滨理工大学的直博选拔方式是什么？"):
    
    # 将用户的问题显示在界面上
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.ui_messages.append({"role": "user", "content": prompt})

    # 调用 RAG 系统生成回答
    with st.chat_message("assistant"):
        # st.spinner 会显示一个转圈的加载动画，用户体验极佳
        with st.spinner("🧠 正在进行多路召回与语义精排..."):
            try:
                # 调用我们封装好的大模型系统
                answer = st.session_state.chatbot.ask(prompt)
                if not answer:
                    answer = "抱歉，系统请求大模型时出现异常，请稍后再试。"
            except Exception as e:
                answer = f"系统发生内部错误：{e}"
                
        # 将回答渲染到页面
        st.markdown(answer)
        
    st.session_state.ui_messages.append({"role": "assistant", "content": answer})