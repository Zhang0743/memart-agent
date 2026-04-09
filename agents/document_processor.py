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
        """搜索相关文档片段"""
        if not query:
            return []
        
        results = []
        query_lower = query.lower()
        
        for doc_id, doc in self.documents.items():
            for chunk in doc['chunks']:
                if query_lower in chunk.lower():
                    results.append(chunk)
                    if len(results) >= k:
                        break
            if len(results) >= k:
                break
        
        return results
    
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