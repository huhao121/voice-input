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
from config import load_llm_config, ensure_config_template, CONFIG_PATH, APP_DIR   # noqa: E402
from model_download import ensure_model, model_present                    # noqa: E402

import time  # noqa: E402

LOG_PATH = os.path.join(APP_DIR, "voice-input.log")


def _log(line: str):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(time.strftime("%H:%M:%S ") + line + "\n")
    except Exception:
        pass

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
        from inject import insert_text, replace_text
        ms = lambda dt: int(dt * 1000)
        t0 = time.time()
        raw = _transcribe(audio)
        print(f"[STT] {raw}")
        insert_text(raw)                      # ① 先把原文秒出到输入框（实时感）
        t_raw = time.time()
        print(f"[出原文] {ms(t_raw - t0)}ms")

        cleaned = cleanup(raw)                # ② 后台整理（cleanup 内部：关了/没key/失败都会原样返回 raw）
        t_clean = time.time()
        if cleaned and cleaned != raw:
            replace_text(len(raw), cleaned)   # ③ 整理好了，把原文替换成干净版
            print(f"[整理] {cleaned}")
        t_end = time.time()

        timing = (f"出原文={ms(t_raw - t0)}ms 整理={ms(t_clean - t_raw)}ms "
                  f"替换={ms(t_end - t_clean)}ms 总计={ms(t_end - t0)}ms")
        print(f"[耗时] {timing}")
        _log(f"{timing} | 原文: {raw} | 整理: {cleaned}")
    except Exception as e:
        print(f"[错误] 处理失败：{e}")
        _log(f"错误: {e}")


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


def _disable_quick_edit():
    """关掉 Windows 控制台的"快速编辑模式"：否则点一下窗口会冻住程序，要按回车才继续。"""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-10)  # STD_INPUT_HANDLE
        mode = ctypes.c_uint()
        if k.GetConsoleMode(h, ctypes.byref(mode)):
            ENABLE_QUICK_EDIT, ENABLE_EXTENDED_FLAGS = 0x40, 0x80
            k.SetConsoleMode(h, (mode.value & ~ENABLE_QUICK_EDIT) | ENABLE_EXTENDED_FLAGS)
    except Exception:
        pass


def main():
    _disable_quick_edit()
    # 1) 配置：没 key 就生成模板，提示用户填好再来
    if ensure_config_template():
        print(f"⚙️  已生成配置模板：{CONFIG_PATH}")
    conf = load_llm_config()
    if conf["api_key"]:
        print(f"整理用模型：{conf['provider']} / {conf['model']}")
    else:
        print(f"⚠️  还没填有效 API key（{CONFIG_PATH} 里 api_key 仍是占位符）。")
        print("   现在能用语音转文字，但不会做去口癖整理。填好 key 重启即可。")
    # 2) 模型：缺失就现在下载，避免第一次按 F9 时卡 250MB
    try:
        if not model_present():
            ensure_model()
        print("预热语音模型…（消除首次识别的冷启动延迟）")
        from stt import warmup
        warmup()
    except Exception as e:
        print(f"⚠️  {e}")
    print(f"语音输入法已启动。按住 [{_HOTKEY_NAME.upper()}] 说话，松开出字。Ctrl+C 退出。")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n再见。")
