import redis
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import Config


class ShortTermMemory:
    """基于Redis的短期记忆"""

    def __init__(self):
        try:
            self.redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
            self.available = True
        except Exception as e:
            print(f"Redis连接失败，使用内存存储: {e}")
            self.available = False
            self.memory_store = {}

        self.ttl = Config.SHORT_TERM_TTL

    def add_memory(self, session_id: str, role: str, content: str, metadata: Dict = None):
        """添加记忆条目"""
        memory = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        if self.available:
            key = f"session:{session_id}:memories"
            self.redis_client.rpush(key, json.dumps(memory))
            self.redis_client.expire(key, self.ttl)
        else:
            if session_id not in self.memory_store:
                self.memory_store[session_id] = []
            self.memory_store[session_id].append(memory)

    def get_memories(self, session_id: str, limit: int = 50) -> List[Dict]:
        """获取最近记忆"""
        if self.available:
            key = f"session:{session_id}:memories"
            memories = self.redis_client.lrange(key, -limit, -1)
            return [json.loads(m) for m in memories]
        else:
            memories = self.memory_store.get(session_id, [])
            return memories[-limit:]

    def clear_session(self, session_id: str):
        """清除会话记忆"""
        if self.available:
            self.redis_client.delete(f"session:{session_id}:memories")
        else:
            self.memory_store[session_id] = []

    def get_last_week_summary(self, session_id: str) -> str:
        """获取最近一周记忆摘要"""
        memories = self.get_memories(session_id, limit=100)
        week_ago = datetime.now() - timedelta(days=7)

        recent = [m for m in memories
                  if datetime.fromisoformat(m["timestamp"]) > week_ago]

        if not recent:
            return "最近7天无历史记忆"

        summary = "【最近7天记忆】\n"
        for m in recent[-5:]:
            summary += f"- [{m['timestamp'][:16]}] {m['role']}: {m['content'][:80]}\n"
        return summary