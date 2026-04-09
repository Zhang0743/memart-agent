import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict
import hashlib
from datetime import datetime
from config import Config


class LongTermMemory:
    """基于ChromaDB的长期记忆"""

    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(path=Config.CHROMA_PERSIST_DIR)
            # 使用简单的embedding函数（不需要OpenAI）
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )

            self.memories_collection = self.client.get_or_create_collection(
                name="user_memories",
                embedding_function=self.embedding_fn
            )
            self.available = True
        except Exception as e:
            print(f"ChromaDB初始化失败: {e}")
            self.available = False

    def add_memory(self, user_id: str, content: str, metadata: Dict = None):
        """添加长期记忆"""
        if not self.available:
            return

        memory_id = hashlib.md5(f"{user_id}:{content}".encode()).hexdigest()
        self.memories_collection.upsert(
            ids=[memory_id],
            documents=[content],
            metadatas=[{"user_id": user_id, "timestamp": datetime.now().isoformat(), **(metadata or {})}]
        )

    def retrieve_relevant_memories(self, user_id: str, query: str, k: int = 3) -> List[str]:
        """检索相关记忆"""
        if not self.available:
            return []

        try:
            results = self.memories_collection.query(
                query_texts=[query],
                n_results=k,
                where={"user_id": user_id}
            )
            return results['documents'][0] if results['documents'] else []
        except:
            return []