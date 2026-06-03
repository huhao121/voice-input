"""把文字插到当前光标处：剪贴板 + Ctrl+V（对中文/Unicode 最可靠）。

会先存下你原来的剪贴板内容，粘贴完再恢复，尽量不打扰你的剪贴板。
"""

import time
import pyperclip
from pynput.keyboard import Controller, Key

_kb = Controller()


def insert_text(text: str):
    if not text:
        return
    # 1) 备份原剪贴板
    original = None
    try:
        original = pyperclip.paste()
    except Exception:
        pass
    # 2) 放入要插入的文字
    pyperclip.copy(text)
    time.sleep(0.05)  # 给剪贴板一点时间就位
    # 3) 模拟 Ctrl+V
    with _kb.pressed(Key.ctrl):
        _kb.press("v")
        _kb.release("v")
    time.sleep(0.1)  # 等粘贴完成再恢复，避免竞态
    # 4) 恢复原剪贴板
    if original is not None:
        try:
            pyperclip.copy(original)
        except Exception:
            pass


def replace_text(n_chars: int, new_text: str):
    """删掉光标前 n_chars 个字符，再插入 new_text。
    用于"先出原文、整理好再替换"——前提是替换期间你没动光标/没继续打字。
    """
    if n_chars > 0:
        for _ in range(n_chars):
            _kb.press(Key.backspace)
            _kb.release(Key.backspace)
    insert_text(new_text)


if __name__ == "__main__":
    print("3 秒后把一段文字粘到你光标处，请把光标放到某个输入框…")
    time.sleep(3)
    insert_text("（来自语音输入法的测试文字）")
