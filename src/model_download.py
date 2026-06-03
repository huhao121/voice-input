"""首次运行自动下载 SenseVoice 语音模型（~250MB）到 config.MODEL_DIR。

下载失败时给出手动下载指引，不让程序崩在这里。
可用环境变量 MODEL_URL 换镜像源。
"""

import os
import sys
import tarfile

import requests

from config import MODEL_DIR

MODEL_URL = os.getenv(
    "MODEL_URL",
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/"
    "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2",
)
WANTED = ("model.int8.onnx", "tokens.txt")


def model_present() -> bool:
    return all(os.path.exists(os.path.join(MODEL_DIR, f)) for f in WANTED)


def ensure_model():
    """模型缺失则下载并解压。已存在则直接返回。"""
    if model_present():
        return
    os.makedirs(MODEL_DIR, exist_ok=True)
    archive = os.path.join(MODEL_DIR, "_model.tar.bz2")
    print(f"首次运行：下载语音模型(~250MB) → {MODEL_DIR}")
    print(f"  源：{MODEL_URL}")
    try:
        _download(MODEL_URL, archive)
        print("解压中…")
        with tarfile.open(archive, "r:bz2") as tf:
            for m in tf.getmembers():
                base = os.path.basename(m.name)
                if base in WANTED:
                    m.name = base                 # 只取文件名，防止路径穿越
                    tf.extract(m, MODEL_DIR)
        if os.path.exists(archive):
            os.remove(archive)
    except Exception as e:
        raise RuntimeError(
            f"模型自动下载失败：{e}\n"
            f"请手动下载 {MODEL_URL}\n"
            f"解压后把 model.int8.onnx 和 tokens.txt 放到：{MODEL_DIR}"
        )
    if not model_present():
        raise RuntimeError(f"解压后仍缺模型文件，请手动放到：{MODEL_DIR}")
    print("✅ 语音模型就绪")


def _download(url: str, dest: str):
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        done = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):  # 1MB
                f.write(chunk)
                done += len(chunk)
                if total:
                    pct = min(100, done * 100 // total)
                    print(f"\r  下载 {pct}%  ({done >> 20}/{total >> 20} MB)", end="", flush=True)
        print()


if __name__ == "__main__":
    ensure_model()
