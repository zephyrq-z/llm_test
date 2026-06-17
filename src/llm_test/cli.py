#!/usr/bin/env python3
"""
LLM 测试工具 CLI

全局命令: llm-test
"""

import sys
import argparse

from llm_test.core import (
    test_llm,
    load_presets,
    load_history,
    save_test_result,
    delete_history_item,
    update_history_item,
)


# ─── Banner ───────────────────────────────────────────────────────

def print_banner():
    print(
        "\n"
        "╔══════════════════════════════════════════════════════════════╗\n"
        "║                                                              ║\n"
        "║           LLM 接口测试工具 v1.0                              ║\n"
        "║                                                              ║\n"
        "║    支持 OpenAI、阿里云通义千问、智谱 AI、DeepSeek 等主流厂商 ║\n"
        "║                                                              ║\n"
        "╚══════════════════════════════════════════════════════════════╝\n"
    )


# ─── 命令实现 ─────────────────────────────────────────────────────

def cmd_test(args):
    """测试 LLM 接口"""
    print(f"\n[测试配置]")
    print(f"  Base URL: {args.baseurl}")
    print(f"  Model:    {args.model}")

    print("\n[执行测试中...]")
    result = test_llm(args.baseurl, args.apikey, args.model)

    print(f"\n[测试结果]")
    print(f"  状态:     {result['status']}")
    print(f"  耗时:     {result['latency_ms']} ms")
    print(f"  模型:     {result['model']}")

    if result.get("response_preview"):
        print(f"  响应:     {result['response_preview']}")
    if result.get("error"):
        print(f"  错误:     {result['error']}")

    config = {
        "baseurl": args.baseurl,
        "apikey": args.apikey,
        "model": args.model,
        "preset_name": getattr(args, "preset_name", "") or "",
    }

    config_id = save_test_result(config, result)
    print(f"\n[保存] 配置已保存，ID: {config_id}")


def cmd_list(args):
    """列出所有预设"""
    presets = load_presets()

    if not presets:
        print("\n[提示] 暂无预设配置")
        return

    print(f"\n[预设配置] 共 {len(presets)} 个\n")

    for i, preset in enumerate(presets, 1):
        print(f"  {i}. {preset['name']}")
        print(f"     模型:     {preset['model']}")
        print(f"     描述:     {preset['description']}")
        print(f"     Base URL: {preset['baseurl']}")
        print()


def cmd_history(args):
    """查看历史记录"""
    history = load_history()

    if not history:
        print("\n[提示] 暂无历史测试记录")
        return

    print(f"\n[历史记录] 共 {len(history)} 条\n")

    for item in history:
        print(f"  ID:       {item['id']}")
        print(f"  时间:     {item['timestamp']}")
        print(f"  Base URL: {item['baseurl']}")
        print(f"  模型:     {item['model']}")

        if item.get("preset_name"):
            print(f"  预设:     {item['preset_name']}")

        print(f"  状态:     {item['status']}")
        print(f"  耗时:     {item['latency_ms']} ms")

        if item.get("response_preview"):
            print(f"  响应:     {item['response_preview']}")
        if item.get("error"):
            print(f"  错误:     {item['error']}")

        print("-" * 60)


def cmd_delete(args):
    """删除历史记录"""
    if not args.id:
        print("\n[错误] 请指定要删除的记录 ID")
        return

    success = delete_history_item(args.id)
    if success:
        print(f"\n[成功] 已删除记录: {args.id}")
    else:
        print(f"\n[错误] 未找到记录: {args.id}")


def cmd_update(args):
    """更新历史记录"""
    history = load_history()

    if not history:
        print("\n[错误] 暂无历史记录")
        return

    found = False
    for item in history:
        if item["id"] == args.id:
            found = True
            updates = {}

            if args.baseurl:
                updates["baseurl"] = args.baseurl
            if args.model:
                updates["model"] = args.model
            if args.apikey:
                updates["apikey"] = args.apikey
            if args.preset_name:
                updates["preset_name"] = args.preset_name

            success = update_history_item(args.id, updates)
            if success:
                print(f"\n[成功] 已更新记录: {args.id}")
                print(f"  更新字段: {', '.join(updates.keys())}")
            else:
                print(f"\n[错误] 更新失败")
            break

    if not found:
        print(f"\n[错误] 未找到记录: {args.id}")


def cmd_run_preset(args):
    """运行预设配置"""
    presets = load_presets()

    if not presets:
        print("\n[错误] 暂无预设配置")
        return

    if args.name:
        preset = next((p for p in presets if p["name"] == args.name), None)
    else:
        cmd_list(None)
        return

    if not preset:
        print(f"\n[错误] 未找到预设: {args.name}")
        return

    # 将预设配置注入 args
    args.baseurl = preset["baseurl"]
    args.model = preset["model"]
    args.preset_name = preset["name"]

    # API Key 优先级: CLI --apikey > 预设中的值 > 交互输入
    apikey = getattr(args, "apikey", None) or preset.get("apikey", "")
    if not apikey:
        apikey = input("请输入 API Key: ").strip()
        if not apikey:
            print("\n[错误] API Key 不能为空")
            return
    args.apikey = apikey

    print(f"\n[预设] 使用配置: {preset['name']}")
    cmd_test(args)


def cmd_ui(args):
    """启动 Streamlit Web UI"""
    import subprocess
    from pathlib import Path

    ui_path = Path(__file__).resolve().parent / "ui.py"
    port = getattr(args, "port", None) or 8501
    headless = getattr(args, "headless", False)

    print(f"\n🧪 启动 LLM 测试工具 Web UI...")
    print(f"   地址: http://localhost:{port}")
    if headless:
        print("   模式: headless（不自动打开浏览器）")
    print()

    cmd = ["streamlit", "run", str(ui_path), "--server.port", str(port)]
    if headless:
        cmd += ["--server.headless", "true"]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n\n[退出] Web UI 已停止")
    except FileNotFoundError:
        print("\n[错误] 未找到 streamlit，请先安装: pip install streamlit")
    except subprocess.CalledProcessError as e:
        print(f"\n[错误] Streamlit 退出码: {e.returncode}")


# ─── 入口 ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="llm-test",
        description="LLM 接口测试工具 — 连通性自测 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  llm-test test --baseurl https://api.openai.com/v1 --apikey sk-xxx --model gpt-4
  llm-test run-preset --name "阿里云通义千问" --apikey sk-xxx
  llm-test list
  llm-test history
  llm-test delete --id test_1234567890
  llm-test update --id test_1234567890 --model glm-4
  llm-test ui
  llm-test ui --port 8502 --headless
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # test
    test_parser = subparsers.add_parser("test", help="测试 LLM 接口")
    test_parser.add_argument("--baseurl", required=True, help="LLM 接口基础地址")
    test_parser.add_argument("--apikey", required=True, help="API 密钥")
    test_parser.add_argument("--model", required=True, help="模型名称")
    test_parser.add_argument("--preset-name", help="预设配置名称（可选）")

    # run-preset
    preset_parser = subparsers.add_parser("run-preset", help="运行预设配置")
    preset_parser.add_argument("--name", help="预设配置名称")
    preset_parser.add_argument("--apikey", help="API 密钥（可选，优先级高于预设中的值）")

    # list
    subparsers.add_parser("list", help="列出所有预设配置")

    # history
    subparsers.add_parser("history", help="查看历史记录")

    # delete
    delete_parser = subparsers.add_parser("delete", help="删除历史记录")
    delete_parser.add_argument("--id", required=True, help="记录 ID")

    # update
    update_parser = subparsers.add_parser("update", help="更新历史记录")
    update_parser.add_argument("--id", required=True, help="记录 ID")
    update_parser.add_argument("--baseurl", help="Base URL")
    update_parser.add_argument("--model", help="模型名称")
    update_parser.add_argument("--apikey", help="API 密钥")
    update_parser.add_argument("--preset-name", help="预设配置名称")

    # ui
    ui_parser = subparsers.add_parser("ui", help="启动 Web UI 界面")
    ui_parser.add_argument("--port", type=int, default=8501, help="端口号（默认 8501）")
    ui_parser.add_argument("--headless", action="store_true", help="不自动打开浏览器")

    args = parser.parse_args()

    if not args.command:
        print_banner()
        parser.print_help()
        return

    dispatch = {
        "test": cmd_test,
        "list": cmd_list,
        "history": cmd_history,
        "delete": cmd_delete,
        "update": cmd_update,
        "run-preset": cmd_run_preset,
        "ui": cmd_ui,
    }

    handler = dispatch.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
