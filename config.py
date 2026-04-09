import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ========== 支持的 API 列表 ==========
    SUPPORTED_APIS = {
        "deepseek": {
            "name": "DeepSeek",
            "icon": "🔵",
            "type": "llm",
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            "description": "性价比高，中文能力强"
        },
        "openai": {
            "name": "OpenAI",
            "icon": "🟢",
            "type": "llm",
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "model": os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
            "description": "功能强大，全球领先"
        },
        "zhipu": {
            "name": "智谱GLM",
            "icon": "🟣",
            "type": "llm",
            "api_key": os.getenv("ZHIPU_API_KEY", ""),
            "base_url": "https://open.bigmodel.cn/api/paas/v4/",
            "model": os.getenv("ZHIPU_MODEL", "glm-4-flash"),
            "description": "国内可用，免费额度"
        },
        "tongyi": {
            "name": "通义千问",
            "icon": "🟠",
            "type": "llm",
            "api_key": os.getenv("TONGYI_API_KEY", ""),
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": os.getenv("TONGYI_MODEL", "qwen-turbo"),
            "description": "阿里出品，中文优化"
        },
        "moonshot": {
            "name": "Moonshot",
            "icon": "🔴",
            "type": "llm",
            "api_key": os.getenv("MOONSHOT_API_KEY", ""),
            "base_url": "https://api.moonshot.cn/v1",
            "model": os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k"),
            "description": "长文本处理能力强"
        }
    }

    # ========== 图像生成 API 配置 ==========
    IMAGE_APIS = {
        "tongyi_image": {
            "name": "通义万相",
            "icon": "🎨",
            "type": "image",
            "api_key": os.getenv("TONGYI_API_KEY", ""),
            "base_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/image-generation",
            "model": os.getenv("TONGYI_IMAGE_MODEL", "wanx2.6-t2i"),
            "description": "阿里通义万相，文生图能力强"
        },
        "replicate": {
            "name": "Replicate",
            "icon": "🖼️",
            "type": "image",
            "api_key": os.getenv("REPLICATE_API_TOKEN", ""),
            "base_url": "https://api.replicate.com/v1",
            "model": os.getenv("SD_MODEL", "stability-ai/sdxl"),
            "description": "Stable Diffusion 图像生成"
        }
    }

    # ========== 当前激活的配置 ==========
    CURRENT_API = os.getenv("CURRENT_API", "deepseek")
    CURRENT_IMAGE_API = os.getenv("CURRENT_IMAGE_API", "tongyi_image")

    # ========== 协作模式配置 ==========
    COLLABORATIVE_MODE = os.getenv("COLLABORATIVE_MODE", "single")  # single, collaborative, chain
    PRIMARY_API = os.getenv("PRIMARY_API", "deepseek")
    SECONDARY_API = os.getenv("SECONDARY_API", "openai")

    # ========== 图像生成API配置 ==========
    IMAGE_API_TYPE = os.getenv("IMAGE_API_TYPE", "tongyi_image")
    REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")
    SD_MODEL = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"

    # 通义万相配置
    TONGYI_API_KEY = os.getenv("TONGYI_API_KEY", "")
    TONGYI_IMAGE_MODEL = os.getenv("TONGYI_IMAGE_MODEL", "wanx2.6-t2i")

    # ========== 记忆配置 ==========
    SHORT_TERM_TTL = 7 * 24 * 3600
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    CHROMA_PERSIST_DIR = "./chroma_db"
    SQLITE_PATH = "./memart.db"
    MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

    # ========== 文档处理配置 ==========
    UPLOAD_FOLDER = "./uploaded_documents"
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50

    # ========== 方法 ==========
    @classmethod
    def get_current_api_config(cls):
        """获取当前 LLM API 配置"""
        return cls.SUPPORTED_APIS.get(cls.CURRENT_API, cls.SUPPORTED_APIS["deepseek"])

    @classmethod
    def get_current_image_api_config(cls):
        """获取当前图像生成 API 配置"""
        return cls.IMAGE_APIS.get(cls.CURRENT_IMAGE_API, cls.IMAGE_APIS["tongyi_image"])

    @classmethod
    def switch_api(cls, api_name: str):
        """切换 LLM API"""
        if api_name in cls.SUPPORTED_APIS:
            cls.CURRENT_API = api_name
            return True
        return False

    @classmethod
    def switch_image_api(cls, api_name: str):
        """切换图像生成 API"""
        if api_name in cls.IMAGE_APIS:
            cls.CURRENT_IMAGE_API = api_name
            cls.IMAGE_API_TYPE = api_name
            return True
        return False

    @classmethod
    def get_llm_config(cls):
        """获取 LLM 配置"""
        api_config = cls.get_current_api_config()
        return {
            "api_key": api_config.get("api_key", ""),
            "base_url": api_config.get("base_url", ""),
            "model": api_config.get("model", ""),
            "name": api_config.get("name", "Unknown"),
            "icon": api_config.get("icon", "")
        }

    @classmethod
    def get_primary_api_config(cls):
        """获取主 API 配置（协作模式）"""
        return cls.SUPPORTED_APIS.get(cls.PRIMARY_API, cls.SUPPORTED_APIS["deepseek"])

    @classmethod
    def get_secondary_api_config(cls):
        """获取副 API 配置（协作模式）"""
        return cls.SUPPORTED_APIS.get(cls.SECONDARY_API, cls.SUPPORTED_APIS["openai"])

    @classmethod
    def get_api_config(cls, api_name: str):
        """获取指定 API 配置"""
        return cls.SUPPORTED_APIS.get(api_name, cls.SUPPORTED_APIS["deepseek"])