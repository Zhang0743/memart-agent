import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def test_deepseek():
    print("="*50)
    print("🧪 测试 DeepSeek API 连接")
    print("="*50)
    
    # 读取配置
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    print(f"API Key: {api_key[:10]}..." if api_key else "❌ API Key 未设置")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print("-"*50)
    
    if not api_key:
        print("❌ 错误: 请在 .env 文件中设置 DEEPSEEK_API_KEY")
        return
    
    try:
        # 初始化客户端
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # 发送测试请求
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个助手"},
                {"role": "user", "content": "你好，请用一句话介绍你自己"}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        print("✅ API 连接成功！")
        print(f"回复: {response.choices[0].message.content}")
        print("\n🎉 DeepSeek API 配置正确，可以启动应用了！")
        
    except Exception as e:
        print(f"❌ API 连接失败: {e}")
        print("\n请检查:")
        print("1. API Key 是否正确")
        print("2. 账户是否有余额")
        print("3. 网络连接是否正常")

if __name__ == "__main__":
    test_deepseek()