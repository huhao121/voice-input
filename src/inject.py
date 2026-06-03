"""把文字插到当前光标处。

默认（Windows）：用 SendInput 直接逐字输入 Unicode —— 不碰剪贴板、不模拟 Ctrl+V，
从机制上杜绝"粘贴两遍"。
备用：剪贴板 + Ctrl+V（在个别 SendInput 不灵的程序里，可在 config.json 设 "insert":"paste"）。
"""

import os
import sys
import time
import json

from config import CONFIG_PATH


def _insert_method() -> str:
    m = os.getenv("INSERT_METHOD", "").lower()
    if m:
        return m
    try:
        return (json.load(open(CONFIG_PATH, encoding="utf-8")).get("insert") or "paste").lower()
    except Exception:
        return "paste"


# ---- 方法一：SendInput 逐字 Unicode（Windows 默认，无剪贴板）----
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    _ULONG_PTR = ctypes.POINTER(ctypes.c_ulong)

    class _KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                    ("dwExtraInfo", _ULONG_PTR)]

    class _INPUT(ctypes.Structure):
        class _U(ctypes.Union):
            _fields_ = [("ki", _KEYBDINPUT)]
        _anonymous_ = ("u",)
        _fields_ = [("type", wintypes.DWORD), ("u", _U)]

    _KEYEVENTF_KEYUP = 0x0002
    _KEYEVENTF_UNICODE = 0x0004
    _VK_RETURN = 0x0D
    _SendInput = ctypes.windll.user32.SendInput

    def _make(vk, scan, flags):
        e = _INPUT()
        e.type = 1  # INPUT_KEYBOARD
        e.ki.wVk = vk
        e.ki.wScan = scan
        e.ki.dwFlags = flags
        e.ki.time = 0
        e.ki.dwExtraInfo = None
        return e

    def _type_unicode(text: str):
        # 把整段文字的所有按键事件一次性发出去 → "唰"地整句出现，没有逐字打字机效果
        evts = []
        for ch in text:
            if ch == "\r":
                continue
            if ch == "\n":
                evts.append(_make(_VK_RETURN, 0, 0))
                evts.append(_make(_VK_RETURN, 0, _KEYEVENTF_KEYUP))
            else:
                code = ord(ch)
                evts.append(_make(0, code, _KEYEVENTF_UNICODE))
                evts.append(_make(0, code, _KEYEVENTF_UNICODE | _KEYEVENTF_KEYUP))
        if not evts:
            return
        arr = (_INPUT * len(evts))(*evts)
        _SendInput(len(evts), arr, ctypes.sizeof(_INPUT))

    _VK_CONTROL = 0x11
    _VK_V = 0x56

    def _ctrl_v():
        # 用 SendInput 发一次干净的 Ctrl+V（不依赖 pynput，避免之前的"粘两遍"）
        evts = [
            _make(_VK_CONTROL, 0, 0),                   # Ctrl ↓
            _make(_VK_V, 0, 0),                         # V ↓
            _make(_VK_V, 0, _KEYEVENTF_KEYUP),          # V ↑
            _make(_VK_CONTROL, 0, _KEYEVENTF_KEYUP),    # Ctrl ↑
        ]
        arr = (_INPUT * len(evts))(*evts)
        _SendInput(len(evts), arr, ctypes.sizeof(_INPUT))

    def _paste_win(text: str):
        # 整段一次性粘贴：瞬间出现（不像逐字那样慢慢投递）
        import pyperclip
        original = None
        try:
            original = pyperclip.paste()
        except Exception:
            pass
        pyperclip.copy(text)
        time.sleep(0.04)
        _ctrl_v()
        time.sleep(0.12)
        if original is not None:
            try:
                pyperclip.copy(original)
            except Exception:
                pass


# ---- 方法二：剪贴板 + Ctrl+V（备用）----
def _insert_clipboard(text: str):
    import pyperclip
    from pynput.keyboard import Controller, Key
    kb = Controller()
    original = None
    try:
        original = pyperclip.paste()
    except Exception:
        pass
    pyperclip.copy(text)
    time.sleep(0.05)
    with kb.pressed(Key.ctrl):
        kb.press("v")
        kb.release("v")
    time.sleep(0.1)
    if original is not None:
        try:
            pyperclip.copy(original)
        except Exception:
            pass


def insert_text(text: str):
    if not text:
        return
    if sys.platform == "win32":
        if _insert_method() == "type":
            _type_unicode(text)      # 备用：逐字（不依赖剪贴板，但长句投递慢）
        else:
            _paste_win(text)         # 默认：整段一次性粘贴（瞬间出现，且单次不重复）
    else:
        _insert_clipboard(text)


if __name__ == "__main__":
    print("3 秒后把一段文字输入到你光标处，请把光标放到某个输入框…")
    time.sleep(3)
    insert_text("（来自语音输入法的测试文字 test 123）")
