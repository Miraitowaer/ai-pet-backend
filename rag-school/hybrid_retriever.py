import chromadb
import requests
import jieba
from rank_bm25 import BM25Okapi

class HybridRerankRetriever:
    def __init__(self, api_key, db_path="./local_knowledge_db"):
        self.api_key = api_key
        
        # 1. 连接 ChromaDB (加载向量图谱)
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_collection(name="kaoyan_docs")
        
        # 2. 动态重建 BM25 倒排索引
        # 因为我们只有几百个 Chunk，直接从 Chroma 中全量提取文本重建 BM25 是最优雅且最快的
        print("⚙️ 正在从本地知识库加载并构建 BM25 索引...")
        all_data = self.collection.get()
        self.corpus_ids = all_data['ids']
        self.corpus_texts = all_data['documents']
        self.corpus_metas = all_data['metadatas']
        
        tokenized_corpus = [list(jieba.cut(text)) for text in self.corpus_texts]
        self.bm25 = BM25Okapi(tokenized_corpus)
        
        # 3. 硅基流动 API 配置
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.embed_url = "https://api.siliconflow.cn/v1/embeddings"
        self.embed_model = "BAAI/bge-m3"
        
        self.rerank_url = "https://api.siliconflow.cn/v1/rerank"
        self.rerank_model = "BAAI/bge-reranker-v2-m3" # 顶级的开源 Rerank 模型

    def _get_embedding(self, query: str):
        """将 Query 转为向量"""
        payload = {"model": self.embed_model, "input": query, "encoding_format": "float"}
        resp = requests.post(self.embed_url, json=payload, headers=self.headers).json()
        return resp["data"][0]["embedding"]

    def _rerank_candidates(self, query: str, candidate_texts: list[str]) -> list[dict]:
        """调用 Reranker 模型对候选集进行终极打分"""
        payload = {
            "model": self.rerank_model,
            "query": query,
            "documents": candidate_texts,
            "return_documents": False
        }
        response = requests.post(self.rerank_url, json=payload, headers=self.headers)
        
        # 增加防御性编程：如果 API 报错，立刻打印出来，绝不偷偷掩盖
        if response.status_code != 200:
            print(f"❌ Reranker API 调用失败: {response.text}")
            return []
            
        resp = response.json()
        return resp.get("results", [])

    def search(self, query: str, top_k: int = 3, recall_k: int = 10):
        """
        混合检索核心逻辑
        :param recall_k: 每路粗排召回的数量 (默认各召回 10 个，最多 20 个候选)
        :param top_k: 经过精排后，最终输出给大模型的数量
        """
        print(f"\n🔍 收到用户问题：【{query}】")
        
        # 存储所有粗排召回的候选者，使用字典去重 (Key为文本，Value为元数据)
        candidates_pool = {}

        # ================= 阶段一：多路召回 (粗排) =================
        
        # 1. BM25 稀疏召回
        print(f"⚡ [粗排] 正在执行 BM25 关键词召回 (Top-{recall_k})...")
        tokenized_query = list(jieba.cut(query))
        bm25_scores = self.bm25.get_scores(tokenized_query)
        # 获取得分最高的 Top-K 索引
        top_n_bm25_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:recall_k]
        
        for idx in top_n_bm25_indices:
            if bm25_scores[idx] > 0: # 必须有匹配得分
                text = self.corpus_texts[idx]
                candidates_pool[text] = {"source": "BM25", "meta": self.corpus_metas[idx]}

        # 2. ChromaDB 向量召回
        print(f"🌌 [粗排] 正在执行 Chroma 稠密向量召回 (Top-{recall_k})...")
        query_vector = self._get_embedding(query)
        chroma_results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=recall_k
        )
        
        for text, meta in zip(chroma_results['documents'][0], chroma_results['metadatas'][0]):
            if text in candidates_pool:
                candidates_pool[text]["source"] = "BM25 + Chroma (双路命中)"
            else:
                candidates_pool[text] = {"source": "Chroma", "meta": meta}

        # 准备送入精排的候选文本列表
        candidate_texts = list(candidates_pool.keys())
        print(f"📦 粗排结束，共召回 {len(candidate_texts)} 个去重后的候选文本块。")

        # ================= 阶段二：Reranker (精排) =================
        if not candidate_texts:
            print("⚠️ 未召回任何相关内容。")
            return []

        print("🧠 [精排] 正在调用 BGE-Reranker 进行深度语义交叉打分...")
        rerank_results = self._rerank_candidates(query, candidate_texts)
        
        # 按照 relevance_score (相关性得分) 降序排序
        rerank_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # 提取最终的 Top-K
        final_top_k = rerank_results[:top_k]
        
        print("\n" + "="*50)
        print(f"🏆 终极精排 Top-{top_k} 结果")
        print("="*50)
        
        final_documents = []
        for rank, result in enumerate(final_top_k):
            text_index = result["index"]
            score = result["relevance_score"]
            text = candidate_texts[text_index]
            meta = candidates_pool[text]["meta"]
            source = candidates_pool[text]["source"]
            
            final_documents.append(text)
            
            print(f"🥇 [Rank {rank+1}] 相关性得分: {score:.4f} | 召回引擎: {source}")
            print(f"🏫 来源高校: {meta.get('school', '未知')}")
            print(f"📄 内容: {text}")
            print("-" * 50)
            
        return final_documents

# ================= 测试你的混合搜索引擎 =================
if __name__ == "__main__":
    # ⚠️ 填入你的真实 API Key
    YOUR_API_KEY = "sk-tkqtgoblxblenofevcpovkirzziuhsptbxbvjzadsvcgtldu" 
    
    retriever = HybridRerankRetriever(api_key=YOUR_API_KEY)
    
    # 测试问题：包含具体的数字、专有名词和语义意图
    test_query = "哈尔滨工业大学初试考什么科目"
    
    retriever.search(query=test_query, top_k=3, recall_k=10)