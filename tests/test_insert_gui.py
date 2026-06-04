"""真实 GUI 插入测试：自建一个 Tkinter 文本框作靶子（避开 Win11 记事本控件坑）。

开一个置顶文本框 → 抢前台 → insert_text → 读回断言。
能自动抓"粘两遍 / 内容不符"。仅 Windows（需真桌面会话，自托管 runner 上跑）。
"""

import os
import sys
import time
import importlib

import pytest

if sys.platform != "win32":
    pytest.skip("仅 Windows 可跑 GUI 插入测试", allow_module_level=True)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

SAMPLE = "零一二三testABC123"
_TITLE = "vi_test_target"


def _insert_and_read(method: str) -> str:
    import tkinter as tk
    import ctypes

    os.environ["INSERT_METHOD"] = method
    import inject
    importlib.reload(inject)

    root = tk.Tk()
    root.title(_TITLE)
    root.geometry("520x220+200+200")
    txt = tk.Text(root)
    txt.pack(fill="both", expand=True)
    root.attributes("-topmost", True)
    root.update()
    root.deiconify()
    root.lift()
    txt.focus_set()
    root.update()
    time.sleep(0.5)

    # 抢到前台（SendInput 只送前台窗口）
    hwnd = ctypes.windll.user32.FindWindowW(None, _TITLE)
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    root.update()
    time.sleep(0.3)

    try:
        inject.insert_text(SAMPLE)
        got = ""
        deadline = time.time() + 5
        while time.time() < deadline:
            root.update()                       # 抽 Tk 事件，接收注入的按键
            got = txt.get("1.0", "end-1c")
            if got.strip():
                break
            time.sleep(0.05)
        return got
    finally:
        root.destroy()


def test_paste_single():
    """整段粘贴：内容正确且不重复。"""
    got = _insert_and_read("paste")
    assert got == SAMPLE, f"paste got={got!r}"


def test_type_single():
    """逐字输入：内容正确且不重复。"""
    got = _insert_and_read("type")
    assert got == SAMPLE, f"type got={got!r}"
