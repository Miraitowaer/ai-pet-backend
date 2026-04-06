import chromadb
import requests

class SingleVectorRetriever:
    def __init__(self, api_key, db_path="./local_knowledge_db"):
        self.api_key = api_key
        # 1. 连接本地已有的 ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        # 获取我们之前建好的集合
        self.collection = self.chroma_client.get_collection(name="kaoyan_docs")
        
        # 硅基流动 API 配置 (必须和入库时用的模型完全一致！)
        self.api_url = "https://api.siliconflow.cn/v1/embeddings"
        self.model_name = "BAAI/bge-m3"

    def _get_query_embedding(self, query: str) -> list[float]:
        """将用户的自然语言问题转化为向量"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "input": query,
            "encoding_format": "float"
        }
        response = requests.post(self.api_url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()["data"][0]["embedding"]
        else:
            raise Exception(f"API 调用失败: HTTP {response.status_code}")

    def search(self, query: str, top_k: int = 3):
        """执行向量检索"""
        print(f"🔍 收到用户问题：【{query}】")
        print("🧠 正在将问题转化为语义向量...")
        
        # 1. 问题向量化
        query_vector = self._get_query_embedding(query)
        
        print(f"📚 正在知识库中进行 HNSW 向量近似搜索 (Top-{top_k})...\n")
        # 2. 去 ChromaDB 中查询最相似的 Chunk
        # n_results 就是我们要的 Top-K
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k
        )
        
        # 3. 解析并打印结果
        # Chroma 返回的是一个嵌套列表，因为你可以一次搜多个 Query。这里我们只搜了一个，所以取 [0]
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0] # 余弦距离，越小代表越相似
        
        print("-" * 50)
        for i in range(len(documents)):
            school = metadatas[i].get('school', '未知高校')
            print(f"🥇 [Top {i+1}] 匹配度得分: {1 - distances[i]:.4f} | 来源: {school}")
            print(f"📄 召回内容: {documents[i]}")
            print("-" * 50)

# ================= 测试你的单路检索器 =================
if __name__ == "__main__":
    # ⚠️ 记得替换为你真实的 API Key
    YOUR_API_KEY = "sk-tkqtgoblxblenofevcpovkirzziuhsptbxbvjzadsvcgtldu" 
    
    retriever = SingleVectorRetriever(api_key=YOUR_API_KEY)
    
    # 你可以随便换成你想问的问题
    user_question = "哈尔滨理工大学2026年直接攻博有什么选拔方式？"
    # user_question = "专业代码 081200表示的是什么专业"
    # user_question = "2025年东南大学计算机学院计算机科学与技术专业招收的研究生有哪些？"
    
    retriever.search(query=user_question, top_k=3)