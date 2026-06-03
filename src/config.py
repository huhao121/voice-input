"""路径 + LLM 配置。让打包成 exe 后也能找对模型/配置位置，并支持多家 LLM。"""

import os
import sys
import json


def app_dir() -> str:
    """程序的"家目录"：模型、配置都放这里。
    - 打包成 exe（PyInstaller）时：exe 所在文件夹（持久、可写）。
    - 源码运行时：项目根目录（src 的上一级）。
    """
    if getattr(sys, "frozen", False):          # PyInstaller 打包后
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


APP_DIR = app_dir()
MODEL_DIR = os.getenv("STT_MODEL_DIR") or os.path.join(APP_DIR, "models", "sense-voice")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

# LLM 服务商预设（整理文字用）。base_url 不带 /v1，避免某些服务 404。
PROVIDERS = {
    "deepseek": {"base_url": "https://api.deepseek.com", "model": "deepseek-chat"},
    "zhipu":    {"base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4-flash"},
    "openai":   {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
}


def load_llm_config() -> dict:
    """解析整理用的 LLM 配置。优先级：环境变量 > config.json > 服务商预设。"""
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            cfg = json.load(open(CONFIG_PATH, encoding="utf-8"))
        except Exception:
            cfg = {}
    provider = (os.getenv("LLM_PROVIDER") or cfg.get("provider") or "deepseek").lower()
    preset = PROVIDERS.get(provider, PROVIDERS["deepseek"])
    api_key = (os.getenv("LLM_API_KEY") or os.getenv("ZHIPU_API_KEY")
               or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
               or cfg.get("api_key", ""))
    # API key 必是 ASCII；含中文（=没填的占位符）一律视为"未配置"，
    # 否则会塞进 HTTP 头导致 latin-1 编码崩溃。
    api_key = api_key.strip()
    try:
        api_key.encode("ascii")
    except UnicodeEncodeError:
        api_key = ""
    # 默认关闭 LLM 整理：纯本地 STT 又快又准；想要润色可在 config.json 设 cleanup=true
    enabled = cfg.get("cleanup", False)
    env = os.getenv("CLEANUP_ENABLED", "").lower()
    if env in ("0", "false", "off"):
        enabled = False
    elif env in ("1", "true", "on"):
        enabled = True
    return {
        "provider": provider,
        "api_key": api_key,
        "base_url": os.getenv("CLEANUP_BASE_URL") or cfg.get("base_url") or preset["base_url"],
        "model": os.getenv("CLEANUP_MODEL") or cfg.get("model") or preset["model"],
        "enabled": enabled,   # False = 跳过 LLM 整理，纯本地 STT（保证 <1s）
    }


def ensure_config_template() -> bool:
    """若既无配置文件、又无环境变量 key，则写一个模板供用户填。返回是否新建了模板。"""
    has_env_key = any(os.getenv(k) for k in ("LLM_API_KEY", "ZHIPU_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_API_KEY"))
    if os.path.exists(CONFIG_PATH) or has_env_key:
        return False
    template = {
        "_说明": "默认 cleanup=false：纯本地语音转文字，又快又准。想要 LLM 润色去口癖再设 true 并填 api_key。",
        "cleanup": False,
        "provider": "zhipu",
        "api_key": "（仅 cleanup=true 时需要）智谱在 open.bigmodel.cn 申请",
        "model": "glm-4-flash",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
    }
    json.dump(template, open(CONFIG_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return True
