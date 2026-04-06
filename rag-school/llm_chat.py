import requests
import json
from hybrid_retriever import HybridRerankRetriever

class KaoyanRAGChatbot:
    def __init__(self, api_key):
        self.api_key = api_key
        
        # 1. 初始化我们之前写好的混合检索引擎
        print("⚙️ 正在唤醒检索大脑...")
        self.retriever = HybridRerankRetriever(api_key=self.api_key)
        
        # 2. 硅基流动 LLM API 配置 (我们使用免费且强大的 Qwen2.5-7B)
        self.chat_url = "https://api.siliconflow.cn/v1/chat/completions"
        self.llm_model = "Qwen/Qwen2.5-7B-Instruct"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 3. 对话状态管理 (滑动窗口 + 摘要)
        self.max_tokens_limit = 6000 # 留出 2K 给检索文档和系统提示词
        self.history = [] # 存储短时记忆 (最近的对话)
        self.global_summary = "" # 存储长时记忆 (早期的压缩摘要)

    def _estimate_tokens(self, text: str) -> int:
        """粗略估算 Token 数量 (中文字符约占 1-1.5 个 Token)"""
        return int(len(text) * 1.5)

    def _compress_history(self):
        """核心亮点：触碰边界时的记忆压缩算法"""
        if len(self.history) <= 2:
            return # 对话太少，没必要压缩
            
        print("\n[系统动作] ⚠️ 触发上下文窗口保护机制，正在进行历史记忆压缩...")
        
        # 把旧摘要和需要压缩的历史对话拼起来
        text_to_summarize = f"之前的摘要：{self.global_summary}\n\n最近的对话：\n"
        # 留下最后 2 轮作为滑动窗口，前面的全部拿去压缩
        for msg in self.history[:-2]:
            text_to_summarize += f"{msg['role']}: {msg['content']}\n"
            
        prompt = [
            {"role": "system", "content": "你是一个记忆压缩助手。请将以下用户的考研咨询对话，提取出关键事实（如目标院校、专业、用户背景等），浓缩成一段200字以内的摘要。不要遗漏核心条件。"},
            {"role": "user", "content": text_to_summarize}
        ]
        
        payload = {"model": self.llm_model, "messages": prompt, "temperature": 0.3}
        resp = requests.post(self.chat_url, json=payload, headers=self.headers).json()
        
        # 更新长时记忆
        self.global_summary = resp['choices'][0]['message']['content']
        # 更新短时记忆 (只保留最新的 2 轮)
        self.history = self.history[-2:]
        print(f"[系统动作] ✅ 记忆压缩完成。当前长时记忆：{self.global_summary}\n")
    
    def _rewrite_query(self, original_query: str) -> str:
        """【新增核心】根据历史对话，将用户省略的问题重写为完整的独立问题"""
        # 如果是第一轮对话，没有上下文，直接返回原问题
        if not self.history:
            return original_query
            
        print("\n✍️ [系统动作] 正在根据上下文重写用户的搜索意图...")
        
        # 提取最近的对话历史作为参考
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.history[-4:]])
        
        rewrite_prompt = f"""
        你是一个专业的搜索词重写助手。
        请根据用户的【历史对话】，将用户的【最新问题】重写为一个独立、完整、不带代词（这个、那个、他等）的查询句子。
        要求：
        1. 补全缺失的主语或专业名词。
        2. 不要回答问题，【只输出重写后的句子】。如果不需要重写，直接输出原句。

        【历史对话】：
        {history_text}

        【最新问题】：{original_query}

        重写后的独立查询："""

        payload = {
            "model": self.llm_model, 
            "messages": [{"role": "user", "content": rewrite_prompt}],
            "temperature": 0.1 # 温度调低，保证只做机械改写，不发散
        }
        
        try:
            resp = requests.post(self.chat_url, json=payload, headers=self.headers).json()
            rewritten_query = resp['choices'][0]['message']['content'].strip()
            # 简单清洗一下 LLM 可能带上的废话（如 "重写后的句子是："）
            rewritten_query = rewritten_query.replace("重写后的独立查询：", "").replace("重写后的句子：", "").strip(' \n"\'')
            print(f"🔄 意图改写: 【{original_query}】 -> 【{rewritten_query}】")
            return rewritten_query
        except Exception as e:
            print(f"⚠️ 改写失败，降级使用原问题。错误: {e}")
            return original_query

    def _build_final_prompt(self, query: str, retrieved_docs: list[str]) -> list[dict]:
        """组装终极 RAG Prompt (系统指令 + 摘要 + 历史 + 检索知识 + 当前问题)"""
        
        # 1. 严格的 System Prompt (防幻觉约束)
        system_content = """你是一个专业的【考研择校咨询专家】。
        请严格遵循以下规则：
        1. 你必须【且只能】根据我提供给你的<参考知识>来回答问题。
        2. 如果<参考知识>中没有相关信息，请直接回答“根据知识库，暂未查到相关信息”，绝不要自己瞎编！
        3. 回答要条理清晰，可以使用 Markdown 列表。"""
        
        # 加入长时记忆摘要
        if self.global_summary:
            system_content += f"\n\n已知用户的历史背景信息：{self.global_summary}"
            
        messages = [{"role": "system", "content": system_content}]
        
        # 2. 注入短时记忆 (滑动窗口)
        messages.extend(self.history)
        
        # 3. 注入检索到的知识和当前问题
        context_str = "\n\n".join([f"[材料 {i+1}] {doc}" for i, doc in enumerate(retrieved_docs)])
        user_prompt = f"【参考知识】：\n{context_str}\n\n【我的问题】：{query}"
        
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def ask(self, query: str):
        """处理一轮对话的主逻辑"""
        # 第一步：检查并控制历史 Token 长度
        current_history_text = str(self.history)
        if self._estimate_tokens(current_history_text) > self.max_tokens_limit:
            self._compress_history()

        # ==================== 【关键修改点】 ====================
        # 第二步：调用 LLM 重写 Query，补全指代
        search_query = self._rewrite_query(query)
        
        # 第三步：用【重写后的完整 Query】去向量库和 BM25 检索
        print("-" * 50)
        retrieved_docs = self.retriever.search(query=search_query, top_k=3, recall_k=10)
        
        # 第四步：组装 Prompt 并请求大模型解答
        # 注意：最终给 LLM 看的还是用户的原始提问(query)，而不是改写后的(search_query)，这样回答更自然
        messages = self._build_final_prompt(query, retrieved_docs)
        # ========================================================
        
        print("\n🤖 考研专家正在思考...")
        payload = {
            "model": self.llm_model,
            "messages": messages,
            "temperature": 0.5, # 偏向严谨
        }
        resp = requests.post(self.chat_url, json=payload, headers=self.headers).json()
        
        if 'choices' not in resp:
            print(f"❌ LLM 请求失败: {resp}")
            return
            
        answer = resp['choices'][0]['message']['content']
        
        # 第四步：将本轮对话存入历史记录
        self.history.append({"role": "user", "content": query})
        self.history.append({"role": "assistant", "content": answer})
        
        print("\n🎓 【专家回复】:")
        print(answer)
        print("-" * 50)
        return answer

# ================= 启动交互式聊天控制台 =================
if __name__ == "__main__":
    # ⚠️ 替换为你真实的 API Key
    YOUR_API_KEY = "sk-tkqtgoblxblenofevcpovkirzziuhsptbxbvjzadsvcgtldu" 
    
    chatbot = KaoyanRAGChatbot(api_key=YOUR_API_KEY)
    
    print("\n" + "="*50)
    print("🎉 面向高校知识库的考研择校系统 (终端测试版) 已启动！")
    print("💡 提示：输入 'quit' 退出，输入 'clear' 清空记忆。")
    print("="*50)
    
    while True:
        user_input = input("\n🧑‍🎓 提问: ")
        if user_input.strip().lower() == 'quit':
            print("再见！祝你考研上岸！")
            break
        if user_input.strip().lower() == 'clear':
            chatbot.history = []
            chatbot.global_summary = ""
            print("🧹 记忆已清空。")
            continue
            
        if user_input.strip():
            chatbot.ask(user_input)