import gradio as gr
from agents.orchestrator_simple import MemArtOrchestrator
from config import Config
import os
from pathlib import Path


def create_interface():
    # 按 session 隔离 orchestrator 实例
    orchestrators = {}

    def get_orchestrator(session_id: str) -> MemArtOrchestrator:
        """获取或创建 session 专属的 orchestrator"""
        if session_id not in orchestrators:
            orchestrators[session_id] = MemArtOrchestrator(session_id)
            print(f"📝 新会话创建: {session_id[:8]}...")
        return orchestrators[session_id]

    def respond(message, history, request: gr.Request):
        if not message:
            return "", history

        if history is None:
            history = ""

        orch = get_orchestrator(request.session_hash)

        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        response_text = ""

        async def get_response():
            nonlocal response_text
            async for chunk in orch.stream_with_strategy(message):
                response_text += chunk

        loop.run_until_complete(get_response())

        history += f"\n\n用户: {message}\n{response_text}\n{'-' * 50}"

        return "", history

    def set_strategy(strategy, request: gr.Request):
        orch = get_orchestrator(request.session_hash)
        return orch.switch_strategy(strategy)

    def set_mode(mode, request: gr.Request):
        orch = get_orchestrator(request.session_hash)
        return orch.switch_mode(mode)

    def toggle_image_gen(enabled, request: gr.Request):
        orch = get_orchestrator(request.session_hash)
        return orch.toggle_image_gen(enabled)

    def switch_api(api_name, request: gr.Request):
        orch = get_orchestrator(request.session_hash)
        success, message = orch.switch_api(api_name)
        return message

    def switch_collaborative_pair(primary, secondary, request: gr.Request):
        orch = get_orchestrator(request.session_hash)
        success, message = orch.switch_collaborative_pair(primary, secondary)
        return message

    def upload_file(file, request: gr.Request):
        if file is None:
            return "请选择文件", None

        orch = get_orchestrator(request.session_hash)

        # 安全处理：只取文件名，丢弃路径
        safe_filename = Path(file.name).name

        # 读取文件内容
        try:
            with open(file.name, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file.name, 'r', encoding='gbk') as f:
                content = f.read()

        # 保存到文档处理器，使用安全文件名
        result = orch.process_document(safe_filename, content)
        return f"✅ {result}", None

    # 获取当前 API 显示名称（需要 session 参数）
    def get_api_display(request: gr.Request):
        orch = get_orchestrator(request.session_hash)
        api_config = Config.get_current_api_config()
        return f"{api_config['icon']} {api_config['name']}"

    # 获取当前模式显示
    def get_mode_display(request: gr.Request):
        orch = get_orchestrator(request.session_hash)
        return orch.collaborative_mode

    # 创建界面
    with gr.Blocks(title="MemArt Agent") as demo:
        gr.Markdown("# 🎨 MemArt Agent - 智能 AI 助手")
        gr.Markdown("支持文档上传、文生图、多 API 协作")

        # 第一行：模式选择和文生图开关
        with gr.Group():
            gr.Markdown("### ⚙️ 核心设置")
            with gr.Row():
                # 工作模式
                with gr.Column(scale=1):
                    gr.Markdown("**工作模式**")
                    mode_display = gr.Textbox(value="single", label="当前模式", interactive=False)
                    with gr.Row():
                        single_mode_btn = gr.Button("🎯 单API模式", size="sm")
                        collab_mode_btn = gr.Button("🤝 协作模式", size="sm")
                        chain_mode_btn = gr.Button("⛓️ 链式模式", size="sm")

                # 文生图开关
                with gr.Column(scale=1):
                    gr.Markdown("**文生图功能**")
                    image_gen_toggle = gr.Checkbox(label="启用文生图", value=True)
                    image_gen_status = gr.Textbox(label="状态", value="✅ 已开启", interactive=False)

        # 第二行：API 选择（单模式）
        with gr.Group(visible=True) as single_api_group:
            gr.Markdown("### 🔌 单模式 API 选择")
            with gr.Row():
                api_status = gr.Textbox(label="当前 API", value="", interactive=False, scale=2)
                with gr.Column(scale=3):
                    llm_apis = ["deepseek", "openai", "zhipu", "tongyi", "moonshot"]
                    for api_key in llm_apis:
                        if api_key in Config.SUPPORTED_APIS:
                            api_info = Config.SUPPORTED_APIS[api_key]
                            btn = gr.Button(f"{api_info['icon']} {api_info['name']}", size="sm")
                            btn.click(lambda x=api_key: switch_api(x), outputs=[api_status])

        # 第三行：协作模式配置
        with gr.Group(visible=False) as collab_group:
            gr.Markdown("### 🤝 协作模式配置")
            gr.Markdown("主 API 负责理解分析，副 API 负责内容生成")
            with gr.Row():
                llm_choices = [(f"{info['icon']} {info['name']}", key)
                               for key, info in Config.SUPPORTED_APIS.items()
                               if key in ["deepseek", "openai", "zhipu", "tongyi", "moonshot"]]

                primary_select = gr.Dropdown(
                    choices=llm_choices,
                    label="主 API（理解分析）",
                    value=Config.PRIMARY_API
                )
                secondary_select = gr.Dropdown(
                    choices=llm_choices,
                    label="副 API（内容生成）",
                    value=Config.SECONDARY_API
                )
                apply_collab_btn = gr.Button("应用协作配置", variant="primary")

            collab_status = gr.Textbox(label="协作状态", interactive=False)
            apply_collab_btn.click(
                lambda p, s, r: switch_collaborative_pair(p, s, r),
                [primary_select, secondary_select],
                [collab_status]
            )

        # 第四行：推理策略
        with gr.Group():
            gr.Markdown("### 🧠 推理策略")
            with gr.Row():
                strategy_display = gr.Textbox(value="🤖 AUTO", label="当前策略", interactive=False, scale=1)
                auto_btn = gr.Button("🤖 AUTO", variant="primary", scale=1)
                react_btn = gr.Button("⚡ REACT", variant="secondary", scale=1)
                cot_btn = gr.Button("💭 COT", variant="secondary", scale=1)

        # 第五行：文档上传
        with gr.Group():
            gr.Markdown("### 📄 文档上传与 RAG")
            with gr.Row():
                file_upload = gr.File(label="上传文档", file_types=[".txt", ".pdf", ".md", ".docx", ".csv"])
                upload_status = gr.Textbox(label="上传状态", interactive=False, scale=2)
            file_upload.upload(upload_file, [file_upload], [upload_status])
            gr.Markdown("💡 提示：上传后系统会自动检索相关文档内容来增强回答")

        # 第六行：对话区域
        with gr.Group():
            gr.Markdown("### 💬 对话")
            chatbot = gr.Textbox(label="对话记录", lines=20, interactive=False)

            with gr.Row():
                msg = gr.Textbox(label="输入消息", placeholder="输入你的问题...", lines=3, scale=4)
                send = gr.Button("发送", variant="primary", scale=1)

            with gr.Row():
                clear = gr.Button("清空对话", variant="secondary", size="sm")

        # 模式切换逻辑
        def show_single_mode():
            return gr.update(visible=True), gr.update(visible=False)

        def show_collab_mode():
            return gr.update(visible=False), gr.update(visible=True)

        single_mode_btn.click(lambda r: set_mode("single", r), outputs=[mode_display])
        single_mode_btn.click(show_single_mode, outputs=[single_api_group, collab_group])

        collab_mode_btn.click(lambda r: set_mode("collaborative", r), outputs=[mode_display])
        collab_mode_btn.click(show_collab_mode, outputs=[single_api_group, collab_group])

        chain_mode_btn.click(lambda r: set_mode("chain", r), outputs=[mode_display])
        chain_mode_btn.click(show_single_mode, outputs=[single_api_group, collab_group])

        # 文生图开关
        def on_toggle_change(enabled, r):
            return toggle_image_gen(enabled, r)

        image_gen_toggle.change(on_toggle_change, [image_gen_toggle], [image_gen_status])

        # 策略事件
        def set_strategy_wrapper(s, r):
            result = set_strategy(s, r)
            display = {"auto": "🤖 AUTO", "react": "⚡ REACT", "cot": "💭 COT"}
            return display.get(s, "🤖 AUTO")

        auto_btn.click(lambda r: set_strategy_wrapper("auto", r), outputs=[strategy_display])
        react_btn.click(lambda r: set_strategy_wrapper("react", r), outputs=[strategy_display])
        cot_btn.click(lambda r: set_strategy_wrapper("cot", r), outputs=[strategy_display])

        # 发送事件
        send.click(respond, [msg, chatbot], [msg, chatbot])
        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        clear.click(lambda: ("", ""), outputs=[msg, chatbot])

    return demo


if __name__ == "__main__":
    demo = create_interface()
    demo.launch()