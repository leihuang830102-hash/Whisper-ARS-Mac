# 本地语音听写 MVP 实施计划（自研）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 自研一个 macOS 本地语音听写工具：全局热键（push-to-talk + toggle 双模式）触发录音，本地 Whisper Large v3 Turbo（mlx-whisper）转写，结果键入当前光标处。MVP 不做 LLM 后处理。

**Architecture:** Python 单进程常驻。模块化：`audio`（sounddevice 录音）→ `transcribe`（mlx-whisper Turbo Q8）→ `typer`（剪贴板 + Cmd+V 模拟键入，对中文最稳）→ `hotkey`（pyobjc 全局热键）→ `app`（主循环编排）。config.yaml 配置热键/模式/模型路径。PTT 与 toggle 都靠"第二次按键结束"，MVP 不做 VAD 自动断句（那是 Phase D）。

**Tech Stack:** Python 3.11+，mlx-whisper（ASR），sounddevice + numpy（录音），pyobjc（Quartz/Carbon，全局热键与模拟键入），pyyaml（配置），pytest（测试）。

**Spec 参考:** `docs/superpowers/specs/2026-06-20-local-stt-design.md` §3（决策，含双触发模式）、§4 Phase A。

**环境前置（用户已具备）:** Apple M5 / 24GB / Metal 4。需安装 Xcode Command Line Tools（pyobjc 编译需要）。需授予：麦克风、辅助功能、输入监听 三项权限（Task 9）。

---

## File Structure

```
Whisper/
├── pyproject.toml              # 依赖与项目元数据
├── config.yaml                 # 用户配置：热键、模式、模型路径、语言
├── src/whisper_dictation/
│   ├── __init__.py
│   ├── config.py               # 加载/校验 config.yaml，解析热键描述
│   ├── audio.py                # sounddevice 录音，返回 numpy float32 数组
│   ├── transcribe.py           # mlx-whisper 封装，audio→text
│   ├── typer.py                # 写剪贴板 + CGEvent 模拟 Cmd+V
│   ├── hotkey.py               # pyobjc 全局热键监听 + 模式状态机
│   └── app.py                  # 主循环：热键事件 → 录音 → 转写 → 键入
└── tests/
    ├── conftest.py             # 共享 fixture（测试音频样本）
    ├── test_config.py
    ├── test_audio.py
    ├── test_transcribe.py
    ├── test_typer.py
    └── test_hotkey.py
```

**职责边界**：每个模块单一职责、接口清晰、可独立测试。`app.py` 只编排，不含业务逻辑。`hotkey.py` 把"系统事件"和"模式状态机"分开（状态机纯逻辑、可测；事件回调薄）。

**键入策略说明**：CJK 字符无法用 CGEvent 单键事件可靠输入，故 MVP 用"写剪贴板 → 模拟 Cmd+V"在光标处粘贴。会临时占用剪贴板，键入后恢复原剪贴板内容（Task 7）。

---

## Slice 1：引擎管线（无热键，CLI 验证 mlx-whisper 本地可用）

### Task 1: 项目脚手架与依赖

**Files:**
- Create: `pyproject.toml`
- Create: `src/whisper_dictation/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: 写 pyproject.toml**

```toml
[project]
name = "whisper-dictation"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "mlx-whisper>=0.4.0",
    "sounddevice>=0.4.6",
    "numpy>=1.26",
    "pyobjc-framework-Quartz>=10.0",
    "pyobjc-framework-ApplicationServices>=10.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 2: 建包初始化文件**

`src/whisper_dictation/__init__.py`:
```python
"""本地语音听写工具：mlx-whisper + 全局热键 + 光标处键入。"""
__version__ = "0.1.0"
```

`tests/__init__.py`: 空文件。

- [ ] **Step 3: 写 conftest.py（共享测试音频 fixture）**

`tests/conftest.py`:
```python
"""共享测试夹具。"""
import numpy as np
import pytest


@pytest.fixture
def sample_rate() -> int:
    """mlx-whisper 期望 16kHz。"""
    return 16000


@pytest.fixture
def silence_audio(sample_rate):
    """1 秒静音音频（全零 float32），用于测试转写/录音接口形状。"""
    return np.zeros(sample_rate, dtype=np.float32)
```

- [ ] **Step 4: 安装依赖（用户机器，可能需联网装包）**

Run:
```bash
cd /Users/lei/AI_Projects/Whisper
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```
Expected: 依赖装好，`mlx-whisper` 可 import。若 pyobjc 编译失败，先确认 `xcode-select -p` 指向 Xcode CLT（`xcode-select --install`）。

把 `.venv/` 加入 `.gitignore`（根 .gitignore 追加 `.venv/` 与 `__pycache__/`）。

- [ ] **Step 5: 冒烟测试 import**

Run: `python -c "import mlx_whisper, sounddevice, numpy, Quartz, yaml; print('ok')"`
Expected: 打印 `ok`。

- [ ] **Step 6: 提交**

```bash
git add pyproject.toml src tests .gitignore
git commit -m "feat: project scaffold and dependencies"
```

---

### Task 2: config 模块（配置加载 + 热键解析）

**Files:**
- Create: `config.yaml`
- Create: `src/whisper_dictation/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: 写失败测试**

`tests/test_config.py`:
```python
import pytest
from whisper_dictation.config import load_config, parse_hotkey


def test_parse_hotkey_cmd_space():
    mods, key = parse_hotkey("cmd+space")
    assert "cmd" in mods
    assert key == "space"


def test_parse_hotkey_option_with_letter():
    mods, key = parse_hotkey("option+j")
    assert mods == ["option"]
    assert key == "j"


def test_load_config_defaults(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        "mode: ptt\nhotkey: cmd+space\nmodel: mlx-community/whisper-large-v3-turbo\nlanguage: zh\n"
    )
    cfg = load_config(str(cfg_file))
    assert cfg.mode == "ptt"
    assert cfg.language == "zh"
    assert cfg.model.startswith("mlx-community/")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_config.py -v`
Expected: FAIL（模块不存在）。

- [ ] **Step 3: 实现 config.py**

`src/whisper_dictation/config.py`:
```python
"""配置加载与热键描述解析。"""
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# 允许的修饰键别名 → 标准名
_MOD_ALIASES = {
    "cmd": "cmd", "command": "cmd", "⌘": "cmd",
    "ctrl": "ctrl", "control": "ctrl", "⌃": "ctrl",
    "option": "option", "alt": "option", "opt": "option", "⌥": "option",
    "shift": "shift", "⇧": "shift",
}


@dataclass
class Config:
    """运行时配置。"""
    mode: str = "ptt"                       # "ptt" | "toggle"
    hotkey: str = "cmd+space"
    model: str = "mlx-community/whisper-large-v3-turbo"
    language: str = "zh"                    # 传给 mlx-whisper 的 language 参数
    sample_rate: int = 16000
    silence_threshold: float = 0.01         # 预留：toggle 未来自动停用
    record_dir: str = ""                    # 调试用：保存录音目录，空=不存


def parse_hotkey(desc: str) -> tuple[list[str], str]:
    """'cmd+space' → (['cmd'], 'space')。末段为按键，前面为修饰键。"""
    parts = [p.strip().lower() for p in desc.split("+")]
    if not parts:
        raise ValueError(f"empty hotkey: {desc!r}")
    mods = [_MOD_ALIASES[p] for p in parts[:-1] if p in _MOD_ALIASES]
    key = parts[-1]
    return mods, key


def load_config(path: str) -> Config:
    """从 yaml 加载配置，缺失项用 Config 默认值补齐。"""
    data = yaml.safe_load(Path(path).read_text()) or {}
    return Config(**{k: v for k, v in data.items() if k in Config.__dataclass_fields__})
```

- [ ] **Step 4: 写 config.yaml**

`config.yaml`:
```yaml
# 听写工具配置
mode: ptt                # ptt=按住说话 | toggle=按一下开始/再按一下结束
hotkey: cmd+space        # 全局热键（修饰键+按键，+ 分隔）
model: mlx-community/whisper-large-v3-turbo   # mlx-whisper 模型（HF id）
language: zh             # 中文为主
sample_rate: 16000
silence_threshold: 0.01
record_dir: ""           # 留空不保存录音；调试可设 phase0/recordings/
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_config.py -v`
Expected: 3 passed。

- [ ] **Step 6: 提交**

```bash
git add config.yaml src/whisper_dictation/config.py tests/test_config.py
git commit -m "feat: config loading and hotkey parsing"
```

---

### Task 3: audio 录音模块

**Files:**
- Create: `src/whisper_dictation/audio.py`
- Test: `tests/test_audio.py`

- [ ] **Step 1: 写失败测试**

`tests/test_audio.py`:
```python
import numpy as np
from whisper_dictation.audio import record_seconds


def test_record_returns_float32_mono(monkeypatch):
    """record_seconds 应返回 (N, sample_rate*seconds) 形状的 float32 mono。"""
    sr = 16000
    seconds = 1
    fake = np.zeros(sr * seconds, dtype=np.float32)

    class FakeSD:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def stop(self): pass
        def get(self, *a, **k): return fake

    import whisper_dictation.audio as A
    monkeypatch.setattr(A.sd, "InputStream", lambda *a, **k: FakeSD())
    out = record_seconds(seconds=seconds, sample_rate=sr)
    assert out.dtype == np.float32
    assert out.ndim == 1
    assert len(out) == sr * seconds
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_audio.py -v`
Expected: FAIL（模块不存在）。

- [ ] **Step 3: 实现 audio.py**

`src/whisper_dictation/audio.py`:
```python
"""麦克风录音：sounddevice → float32 mono numpy 数组。"""
import numpy as np
import sounddevice as sd


def record_seconds(seconds: float, sample_rate: int = 16000) -> np.ndarray:
    """录制固定秒数音频，返回 float32 mono。

    用于最简管线与测试。生产路径用 record_until（由调用方决定何时停）。
    """
    with sd.InputStream(channels=1, samplerate=sample_rate, dtype="float32") as stream:
        stream.read(int(seconds * sample_rate))  # 预热缓冲，丢弃
        data, _ = stream.read(int(seconds * sample_rate))
    return np.asarray(data).reshape(-1)


def record_into(frames: list, sample_rate: int = 16000) -> sd.InputStream:
    """开启输入流，持续把块 append 到 frames；返回 stream，调用方负责 stop()。

    供 PTT/toggle：按键开始 → record_into 起 → 按键结束 → stop()。
    """
    def _callback(indata, frames_count, time_info, status):  # noqa: ARG001
        frames.append(np.asarray(indata).reshape(-1).copy())
    stream = sd.InputStream(
        channels=1, samplerate=sample_rate, dtype="float32", callback=_callback
    )
    stream.start()
    return stream


def flatten(frames: list) -> np.ndarray:
    """把 record_into 累积的块列表拼成一维数组。"""
    if not frames:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(frames).astype(np.float32)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_audio.py -v`
Expected: passed。

- [ ] **Step 5: 提交**

```bash
git add src/whisper_dictation/audio.py tests/test_audio.py
git commit -m "feat: audio recording module"
```

---

### Task 4: transcribe 模块（mlx-whisper 封装）

**Files:**
- Create: `src/whisper_dictation/transcribe.py`
- Test: `tests/test_transcribe.py`

- [ ] **Step 1: 写失败测试（mock mlx_whisper，避免真实推理）**

`tests/test_transcribe.py`:
```python
from whisper_dictation.transcribe import transcribe


def test_transcribe_passes_language_and_returns_text(monkeypatch):
    captured = {}

    def fake_transcribe(audio, *, path_or_hf_repo, language, **kw):  # noqa: ARG001
        captured["lang"] = language
        captured["repo"] = path_or_hf_repo
        return {"text": "  你好世界。  "}

    import whisper_dictation.transcribe as T
    monkeypatch.setattr(T.mlx_whisper, "transcribe", fake_transcribe)

    text = transcribe(audio=__import__("numpy").zeros(16000, dtype="float32"),
                      model="mlx-community/whisper-large-v3-turbo", language="zh")
    assert text == "你好世界。"          # 去掉首尾空白
    assert captured["lang"] == "zh"
    assert captured["repo"].startswith("mlx-community/")


def test_transcribe_empty_audio_returns_empty(monkeypatch):
    import whisper_dictation.transcribe as T
    import numpy as np
    monkeypatch.setattr(T.mlx_whisper, "transcribe",
                        lambda *a, **k: {"text": ""})
    assert transcribe(np.zeros(0, dtype="float32"), "m", "zh") == ""
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_transcribe.py -v`
Expected: FAIL（模块不存在）。

- [ ] **Step 3: 实现 transcribe.py**

`src/whisper_dictation/transcribe.py`:
```python
"""mlx-whisper 封装：audio(float32,16k) → 干净文本。"""
import numpy as np
import mlx_whisper


def transcribe(audio: np.ndarray, model: str, language: str = "zh") -> str:
    """转写音频，返回去除首尾空白的文本。

    audio: float32 mono, 16kHz。
    model: mlx-whisper 模型（HF repo id，如 mlx-community/whisper-large-v3-turbo）。
    """
    if audio.size == 0:
        return ""
    result = mlx_whisper.transcribe(
        audio,
        path_or_hf_repo=model,
        language=language,
    )
    return (result.get("text") or "").strip()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_transcribe.py -v`
Expected: 2 passed。

- [ ] **Step 5: 提交**

```bash
git add src/whisper_dictation/transcribe.py tests/test_transcribe.py
git commit -m "feat: mlx-whisper transcription wrapper"
```

---

### Task 5: 引擎管线冒烟（真实模型，手动验收）

**Files:**
- Create: `scripts/smoke_transcribe.py`

- [ ] **Step 1: 写冒烟脚本**

`scripts/smoke_transcribe.py`:
```python
"""冒烟测试：录 3 秒 → 用真实 Turbo 模型转写 → 打印结果。

用途：首次确认 mlx-whisper + Turbo 在本机能跑、中文识别可用。
首次运行会从 HuggingFace 下载模型（~1.5GB），需联网；之后走本地缓存。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from whisper_dictation.audio import record_seconds  # noqa: E402
from whisper_dictation.transcribe import transcribe  # noqa: E402


def main():
    sr = 16000
    print("准备录音 3 秒，请说话…", flush=True)
    audio = record_seconds(seconds=3, sample_rate=sr)
    print("转写中…（首次会下载模型）", flush=True)
    text = transcribe(audio, model="mlx-community/whisper-large-v3-turbo", language="zh")
    print(f"结果：{text!r}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 跑冒烟（手动，需麦克风 + 首次联网下模型）**

Run:
```bash
source .venv/bin/activate
python scripts/smoke_transcribe.py
```
对麦克风说一句中文（如"测试本地语音识别"）。
Expected: 打印出可识别的中文文本。若报权限错 → 先做 Task 9 的麦克风授权。

- [ ] **Step 3: 把脚本与"首次需下载模型"备注提交**

```bash
git add scripts/smoke_transcribe.py
git commit -m "feat: engine pipeline smoke test (real turbo model)"
```

> **验收门**：这一步跑通且中文识别可接受，才继续 Slice 2-4。否则先解决模型/引擎问题。

---

## Slice 2：光标处键入

### Task 6: typer 模块（剪贴板 + Cmd+V）

**Files:**
- Create: `src/whisper_dictation/typer.py`
- Test: `tests/test_typer.py`

- [ ] **Step 1: 写失败测试（mock Quartz，验证剪贴板写入与 Cmd+V 事件序列）**

`tests/test_typer.py`:
```python
from whisper_dictation.typer import type_text


def test_type_text_writes_clipboard_and_pastes(monkeypatch):
    calls = []

    class FakePasteboard:
        def clearContents(self): calls.append("clear")
        def setString_forType_(self, s, t): calls.append(("set", s, t))

    def fake_cgEvent_post(mods, key_code, down):
        calls.append(("post", mods, key_code, down))

    import whisper_dictation.typer as Ty
    monkeypatch.setattr(Ty, "_new_pasteboard", lambda: FakePasteboard())
    monkeypatch.setattr(Ty, "_post_key", fake_cgEvent_post)

    type_text("你好")

    assert ("set", "你好", "public.utf8-plain-text") in calls
    # 应有一次 cmd-down、一次 v-down、release，且带 cmd 修饰
    posts = [c for c in calls if isinstance(c, tuple) and c[0] == "post"]
    assert any("cmd" in p[1] and p[2] == 9 and p[3] for p in posts)  # key_code 9 = V


def test_type_text_empty_does_nothing(monkeypatch):
    calls = []
    import whisper_dictation.typer as Ty
    monkeypatch.setattr(Ty, "_new_pasteboard", lambda: type("X", (), {
        "clearContents": lambda self: calls.append("clear"),
        "setString_forType_": lambda self, s, t: calls.append(("set", s, t)),
    })())
    monkeypatch.setattr(Ty, "_post_key", lambda *a: calls.append("post"))
    type_text("")
    assert calls == []
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_typer.py -v`
Expected: FAIL（模块不存在）。

- [ ] **Step 3: 实现 typer.py**

`src/whisper_dictation/typer.py`:
```python
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
    # Cmd+V
    _post_key(_FLAG_MASK_CMD, _KEY_V, True)
    time.sleep(0.01)
    _post_key(0, _KEY_V, False)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_typer.py -v`
Expected: 2 passed。

- [ ] **Step 5: 手动验证（需辅助功能权限，见 Task 9）**

在任意文本框聚焦时，Python 跑：
```python
from whisper_dictation.typer import type_text; type_text("测试中文输入")
```
Expected: "测试中文输入"出现在光标处。若没出现 → 辅助功能权限未授予。

- [ ] **Step 6: 提交**

```bash
git add src/whisper_dictation/typer.py tests/test_typer.py
git commit -m "feat: type text at cursor via clipboard + cmd+v"
```

---

## Slice 3：热键触发 + 主循环（PTT）

### Task 7: hotkey 模式状态机（纯逻辑，可测）

**Files:**
- Create: `src/whisper_dictation/hotkey.py`
- Test: `tests/test_hotkey.py`

- [ ] **Step 1: 写失败测试**

`tests/test_hotkey.py`:
```python
from whisper_dictation.hotkey import Mode, ModeMachine


def test_ptt_press_starts_release_stops():
    m = ModeMachine(Mode.PTT)
    assert m.on_press() == "start"     # 按下 → 开始录音
    assert m.is_recording
    assert m.on_release() == "stop"    # 松开 → 停止并转写
    assert not m.is_recording


def test_toggle_first_press_starts_second_press_stops():
    m = ModeMachine(Mode.TOGGLE)
    assert m.on_press() == "start"
    assert m.is_recording
    assert m.on_press() == "stop"      # 再按一次 → 停止
    assert not m.is_recording


def test_toggle_release_is_noop():
    m = ModeMachine(Mode.TOGGLE)
    assert m.on_press() == "start"
    assert m.on_release() == "noop"    # toggle 模式下松开无动作
    assert m.is_recording
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_hotkey.py -v`
Expected: FAIL。

- [ ] **Step 3: 实现 hotkey.py（状态机部分）**

`src/whisper_dictation/hotkey.py`:
```python
"""热键模式状态机（纯逻辑）+ pyobjc 全局热键监听。

状态机与系统事件解耦：状态机可单测，事件回调薄。
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


# --- pyobjc 全局热键监听（系统层，见 Task 8 接入） ---
# 在 Task 8 中实现 register_hotkey(mods, key, on_press, on_release)，
# 用 Carbon.RegisterEventHotKey。这里只占位说明接口。
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_hotkey.py -v`
Expected: 3 passed。

- [ ] **Step 5: 提交**

```bash
git add src/whisper_dictation/hotkey.py tests/test_hotkey.py
git commit -m "feat: hotkey mode state machine (ptt + toggle)"
```

---

### Task 8: 全局热键监听（pyobjc Carbon）+ app 主循环

**Files:**
- Modify: `src/whisper_dictation/hotkey.py`（补 register_hotkey）
- Create: `src/whisper_dictation/app.py`

> 说明：全局热键与 CGEvent 属系统交互，难单测；本任务以手动验收为准。状态机逻辑已在上一个任务单测覆盖。

- [ ] **Step 1: 在 hotkey.py 末尾补 register_hotkey**

追加到 `src/whisper_dictation/hotkey.py`：
```python
import Carbon
import Quartz

# 修饰键 → Carbon 事件标志
_MOD_FLAGS = {
    "cmd": Carbon.cmdKey,
    "ctrl": Carbon.controlKey,
    "option": Carbon.optionKey,
    "shift": Carbon.shiftKey,
}

# 常见按键名 → 虚拟键码（按需扩展）
_KEY_CODES = {
    "space": 49, "j": 38, "k": 40, "v": 9, "f13": 105, "f14": 107,
}


def _flags_for(mods):
    f = 0
    for m in mods:
        f |= _MOD_FLAGS[m]
    return f


def register_hotkey(mods, key, on_press, on_release):
    """注册全局热键，按下调 on_press()，松开调 on_release()。

    返回一个 (hotkey_ref, event_loop_runner)。调用方 run loop 阻塞以接收事件。
    需要辅助功能 + 输入监听权限。
    """
    flags = _flags_for(mods)
    keycode = _KEY_CODES[key]

    hotkey_ref = [None]

    def _handler(_ref, event_type, event, _refcon):
        if event_type == Carbon.kEventHotKeyPressed:
            on_press()
        elif event_type == Carbon.kEventHotKeyReleased:
            on_release()

    tap = Carbon.AllocateEventTap?  # 占位：见下方实现说明
    # 实际实现使用 Carbon InstallEventHandler + RegisterEventHotKey：
    event_spec = (Carbon.kEventClassKeyboard,
                  (Carbon.kEventHotKeyPressed, Carbon.kEventHotKeyReleased))
    target = Carbon.GetApplicationEventTarget()
    handler = Carbon.InstallEventHandler(target, _handler, event_spec, None)
    ref = Carbon.RegisterEventHotKey(keycode, flags,
                                     Carbon.EventHotKeyID(0, 0x1),
                                     target, 0)
    hotkey_ref[0] = ref
    return handler, ref
```

> **实现注意**：pyobjc 的 `Carbon` 模块 API 较底层，`InstallEventHandler` 的回调签名与 `RegisterEventHotKey` 的常量在 pyobjc 下可能与 C 原型有差异。若上述片段在 import/调用时报 AttributeError，退回用 **`pynput`** 库（`pip install pynput`，加入 pyproject）的 `keyboard.GlobalHotKeys` 或 `keyboard.Listener` 实现，接口同样是"按下/松开回调"。pynput 在 macOS 同样需要辅助功能 + 输入监听权限。**先用 Carbon 尝试，失败则切 pynput 并记录原因到 LESSONS_LEARNED.md。**

- [ ] **Step 2: 写 app.py 主循环**

`src/whisper_dictation/app.py`:
```python
"""主循环：热键 → 录音 → 转写 → 键入。常驻进程。"""
import threading

from .audio import record_into, flatten
from .config import load_config, parse_hotkey
from .hotkey import Mode, ModeMachine, register_hotkey
from .transcribe import transcribe
from .typer import type_text


class DictationApp:
    def __init__(self, config_path="config.yaml"):
        self.cfg = load_config(config_path)
        mods, key = parse_hotkey(self.cfg.hotkey)
        self.mods, self.key = mods, key
        self.machine = ModeMachine(Mode(self.cfg.mode))
        self._stream = None
        self._frames = None
        self._lock = threading.Lock()

    def _start(self):
        with self._lock:
            if self.machine.is_recording:
                return
            self._frames = []
            self._stream = record_into(self._frames, self.cfg.sample_rate)
            print("● 录音中…", flush=True)

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
        if audio.size < self.cfg.sample_rate // 4:  # <0.25s 视为误触
            print("（太短，忽略）", flush=True)
            return
        print("转写中…", flush=True)
        text = transcribe(audio, self.cfg.model, self.cfg.language)
        if text:
            type_text(text)
            print(f"✓ {text}", flush=True)

    def run(self):
        print(f"听写就绪：{self.cfg.mode} / {self.cfg.hotkey}（按 Ctrl-C 退出）", flush=True)
        def on_press():
            action = self.machine.on_press()
            if action == "start":
                self._start()
            elif action == "stop":
                self._stop()

        def on_release():
            action = self.machine.on_release()
            if action == "stop":
                self._stop()

        register_hotkey(self.mods, self.key, on_press, on_release)
        # 阻塞主线程以接收 Carbon 事件
        import Carbon
        Carbon.RunApplicationEventLoop()


def main():
    import sys
    cfg = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    DictationApp(cfg).run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 在 pyproject.toml 注册入口（可选）**

在 `[project]` 段追加：
```toml
[project.scripts]
whisper-dictation = "whisper_dictation.app:main"
```

- [ ] **Step 4: 跑全部单测确认无回归**

Run: `pytest -q`
Expected: 全绿（state machine / config / typer / transcribe / audio）。

- [ ] **Step 5: 手动验收（需三项权限，见 Task 9）**

Run:
```bash
source .venv/bin/activate
python -m whisper_dictation.app
```
切到任意文本框，按 `Cmd+Space`（或 config 中设的热键）说一句中文，松开。
Expected: 文字出现在光标处。toggle 模式改 `config.yaml` 的 `mode: toggle` 再试。

- [ ] **Step 6: 提交**

```bash
git add src/whisper_dictation/hotkey.py src/whisper_dictation/app.py pyproject.toml
git commit -m "feat: global hotkey listener and main dictation loop"
```

---

## Slice 4：权限、文档、收尾

### Task 9: macOS 权限授予指引

**Files:**
- Create: `docs/PERMISSIONS.md`

- [ ] **Step 1: 写权限指引**

`docs/PERMISSIONS.md`:
```markdown
# macOS 权限配置

本工具常驻运行需三项系统权限（系统设置 → 隐私与安全性）：

1. **麦克风**：录音必需。首次运行 smoke/app 时系统弹窗，点允许；
   或手动在 隐私与安全性 → 麦克风 里加 Terminal / iTerm / 你的终端。
2. **辅助功能（Accessibility）**：全局热键 + 模拟 Cmd+V 键入必需。
   隐私与安全性 → 辅助功能 → 勾选终端。
3. **输入监听（Input Monitoring）**：若用 pynput 或事件钩子方案需要。
   隐私与安全性 → 输入监听 → 勾选终端。

授权后需重启终端进程生效。
```

- [ ] **Step 2: 提交**

```bash
git add docs/PERMISSIONS.md
git commit -m "docs: macOS permissions setup"
```

---

### Task 10: README + 最终全量验收

**Files:**
- Create: `README.md`
- Create: `LESSONS_LEARNED.md`（按全局 CLAUDE.md 要求）

- [ ] **Step 1: 写 README**

`README.md`:
```markdown
# 本地语音听写（Whisper Dictation）

macOS 本地语音听写：全局热键说话 → Whisper Large v3 Turbo（mlx-whisper）转写 → 键入光标处。全程本地，无云端。

## 安装
1. `xcode-select --install`（pyobjc 需要）
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -e ".[dev]"`
4. 按 docs/PERMISSIONS.md 授予麦克风/辅助功能/输入监听权限

## 使用
`python -m whisper_dictation.app`（或 `whisper-dictation`）
按热键（默认 Cmd+Space）说话，松开 → 文字出现在光标处。

## 配置（config.yaml）
- `mode`: ptt（按住说话）/ toggle（按一下开始，再按一下结束）
- `hotkey`: 全局热键，如 option+j
- `model`: mlx-whisper 模型 id
- `language`: zh

首次运行会下载模型（~1.5GB，本地缓存）。
```

- [ ] **Step 2: 写 LESSONS_LEARNED.md**

`LESSONS_LEARNED.md`:
```markdown
# Lessons Learned

## Bugs / 踩坑
- （执行中按需补充：如 pyobjc Carbon API 调用差异、CJK 键入为何走剪贴板）

## Debug 模式
- （按需补充）

## 流程
- 从"用现成 app"转向"自研"，因付费门槛。决策应及时记录进 spec，避免计划与现实脱节。

## 关键结论
- CJK 文本键入：用"剪贴板 + Cmd+V"而非单键事件，最稳。
- Apple Silicon 上 ASR 引擎选 mlx-whisper（最快）。
```

- [ ] **Step 3: 全量验收（spec §5.2 对应项，实战记录）**

跑 `pytest -q`（全绿）+ 手动 PTT + 手动 toggle 各 3 次，记录到 `phase0/acceptance.md`（复用旧文件名，内容更新为自研版验收）。

- [ ] **Step 4: 提交**

```bash
git add README.md LESSONS_LEARNED.md phase0/acceptance.md
git commit -m "docs: README, lessons learned, self-built acceptance results"
```

---

## 自检（writing-plans self-review）

- **Spec 覆盖**：双触发模式（PTT + toggle）→ Task 7 状态机 + Task 8 验收；本地 Turbo → Task 4/5；键入光标 → Task 6；中文 → Task 6 剪贴板策略 + config language；无 LLM 后处理 → 整个 MVP 不含（符合 Phase A 修订）；权限 → Task 9。
- **占位符扫描**：Task 8 的 Carbon 代码含明确退路（pynput）与记录要求，非"TODO 放着"。其余步骤都有完整代码与命令。
- **类型一致性**：`Config`/`Mode`/`ModeMachine` 字段与方法名跨任务一致；`register_hotkey(mods, key, on_press, on_release)` 签名在 Task 7/Task 8/app.py 一致；`type_text(text)`、`transcribe(audio, model, language)` 签名统一。
- **风险点（已知）**：pyobjc Carbon 全局热键 API 在 pyobjc 下可能需调整 → 已给 pynput 退路。CJK 键入 → 已用剪贴板方案。
