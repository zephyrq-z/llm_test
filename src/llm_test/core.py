"""
LLM 接口测试核心引擎

提供连通性测试、预设加载、历史记录管理等功能。
数据文件 (config.json / history.json) 固定存放在包所在项目的根目录下。
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

import requests
from openai import OpenAI

# ─── 项目根目录：即 pyproject.toml 所在目录 ───────────────────────
# 包安装后通过 ../../ 回到项目根；开发模式下同样有效。
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE = PROJECT_ROOT / "config.json"
HISTORY_FILE = PROJECT_ROOT / "history.json"


class LLMTester:
    """LLM 接口测试类"""

    def __init__(self, baseurl: str, apikey: str, model: str):
        self.baseurl = baseurl.rstrip("/")
        self.apikey = apikey
        self.model = model
        self.client: Optional[OpenAI] = None

    def connect(self) -> Dict[str, Any]:
        """
        测试 LLM 接口连通性

        Returns:
            Dict: 测试结果，包含 status / latency_ms / error / response_preview / model / baseurl
        """
        result: Dict[str, Any] = {
            "status": "success",
            "latency_ms": 0,
            "error": None,
            "response_preview": None,
            "model": self.model,
            "baseurl": self.baseurl,
        }

        start_time = time.time()

        try:
            self.client = OpenAI(base_url=self.baseurl, api_key=self.apikey)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
                temperature=0,
            )

            latency_ms = (time.time() - start_time) * 1000
            result["latency_ms"] = round(latency_ms, 2)
            result["response_preview"] = response.choices[0].message.content
            return result

        except requests.exceptions.Timeout as e:
            result["status"] = "timeout"
            result["latency_ms"] = round((time.time() - start_time) * 1000, 2)
            result["error"] = f"请求超时: {e}"
            return result

        except requests.exceptions.ConnectionError as e:
            result["status"] = "connection_error"
            result["latency_ms"] = round((time.time() - start_time) * 1000, 2)
            result["error"] = f"连接失败: {e}"
            return result

        except requests.exceptions.HTTPError as e:
            result["status"] = "http_error"
            result["latency_ms"] = round((time.time() - start_time) * 1000, 2)
            result["error"] = f"HTTP 错误 {e.response.status_code}: {e}"
            return result

        except Exception as e:
            result["status"] = "error"
            result["latency_ms"] = round((time.time() - start_time) * 1000, 2)
            result["error"] = f"未知错误: {e}"
            return result

    def get_info(self) -> Dict[str, Any]:
        """获取可用模型列表（需先调用 connect 初始化客户端）"""
        if not self.client:
            return {"status": "error", "error": "未连接"}

        try:
            models = self.client.models.list()
            model_list = [m.id for m in models.data if self.model in m.id]
            return {"status": "success", "available_models": model_list, "model": self.model}
        except Exception as e:
            return {"status": "error", "error": f"获取模型信息失败: {e}"}


# ─── 便捷函数 ─────────────────────────────────────────────────────

def test_llm(baseurl: str, apikey: str, model: str) -> Dict[str, Any]:
    """测试 LLM 接口连通性（一行调用）"""
    return LLMTester(baseurl, apikey, model).connect()


# ─── 持久化函数 ───────────────────────────────────────────────────

def load_history() -> list:
    """加载历史测试记录"""
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def load_presets() -> list:
    """加载预设配置"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("presets", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_test_result(config: Dict[str, str], result: Dict[str, Any]) -> str:
    """保存测试结果到历史记录，返回生成的配置 ID"""
    history = load_history()
    config_id = f"test_{int(time.time() * 1000)}"

    history_item = {
        "id": config_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "baseurl": config.get("baseurl", ""),
        "apikey": "***" if config.get("apikey") else "",
        "model": config.get("model", ""),
        "preset_name": config.get("preset_name", ""),
        **result,
    }

    history.append(history_item)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return config_id


def delete_history_item(config_id: str) -> bool:
    """按 ID 删除历史记录"""
    history = load_history()
    original_count = len(history)
    history = [item for item in history if item["id"] != config_id]

    if len(history) < original_count:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True

    return False


def update_history_item(config_id: str, updates: Dict[str, Any]) -> bool:
    """按 ID 更新历史记录字段"""
    history = load_history()

    for item in history:
        if item["id"] == config_id:
            item.update(updates)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            return True

    return False
