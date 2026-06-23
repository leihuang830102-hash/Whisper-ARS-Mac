# 本地语音听写（Whisper Dictation）

macOS 本地语音听写：全局热键说话 → **Whisper Large v3 Turbo（mlx-whisper）**本地转写 → 文字粘到当前光标处。全程本地、零云端、零订阅。

实测在 Apple M5 上：整句转写 ~0.8s，中英文准确率高。

> License: MIT（见 [LICENSE](LICENSE)）。本项目不分发下列第三方依赖与模型——用户自行通过 pip 安装依赖、通过 `scripts/download_model.py` 下载模型。各依赖保留其原始 license。

## 它能做什么
- 按住热键说话，松开 → 转写文字粘到**任意**文本框的光标处（聊天框、编辑器、浏览器、终端…）。
- 两种触发模式：`ptt`（按住说话）/ `toggle`（按一下开始，再按一下结束）。
- 静音/过短自动忽略（避免 Whisper 静音幻觉污染输入）。
- 默认热键 `Ctrl+Shift+Space`（避开 Spotlight、F 键多媒体码、option+space 输入不间断空格等坑）。

## 安装

> 要求：macOS Apple Silicon、Xcode Command Line Tools（`xcode-select --install`）。

```bash
cd Whisper
python3 -m venv .venv          # 需 Python 3.11+；若系统 python3 太旧用 miniconda 的
source .venv/bin/activate
pip install -e ".[dev]"
```

## 下载模型（国内必做）

HuggingFace 在国内被墙、hf-mirror 会重定向回源。本工具走 **ModelScope（阿里，直连）**：

```bash
source .venv/bin/activate
python scripts/download_model.py     # 下载 MLX Turbo 到 models/whisper-large-v3-turbo/（~1.6GB，不入库）
```

`config.yaml` 的 `model` 已指向该本地目录——`mlx_whisper` 检测到目录存在就跳过 HF 下载，**完全离线**。

## 授予 macOS 权限（关键，否则热键/粘贴无效）

详见 [docs/PERMISSIONS.md](docs/PERMISSIONS.md)。要点：
- **必须从独立签名终端（Terminal.app / iTerm）运行**——IDE 内部跑会被 Helper 子进程拦在权限外。
- 给该终端授三项：**麦克风**、**辅助功能**、**输入监听**。
- 授权后 **Cmd+Q 完全退出终端再重开**。

## 使用

```bash
source .venv/bin/activate
python -m whisper_dictation.app      # 或装好后直接 whisper-dictation
```

看到 `听写就绪…` 后，切到任意文本框，按住 `Ctrl+Shift+Space` 说话，松开。

## 配置（config.yaml）

| 字段 | 说明 | 示例 |
|---|---|---|
| `mode` | 触发模式 | `ptt` / `toggle` |
| `hotkey` | 全局热键（修饰键+按键） | `ctrl+shift+space`、`option+j`、`control+f5` |
| `model` | 本地模型目录或 HF id | `models/whisper-large-v3-turbo` |
| `language` | 转写语言 | `zh` |

支持的热键：修饰键 `ctrl/option/cmd/shift` + 按键（字母、数字、`space`、`enter`、`f1`-`f20` 等）。
⚠️ `fn` 键不支持（系统底层拦截）；`cmd+space` 会和 Spotlight 冲突。

## 项目结构

```
src/whisper_dictation/
├── config.py     # 配置加载 + 热键解析
├── audio.py      # 录音（sounddevice）+ 静音判定
├── transcribe.py # mlx-whisper 封装
├── typer.py      # 写剪贴板 + 模拟 Cmd+V 粘到光标处
├── hotkey.py     # 模式状态机（纯逻辑）+ pynput 全局热键
└── app.py        # 主循环：热键→录音→转写→键入
tests/            # 14 个单测
scripts/
├── download_model.py   # ModelScope 下载
└── smoke_transcribe.py # 引擎冒烟测试
```

## 踩坑记录
见 [LESSONS_LEARNED.md](LESSONS_LEARNED.md)（HF 被墙走 ModelScope、本地加载、静音幻觉、macOS 责任进程权限、pyobjc API 等）。

## 后续（按需，当前不做）
- **Phase B**：转写后过本地 LLM（Ollama）清理——仅当实测原始 Turbo 输出不够好（目前整句已很好，暂不需要）。
- **Phase C**：ASR 生态功能调研（说话人区分、语音命令等）。
- **Phase D**：自然语言语音对话（流式 ASR + TTS，像打电话）。

## 致谢与第三方依赖（Credits）

本项目（MIT）使用/基于下列开源软件与模型（按各自原始 license；本项目不重新分发它们，用户自行安装/下载）：

| 依赖 / 模型 | 用途 | License |
|---|---|---|
| [OpenAI Whisper Large v3 Turbo](https://github.com/openai/whisper) | 语音识别模型权重 | MIT |
| [mlx-whisper](https://github.com/ml-explore/mlx-examples) / [MLX](https://github.com/ml-explore/mlx) | Apple Silicon 上的 Whisper 推理引擎 | MIT / Apache-2.0 |
| [pynput](https://github.com/moses-palmer/pynput) | 全局热键监听 | **LGPL-3.0-or-later**（可独立替换的库） |
| [pyobjc](https://pyobjc.readthedocs.io/) (Quartz / AppKit) | macOS 剪贴板 + 模拟键盘输入 | MIT |
| [sounddevice](https://python-sounddevice.readthedocs.io/) / [PortAudio](http://www.portaudio.com/) | 麦克风录音 | MIT / PortAudio |
| [NumPy](https://numpy.org/) | 音频数组处理 | BSD-3-Clause |
| [PyYAML](https://pyyaml.org/) | 配置文件解析 | MIT |
| [pytest](https://docs.pytest.org/) | 单元测试 | MIT |

模型经 [ModelScope（魔搭社区）](https://modelscope.cn/) 镜像下载（HuggingFace 在国内不可达）。
