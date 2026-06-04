"""无需 GUI/麦克风的逻辑测试（任何系统都能跑）。"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

_KEYS = ["LLM_PROVIDER", "CLEANUP_ENABLED", "LLM_API_KEY",
         "ZHIPU_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_API_KEY",
         "CLEANUP_BASE_URL", "CLEANUP_MODEL"]


def _clear_env():
    for k in _KEYS:
        os.environ.pop(k, None)


def test_cleanup_off_by_default():
    _clear_env()
    import importlib, config
    importlib.reload(config)
    assert config.load_llm_config()["enabled"] is False


def test_zhipu_preset_url_and_model():
    _clear_env()
    os.environ["LLM_PROVIDER"] = "zhipu"
    import importlib, config
    importlib.reload(config)
    c = config.load_llm_config()
    assert "bigmodel.cn" in c["base_url"]
    assert c["model"].startswith("glm")
    _clear_env()


def test_non_ascii_key_treated_as_empty():
    # 中文占位符 key 应被视作未配置（否则会塞进 HTTP 头崩溃）
    _clear_env()
    os.environ["ZHIPU_API_KEY"] = "在这里填你的key"
    import importlib, config
    importlib.reload(config)
    assert config.load_llm_config()["api_key"] == ""
    _clear_env()


def test_cleanup_returns_raw_when_disabled():
    _clear_env()
    import importlib, config, cleanup
    importlib.reload(config)
    importlib.reload(cleanup)
    raw = "嗯那个测试一下"
    assert cleanup.cleanup(raw) == raw   # 关闭整理时原样返回，绝不改写
