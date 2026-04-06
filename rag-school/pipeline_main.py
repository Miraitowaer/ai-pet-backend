import os
import re
import time
# 导入我们之前写好的向量库与 BM25 管理器
from knowledge_base import KnowledgeBaseManager

class MarkdownSemanticChunker:
    """专为 Markdown 格式打造的语义切分器"""
    def __init__(self, max_chunk_size=400, overlap=50):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        
        # 匹配 Markdown 的 1-3 级标题
        self.header_patterns = [
            {"level": 1, "pattern": re.compile(r"^#\s+(.*)")},      # 匹配: # 标题
            {"level": 2, "pattern": re.compile(r"^##\s+(.*)")},     # 匹配: ## 标题
            {"level": 3, "pattern": re.compile(r"^###\s+(.*)")},    # 匹配: ### 标题
        ]

    def _slide_window_split(self, text, context_prefix=""):
        """微观滑动窗口：对超长段落进行截断，并保留上下文前缀"""
        chunks = []
        effective_chunk_size = self.max_chunk_size - len(context_prefix)
        
        if len(text) <= effective_chunk_size:
            return [context_prefix + text]

        start = 0
        while start < len(text):
            end = min(start + effective_chunk_size, len(text))
            chunk_text = text[start:end]
            chunks.append(context_prefix + chunk_text)
            start += (effective_chunk_size - self.overlap)
            if effective_chunk_size <= self.overlap: break
        return chunks

    def split_markdown(self, markdown_text, source_meta=None):
        """宏观语义切分：解析 MD 结构，生成带完整语义前缀的 Chunk"""
        if source_meta is None: source_meta = {}
        lines = markdown_text.split('\n')
        
        current_headers = {1: "", 2: "", 3: ""}
        current_paragraph = []
        final_chunks = []
        
        def flush_paragraph():
            if not current_paragraph: return
            text_block = " ".join(current_paragraph).strip()
            if not text_block: return
            
            # 组装黄金语义路径，例如: "[哈尔滨理工大学 - 一、招生规模 - （一）直接攻博]"
            path_elements = [source_meta.get("school", "")] + [v for k, v in sorted(current_headers.items()) if v]
            context_prefix = f"[{' - '.join(filter(None, path_elements))}] " if path_elements else ""
            
            split_blocks = self._slide_window_split(text_block, context_prefix)
            
            for i, block in enumerate(split_blocks):
                final_chunks.append({
                    "id": f"{source_meta.get('school', 'doc')}_chunk_{len(final_chunks)}_{i}",
                    "text": block,
                    "meta": {
                        "school": source_meta.get("school", ""),
                        "h1": current_headers[1],
                        "h2": current_headers[2],
                        "h3": current_headers[3]
                    }
                })
            current_paragraph.clear()

        for line in lines:
            line = line.strip()
            if not line: continue
            
            matched_level = None
            for hp in self.header_patterns:
                match = hp["pattern"].match(line)
                if match:
                    matched_level = hp["level"]
                    flush_paragraph() # 遇到新标题，把上一段入库
                    current_headers[matched_level] = match.group(1).strip()
                    # 清空更低级别的标题
                    for level in range(matched_level + 1, 4):
                        current_headers[level] = ""
                    break
                    
            if not matched_level:
                current_paragraph.append(line)
                
        flush_paragraph()
        return final_chunks

def run_pipeline():
    # 1. 初始化配置
    raw_data_dir = "./raw_data"
    # 填入你的硅基流动 API Key
    YOUR_API_KEY = "sk-tkqtgoblxblenofevcpovkirzziuhsptbxbvjzadsvcgtldu" 
    
    print("🚀 正在初始化知识库引擎...")
    kb_manager = KnowledgeBaseManager(api_key=YOUR_API_KEY)
    chunker = MarkdownSemanticChunker(max_chunk_size=400, overlap=50)
    
    # 2. 读取所有的 Markdown 文件
    md_files = [f for f in os.listdir(raw_data_dir) if f.endswith('.md')]
    if not md_files:
        print("❌ 未在 raw_data 目录下找到 Markdown 文件！")
        return
        
    print(f"📦 发现 {len(md_files)} 个高校招生简章，开始执行 ETL 流水线...\n")
    
    all_chunks = []
    
    # 3. 逐个文件进行清洗和切块
    for filename in md_files:
        filepath = os.path.join(raw_data_dir, filename)
        # 从文件名推断学校名称 (假设文件名为 "哈尔滨理工大学2026年...招生简章.md")
        clean_name = re.sub(r'\d{4}年?', '', filename) # 删掉 "2026", "2025年" 等
        school_name = clean_name.replace('博士研究生招生简章', '').replace('招生简章', '').replace('.md', '').strip()
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        # 调用切分器
        chunks = chunker.split_markdown(content, source_meta={"school": school_name})
        all_chunks.extend(chunks)
        print(f"✂️  [{school_name}] 切分完成，产生 {len(chunks)} 个 Chunk。")
        
    print(f"\n🧠 全局总计生成 {len(all_chunks)} 个 Chunk，准备开始向量化入库...")
    
    # 4. 批量存入 ChromaDB 与 BM25 (分批次请求防止 API 超时)
    batch_size = 50 # 每次发 50 个给硅基流动 API
    for i in range(0, len(all_chunks), batch_size):
        batch_chunks = all_chunks[i:i + batch_size]
        print(f"⏳ 正在入库批次 {i//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}...")
        
        try:
            kb_manager.add_documents(batch_chunks)
            time.sleep(1) # 给 API 喘口气
        except Exception as e:
            print(f"❌ 批次入库失败: {e}")
            
    print("\n🎉 恭喜！所有高校数据已成功转化为向量图谱并建立倒排索引！系统的基建彻底完工！")

if __name__ == "__main__":
    run_pipeline()