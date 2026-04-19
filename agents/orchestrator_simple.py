import threading
from config import Config
from openai import OpenAI
from agents.vision_agent import VisionAgent
from agents.document_processor import DocumentProcessor
from agents.collaborative_client import CollaborativeClient
from agents.cache import ResponseCache
from tools import ToolRegistry, ImageGenTool, DocumentSearchTool


class MemArtOrchestrator:
    def __init__(self, session_id: str = "default", default_strategy: str = "auto"):
        self._lock = threading.RLock()
        self.session_id = session_id
        self.current_strategy = default_strategy
        self.current_api = Config.CURRENT_API
        self.collaborative_mode = getattr(Config, 'COLLABORATIVE_MODE', 'single')
        self.enable_image_gen = True

        # 初始化各个组件
        self.vision_agent = VisionAgent()
        self.doc_processor = DocumentProcessor()
        self.collab_client = CollaborativeClient()

        # 初始化单模式客户端
        self.client = None
        self._init_client()

        # 初始化缓存
        self.cache = ResponseCache(
            redis_host=getattr(Config, 'REDIS_HOST', 'localhost'),
            redis_port=getattr(Config, 'REDIS_PORT', 6379),
            ttl=3600
        )

        # 初始化工具系统
        self.tool_registry = ToolRegistry()
        self._init_tools()

        print(f"✅ MemArt Agent 初始化成功")
        print(f"   协作模式: {self.collaborative_mode}")
        print(f"   文生图: {'开启' if self.enable_image_gen else '关闭'}")
        print(f"   已注册工具: {len(self.tool_registry.list_tools())} 个")

    def _init_tools(self):
        """初始化并注册所有工具"""
        self.tool_registry.register(ImageGenTool(self.vision_agent))
        self.tool_registry.register(DocumentSearchTool(self.doc_processor))

    def _init_client(self):
        """初始化单模式 API 客户端"""
        api_config = Config.get_current_api_config()
        if api_config.get("api_key") and api_config["api_key"] != "":
            try:
                self.client = OpenAI(
                    api_key=api_config["api_key"],
                    base_url=api_config["base_url"]
                )
                print(f"✅ API 客户端初始化成功: {api_config['name']}")
            except Exception as e:
                self.client = None
                print(f"❌ API 客户端初始化失败: {e}")
        else:
            print(f"⚠️ {api_config.get('name', 'API')} API Key 未配置")

    def _get_api_display(self):
        """获取当前 API 显示信息"""
        api_config = Config.get_current_api_config()
        return f"{api_config.get('icon', '')} {api_config.get('name', 'Unknown')} ({api_config.get('model', 'unknown')})"

    def switch_strategy(self, strategy: str) -> str:
        """切换推理策略"""
        with self._lock:
            valid = ["react", "cot", "auto"]
            if strategy not in valid:
                return f"无效策略，可选: {valid}"
            self.current_strategy = strategy
            return f"已切换到 {strategy.upper()}"

    def toggle_image_gen(self, enabled: bool) -> str:
        """切换文生图开关"""
        with self._lock:
            self.enable_image_gen = enabled
            return f"文生图功能已{'开启' if enabled else '关闭'}"

    def switch_mode(self, mode: str) -> str:
        """切换工作模式"""
        with self._lock:
            valid_modes = ["single", "collaborative", "chain"]
            if mode not in valid_modes:
                return f"无效模式，可选: {valid_modes}"
            self.collaborative_mode = mode
            Config.COLLABORATIVE_MODE = mode
            return f"已切换到 {mode} 模式"

    def switch_api(self, api_name: str) -> tuple:
        """切换单模式 API"""
        with self._lock:
            if api_name not in Config.SUPPORTED_APIS:
                return False, f"不支持的 API: {api_name}"

            Config.switch_api(api_name)
            self.current_api = api_name
            self._init_client()

            api_config = Config.get_current_api_config()
            if self.client:
                return True, f"{api_config.get('icon', '')} 已切换到 {api_config.get('name', api_name)}"
            else:
                return False, f"{api_config.get('icon', '')} {api_config.get('name', api_name)} API Key 未配置"

    def switch_collaborative_pair(self, primary: str, secondary: str) -> tuple:
        """切换协作 API 对"""
        return self.collab_client.switch_collaborative_pair(primary, secondary)

    def process_document(self, file_path: str, content: str) -> str:
        """处理上传的文档"""
        return self.doc_processor.save_document(file_path, content)

    def search_documents(self, query: str):
        """搜索文档"""
        return self.doc_processor.search_documents(query)

    def _is_image_request(self, text: str) -> bool:
        """判断是否请求生成图片"""
        if not self.enable_image_gen:
            return False
        keywords = ["生成", "图片", "画", "绘制", "创建", "制作", "给我", "一张", "幅"]
        image_keywords = ["图片", "图像", "画", "图", "照片"]
        return any(kw in text for kw in keywords) and any(kw in text for kw in image_keywords)

    async def stream_with_strategy(self, user_input: str, strategy: str = None):
        """流式处理用户输入"""
        strategy = strategy or self.current_strategy
        display = {"react": "⚡ REACT", "cot": "💭 COT", "auto": "🤖 AUTO"}.get(strategy, strategy)

        # 显示当前状态
        if self.collaborative_mode == "single":
            api_config = Config.get_current_api_config()
            yield f"**模式**: 单API模式 | **API**: {api_config.get('icon', '')} {api_config.get('name', 'Unknown')}\n"
        else:
            primary = Config.get_primary_api_config()
            secondary = Config.get_secondary_api_config()
            yield f"**模式**: 🤝 协作模式 | **主**: {primary.get('icon', '')} {primary.get('name', 'Unknown')} | **副**: {secondary.get('icon', '')} {secondary.get('name', 'Unknown')}\n"

        yield f"**推理策略**: {display} | **文生图**: {'✅ 开启' if self.enable_image_gen else '❌ 关闭'}\n\n"

        # 搜索相关文档（使用带rerank的方法）
        if hasattr(self.doc_processor, 'search_and_rerank'):
            relevant_docs = self.doc_processor.search_and_rerank(user_input, k=3)
        else:
            relevant_docs = self.doc_processor.search_documents(user_input)[:3]

        if relevant_docs:
            yield f"**📄 相关文档片段**:\n"
            for i, doc in enumerate(relevant_docs):
                yield f"{i + 1}. {doc[:200]}...\n"
            yield "\n"

        # 检查是否是图片生成请求
        if self._is_image_request(user_input):
            yield "🎨 正在生成图片...\n\n"
            image_prompt = user_input.replace("生成", "").replace("给我", "").replace("一张", "").replace("幅",
                                                                                                          "").strip()
            image_url = self.vision_agent.generate_image(image_prompt)

            if image_url.startswith("http"):
                yield f"✅ 图片已生成！\n\n![生成的图片]({image_url})\n\n**描述**: {image_prompt}"
            else:
                yield f"✅ 图片已生成！\n\n本地路径: `{image_url}`\n\n**描述**: {image_prompt}"
            return

        # 根据模式处理对话
        if self.collaborative_mode == "collaborative":
            async for chunk in self.collab_client.collaborative_chat(user_input, strategy):
                yield chunk
        elif self.collaborative_mode == "chain":
            result = await self.collab_client.chain_chat(user_input)
            yield result
        else:
            # 单模式
            if not self.client:
                api_config = Config.get_current_api_config()
                yield f"❌ {api_config.get('name', 'API')} API 未配置\n\n请在 .env 文件中设置相应的 API Key"
                return

            system_prompt = "你是 MemArt AI 助手，专业、友好、乐于助人。"
            if strategy == "cot":
                system_prompt += " 请使用 Chain of Thought 思维链方法，逐步推理后再给出答案。"

            if relevant_docs:
                system_prompt += f"\n\n参考以下文档内容:\n{chr(10).join(relevant_docs)}"

            try:
                api_config = Config.get_current_api_config()
                response = self.client.chat.completions.create(
                    model=api_config["model"],
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                yield response.choices[0].message.content
            except Exception as e:
                yield f"API 调用失败: {str(e)}"