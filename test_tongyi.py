import os
from dotenv import load_dotenv
import dashscope
from dashscope import ImageSynthesis

load_dotenv()

def test_tongyi():
    print("="*50)
    print("🧪 测试通义万相 API")
    print("="*50)
    
    api_key = os.getenv("TONGYI_API_KEY")
    if not api_key:
        print("❌ 请设置 TONGYI_API_KEY")
        return
    
    dashscope.api_key = api_key
    
    try:
        rsp = ImageSynthesis.call(
            model="wanx2.6-t2i",
            prompt="一只可爱的橘猫坐在窗台上，阳光洒在身上，温馨风格",
            size="1024*1024",
            n=1
        )
        
        if rsp.status_code == 200:
            print("✅ 生成成功！")
            print(f"图片 URL: {rsp.output.results[0].url}")
        else:
            print(f"❌ 生成失败: {rsp.message}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    test_tongyi()