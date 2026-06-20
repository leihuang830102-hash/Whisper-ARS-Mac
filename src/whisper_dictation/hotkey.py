"""热键模式状态机（纯逻辑）。

状态机与系统事件解耦：状态机可单测，系统事件回调由后续任务接入。
"""
from enum import Enum


class Mode(str, Enum):
    PTT = "ptt"
    TOGGLE = "toggle"


class ModeMachine:
    """根据模式把按键事件翻译成 'start'/'stop'/'noop' 动作。"""

    def __init__(self, mode: Mode):
        self.mode = mode
        self.is_recording = False

    def on_press(self) -> str:
        if self.mode == Mode.PTT:
            self.is_recording = True
            return "start"
        # toggle
        if self.is_recording:
            self.is_recording = False
            return "stop"
        self.is_recording = True
        return "start"

    def on_release(self) -> str:
        if self.mode == Mode.PTT:
            self.is_recording = False
            return "stop"
        return "noop"  # toggle 不在松开时动作


# --- 全局热键监听（pynput） ---
# 用 keyboard.Listener：target key 按下（且所需修饰键在按）→ on_press；
# target key 松开 → on_release。PTT 与 toggle 都靠它驱动，由 ModeMachine 决定动作。
from pynput import keyboard  # noqa: E402

# config 修饰键名 → pynput 修饰键集合（含左右两侧变体）
_MOD_SETS = {
    "cmd": {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r},
    "ctrl": {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r},
    "option": {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r},
    "shift": {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r},
}
# config 按键名 → pynput 键
_SPECIAL_KEYS = {
    "space": keyboard.Key.space, "enter": keyboard.Key.enter,
    "tab": keyboard.Key.tab, "esc": keyboard.Key.esc,
    "up": keyboard.Key.up, "down": keyboard.Key.down,
    "left": keyboard.Key.left, "right": keyboard.Key.right,
}


def _target_key_for(name: str):
    n = name.lower()
    if n in _SPECIAL_KEYS:
        return _SPECIAL_KEYS[n]
    # 单个字母/数字键 → KeyCode
    if len(n) == 1 and n.isalnum():
        return keyboard.KeyCode.from_char(n)
    raise ValueError(f"unsupported key: {name!r}")


def register_hotkey(mods, key, on_press, on_release):
    """注册全局热键。返回已启动的 pynput Listener（调用方 .stop() 停止）。

    需要 macOS 辅助功能 + 输入监听权限。
    """
    target = _target_key_for(key)
    required = [_MOD_SETS[m] for m in mods]
    held_mods = set()

    def _is_modifier(k):
        return any(k in s for s in _MOD_SETS.values())

    def _mods_satisfied():
        return all((held_mods & s) for s in required)

    def _on_press(k):
        if _is_modifier(k):
            held_mods.add(k)
        elif k == target and _mods_satisfied():
            try:
                on_press()
            except Exception as e:  # 回调异常不能挂掉监听线程
                print(f"[hotkey on_press error] {e}", flush=True)

    def _on_release(k):
        if _is_modifier(k):
            held_mods.discard(k)
        elif k == target:
            try:
                on_release()
            except Exception as e:
                print(f"[hotkey on_release error] {e}", flush=True)

    listener = keyboard.Listener(on_press=_on_press, on_release=_on_release)
    listener.start()
    return listener
