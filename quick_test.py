import os
from dotenv import load_dotenv

load_dotenv()

print("="*50)
print("📋 检查配置")
print("="*50)

# 检查 API 类型
api_type = os.getenv("API_TYPE", "not set")
print(f"API 类型: {api_type}")

# 检查 DeepSeek 配置
deepseek_key = os.getenv("DEEPSEEK_API_KEY")
if deepseek_key:
    print(f"✅ DeepSeek API Key: {deepseek_key[:10]}...{deepseek_key[-4:]}")
else:
    print("❌ DeepSeek API Key: 未设置")

deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
print(f"DeepSeek 模型: {deepseek_model}")

# 检查 Mock 模式
mock_mode = os.getenv("MOCK_MODE", "true")
print(f"Mock 模式: {mock_mode}")

print("\n" + "="*50)
print("🚀 准备启动应用...")
print("="*50)

# 尝试导入必要模块
try:
    from agents.orchestrator import MemArtOrchestrator
    print("✅ 模块导入成功")
    
    # 尝试初始化
    print("正在初始化 Orchestrator...")
    orch = MemArtOrchestrator(session_id="test")
    print("✅ Orchestrator 初始化成功")
    
except Exception as e:
    print(f"❌ 初始化失败: {e}")
    
print("\n现在可以运行: python run.py")