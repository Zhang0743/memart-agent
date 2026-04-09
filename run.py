#!/usr/bin/env python
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    print("=" * 50)
    print("🚀 MemArt Agent 启动中...")
    print("=" * 50)

    # 创建必要目录
    os.makedirs("./generated_images", exist_ok=True)
    os.makedirs("./chroma_db", exist_ok=True)

    print("\n🎨 启动 Web 界面...")
    print("访问地址: http://localhost:7860")
    print("=" * 50)

    from web.app import create_interface
    demo = create_interface()
    demo.launch(server_port=7860)


if __name__ == "__main__":
    main()