"""
图像生成工具
"""

from .base import BaseTool
from typing import Dict, Any


class ImageGenTool(BaseTool):
    """文生图工具"""

    def __init__(self, vision_agent):
        super().__init__(
            name="image_generation",
            description="根据文本描述生成图片。参数: prompt (str) - 图片描述文本"
        )
        self.vision_agent = vision_agent

    def execute(self, prompt: str, **kwargs) -> str:
        """执行图片生成"""
        try:
            result = self.vision_agent.generate_image(prompt)
            return f"✅ 图片生成成功: {result}"
        except Exception as e:
            return f"❌ 图片生成失败: {e}"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "prompt": {
                    "type": "string",
                    "description": "图片描述文本"
                }
            }
        }