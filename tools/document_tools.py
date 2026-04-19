"""
文档搜索工具（RAG）
"""

from .base import BaseTool
from typing import Dict, Any


class DocumentSearchTool(BaseTool):
    """文档搜索工具（RAG）"""

    def __init__(self, doc_processor):
        super().__init__(
            name="document_search",
            description="搜索已上传的文档内容。参数: query (str) - 搜索关键词"
        )
        self.doc_processor = doc_processor

    def execute(self, query: str, **kwargs) -> str:
        """执行文档搜索（带rerank）"""
        try:
            # 使用带rerank的检索方法
            if hasattr(self.doc_processor, 'search_and_rerank'):
                results = self.doc_processor.search_and_rerank(query, k=3)
            else:
                results = self.doc_processor.search_documents(query, k=3)

            if not results:
                return "未找到相关文档内容"

            formatted = "\n\n---\n\n".join(results)
            return f"📄 找到 {len(results)} 条相关内容:\n\n{formatted}"
        except Exception as e:
            return f"❌ 搜索失败: {e}"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                }
            }
        }