import chromadb
from rank_bm25 import BM25Okapi
import jieba
import requests
import os

class KnowledgeBaseManager:
    def __init__(self, api_key, db_path="./local_knowledge_db"):
        # 1. 初始化 ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name="kaoyan_docs",
            metadata={"hnsw:space": "cosine"} 
        )
        
        self.corpus_chunks = []
        self.bm25_model = None
        
        # 2. 硅基流动 API 配置
        self.api_key = api_key
        self.api_url = "https://api.siliconflow.cn/v1/embeddings"
        # 推荐使用 BGE-M3，这是目前中文检索的顶流开源模型
        self.model_name = "BAAI/bge-m3" 

    def _get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """调用硅基流动 API，批量获取文本向量"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "input": texts,
            "encoding_format": "float"
        }
        
        print(f"正在通过硅基流动API对 {len(texts)} 个文本块进行向量化...")
        response = requests.post(self.api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()["data"]
            # API 返回的数据结构中，每个 item 包含一个 'embedding' 数组
            return [item["embedding"] for item in data]
        else:
            raise Exception(f"Embedding API 调用失败: HTTP {response.status_code} - {response.text}")

    def add_documents(self, documents: list[dict]):
        if not documents:
            return

        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["meta"] for doc in documents]
        
        # ----------------- A路：存入 ChromaDB (调用 API 生成向量) -----------------
        # 注意：如果单次入库的 texts 超过百条，建议在外部进行分批次 (如每批 50 条) 调用此方法
        embeddings = self._get_embeddings_batch(texts)

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        print(f"成功将 {len(ids)} 个 chunks 的向量存入 ChromaDB!")

        # ----------------- B路：构建 BM25 索引 -----------------
        self.corpus_chunks.extend(texts)
        tokenized_corpus = [list(jieba.cut(text)) for text in self.corpus_chunks]
        self.bm25_model = BM25Okapi(tokenized_corpus)
        print(f"成功更新 BM25 索引，当前库中共有 {len(self.corpus_chunks)} 个 chunks。")

# ================= 测试你的云端向量化引擎 =================
if __name__ == "__main__":
    # 替换为你自己在硅基流动控制台申请的 API Key (通常以 sk- 开头)
    YOUR_API_KEY = "sk-tkqtgoblxblenofevcpovkirzziuhsptbxbvjzadsvcgtldu" 
    
    kb = KnowledgeBaseManager(api_key=YOUR_API_KEY)
    
    mock_chunks = [
        {"id": "doc_01", "text": "清华大学计算机系招生计划包含人工智能方向15人。", "meta": {"school": "清华大学"}},
        {"id": "doc_02", "text": "北京大学软件工程专业不接受同等学力跨考。", "meta": {"school": "北京大学"}}
    ]
    
    kb.add_documents(mock_chunks)