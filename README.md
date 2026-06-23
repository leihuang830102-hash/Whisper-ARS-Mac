# Whisper Dictation / 本地语音听写

A self-built, fully-local macOS voice-dictation tool. Hold a global hotkey, speak, and the text is typed at your cursor — transcribed on-device by Whisper Large v3 Turbo (via mlx-whisper). No cloud, no subscription, no API keys.

自建的、完全本地的 macOS 语音听写工具。按住全局热键说话，文字即输入到当前光标处——由本机的 Whisper Large v3 Turbo（mlx-whisper）转写。无云端、无订阅、无需 API key。

Tested on Apple M5: ~0.8s per sentence, high accuracy for Chinese and English.
实测 Apple M5：每句约 0.8 秒，中英文准确率高。

> **License:** MIT — see [LICENSE](LICENSE).

---

# English

## What it does
- Hold the hotkey, speak, release → the transcription is pasted into **any** focused text field (chat, editor, browser, terminal…).
- Two trigger modes: `ptt` (push-to-talk, hold) / `toggle` (press once to start, again to stop).
- Silence / too-short audio is auto-rejected (avoids Whisper's hallucination-on-silence).
- Default hotkey `Ctrl+Shift+Space` (avoids Spotlight, F-key media codes, and option+space's non-breaking space).

## Install
Requires: Apple Silicon macOS, Xcode Command Line Tools (`xcode-select --install`), Python ≥ 3.11.
```bash
cd Whisper
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Get the model
```bash
python scripts/download_model.py      # → models/whisper-large-v3-turbo/ (~1.6GB)
```
After download, `config.yaml:model` points at the local directory, and the app runs fully offline. (In regions where the default source is unreachable, e.g. mainland China, the script fetches from a reachable mirror — no manual setup needed.)

## macOS permissions (the main friction)
Global hotkey + synthetic keystrokes need TCC permissions, attributed to the **responsible process**. See [docs/PERMISSIONS.md](docs/PERMISSIONS.md). Key points:
- **Run from a signed standalone terminal** (Terminal.app / iTerm). Running inside an IDE fails silently — its main-app permission doesn't cover the Helper subprocess, so the hotkey listener reports "running" but receives 0 events.
- Grant the terminal: **Microphone**, **Accessibility**, **Input Monitoring**.
- Fully quit + reopen the terminal after granting.

## Usage
```bash
source .venv/bin/activate
python -m whisper_dictation.app      # or: whisper-dictation
```
When you see `听写就绪…`, focus any text field, hold `Ctrl+Shift+Space`, speak, release.

Double-clickable wrapper (opens Terminal for you): `bash scripts/build_app.sh` → `~/Applications/WhisperDictation.app`.

## Config (`config.yaml`)
| Field | Meaning | Example |
|---|---|---|
| `mode` | trigger mode | `ptt` / `toggle` |
| `hotkey` | global hotkey (modifier+key) | `ctrl+shift+space`, `option+j`, `control+f5` |
| `model` | local model dir or HF id | `models/whisper-large-v3-turbo` |
| `language` | transcription language | `zh` |

Supported hotkeys: modifiers `ctrl/option/cmd/shift` + a key (letters, digits, `space`, `enter`, `f1`–`f20`).
⚠️ `fn` is not detectable (system-intercepted); `cmd+space` conflicts with Spotlight; bare F-keys may arrive as media keys.

## Roadmap (optional, not done)
- **Phase B:** post-transcription cleanup via a local LLM (Ollama) — only if raw output quality drops.
- **Phase C:** research ASR ecosystem features (diarization, voice commands…).
- **Phase D:** natural voice conversation (streaming ASR + TTS, like a phone call).

---

# 中文

## 功能
- 按住热键说话，松开 → 转写文字粘到**任意**获得焦点的文本框（聊天框、编辑器、浏览器、终端…）。
- 两种触发模式：`ptt`（按住说话）/ `toggle`（按一下开始，再按一下结束）。
- 静音 / 过短音频自动忽略（避免 Whisper 对静音产生幻觉）。
- 默认热键 `Ctrl+Shift+Space`（避开 Spotlight、F 键多媒体码、option+space 输入不间断空格）。

## 安装
需要：Apple Silicon macOS、Xcode Command Line Tools（`xcode-select --install`）、Python ≥ 3.11。
```bash
cd Whisper
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 获取模型
```bash
python scripts/download_model.py      # → models/whisper-large-v3-turbo/（约 1.6GB）
```
下载后 `config.yaml:model` 指向本地目录，应用完全离线运行。（默认源在部分区域无法访问时，例如中国大陆，脚本会从可达的镜像拉取，无需手动配置。）

## macOS 权限（主要摩擦点）
全局热键 + 模拟按键需要 TCC 权限，且按**责任进程**判定。详见 [docs/PERMISSIONS.md](docs/PERMISSIONS.md)。要点：
- **用签名的独立终端运行**（Terminal.app / iTerm）。从 IDE 内部跑会静默失败——主 app 的权限覆盖不到 Helper 子进程，监听器显示"运行中"却收到 0 事件。
- 给该终端授：**麦克风**、**辅助功能**、**输入监听**。
- 授权后**完全退出再重开**该终端。

## 使用
```bash
source .venv/bin/activate
python -m whisper_dictation.app      # 或：whisper-dictation
```
看到 `听写就绪…` 后，聚焦任意文本框，按住 `Ctrl+Shift+Space` 说话松开。

双击即用的包装器（自动打开 Terminal）：`bash scripts/build_app.sh` → `~/Applications/WhisperDictation.app`。

## 配置（`config.yaml`）
| 字段 | 含义 | 示例 |
|---|---|---|
| `mode` | 触发模式 | `ptt` / `toggle` |
| `hotkey` | 全局热键（修饰键+按键） | `ctrl+shift+space`、`option+j`、`control+f5` |
| `model` | 本地模型目录或 HF id | `models/whisper-large-v3-turbo` |
| `language` | 转写语言 | `zh` |

支持的热键：修饰键 `ctrl/option/cmd/shift` + 按键（字母、数字、`space`、`enter`、`f1`-`f20`）。
⚠️ `fn` 键不支持（系统底层拦截）；`cmd+space` 与 Spotlight 冲突；裸 F 键可能作为多媒体键上报。

## 后续（按需，当前未做）
- **Phase B**：转写后用本地 LLM（Ollama）清理——仅当原始输出质量下降时。
- **Phase C**：调研 ASR 生态功能（说话人区分、语音命令等）。
- **Phase D**：自然语音对话（流式 ASR + TTS，像打电话）。

---

# Credits & Acknowledgements / 致谢

This project (MIT) builds on the following open-source software and model. They keep their original licenses; this project does **not** redistribute them — users install dependencies via pip and download the model separately.

本项目（MIT）基于下列开源软件与模型构建，它们保留各自原始 license；本项目**不分发**它们——用户通过 pip 安装依赖、自行下载模型。

| Dependency / 依赖 | Use / 用途 | License |
|---|---|---|
| [OpenAI Whisper Large v3 Turbo](https://github.com/openai/whisper) | ASR model weights / 语音识别模型 | MIT |
| [mlx-whisper](https://github.com/ml-explore/mlx-examples) / [MLX](https://github.com/ml-explore/mlx) | Whisper inference on Apple Silicon / Apple Silicon 上的推理引擎 | MIT / Apache-2.0 |
| [pynput](https://github.com/moses-palmer/pynput) | Global hotkey listener / 全局热键监听 | LGPL-3.0-or-later |
| [pyobjc](https://pyobjc.readthedocs.io/) (Quartz / AppKit) | macOS clipboard + synthetic input / 剪贴板 + 模拟输入 | MIT |
| [sounddevice](https://python-sounddevice.readthedocs.io/) / [PortAudio](http://www.portaudio.com/) | Microphone capture / 麦克风录音 | MIT / PortAudio |
| [NumPy](https://numpy.org/) | Audio array processing / 音频数组处理 | BSD-3-Clause |
| [PyYAML](https://pyyaml.org/) | Config parsing / 配置解析 | MIT |
| [pytest](https://docs.pytest.org/) | Unit tests / 单元测试 | MIT |

Pitfalls & lessons are recorded in [LESSONS_LEARNED.md](LESSONS_LEARNED.md). Project layout and architecture are documented in [CLAUDE.md](CLAUDE.md).
