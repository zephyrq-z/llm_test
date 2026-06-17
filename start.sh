#!/bin/bash

# LLM 测试工具启动脚本

cd "$(dirname "$0")"

echo "🧪 LLM 接口测试工具"
echo "==================="
echo ""
echo "选项:"
echo "  1) 启动可视化界面"
echo "  2) CLI 命令行帮助"
echo ""
read -p "请选择 (1-2): " choice

case $choice in
  1)
    echo ""
    echo "启动可视化界面..."
    streamlit run src/llm_test/ui.py
    ;;
  2)
    echo ""
    llm-test --help
    ;;
  *)
    echo "无效选择"
    ;;
esac
