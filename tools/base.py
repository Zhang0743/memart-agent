"""
工具基类和注册表
定义所有工具的标准化接口
"""

from typing import Dict, Any, Optional, List


class BaseTool:
    """所有工具的基类，定义了标准接口"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def execute(self, **kwargs) -> str:
        """
        执行工具的核心方法
        子类必须实现此方法
        """
        raise NotImplementedError(f"Tool {self.name} must implement execute()")

    def get_schema(self) -> Dict[str, Any]:
        """返回工具的参数schema，用于LLM理解如何调用"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {}
        }


class ToolRegistry:
    """工具注册表，管理所有可用工具"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool
        print(f"🔧 工具已注册: {tool.name}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        """列出所有工具"""
        return [
            {"name": t.name, "description": t.description}
            for t in self._tools.values()
        ]

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """获取所有工具的schema，供LLM理解"""
        return [t.get_schema() for t in self._tools.values()]

    def execute_tool(self, name: str, **kwargs) -> str:
        """执行指定工具"""
        tool = self.get_tool(name)
        if not tool:
            return f"❌ 未知工具: {name}"
        return tool.execute(**kwargs)