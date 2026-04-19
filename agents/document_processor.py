import os
import hashlib
from typing import List, Dict
from datetime import datetime
from config import Config

class DocumentProcessor:
    """文档上传和RAG处理"""
    
    def __init__(self):
        # 确保上传目录存在
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # 使用内存存储文档
        self.documents = {}
        self.available = True
        print("✅ 文档处理模块初始化成功")
    
    def save_document(self, file_path: str, content: str, metadata: Dict = None) -> str:
        """保存文档"""
        doc_id = hashlib.md5(f"{file_path}{datetime.now()}".encode()).hexdigest()
        
        # 分块处理
        chunks = self._chunk_text(content, Config.CHUNK_SIZE)
        
        self.documents[doc_id] = {
            "source": file_path,
            "chunks": chunks,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        return f"文档已保存: {os.path.basename(file_path)}，共 {len(chunks)} 个片段"
    
    def _chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """文本分块"""
        # 按段落分割
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # 如果没有分块成功，按单词分块
        if not chunks:
            words = text.split()
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i+chunk_size])
                chunks.append(chunk)
        
        return chunks

    def search_documents(self, query: str, k: int = 5) -> List[str]:
        """搜索相关文档片段（支持中文）"""
        if not query:
            return []

        results = []
        query_lower = query.lower()

        for doc_id, doc in self.documents.items():
            for chunk in doc['chunks']:
                chunk_lower = chunk.lower()
                # 对于中文：直接检查查询字符串是否部分包含于 chunk
                # 或者检查 chunk 是否包含查询中长度>=2的子串
                if query_lower in chunk_lower:
                    results.append(chunk)
                    if len(results) >= k:
                        return results[:k]
                else:
                    # 检查是否有部分重叠（任意长度≥2的子串匹配）
                    matched = False
                    for i in range(len(query_lower) - 1):
                        sub = query_lower[i:i + 2]
                        if sub in chunk_lower:
                            matched = True
                            break
                    if matched:
                        results.append(chunk)
                        if len(results) >= k:
                            return results[:k]
        return results[:k]
    
    def get_all_documents(self) -> List[Dict]:
        """获取所有文档信息"""
        docs = []
        for doc_id, doc in self.documents.items():
            docs.append({
                'source': doc['source'],
                'chunks': len(doc['chunks']),
                'timestamp': doc['timestamp']
            })
        return docs
    
    def clear_documents(self) -> str:
        """清空所有文档"""
        self.documents.clear()
        return "已清空所有文档"

    def search_and_rerank(self, query: str, k: int = 3) -> List[str]:
        candidates = self.search_documents(query, k=k * 3)  # 多取一些候选
        if not candidates:
            return []


        query_words = set(query.lower().split())

        def score(chunk: str) -> int:
            chunk_lower = chunk.lower()
            hit_score = sum(1 for word in query_words if word in chunk_lower)
            if query.lower() in chunk_lower:
                hit_score += 10
            return hit_score

        reranked = sorted(candidates, key=score, reverse=True)
        return reranked[:k]