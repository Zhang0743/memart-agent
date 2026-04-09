# 🎨 MemArt Agent

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-green.svg)](https://langchain.com)
[![Gradio](https://img.shields.io/badge/Gradio-4.0+-orange.svg)](https://gradio.app)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

**一个支持多策略推理、多API协作、文档RAG的智能AI助手系统**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [架构设计](#-架构设计) • [使用指南](#-使用指南) • [API支持](#-api支持)

</div>

---

## ✨ 功能特性

### 🧠 多策略推理
- **ReAct** - 推理+行动交替，适合工具调用场景
- **Chain-of-Thought** - 思维链逐步推理，适合复杂分析
- **Auto** - 智能自动选择最优策略

### 🤝 多API协作
- **单API模式** - 使用单个LLM完成所有任务
- **协作模式** - 主API理解分析 + 副API内容生成
- **链式模式** - 多API接力处理，逐步优化答案

### 📄 文档RAG
- 支持上传 `.txt`、`.pdf`、`.md`、`.docx`、`.csv` 文件
- 自动分块处理，向量化存储
- 对话时智能检索相关文档内容

### 🎨 图像生成
- 集成通义万相 API
- 支持 Replicate (Stable Diffusion)
- Mock 模式用于测试

### 💾 分层记忆
- **短期记忆** - Redis存储，7天自动过期
- **长期记忆** - ChromaDB向量存储，支持语义检索
- 跨会话知识保留

### 🌊 流式输出
- 实时显示AI思考过程
- 逐字输出，提升交互体验

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Redis (可选，用于短期记忆)
- 至少一个LLM API密钥

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/Zhang0743/memart-agent.git
cd memart-agent

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥

# 5. 启动应用
python run.py
### Docker 部署 (可选)

```bash
docker build -t memart-agent .
docker run -p 7860:7860 --gpus all memart-agent
### 🏗️ 架构设计

```text
┌─────────────────────────────────────────────────────────────┐
│                     用户界面 (Gradio)                        │
...│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  策略选择器  │  │  API切换器  │  │  文档上传   │         │
│  │ ReAct/CoT   │  │ 单/协作/链式 │  │   RAG检索   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                    核心编排层 (Orchestrator)                 │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  记忆模块     │  推理引擎     │  协作客户端   │  文档处理器   │
│  Redis       │  ReAct/CoT   │  多API调度   │  ChromaDB    │
│  ChromaDB    │              │              │              │
├──────────────┴──────────────┴──────────────┴───────────────┤
│                      工具层 (Tools)                          │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  SQL Agent   │ Vision Agent │  Image Gen   │  Search      │
│  数据库查询   │  图像处理     │  图片生成     │  知识检索     │
└──────────────┴──────────────┴──────────────┴───────────────┘
📖 使用指南
基础对话
text
用户: 你好，请介绍一下自己
助手: 我是MemArt Agent，一个智能AI助手...
图片生成
text
用户: 生成一张星空下的城堡图片
助手: 🎨 正在生成图片...
      ✅ 图片已生成！
文档问答
text
1. 点击"上传文档"按钮
2. 选择你的PDF/TXT文件
3. 提问: 根据上传的文档，总结一下主要内容
协作模式
text
1. 点击"协作模式"按钮
2. 选择主API (负责理解) 和副API (负责生成)
3. 提问: 帮我写一篇关于AI的短文
   → 主API分析需求 → 副API生成内容
🔌 API支持
LLM API
API	图标	特点	配置变量
DeepSeek	🔵	性价比高，中文能力强	DEEPSEEK_API_KEY
OpenAI	🟢	功能强大，全球领先	OPENAI_API_KEY
智谱GLM	🟣	国内可用，免费额度	ZHIPU_API_KEY
通义千问	🟠	阿里出品，中文优化	TONGYI_API_KEY
Moonshot	🔴	长文本处理能力强	MOONSHOT_API_KEY
图像生成 API
API	图标	特点	配置变量
通义万相	🎨	中文优化，质量优秀	TONGYI_API_KEY
Replicate	🖼️	Stable Diffusion	REPLICATE_API_TOKEN

### 📁 项目结构

```text
memart-agent/
├── agents/
...            # Agent 核心模块
│   ├── orchestrator_simple.py # 主协调器
│   ├── collaborative_client.py # 多API协作客户端
│   ├── document_processor.py   # 文档处理与RAG
│   ├── vision_agent.py         # 图像生成Agent
│   └── sql_agent.py            # SQL查询Agent
├── memory/                    # 记忆系统
│   ├── short_term.py          # 短期记忆 (Redis)
│   └── long_term.py           # 长期记忆 (ChromaDB)
├── web/                       # Web界面
│   └── app.py                 # Gradio应用
├── config.py                  # 配置文件
├── run.py                     # 启动入口
├── requirements.txt           # 依赖列表
└── .env                       # 环境变量 (不提交)
🛠️ 技术栈
类别	技术
核心语言	Python 3.10+
LLM框架	LangChain, OpenAI SDK
Web框架	Gradio
向量数据库	ChromaDB
缓存	Redis
图像生成	通义万相, Replicate
异步处理	asyncio
📊 性能优化
流式输出：首字延迟 < 500ms

文档检索：毫秒级向量搜索

API切换：热切换，无需重启

记忆存储：支持1000+条对话记录

🤝 贡献
欢迎提交 Issue 和 Pull Request！

Fork 本仓库

创建你的特性分支 (git checkout -b feature/AmazingFeature)

提交你的更改 (git commit -m 'Add some AmazingFeature')

推送到分支 (git push origin feature/AmazingFeature)

打开 Pull Request

📄 许可证
本项目采用 MIT 许可证 - 详见 LICENSE 文件

📧 联系方式
作者: [Yun Zhang]

GitHub: @Zhang0743

邮箱: 3339160743@qq.com

🙏 致谢
LangChain - 优秀的LLM应用框架

Gradio - 便捷的ML Web界面库

ChromaDB - 轻量级向量数据库

DeepSeek - 提供优质API服务

<div align="center">
如果这个项目对你有帮助，请给个 ⭐️ Star 支持一下！

</div> ```
创建 screenshots 目录和占位文件
powershell
mkdir screenshots

# 创建占位文件说明
echo "# 截图目录

请添加以下截图：
- main.png: 主界面截图
- collab.png: 协作模式截图  
- rag.png: 文档上传RAG截图
- image_gen.png: 图片生成截图
" > screenshots\README.md
创建 LICENSE 文件
powershell
notepad LICENSE
text
MIT License

Copyright (c) 2024 [你的名字]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
创建 .gitignore 文件
powershell
notepad .gitignore
gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
env/
ENV/
.env
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project specific
chroma_db/
generated_images/
uploaded_documents/
memart.db
*.db

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Gradio
gradio_cached_examples/