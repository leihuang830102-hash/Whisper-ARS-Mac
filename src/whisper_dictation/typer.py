"""把文本键入到当前光标处：写剪贴板 → 模拟 Cmd+V。

CJK 字符无法用单键事件可靠输入，故走粘贴路径。
"""
import time

import AppKit
import Quartz

# macOS 虚拟键码
_KEY_V = 9
_FLAG_MASK_CMD = Quartz.kCGEventFlagMaskCommand
_DOWN = Quartz.kCGEventKeyDown
_UP = Quartz.kCGEventKeyUp


def _new_pasteboard():
    return AppKit.NSPasteboard.generalPasteboard()


def _post_key(mods_flags: int, key_code: int, down: bool) -> None:
    """构造并发送一个键盘事件。"""
    event = Quartz.CGEventCreateKeyboardEvent(None, key_code, down)
    event.setFlags(mods_flags)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def type_text(text: str) -> None:
    """把 text 写入剪贴板并在当前光标处 Cmd+V 粘贴。空串直接返回。"""
    if not text:
        return
    pb = _new_pasteboard()
    pb.clearContents()
    pb.setString_forType_(text, "public.utf8-plain-text")
    # Cmd+V: 按下时带 cmd flag，松开时不带
    _post_key(_FLAG_MASK_CMD, _KEY_V, True)
    time.sleep(0.01)
    _post_key(0, _KEY_V, False)
