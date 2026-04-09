import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

print("="*50)
print("测试配置")
print("="*50)

api_key = os.getenv("DEEPSEEK_API_KEY")
print(f"API Key: {api_key[:10]}...{api_key[-4:] if api_key else '未设置'}")

if not api_key or api_key == "sk-你的真实DeepSeek密钥":
    print("❌ 请先配置真实的 DeepSeek API Key")
    print("获取地址: https://platform.deepseek.com/")
    exit(1)

try:
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "说'你好'"}],
        max_tokens=20
    )
    print("✅ API 连接成功！")
    print(f"回复: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ API 错误: {e}")
