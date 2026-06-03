"""语音输入法 MVP · 串联：按住热键 → 录音 → 转写 → LLM 整理 → 粘到光标处。

用法：运行后，**按住 F9 说话，松开**即出字。Esc 连按两下退出（或关窗口）。
热键可用环境变量 VOICE_HOTKEY 改（如 f9 / f8 / ctrl_r）。
"""

import os
import sys
import threading

from pynput import keyboard

sys.path.insert(0, os.path.dirname(__file__))
from recorder import Recorder          # noqa: E402
from cleanup import cleanup            # noqa: E402

# STT 延迟导入：没装 sherpa-onnx 时仍能启动（会在第一次录音时报错提示）
def _transcribe(audio):
    from stt import transcribe
    return transcribe(audio)


# 触发键（按住录音）。默认 F9。
_HOTKEY_NAME = os.getenv("VOICE_HOTKEY", "f9")
TRIGGER = getattr(keyboard.Key, _HOTKEY_NAME, keyboard.Key.f9)

recorder = Recorder()
_recording = False
_lock = threading.Lock()


def _process(audio):
    """后台线程：转写 → 整理 → 插入。不阻塞热键监听。"""
    if len(audio) < 1600:   # < 0.1 秒，当作误触，忽略
        return
    try:
        raw = _transcribe(audio)
        print(f"[STT] {raw}")
        text = cleanup(raw)
        print(f"[整理] {text}")
        from inject import insert_text
        insert_text(text)
    except Exception as e:
        print(f"[错误] 处理失败：{e}")


def on_press(key):
    global _recording
    if key == TRIGGER:
        with _lock:
            if not _recording:
                _recording = True
                print("● 录音中…（松开 F9 结束）")
                recorder.start()


def on_release(key):
    global _recording
    if key == TRIGGER:
        with _lock:
            if _recording:
                _recording = False
                audio = recorder.stop()
                print("■ 处理中…")
                threading.Thread(target=_process, args=(audio,), daemon=True).start()


def main():
    if not os.getenv("DEEPSEEK_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("⚠️  未设置 DEEPSEEK_API_KEY，整理步骤会回退为原文。")
    print(f"语音输入法已启动。按住 [{_HOTKEY_NAME.upper()}] 说话，松开出字。Ctrl+C 退出。")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n再见。")
