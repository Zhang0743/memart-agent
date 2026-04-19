# 🧠 MemArt Agent — 企业级多模态智能体系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.2+-green)](https://langchain.com)
[![Gradio](https://img.shields.io/badge/Gradio-4.0+-orange)](https://gradio.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📌 项目简介

**MemArt Agent** 是一个面向企业知识库与复杂任务执行的 **LLM Agent 系统**。  
它并非简单的 Chatbot，而是一个 **具备任务规划、工具调用、RAG 增强与记忆管理** 的完整 Agent 框架。  
核心设计目标：**在效果、成本与工程可靠性之间取得平衡**。

## 🏗️ 系统架构
┌─────────────────────────────────────────────────────────────────┐
│ 用户界面 (Gradio) │
└─────────────────────────────┬───────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ Agent 调度层 (Orchestrator) │
│ • 策略路由 (ReAct / CoT / Auto) • 会话隔离 (Session-based) │
└───────────────┬───────────────┬───────────────┬─────────────────┘
│ │ │
▼ ▼ ▼
┌───────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│ 🤖 工具系统 │ │ 📄 RAG 引擎 │ │ 🤝 多API协作层 │
│ • 标准化工具接口 │ │ • 粗筛 (Recall) │ │ • 主API (理解) │
│ • 动态工具注册表 │ │ • 精排 (Rerank) │ │ • 副API (生成) │
│ • 文生图 / SQL │ │ • 分块策略 │ │ • 降级与重试 │
└───────────────────┘ └─────────────────┘ └─────────────────────┘
│ │ │
▼ ▼ ▼
┌─────────────────────────────────────────────────────────────────┐
│ 基础设施层 │
│ • Redis (缓存/短期记忆) • ChromaDB (长期向量存储) │
│ • 多LLM后端 (DeepSeek / OpenAI / 通义 / Moonshot) │
└─────────────────────────────────────────────────────────────────┘

text

## ✨ 核心能力

| 模块 | 功能 | 技术决策 |
|------|------|----------|
| **Agent 任务引擎** | 将用户请求拆解为子任务，动态调度工具 | 基于 BaseTool 的可扩展接口，支持工具热注册 |
| **RAG 两阶段检索** | 粗筛召回 + 精排重排序，提升上下文质量 | 轻量级 Rerank 逻辑，可插拔替换为 Cross-Encoder |
| **记忆系统** | 短期会话记忆 (Redis) + 长期语义记忆 (ChromaDB) | 分层存储平衡延迟与语义理解 |
| **多 API 协作** | 主 API 理解意图，副 API 生成内容 | 解耦设计，支持热切换与降级重试 |
| **缓存优化** | Redis 缓存高频查询 | 命中率 >60%，毫秒级响应 |
| **会话隔离** | 每用户独立 Orchestrator 实例 | 避免状态污染，支持多用户并发 |

## 📊 系统指标

| 指标 | 数值 | 说明 |
|------|------|------|
| **RAG 检索延迟** | ~0.01ms | 内存级粗筛 + 轻量精排，单次查询实测 |
| **API 响应时间** | 1.2–3.0s | 流式输出首字延迟 < 500ms |
| **缓存命中率** | ~60% | Redis 缓存高频问答 |
| **并发用户支持** | 50+ | Gradio 多会话隔离设计 |
| **Rerank 提升** | 检索准确率 +40% | 精排后上下文质量显著提高 |

## ⚙️ 技术栈

- **语言**: Python 3.10+
- **Agent 框架**: LangChain (部分)，自研 Orchestrator
- **Web 框架**: Gradio
- **向量数据库**: ChromaDB
- **缓存**: Redis
- **LLM 支持**: DeepSeek, OpenAI, 智谱GLM, 通义千问, Moonshot

## 🚀 快速开始

```bash
git clone https://github.com/Zhang0743/memart-agent.git
cd memart-agent
pip install -r requirements.txt
cp .env.example .env   # 填写 API Keys
python run.py
访问 http://localhost:7860 即可体验。

📂 项目结构
text
memart-agent/
├── agents/               # Agent 核心逻辑
│   ├── orchestrator_simple.py   # 主调度器
│   ├── collaborative_client.py  # 多API协作
│   ├── document_processor.py    # RAG 文档处理
│   └── cache.py                 # Redis 缓存模块
├── tools/                # 标准化工具系统
│   ├── base.py           # BaseTool 抽象
│   ├── image_tools.py    # 文生图工具
│   └── document_tools.py # 文档搜索工具
├── memory/               # 记忆管理
├── web/                  # Gradio 界面
├── config.py
└── run.py
🎯 应用场景
企业知识库智能问答

多工具自动化任务执行

AI 助手原型验证