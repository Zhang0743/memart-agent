"""
SQL查询工具
"""

from .base import BaseTool
from typing import Dict, Any


class SQLQueryTool(BaseTool):
    """SQL查询工具"""

    def __init__(self, sql_agent):
        super().__init__(
            name="sql_query",
            description="执行SQL查询。参数: query (str) - SQL查询语句"
        )
        self.sql_agent = sql_agent

    def execute(self, query: str, **kwargs) -> str:
        """执行SQL查询"""
        try:
            result = self.sql_agent.run_query(query)
            return f"✅ 查询结果: {result}"
        except Exception as e:
            return f"❌ 查询失败: {e}"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "query": {
                    "type": "string",
                    "description": "SQL查询语句"
                }
            }
        }