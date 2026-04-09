from typing import Optional, Dict, Any
from PIL import Image, ImageDraw
import random
from datetime import datetime
import os
import requests
import base64
from io import BytesIO
from config import Config


class VisionAgent:
    """图像生成和编辑Agent - 支持通义万相"""

    def __init__(self):
        self.mock_mode = Config.MOCK_MODE

        # 初始化通义万相客户端
        if not self.mock_mode and Config.IMAGE_API_TYPE == "tongyi":
            try:
                import dashscope
                from dashscope import ImageSynthesis
                self.ImageSynthesis = ImageSynthesis
                dashscope.api_key = Config.TONGYI_API_KEY
                print("✅ 通义万相 API 已初始化")
            except ImportError:
                print("⚠️ 请安装 dashscope: pip install dashscope")
                self.mock_mode = True
        elif not self.mock_mode and Config.IMAGE_API_TYPE == "replicate":
            import replicate
            self.replicate = replicate
            replicate.Client(api_token=Config.REPLICATE_API_TOKEN)

    def generate_image(self, prompt: str, negative_prompt: str = "",
                       width: int = 1024, height: int = 1024) -> str:
        """根据文本生成图片"""

        if self.mock_mode:
            return self._generate_mock_image(prompt)

        try:
            if Config.IMAGE_API_TYPE == "tongyi":
                return self._generate_tongyi_image(prompt, negative_prompt, width, height)
            elif Config.IMAGE_API_TYPE == "replicate":
                return self._generate_replicate_image(prompt, negative_prompt, width, height)
            else:
                return self._generate_mock_image(prompt)
        except Exception as e:
            return f"生成失败: {str(e)}"

    def _generate_tongyi_image(self, prompt: str, negative_prompt: str = "",
                               width: int = 1024, height: int = 1024) -> str:
        """使用通义万相生成图片"""

        # 通义万相推荐尺寸
        size = f"{width}*{height}"

        rsp = self.ImageSynthesis.call(
            model=Config.TONGYI_MODEL,
            prompt=prompt,
            negative_prompt=negative_prompt,
            size=size,
            n=1,
            watermark=False  # 不添加水印
        )

        if rsp.status_code == 200:
            # 获取图片 URL
            image_url = rsp.output.results[0].url
            return image_url
        else:
            return f"生成失败: {rsp.message}"

    def _generate_replicate_image(self, prompt: str, negative_prompt: str = "",
                                  width: int = 1024, height: int = 1024) -> str:
        """使用 Replicate 生成图片"""
        output = self.replicate.run(
            Config.SD_MODEL,
            input={
                "prompt": prompt,
                "negative_prompt": negative_prompt or "blurry, bad quality",
                "width": width,
                "height": height,
                "num_outputs": 1
            }
        )
        return output[0] if output else "生成失败"

    def _generate_mock_image(self, prompt: str) -> str:
        """生成模拟图片（测试用）"""
        img = Image.new('RGB', (512, 512), color=(random.randint(0, 255),
                                                  random.randint(0, 255),
                                                  random.randint(0, 255)))
        draw = ImageDraw.Draw(img)
        text = prompt[:50]
        draw.text((10, 10), text, fill='white')

        os.makedirs("./generated_images", exist_ok=True)
        filename = f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = f"./generated_images/{filename}"
        img.save(filepath)

        return filepath

    def edit_image(self, image_path: str, instruction: str) -> str:
        """编辑图片"""
        if self.mock_mode:
            return f"模拟编辑: 对 {image_path} 执行了 '{instruction}'"

        try:
            if Config.IMAGE_API_TYPE == "tongyi":
                # 通义万相图片编辑功能
                return self._edit_tongyi_image(image_path, instruction)
            else:
                return f"编辑完成: {instruction}"
        except Exception as e:
            return f"编辑失败: {str(e)}"

    def _edit_tongyi_image(self, image_path: str, instruction: str) -> str:
        """使用通义万相编辑图片"""
        # 读取图片为 base64
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode('utf-8')

        # 调用图片编辑 API
        rsp = self.ImageSynthesis.call(
            model="wanx2.1-imageedit",
            prompt=instruction,
            base_image_url=f"data:image/png;base64,{image_base64}",
            n=1
        )

        if rsp.status_code == 200:
            return rsp.output.results[0].url
        else:
            return f"编辑失败: {rsp.message}"