import gradio as gr
from agents.orchestrator_simple import MemArtOrchestrator
from config import Config
from pathlib import Path
import uuid


def create_interface():
    # 全局存储：session_id -> orchestrator
    orchestrators = {}

    def get_orchestrator(session_id: str) -> MemArtOrchestrator:
        if session_id not in orchestrators:
            orchestrators[session_id] = MemArtOrchestrator(session_id)
            print(f"📝 新会话创建: {session_id[:8]}...")
        return orchestrators[session_id]

    # === 页面加载时初始化会话 ===
    def init_session(request: gr.Request):
        """返回 session_id 和初始状态值"""
        session_id = request.session_hash
        orch = get_orchestrator(session_id)
        return (
            session_id,
            orch.collaborative_mode or "single",
            "✅ 已开启" if orch.enable_image_gen else "❌ 已关闭",
            {"auto": "🤖 AUTO", "react": "⚡ REACT", "cot": "💭 COT"}.get(orch.current_strategy, "🤖 AUTO"),
            f"{Config.get_current_api_config().get('icon', '')} {Config.get_current_api_config().get('name', 'Unknown')}"
        )

    # === 交互函数（接收 session_id 而非 request） ===
    def respond(message, history, session_id):
        if not message:
            return "", history, session_id
        if history is None:
            history = ""

        orch = get_orchestrator(session_id)

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
        return "", history, session_id

    def set_strategy(strategy, session_id):
        orch = get_orchestrator(session_id)
        orch.switch_strategy(strategy)
        display = {"auto": "🤖 AUTO", "react": "⚡ REACT", "cot": "💭 COT"}
        return display.get(strategy, "🤖 AUTO")

    def set_mode(mode, session_id):
        orch = get_orchestrator(session_id)
        return orch.switch_mode(mode)

    def toggle_image_gen(enabled, session_id):
        orch = get_orchestrator(session_id)
        return orch.toggle_image_gen(enabled)

    def switch_api(api_name, session_id):
        orch = get_orchestrator(session_id)
        orch.switch_api(api_name)
        api_config = Config.get_current_api_config()
        return f"{api_config.get('icon', '')} {api_config.get('name', 'Unknown')}"

    def switch_collaborative_pair(primary, secondary, session_id):
        orch = get_orchestrator(session_id)
        success, msg = orch.switch_collaborative_pair(primary, secondary)
        return msg

    def upload_file(file, session_id):
        if file is None:
            return "请选择文件"
        orch = get_orchestrator(session_id)
        safe_filename = Path(file.name).name
        try:
            with open(file.name, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file.name, 'r', encoding='gbk') as f:
                content = f.read()
        result = orch.process_document(safe_filename, content)
        return f"✅ {result}"

    # === 构建界面 ===
    with gr.Blocks(title="MemArt Agent") as demo:
        # 隐藏的会话状态组件
        session_state = gr.State(value="")

        with gr.Group():
            gr.Markdown("# 🎨 MemArt Agent - 智能 AI 助手")
            gr.Markdown("支持文档上传、文生图、多 API 协作")

        with gr.Group():
            gr.Markdown("### ⚙️ 核心设置")
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("**工作模式**")
                    mode_display = gr.Textbox(label="当前模式", interactive=False)
                    with gr.Row():
                        single_btn = gr.Button("🎯 单API模式", size="sm")
                        collab_btn = gr.Button("🤝 协作模式", size="sm")
                        chain_btn = gr.Button("⛓️ 链式模式", size="sm")
                with gr.Column(scale=1):
                    gr.Markdown("**文生图功能**")
                    image_gen_toggle = gr.Checkbox(label="启用文生图", value=True)
                    image_gen_status = gr.Textbox(label="状态", interactive=False)

        with gr.Group(visible=True) as single_api_group:
            gr.Markdown("### 🔌 单模式 API 选择")
            with gr.Row():
                api_status = gr.Textbox(label="当前 API", interactive=False, scale=2)
                with gr.Column(scale=3):
                    llm_apis = ["deepseek", "openai", "zhipu", "tongyi", "moonshot"]
                    for api_key in llm_apis:
                        if api_key in Config.SUPPORTED_APIS:
                            info = Config.SUPPORTED_APIS[api_key]
                            btn = gr.Button(f"{info['icon']} {info['name']}", size="sm")
                            btn.click(
                                fn=lambda key=api_key, sid=session_state: switch_api(key, sid),
                                inputs=[session_state],
                                outputs=[api_status]
                            )

        with gr.Group(visible=False) as collab_group:
            gr.Markdown("### 🤝 协作模式配置")
            with gr.Row():
                llm_choices = [(f"{info['icon']} {info['name']}", key)
                               for key, info in Config.SUPPORTED_APIS.items()
                               if key in llm_apis]
                primary_select = gr.Dropdown(choices=llm_choices, label="主 API", value=Config.PRIMARY_API)
                secondary_select = gr.Dropdown(choices=llm_choices, label="副 API", value=Config.SECONDARY_API)
                apply_btn = gr.Button("应用", variant="primary")
            collab_status = gr.Textbox(label="协作状态", interactive=False)
            apply_btn.click(
                fn=lambda p, s, sid: switch_collaborative_pair(p, s, sid),
                inputs=[primary_select, secondary_select, session_state],
                outputs=[collab_status]
            )

        with gr.Group():
            gr.Markdown("### 🧠 推理策略")
            with gr.Row():
                strategy_display = gr.Textbox(label="当前策略", interactive=False, scale=1)
                auto_btn = gr.Button("🤖 AUTO", variant="primary", scale=1)
                react_btn = gr.Button("⚡ REACT", variant="secondary", scale=1)
                cot_btn = gr.Button("💭 COT", variant="secondary", scale=1)

        with gr.Group():
            gr.Markdown("### 📄 文档上传与 RAG")
            with gr.Row():
                file_upload = gr.File(label="上传文档", file_types=[".txt", ".pdf", ".md", ".docx", ".csv"])
                upload_status = gr.Textbox(label="上传状态", interactive=False, scale=2)
            file_upload.upload(fn=upload_file, inputs=[file_upload, session_state], outputs=[upload_status])

        with gr.Group():
            gr.Markdown("### 💬 对话")
            chatbot = gr.Textbox(label="对话记录", lines=20, interactive=False)
            with gr.Row():
                msg = gr.Textbox(label="输入消息", placeholder="输入你的问题...", lines=3, scale=4)
                send = gr.Button("发送", variant="primary", scale=1)
            with gr.Row():
                clear = gr.Button("清空对话", variant="secondary", size="sm")

        # === 页面加载时初始化会话状态 ===
        demo.load(
            fn=init_session,
            outputs=[session_state, mode_display, image_gen_status, strategy_display, api_status]
        )

        # === 事件绑定 ===
        single_btn.click(
            fn=lambda sid: set_mode("single", sid),
            inputs=[session_state],
            outputs=[mode_display]
        ).then(
            fn=lambda: (gr.update(visible=True), gr.update(visible=False)),
            outputs=[single_api_group, collab_group]
        )

        collab_btn.click(
            fn=lambda sid: set_mode("collaborative", sid),
            inputs=[session_state],
            outputs=[mode_display]
        ).then(
            fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
            outputs=[single_api_group, collab_group]
        )

        chain_btn.click(
            fn=lambda sid: set_mode("chain", sid),
            inputs=[session_state],
            outputs=[mode_display]
        ).then(
            fn=lambda: (gr.update(visible=True), gr.update(visible=False)),
            outputs=[single_api_group, collab_group]
        )

        image_gen_toggle.change(
            fn=toggle_image_gen,
            inputs=[image_gen_toggle, session_state],
            outputs=[image_gen_status]
        )

        auto_btn.click(
            fn=lambda sid: set_strategy("auto", sid),
            inputs=[session_state],
            outputs=[strategy_display]
        )
        react_btn.click(
            fn=lambda sid: set_strategy("react", sid),
            inputs=[session_state],
            outputs=[strategy_display]
        )
        cot_btn.click(
            fn=lambda sid: set_strategy("cot", sid),
            inputs=[session_state],
            outputs=[strategy_display]
        )

        send.click(
            fn=respond,
            inputs=[msg, chatbot, session_state],
            outputs=[msg, chatbot, session_state]
        )
        msg.submit(
            fn=respond,
            inputs=[msg, chatbot, session_state],
            outputs=[msg, chatbot, session_state]
        )
        clear.click(
            fn=lambda: ("", ""),
            outputs=[msg, chatbot]
        )

    return demo


if __name__ == "__main__":
    demo = create_interface()
    demo.launch(server_port=7861)