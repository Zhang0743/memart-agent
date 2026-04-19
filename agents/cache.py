"""
Redis 缓存模块
用于缓存高频查询结果，降低API调用延迟和成本
"""

import json
import hashlib
from typing import Optional, Any

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️ Redis未安装，使用内存缓存降级")


class ResponseCache:
    """响应缓存，支持Redis和内存两种模式"""

    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, ttl: int = 3600):
        self.ttl = ttl
        self.redis_client = None
        self.memory_cache = {}

        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    decode_responses=True,
                    socket_connect_timeout=3
                )
                self.redis_client.ping()
                print("✅ Redis缓存已启用")
            except Exception as e:
                print(f"⚠️ Redis连接失败，使用内存缓存: {e}")
                self.redis_client = None
        else:
            print("ℹ️ 使用内存缓存模式")

    def _generate_key(self, query: str, context: str = "") -> str:
        """生成缓存key"""
        content = f"{query}:{context}"
        return f"memart:cache:{hashlib.md5(content.encode()).hexdigest()}"

    def get(self, query: str, context: str = "") -> Optional[Any]:
        """获取缓存"""
        key = self._generate_key(query, context)

        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val:
                    print(f"💾 Redis缓存命中")
                    return json.loads(val)
            except Exception as e:
                print(f"⚠️ Redis读取失败: {e}")

        if key in self.memory_cache:
            print(f"💾 内存缓存命中")
            return self.memory_cache[key]

        return None

    def set(self, query: str, value: Any, context: str = "") -> None:
        """设置缓存"""
        key = self._generate_key(query, context)
        json_value = json.dumps(value, ensure_ascii=False)

        if self.redis_client:
            try:
                self.redis_client.setex(key, self.ttl, json_value)
                print(f"📝 已缓存到Redis")
                return
            except Exception as e:
                print(f"⚠️ Redis写入失败: {e}")

        self.memory_cache[key] = value
        print(f"📝 已缓存到内存")

        if len(self.memory_cache) > 1000:
            keys = list(self.memory_cache.keys())[:500]
            for k in keys:
                del self.memory_cache[k]

    def clear(self) -> None:
        """清空缓存"""
        self.memory_cache.clear()
        if self.redis_client:
            try:
                keys = self.redis_client.keys("memart:cache:*")
                if keys:
                    self.redis_client.delete(*keys)
            except Exception:
                pass