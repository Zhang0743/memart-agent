from openai import OpenAI
from config import Config
import asyncio
import time
from typing import Optional, Tuple

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 1  # 秒
REQUEST_TIMEOUT = 30  # 秒

async def retry_with_backoff(func, *args, max_retries=MAX_RETRIES, **kwargs):
    """带指数退避的重试机制"""
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=REQUEST_TIMEOUT
            )
        except (Exception, asyncio.TimeoutError) as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = RETRY_DELAY * (2 ** attempt)  # 指数退避: 1s, 2s, 4s
                print(f"⚠️ 调用失败，{wait_time}秒后重试 (尝试 {attempt + 1}/{max_retries}): {e}")
                await asyncio.sleep(wait_time)
            else:
                print(f"❌ 重试{max_retries}次后仍失败: {e}")
    
    raise last_error

class CollaborativeClient:
    """多 API 协作客户端"""
    
    def __init__(self):
        self.primary_client = None
        self.secondary_client = None
        self._init_clients()
    
    def _init_clients(self):
        """初始化客户端"""
        primary_config = Config.get_primary_api_config()
        secondary_config = Config.get_secondary_api_config()
        
        if primary_config.get("api_key") and primary_config["api_key"]:
            try:
                self.primary_client = OpenAI(
                    api_key=primary_config["api_key"],
                    base_url=primary_config["base_url"]
                )
                print(f"✅ 主 API 初始化: {primary_config.get('icon', '')} {primary_config.get('name', 'Unknown')}")
            except Exception as e:
                print(f"❌ 主 API 初始化失败: {e}")
        
        if secondary_config.get("api_key") and secondary_config["api_key"]:
            try:
                self.secondary_client = OpenAI(
                    api_key=secondary_config["api_key"],
                    base_url=secondary_config["base_url"]
                )
                print(f"✅ 副 API 初始化: {secondary_config.get('icon', '')} {secondary_config.get('name', 'Unknown')}")
            except Exception as e:
                print(f"❌ 副 API 初始化失败: {e}")

    def check_api_health(self, client, api_name: str) -> bool:
        """检查 API 是否可用"""
        if not client:
            return False
        try:
            # 发送一个最小请求测试连通性
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # 或从配置读取
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
                timeout=5
            )
            return True
        except Exception as e:
            print(f"⚠️ {api_name} 健康检查失败: {e}")
            return False

    async def collaborative_chat(self, user_input: str, strategy: str = "auto"):
            """协作对话 - 主 API 理解，副 API 生成（带重试和降级）"""

            primary_config = Config.get_primary_api_config()
            secondary_config = Config.get_secondary_api_config()

            # 第一步：主 API 负责理解和分析（带重试和降级）
            analysis = ""
            analysis_source = ""

            if self.primary_client:
                try:
                    analysis_prompt = f"""请分析以下用户需求，提取关键信息：

    用户输入: {user_input}

    请按以下格式输出：
    1. 需求类型：[问题/创意/指令/其他]
    2. 关键要素：[列出3-5个关键点]
    3. 建议回答方向：[简要建议如何回答]
    """

                    # 定义异步调用函数
                    async def call_primary_analysis():
                        response = self.primary_client.chat.completions.create(
                            model=primary_config["model"],
                            messages=[
                                {"role": "system", "content": "你是需求分析专家，擅长理解用户意图。"},
                                {"role": "user", "content": analysis_prompt}
                            ],
                            temperature=0.5,
                            max_tokens=500
                        )
                        return response.choices[0].message.content

                    analysis = await retry_with_backoff(call_primary_analysis)
                    analysis_source = f"主API: {primary_config.get('name', 'Unknown')}"
                    yield f"**🔍 分析结果 ({analysis_source})**:\n{analysis}\n\n"

                except Exception as e:
                    yield f"⚠️ 主API分析失败: {e}\n"
                    yield f"🔄 尝试降级到副API进行分析...\n\n"

                    # 降级：用副 API 做分析
                    if self.secondary_client:
                        try:
                            async def call_secondary_analysis():
                                response = self.secondary_client.chat.completions.create(
                                    model=secondary_config["model"],
                                    messages=[
                                        {"role": "system", "content": "你是需求分析专家，擅长理解用户意图。"},
                                        {"role": "user", "content": analysis_prompt}
                                    ],
                                    temperature=0.5,
                                    max_tokens=500
                                )
                                return response.choices[0].message.content

                            analysis = await retry_with_backoff(call_secondary_analysis)
                            analysis_source = f"副API(降级): {secondary_config.get('name', 'Unknown')}"
                            yield f"**🔍 分析结果 ({analysis_source})**:\n{analysis}\n\n"

                        except Exception as e2:
                            yield f"❌ 降级分析也失败: {e2}\n\n"
                            analysis = ""
                    else:
                        yield f"❌ 无可用的分析 API\n\n"
            else:
                yield f"⚠️ 主 API ({primary_config.get('name', 'Unknown')}) 未配置\n\n"

            # 第二步：副 API 负责生成回答（带重试和降级）
            if self.secondary_client:
                try:
                    generation_prompt = f"""基于以下分析，生成高质量的回答：

    用户原始输入: {user_input}

    分析结果:
    {analysis if analysis else '无详细分析'}

    请生成专业、友好、有帮助的回答。"""

                    async def call_secondary_generation():
                        response = self.secondary_client.chat.completions.create(
                            model=secondary_config["model"],
                            messages=[
                                {"role": "system", "content": "你是内容生成专家，擅长创作高质量的回答。"},
                                {"role": "user", "content": generation_prompt}
                            ],
                            temperature=0.8,
                            max_tokens=1000
                        )
                        return response.choices[0].message.content

                    final_answer = await retry_with_backoff(call_secondary_generation)
                    yield f"**✨ 生成结果 (副API: {secondary_config.get('name', 'Unknown')})**:\n{final_answer}"

                except Exception as e:
                    yield f"❌ 副API生成失败（已重试{MAX_RETRIES}次）: {e}\n"
                    yield f"🔄 尝试降级到主API生成...\n\n"

                    # 降级：用主 API 生成
                    if self.primary_client:
                        try:
                            async def call_primary_generation():
                                response = self.primary_client.chat.completions.create(
                                    model=primary_config["model"],
                                    messages=[
                                        {"role": "system", "content": "请直接回答用户问题。"},
                                        {"role": "user", "content": user_input}
                                    ],
                                    temperature=0.8,
                                    max_tokens=1000
                                )
                                return response.choices[0].message.content

                            fallback_answer = await retry_with_backoff(call_primary_generation)
                            yield f"**✨ 生成结果 (主API-降级):**\n{fallback_answer}"

                        except Exception as e2:
                            yield f"❌ 降级生成也失败: {e2}"
                    else:
                        yield f"❌ 无可用 API 进行降级"
            else:
                # 副 API 不可用，尝试用主 API 直接回答
                if self.primary_client:
                    yield f"⚠️ 副 API ({secondary_config.get('name', 'Unknown')}) 未配置\n"
                    yield f"🔄 使用主 API 直接回答...\n\n"
                    try:
                        async def call_primary_direct():
                            response = self.primary_client.chat.completions.create(
                                model=primary_config["model"],
                                messages=[
                                    {"role": "system", "content": "你是AI助手，请直接回答用户问题。"},
                                    {"role": "user", "content": user_input}
                                ],
                                temperature=0.8,
                                max_tokens=1000
                            )
                            return response.choices[0].message.content

                        direct_answer = await retry_with_backoff(call_primary_direct)
                        yield f"**✨ 回答 (主API直接生成)**:\n{direct_answer}"
                    except Exception as e:
                        yield f"❌ 主API生成失败: {e}"
                else:
                    yield f"❌ 无可用 API，无法生成回答"
    
    async def chain_chat(self, user_input: str) -> str:
        """链式对话 - 多 API 接力处理"""
        
        current_input = user_input
        results = []
        
        # 定义 API 处理顺序
        apis = ["deepseek", "openai"]
        
        for i, api_name in enumerate(apis):
            api_config = Config.get_api_config(api_name)
            if not api_config.get("api_key") or not api_config["api_key"]:
                results.append(f"⚠️ {api_config.get('name', api_name)} API Key 未配置，跳过")
                continue
            
            try:
                client = OpenAI(
                    api_key=api_config["api_key"],
                    base_url=api_config["base_url"]
                )
                
                prompt = f"""请基于以下内容继续完善：

当前内容: {current_input}

请给出更完善、更详细的回答。"""
                
                response = client.chat.completions.create(
                    model=api_config["model"],
                    messages=[
                        {"role": "system", "content": f"你是第{i+1}轮处理的AI助手，请在前人基础上优化答案。"},
                        {"role": "user", "content": prompt if i > 0 else user_input}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                current_input = response.choices[0].message.content
                results.append(f"**{api_config.get('icon', '')} {api_config.get('name', api_name)} 第{i+1}轮**:\n{current_input}\n")
                
            except Exception as e:
                results.append(f"❌ {api_config.get('name', api_name)} 处理失败: {e}")
        
        return "\n\n".join(results) if results else "链式处理失败"
    
    def switch_collaborative_pair(self, primary: str, secondary: str) -> tuple:
        """切换协作 API 对"""
        if primary not in Config.SUPPORTED_APIS or secondary not in Config.SUPPORTED_APIS:
            return False, "切换失败，请检查 API 名称"
        
        Config.PRIMARY_API = primary
        Config.SECONDARY_API = secondary
        self._init_clients()
        
        primary_config = Config.get_primary_api_config()
        secondary_config = Config.get_secondary_api_config()
        
        return True, f"已切换到协作模式: {primary_config.get('icon', '')} {primary_config.get('name', primary)} + {secondary_config.get('icon', '')} {secondary_config.get('name', secondary)}"