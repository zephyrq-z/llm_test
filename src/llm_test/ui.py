"""
LLM 测试工具 UI (Streamlit)

启动方式:
    llm-test-ui          # 注册的 CLI 命令
    streamlit run src/llm_test/ui.py
"""

import streamlit as st

from llm_test.core import (
    test_llm,
    load_presets,
    load_history,
    save_test_result,
    delete_history_item,
    update_history_item,
)


# ─── 页面配置 ────────────────────────────────────────────────────

st.set_page_config(
    page_title="LLM 接口测试工具",
    page_icon="🧪",
    layout="wide",
)

STATUS_COLORS = {
    "success": "green",
    "timeout": "orange",
    "connection_error": "red",
    "http_error": "red",
    "error": "red",
}


# ─── 通用渲染 ────────────────────────────────────────────────────

def render_result(result: dict, col) -> None:
    """在指定列中渲染测试结果"""
    with col:
        st.subheader("测试结果")
        status = result.get("status", "unknown")
        color = STATUS_COLORS.get(status, "gray")

        st.metric("状态", status.upper(), delta=None, delta_color=color)
        st.metric("耗时", f"{result.get('latency_ms', 0)} ms")

        if result.get("response_preview"):
            st.info(f"**响应预览:**\n\n{result['response_preview']}")
        if result.get("error"):
            st.error(f"**错误信息:**\n\n{result['error']}")


def run_test_and_save(baseurl: str, apikey: str, model: str, preset_name: str = "") -> None:
    """执行测试并保存结果"""
    with st.spinner("正在测试..."):
        result = test_llm(baseurl, apikey, model)

    col_result, col_config = st.columns(2)
    render_result(result, col_result)

    with col_config:
        st.subheader("配置信息")
        st.json({"baseurl": baseurl, "model": model, "preset_name": preset_name})

        config = {
            "baseurl": baseurl,
            "apikey": apikey,
            "model": model,
            "preset_name": preset_name,
        }
        save_test_result(config, result)
        st.success("✓ 配置已保存到历史记录")


# ─── 主界面 ──────────────────────────────────────────────────────

def main():
    st.title("🧪 LLM 接口测试工具")
    st.markdown(
        "**支持主流 LLM 提供商的连通性测试**\n\n"
        "- OpenAI (GPT-3.5/4)\n"
        "- 阿里云通义千问\n"
        "- 智谱 AI (GLM)\n"
        "- DeepSeek\n"
        "- Moonshot AI (Kimi)\n"
        "- 01.AI Yi\n"
        "- Groq"
    )

    tab1, tab2, tab3 = st.tabs(["✨ 快速测试", "📚 预设配置", "📋 历史记录"])

    # ── Tab 1: 快速测试 ──────────────────────────────────────────
    with tab1:
        st.header("快速测试")

        with st.form("test_form", clear_on_submit=False):
            col1, col2 = st.columns(2)

            with col1:
                baseurl = st.text_input(
                    "Base URL",
                    placeholder="https://api.openai.com/v1",
                    help="LLM 接口基础地址",
                )
                apikey = st.text_input("API Key", type="password", placeholder="sk-xxx")

            with col2:
                model = st.text_input("模型名称", placeholder="gpt-4")
                preset_name = st.text_input("预设名称（可选）", placeholder="OpenAI GPT-4")

            submitted = st.form_submit_button("🚀 开始测试", type="primary")

            if submitted:
                if not baseurl or not apikey or not model:
                    st.error("请填写完整的配置信息")
                else:
                    run_test_and_save(baseurl, apikey, model, preset_name)

    # ── Tab 2: 预设配置 ──────────────────────────────────────────
    with tab2:
        st.header("预设配置")
        presets = load_presets()

        if not presets:
            st.warning("暂无预设配置")
        else:
            st.info(f"共加载 {len(presets)} 个预设配置")

            for i, preset in enumerate(presets, 1):
                with st.expander(f"{i}. {preset['name']} — {preset['model']}", expanded=(i == 1)):
                    st.markdown(f"**描述:** {preset['description']}")

                    c1, c2 = st.columns(2)
                    with c1:
                        st.text(f"Base URL: {preset['baseurl']}")
                        st.text(f"模型:     {preset['model']}")
                    with c2:
                        st.text(f"预设名称: {preset['name']}")

                    apikey_key = f"preset_apikey_{i}"
                    if apikey_key not in st.session_state:
                        st.session_state[apikey_key] = preset.get("apikey", "")

                    apikey_val = st.text_input(
                        "API Key",
                        value=st.session_state[apikey_key],
                        type="password",
                        placeholder="请输入 API Key",
                        key=f"apikey_input_{i}",
                    )
                    st.session_state[apikey_key] = apikey_val

                    if st.button("🧪 测试此预设", key=f"test_{i}"):
                        if not apikey_val:
                            st.error("请先填写 API Key")
                        else:
                            with st.spinner("正在测试..."):
                                result = test_llm(preset["baseurl"], apikey_val, preset["model"])

                            col_result, col_config = st.columns(2)
                            render_result(result, col_result)

                            with col_config:
                                st.json({
                                    "baseurl": preset["baseurl"],
                                    "model": preset["model"],
                                    "preset_name": preset["name"],
                                })

                                config = {
                                    "baseurl": preset["baseurl"],
                                    "apikey": apikey_val,
                                    "model": preset["model"],
                                    "preset_name": preset["name"],
                                }
                                save_test_result(config, result)
                                st.success("✓ 配置已保存到历史记录")

    # ── Tab 3: 历史记录 ──────────────────────────────────────────
    with tab3:
        st.header("历史记录")
        history = load_history()

        if not history:
            st.warning("暂无历史记录")
        else:
            selected_ids = st.multiselect(
                "选择要删除的记录",
                [item["id"] for item in history],
                format_func=lambda x: next(
                    (f"{i['id']} — {i['timestamp']}" for i in history if i["id"] == x), x
                ),
            )

            if selected_ids:
                if st.button("🗑️ 删除选中记录", type="secondary"):
                    for cid in selected_ids:
                        delete_history_item(cid)
                    st.rerun()

            st.info(f"共 {len(history)} 条记录")

            for item in reversed(history):
                with st.expander(f"{item['id']} — {item['timestamp']}", expanded=False):
                    st.markdown("**配置信息**")

                    c1, c2 = st.columns(2)

                    with c1:
                        st.text(f"Base URL: {item['baseurl']}")
                        st.text(f"模型:     {item['model']}")
                        if item.get("preset_name"):
                            st.text(f"预设名称: {item['preset_name']}")
                        st.text(f"API Key:  {'***' if item.get('apikey') else '(未设置)'}")

                    with c2:
                        status = item.get("status", "unknown")
                        color = STATUS_COLORS.get(status, "gray")
                        st.metric("状态", status.upper(), delta=None, delta_color=color)
                        st.metric("耗时", f"{item.get('latency_ms', 0)} ms")

                    if item.get("response_preview"):
                        st.info(f"**响应预览:**\n\n{item['response_preview']}")
                    if item.get("error"):
                        st.error(f"**错误信息:**\n\n{item['error']}")

                    ce, cd = st.columns(2)
                    with ce:
                        if st.button("✏️ 编辑", key=f"edit_{item['id']}"):
                            st.session_state["editing_id"] = item["id"]
                            st.session_state["editing_item"] = item
                            st.rerun()
                    with cd:
                        if st.button("🗑️ 删除", key=f"delete_{item['id']}"):
                            if st.session_state.get("editing_id") == item["id"]:
                                st.session_state["editing_id"] = None
                                st.session_state["editing_item"] = None
                            delete_history_item(item["id"])
                            st.rerun()

    # ── 编辑模式 ─────────────────────────────────────────────────
    if st.session_state.get("editing_id"):
        st.divider()
        st.subheader("✏️ 编辑记录")

        item = st.session_state["editing_item"]

        with st.form("edit_form", clear_on_submit=False):
            c1, c2 = st.columns(2)

            with c1:
                new_baseurl = st.text_input("Base URL", value=item.get("baseurl", ""), key="edit_baseurl")
                new_model = st.text_input("模型名称", value=item.get("model", ""), key="edit_model")
                new_preset_name = st.text_input("预设名称", value=item.get("preset_name", ""), key="edit_preset_name")

            with c2:
                new_apikey = st.text_input(
                    "API Key", value="", type="password", key="edit_apikey",
                    placeholder="留空则不更新",
                )

            submitted = st.form_submit_button("💾 保存修改", type="primary")

            if submitted:
                updates = {}
                if new_baseurl:
                    updates["baseurl"] = new_baseurl
                if new_model:
                    updates["model"] = new_model
                if new_preset_name:
                    updates["preset_name"] = new_preset_name
                if new_apikey:
                    updates["apikey"] = new_apikey

                update_history_item(st.session_state["editing_id"], updates)
                st.success("✓ 保存成功")
                st.session_state["editing_id"] = None
                st.session_state["editing_item"] = None
                st.rerun()


if __name__ == "__main__":
    main()
