from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入"""
        pass

    @abstractmethod
    def get_capabilities(self) -> list:
        """返回Agent能力列表"""
        pass


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self.tools = {}

    def register(self, name: str, func: callable, description: str):
        self.tools[name] = {
            "func": func,
            "description": description
        }

    def get_tool(self, name: str):
        return self.tools.get(name)

    def list_tools(self):
        return [(name, info["description"]) for name, info in self.tools.items()]