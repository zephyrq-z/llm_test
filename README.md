# LLM 接口测试工具

一套用于测试大模型接口连通性的命令行工具与可视化 UI。

## 功能特性

- ✅ **接口连通测试** — 输入 baseurl / API Key / 模型名，一键验证接口可用性
- ✅ **厂商 & 模型预设库** — 内置 7 家主流厂商、12 个常用模型配置模板，一键选用
- ✅ **配置持久化** — 每次测试自动保存完整配置为独立项目，支持查看 / 编辑 / 删除
- ✅ **CLI 命令行** — `llm-test` 全局命令，适合脚本集成与批量测试
- ✅ **Web 可视化** — `llm-test ui` 启动 Streamlit 界面，表单操作更直观

## 支持的厂商 & 模型

| 厂商 | Base URL | 模型 |
|------|----------|------|
| OpenAI | `https://api.openai.com/v1` | gpt-4, gpt-3.5-turbo |
| 阿里云通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | qwen-max, qwen-turbo, qwen-light |
| 智谱 AI | `https://open.bigmodel.cn/api/paas/v4` | glm-4, glm-3-turbo |
| DeepSeek | `https://api.deepseek.com` | deepseek-chat |
| Moonshot AI (Kimi) | `https://api.moonshot.cn/v1` | moonshot-v1-8k, moonshot-v1-32k |
| 01.AI Yi | `https://api01.01.ai/v1` | yi-34b-chat |
| Groq | `https://api.groq.com/openai/v1` | llama3-8b-8192 |

> 所有兼容 OpenAI Chat Completions 协议的接口均可通过 `llm-test test` 直接测试，不限于上述厂商。

## 安装

```bash
cd llm_test
pip install -e .
```

安装后即可在任意目录使用 `llm-test` 命令。

## 快速开始

```bash
# 1. 查看内置预设
llm-test list

# 2. 用预设测试（会交互式提示输入 API Key）
llm-test run-preset --name "DeepSeek"

# 3. 手动指定参数测试
llm-test test \
  --baseurl https://api.deepseek.com \
  --apikey sk-xxx \
  --model deepseek-chat

# 4. 启动 Web UI
llm-test ui
```

## CLI 命令参考

### `llm-test test` — 手动测试接口

```bash
llm-test test --baseurl <URL> --apikey <KEY> --model <MODEL> [--preset-name <NAME>]
```

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--baseurl` | ✅ | LLM 接口基础地址 |
| `--apikey` | ✅ | API 密钥 |
| `--model` | ✅ | 模型名称 |
| `--preset-name` | ❌ | 标记来源预设名（仅用于记录） |

### `llm-test run-preset` — 使用预设测试

```bash
llm-test run-preset --name <预设名> [--apikey <KEY>]
```

按预设名精确匹配，自动填充 baseurl 和 model。API Key 取值优先级：`--apikey` 参数 > 预设中的值 > 交互式输入。

### `llm-test list` — 列出所有预设

```bash
llm-test list
```

### `llm-test history` — 查看历史记录

```bash
llm-test history
```

### `llm-test delete` — 删除历史记录

```bash
llm-test delete --id <记录ID>
```

### `llm-test update` — 更新历史记录

```bash
llm-test update --id <记录ID> [--baseurl <URL>] [--model <MODEL>] [--apikey <KEY>] [--preset-name <NAME>]
```

仅更新传入的字段，未传入的字段保持不变。

### `llm-test ui` — 启动 Web UI

```bash
llm-test ui [--port PORT] [--headless]
```

| 参数 | 默认值 | 说明 |
|------|:------:|------|
| `--port` | 8501 | Streamlit 服务端口 |
| `--headless` | 关 | 不自动打开浏览器 |

启动后访问 `http://localhost:8501`（或自定义端口）。

## 测试结果状态码

| 状态 | 说明 |
|------|------|
| `success` | 测试成功，接口连通且返回有效响应 |
| `timeout` | 请求超时 |
| `connection_error` | 连接失败（DNS / 网络不可达） |
| `http_error` | HTTP 错误（401 / 403 / 429 / 5xx 等） |
| `error` | 其他未知错误 |

## 项目结构

```
llm_test/
├── pyproject.toml               # 包配置 + CLI 入口注册
├── config.json                  # 预设配置库（厂商 & 模型模板）
├── history.json                 # 历史记录（运行时自动生成）
├── start.sh                     # 交互式启动脚本
├── README.md                    # 本文件
├── DEVELOPMENT.md               # 开发设计文档
└── src/
    └── llm_test/
        ├── __init__.py           # 包初始化（版本号）
        ├── cli.py                # CLI 入口（llm-test 命令）
        ├── core.py               # 核心引擎（LLMTester + 持久化）
        └── ui.py                 # Streamlit Web UI
```

## 开发

```bash
# 开发模式安装
pip install -e .

# 代码修改后无需重新安装，CLI 自动生效

# 本地启动 UI（开发调试）
llm-test ui --port 8501

# 构建分发包
pip install build
python -m build
```

## 许可证

MIT License
