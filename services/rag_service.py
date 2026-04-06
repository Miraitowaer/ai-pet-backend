import os
import sys

# 将 rag-school 临时挂载到 Python 路径下，方便直接导入
rag_school_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rag-school")
if rag_school_path not in sys.path:
    sys.path.insert(0, rag_school_path)

from config import settings

class RAGServiceManager:
    """
    独立且封闭的 RAG 微模型管理核心。
    采用单例模式，保证 Chromadb 引擎和 BM25 内存只加载一次。
    """
    _instance = None
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized: return
        self._initialized = True
        self.retriever = None
        
        # 强制指向上游的知识图谱物理库文件
        local_db_path = os.path.join(rag_school_path, "local_knowledge_db")
        print(f"[*] 侦测 RAG 数据库路径: {local_db_path}")
        
        if os.path.exists(local_db_path):
            try:
                # 这种动态引入方式避免了它因缺乏库而让整个网关崩溃
                from hybrid_retriever import HybridRerankRetriever
                print("[*] 正在向硅基流动云端请求鉴权并加载 BGE 混合物理跨引擎...")
                self.retriever = HybridRerankRetriever(
                    api_key=settings.llm_api_key,
                    db_path=local_db_path
                )
                print("[*] ✅ RAG 多模态知识图谱热插拔成功！")
            except Exception as e:
                print(f"[*] ❌ RAG 底层加载失败: {e}")
        else:
            print("[*] ⚠️ 找不到 local_knowledge_db 目录，RAG 高级挂图瘫痪。")
            
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def query(self, text: str, top_k: int = 2) -> str:
        """从专家库捞取内容并将其格式化为上下文"""
        if not self.retriever:
            return "对不起主人，我这里的考研知识库系统出了点故障或者未挂载，暂时无法访问学术档案。"
        
        try:
            # 双路召回提取
            results = self.retriever.search(query=text, top_k=top_k, recall_k=10)
            if not results:
                return "我在档案图谱里努力用量子检索搜过啦，但是知识库中没有任何关于这个问题的记录..."
            return "\n\n".join([f"【检索证据片段 {i+1}】\n{r}" for i, r in enumerate(results)])
        except Exception as e:
            return f"发生了次元断裂，检索失败：{str(e)}"
            
# 我们去掉了底层自动 rag_manager = RAGServiceManager.get_instance() 的急切初始化
# 保证引入模块本身是非常轻量的！
