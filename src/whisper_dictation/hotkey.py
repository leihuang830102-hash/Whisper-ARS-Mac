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
