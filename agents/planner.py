"""
任务规划器 (Planner)
负责将复杂用户请求拆解为结构化的子任务序列
"""

import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from config import Config


class TaskPlanner:
    """负责任务拆解，将用户复杂意图转为可执行的子任务序列"""

    def __init__(self):
        self.client: Optional[OpenAI] = None
        self._init_client()

    def _init_client(self) -> None:
        """初始化 LLM 客户端，用于任务规划"""
        api_config = Config.get_current_api_config()
        if api_config.get("api_key") and api_config["api_key"] != "":
            try:
                self.client = OpenAI(
                    api_key=api_config["api_key"],
                    base_url=api_config["base_url"]
                )
                print(f"✅ Planner 初始化成功: {api_config['name']}")
            except Exception as e:
                self.client = None
                print(f"⚠️ Planner 初始化失败，将使用降级模式: {e}")
        else:
            print(f"⚠️ {api_config.get('name', 'API')} Key 未配置，Planner 使用降级模式")

    def plan(self, user_input: str, available_tools: List[str]) -> List[Dict[str, Any]]:
        """
        将用户输入拆解为子任务序列

        Args:
            user_input: 用户原始输入
            available_tools: 当前可用的工具名称列表

        Returns:
            子任务列表，每个子任务格式：
            {
                "step": int,           # 步骤序号
                "type": str,           # 任务类型: retrieve/search/tool/generate/image_gen
                "query": str,          # 该步骤的具体查询/输入
                "tool": Optional[str]  # 需要调用的工具名（当 type 为 tool 或 image_gen 时）
            }
        """
        # 如果没有客户端或工具列表为空，降级为单步生成任务
        if not self.client or not available_tools:
            return self._fallback_plan(user_input)

        system_prompt = self._build_system_prompt(available_tools)

        try:
            response = self.client.chat.completions.create(
                model=Config.get_current_api_config()["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3,
                max_tokens=800
            )
            plan_text = response.choices[0].message.content.strip()
            return self._parse_plan(plan_text, user_input)

        except Exception as e:
            print(f"❌ Planner 调用失败，降级为单步任务: {e}")
            return self._fallback_plan(user_input)

    def _build_system_prompt(self, available_tools: List[str]) -> str:
        """构建系统提示词"""
        tools_desc = ", ".join(available_tools) if available_tools else "无"
        return f"""你是一个专业的任务规划专家。请将用户的复杂请求拆解为清晰的子任务序列。

【可用工具】
{tools_desc}

【任务类型说明】
- retrieve: 从本地知识库检索相关文档
- search: 搜索外部信息（当前复用知识库检索）
- tool: 调用指定工具执行操作（如 SQL 查询）
- image_gen: 生成图片
- generate: 生成最终回答（必须是最后一步）

【输出格式】
严格按照以下 JSON 数组格式输出，不要添加任何解释或额外文本：
[
  {{"step": 1, "type": "retrieve", "query": "具体的检索关键词", "tool": null}},
  {{"step": 2, "type": "generate", "query": "基于检索结果回答用户的问题", "tool": null}}
]

【规则】
1. 如果用户只是简单闲聊或简单问答，直接输出单步 generate。
2. 最后一步必须是 generate。
3. 只输出 JSON 数组，不要有任何其他内容。"""

    def _parse_plan(self, plan_text: str, fallback_input: str) -> List[Dict[str, Any]]:
        """解析 LLM 返回的计划文本"""
        # 尝试提取 JSON 部分（防止 LLM 返回了多余的解释）
        try:
            # 找到第一个 '[' 和最后一个 ']'
            start = plan_text.find('[')
            end = plan_text.rfind(']')
            if start != -1 and end != -1:
                json_str = plan_text[start:end+1]
                plan = json.loads(json_str)
                if isinstance(plan, list) and len(plan) > 0:
                    # 确保最后一步是 generate
                    if plan[-1].get("type") != "generate":
                        plan.append({"step": len(plan)+1, "type": "generate", "query": fallback_input, "tool": None})
                    return plan
        except json.JSONDecodeError:
            pass

        # 解析失败，降级
        return self._fallback_plan(fallback_input)

    def _fallback_plan(self, user_input: str) -> List[Dict[str, Any]]:
        """降级方案：直接作为单步生成任务"""
        return [{"step": 1, "type": "generate", "query": user_input, "tool": None}]