"""主循环：热键 → 录音 → 转写 → 键入。常驻进程。

运行：
    source .venv/bin/activate
    python -m whisper_dictation.app
需先授予麦克风 + 辅助功能 + 输入监听权限（见 docs/PERMISSIONS.md）。
"""
import sys
import threading
import time

from .audio import flatten, record_into, should_transcribe
from .config import load_config, parse_hotkey
from .hotkey import Mode, ModeMachine, register_hotkey
from .transcribe import transcribe
from .typer import type_text


class DictationApp:
    def __init__(self, config_path="config.yaml"):
        self.cfg = load_config(config_path)
        self.machine = ModeMachine(Mode(self.cfg.mode))
        self._stream = None
        self._frames = None
        self._lock = threading.Lock()
        self._listener = None

    def _start(self):
        with self._lock:
            if self._stream is not None:  # 已在录音，防重入
                return
            self._frames = []
            self._stream = record_into(self._frames, self.cfg.sample_rate)
            print("● 录音中…（说完松开/再按一次结束）", flush=True)

    def _stop(self):
        with self._lock:
            if self._stream is None:
                return
            self._stream.stop()
            self._stream.close()
            self._stream = None
            frames = self._frames or []
            self._frames = None
        audio = flatten(frames)
        if not should_transcribe(audio, self.cfg.sample_rate):
            print("（静音或太短，忽略）", flush=True)
            return
        print("转写中…", flush=True)
        text = transcribe(audio, self.cfg.model, self.cfg.language)
        if text:
            type_text(text)
            print(f"✓ {text}", flush=True)

    def _on_press(self):
        action = self.machine.on_press()
        if action == "start":
            self._start()
        elif action == "stop":
            self._stop()

    def _on_release(self):
        if self.machine.on_release() == "stop":
            self._stop()

    def run(self):
        mods, key = parse_hotkey(self.cfg.hotkey)
        print(f"听写就绪：mode={self.cfg.mode} hotkey={self.cfg.hotkey} "
              f"model={self.cfg.model}（Ctrl-C 退出）", flush=True)
        self._listener = register_hotkey(mods, key, self._on_press, self._on_release)
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("退出…", flush=True)
        finally:
            if self._listener:
                self._listener.stop()


def main():
    cfg = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    DictationApp(cfg).run()


if __name__ == "__main__":
    main()
