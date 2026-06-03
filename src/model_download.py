"""首次运行自动下载 SenseVoice 语音模型到 config.MODEL_DIR。

只下需要的两个文件（int8 模型 ~228MB + tokens），默认走国内快的 hf-mirror。
换源：设环境变量 MODEL_BASE_URL（如 https://huggingface.co/<repo>/resolve/main）。
"""

import os
import requests

from config import MODEL_DIR

# 默认 hf-mirror（国内快）。仅下 int8 模型 + tokens，不下 1GB 的 fp32 整包。
BASE_URL = os.getenv(
    "MODEL_BASE_URL",
    "https://hf-mirror.com/csukuangfj/"
    "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/resolve/main",
)
FILES = ("model.int8.onnx", "tokens.txt")


def model_present() -> bool:
    return all(os.path.exists(os.path.join(MODEL_DIR, f)) for f in FILES)


def ensure_model():
    """模型缺失则逐个文件下载。已存在则直接返回。"""
    if model_present():
        return
    os.makedirs(MODEL_DIR, exist_ok=True)
    print(f"首次运行：下载语音模型(~230MB) → {MODEL_DIR}")
    for fname in FILES:
        dest = os.path.join(MODEL_DIR, fname)
        if os.path.exists(dest):
            continue
        url = f"{BASE_URL}/{fname}"
        print(f"  {fname} …")
        try:
            _download(url, dest)
        except Exception as e:
            part = dest + ".part"
            for p in (part, dest):
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
            raise RuntimeError(
                f"下载 {fname} 失败：{e}\n"
                f"请手动下载 {url}\n放到 {MODEL_DIR}"
            )
    if not model_present():
        raise RuntimeError(f"模型文件不全，请手动放到 {MODEL_DIR}")
    print("✅ 语音模型就绪")


def _download(url: str, dest: str):
    """下载到 .part 再改名，避免半截文件被误当成"已下载"。"""
    tmp = dest + ".part"
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        done = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):  # 1MB
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\r    {min(100, done * 100 // total)}%  "
                          f"({done >> 20}/{total >> 20} MB)", end="", flush=True)
        if total:
            print()
    os.replace(tmp, dest)


if __name__ == "__main__":
    ensure_model()
