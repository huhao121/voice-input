"""真实 Windows GUI 插入测试：开记事本 → insert_text → 读回断言。

这正是能自动抓到"粘两遍 / 插入慢"的测试。仅在 Windows 上跑（CI 的 windows-latest 即可）。
"""

import os
import sys
import time

import pytest

if sys.platform != "win32":
    pytest.skip("仅 Windows 可跑 GUI 插入测试", allow_module_level=True)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

SAMPLE = "零一二三testABC123"


def _open_notepad():
    import ctypes
    from pywinauto.application import Application
    app = Application(backend="win32").start("notepad.exe")
    dlg = app.window(class_name="Notepad")
    dlg.wait("visible ready", timeout=15)
    edit = dlg.child_window(class_name="Edit")
    edit.wait("visible ready", timeout=10)
    hwnd = dlg.handle
    # 无头 CI 上抢前台焦点很难，多试几次
    for _ in range(5):
        try:
            ctypes.windll.user32.ShowWindow(hwnd, 9)        # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass
        try:
            edit.set_focus()
        except Exception:
            pass
        time.sleep(0.5)
    return app, edit


def _insert_and_read(method):
    os.environ["INSERT_METHOD"] = method
    import importlib
    import inject
    importlib.reload(inject)
    app, edit = _open_notepad()
    try:
        t0 = time.time()
        inject.insert_text(SAMPLE)
        got = ""
        deadline = time.time() + 5
        while time.time() < deadline:
            got = edit.window_text()
            if got.strip():
                break
            time.sleep(0.05)
        latency = time.time() - t0
        return got, latency
    finally:
        try:
            app.kill()
        except Exception:
            pass


def test_paste_single_and_fast():
    """整段粘贴：内容正确（不重复）且 <1.5s 出现。"""
    got, latency = _insert_and_read("paste")
    assert got == SAMPLE, f"粘贴内容不符（重复/缺失？）got={got!r}"
    assert latency < 1.5, f"粘贴太慢: {latency:.2f}s"


def test_type_single():
    """逐字输入：至少内容正确不重复（速度可能略慢，这里只验正确性）。"""
    got, _ = _insert_and_read("type")
    assert got == SAMPLE, f"逐字输入内容不符（重复/缺失？）got={got!r}"
