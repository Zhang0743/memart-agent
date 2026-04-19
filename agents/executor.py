"""
任务执行器 (Executor)
负责按顺序执行 Planner 生成的子任务序列，并流式输出结果
"""

from typing import List, Dict, Any, AsyncGenerator, Optional
from agents.document_processor import DocumentProcessor
from agents.cache import ResponseCache
from tools import ToolRegistry
from openai import OpenAI
from config import Config


class TaskExecutor:
    """执行规划好的子任务序列"""

    def __init__(self, doc_processor: DocumentProcessor, tool_registry: ToolRegistry, cache: ResponseCache):
        self.doc_processor = doc_processor
        self.tool_registry = tool_registry
        self.cache = cache
        self.llm_client: Optional[OpenAI] = None
        self._init_llm_client()

    def _init_llm_client(self) -> None:
        """初始化 LLM 客户端用于最终生成"""
        api_config = Config.get_current_api_config()
        if api_config.get("api_key") and api_config["api_key"] != "":
            try:
                self.llm_client = OpenAI(
                    api_key=api_config["api_key"],
                    base_url=api_config["base_url"]
                )
            except Exception as e:
                self.llm_client = None
                print(f"⚠️ Executor LLM 初始化失败: {e}")

    async def execute_plan(self, plan: List[Dict[str, Any]], original_query: str) -> AsyncGenerator[str, None]:
        """
        按顺序执行子任务，流式输出执行过程和最终结果

        Args:
            plan: Planner 生成的子任务列表
            original_query: 用户原始输入

        Yields:
            执行过程的流式文本
        """
        context = {
            "retrieved_docs": [],      # 存储检索到的文档片段
            "tool_results": [],        # 存储工具执行结果
            "steps_completed": 0
        }

        # 先检查缓存（仅对单步 generate 任务有效）
        if len(plan) == 1 and plan[0]["type"] == "generate":
            cached = self.cache.get(original_query, "planner")
            if cached:
                yield f"💾 [缓存命中] {cached}\n"
                return

        # 逐步执行子任务
        for task in plan:
            step = task.get("step", len(context["steps_completed"]) + 1)
            task_type = task.get("type", "generate")
            query = task.get("query", original_query)
            tool_name = task.get("tool")

            yield f"\n🔹 **子任务 {step}** ({task_type})\n"

            if task_type == "retrieve":
                docs = self.doc_processor.search_and_rerank(query, k=3)
                if docs:
                    context["retrieved_docs"].extend(docs)
                    yield f"   📄 检索到 {len(docs)} 条相关文档\n"
                else:
                    yield f"   📄 未检索到相关文档\n"

            elif task_type == "search":
                # 当前复用文档检索，未来可扩展为网络搜索
                docs = self.doc_processor.search_and_rerank(query, k=2)
                if docs:
                    context["retrieved_docs"].extend(docs)
                    yield f"   🔍 搜索到 {len(docs)} 条信息\n"
                else:
                    yield f"   🔍 未搜索到相关信息\n"

            elif task_type == "tool":
                if tool_name:
                    result = self.tool_registry.execute_tool(tool_name, query=query)
                    context["tool_results"].append(result)
                    yield f"   🛠️ 工具 [{tool_name}] 执行完成\n"
                else:
                    yield f"   ⚠️ 未指定工具，跳过\n"

            elif task_type == "image_gen":
                if tool_name == "image_generation":
                    result = self.tool_registry.execute_tool("image_generation", prompt=query)
                    yield f"   🎨 {result}\n"
                    # 图片生成后通常不需要继续执行其他任务
                    return
                else:
                    yield f"   ⚠️ 图片生成工具不可用\n"

            elif task_type == "generate":
                # 最终生成回答，会整合所有上下文
                pass

            context["steps_completed"] += 1

        # 最后一步：生成最终回答（整合上下文）
        yield "\n---\n**💡 最终回答**:\n"
        final_answer = await self._generate_final_answer(original_query, context)
        yield final_answer

        # 缓存单步生成的结果
        if len(plan) == 1 and plan[0]["type"] == "generate":
            self.cache.set(original_query, final_answer, "planner")

    async def _generate_final_answer(self, original_query: str, context: Dict[str, Any]) -> str:
        """基于上下文生成最终回答"""
        if not self.llm_client:
            return "（LLM 客户端未初始化，无法生成回答）"

        # 构建上下文
        context_text = ""
        if context["retrieved_docs"]:
            docs_text = "\n\n".join(context["retrieved_docs"][:3])
            context_text += f"\n【检索到的相关资料】\n{docs_text}\n"
        if context["tool_results"]:
            tools_text = "\n".join(context["tool_results"])
            context_text += f"\n【工具执行结果】\n{tools_text}\n"

        system_prompt = "你是一个专业、友好的AI助手。请基于提供的上下文信息回答用户问题。如果上下文不足，请如实告知。"
        user_prompt = f"用户问题：{original_query}\n{context_text}\n请给出准确、完整的回答。"

        try:
            response = self.llm_client.chat.completions.create(
                model=Config.get_current_api_config()["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"生成回答时出错: {e}"