# 修复导入 - 使用新的 LangChain API
from langchain.tools import tool
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from agents.sql_agent import SQLAgent
from agents.vision_agent import VisionAgent
from config import Config

class MemArtOrchestrator:
    """主协调Agent"""
    
    def __init__(self, session_id: str = "default", default_strategy: str = "auto"):
        self.session_id = session_id
        self.short_memory = ShortTermMemory()
        self.long_memory = LongTermMemory()
        self.sql_agent = SQLAgent(Config.SQLITE_PATH)
        self.vision_agent = VisionAgent()
        
        # 根据配置选择LLM
        llm_config = Config.get_llm_config()
        
        # 使用 OpenAI 兼容 API (包括 DeepSeek)
        self.llm = ChatOpenAI(
            api_key=llm_config["api_key"],
            base_url=llm_config["base_url"],
            model=llm_config["model"],
            temperature=0.7,
            streaming=True
        )
        print(f"✅ 使用 {Config.API_TYPE.upper()} API: {llm_config['model']}")
        
        # 定义工具函数
        self.tools = self._create_tools()
        self.current_strategy = default_strategy
    
    def _create_tools(self):
        """创建工具列表"""
        
        @tool
        def generate_image(prompt: str) -> str:
            """根据文本生成图片，输入图片描述"""
            return self.vision_agent.generate_image(prompt)
        
        @tool
        def save_image_record(filename: str) -> str:
            """保存图片记录到数据库"""
            return self.sql_agent.save_image_record(filename, "auto_generated")
        
        @tool
        def query_database(query: str) -> str:
            """查询数据库，输入SQL语句或自然语言查询"""
            return self.sql_agent.execute_query(query)
        
        return [generate_image, save_image_record, query_database]
    
    def switch_strategy(self, strategy: str) -> str:
        """切换推理策略"""
        valid = ["react", "cot", "auto"]
        if strategy not in valid:
            return f"无效策略，可选: {valid}"
        self.current_strategy = strategy
        return f"已切换到 {strategy.upper()}"
    
    def process_with_strategy(self, user_input: str, force_strategy: str = None):
        """使用指定策略处理请求"""
        strategy = force_strategy or self.current_strategy
        
        # 获取记忆上下文
        short_mem = self.short_memory.get_last_week_summary(self.session_id)
        long_mem = self.long_memory.retrieve_relevant_memories(self.session_id, user_input)
        context = f"短期: {short_mem}\n长期: {chr(10).join(long_mem)}"
        
        # 根据策略构建提示
        if strategy == "cot":
            prompt = f"""你是一个AI助手MemArt。请使用Chain of Thought（思维链）方法逐步推理。

背景记忆:
{context}

用户问题: {user_input}

请按以下格式回答：
1. 理解问题
2. 分析要点
3. 逐步推理
4. 综合结论

回答:"""
        else:
            prompt = f"""你是一个AI助手MemArt。
背景记忆: {context}
用户问题: {user_input}

请直接回答用户的问题。"""
        
        # 调用 LLM
        try:
            response = self.llm.invoke(prompt)
            answer = response.content
        except Exception as e:
            answer = f"调用API时出错: {str(e)}"
        
        # 保存记忆
        self.short_memory.add_memory(self.session_id, "user", user_input)
        self.short_memory.add_memory(self.session_id, "assistant", answer[:200])
        
        return {
            "selected_strategy": strategy,
            "final_answer": answer,
            "reasoning_process": answer if strategy == "cot" else ""
        }
    
    async def stream_with_strategy(self, user_input: str, strategy: str = None):
        """流式输出"""
        result = self.process_with_strategy(user_input, strategy)
        
        display = {
            "react": "⚡ REACT",
            "cot": "💭 COT",
            "auto": "🤖 AUTO"
        }.get(result["selected_strategy"], result["selected_strategy"])
        
        yield f"**策略**: {display}\n\n"
        
        if result["selected_strategy"] == "cot":
            yield result["reasoning_process"]
        else:
            yield result["final_answer"]
