# Lessons Learned

## Bugs / 踩坑

### 1. HuggingFace 在国内被墙，hf-mirror.com 也失效
- **现象**：`mlx_whisper` 首次转写报 `SSL: UNEXPECTED_EOF_WHILE_READING`；设 `HF_ENDPOINT=https://hf-mirror.com` 后仍失败。
- **根因**：huggingface.co 被墙（curl 状态码 000）；hf-mirror.com 虽可达，但把 `resolve/` 文件请求 **308 重定向回 huggingface.co**（被墙的源头），等于没镜像。
- **修复**：改从 **ModelScope（魔搭，阿里，国内直连）** 下载 MLX 权重到本地目录 `models/whisper-large-v3-turbo/`，让 `mlx_whisper` 走本地加载（见下条）。脚本：`scripts/download_model.py`。
- **预防规则**：国内环境下，任何依赖 HuggingFace hub 的库，先验证直连；失败直接走 ModelScope + 本地路径，别在 hf-mirror 上浪费时间（它会重定向回源）。

### 2. mlx_whisper 支持本地目录加载，跳过 HF
- **要点**：`mlx_whisper.load_model()` 第一步判断 `Path(path_or_hf_repo).exists()`——若传入已存在的本地目录（含 `config.json` + `weights.safetensors`），**完全跳过 HF 下载**。所以把模型下到本地后，`config.yaml` 的 `model` 指向该目录即可，无需联网、无需代理、无需 `HF_ENDPOINT`。

### 3. Whisper 对静音/孤立词会产生幻觉
- **现象 A（静音）**：纯静音或没说话时，模型吐出"优优独播剧场…"或"会会会会…"无限重复（重复幻觉，转写耗时飙到 5s+）。
- **现象 B（孤立词）**：孤立重复"测试"被识别成"措施"（cè shì / cuò shī 近音混淆，无句子上下文消歧）。
- **现象 C（整句）**：真实整句"帮我把这个函数重构一下" → **100% 正确**，0.8s。
- **结论**：原始 Turbo 在真实整句场景已足够好；问题集中在"静音/近静音"输入。
- **预防规则**（影响 app 层）：
  - 转写前必须做**能量检测**，静音（RMS < ~0.005）不送模型、不输出（避免幻觉污染光标处）。
  - 录音过短（< 0.25s）直接忽略（已在 app.py 计划中）。
  - 可加 `no_speech_threshold` / 重复检测兜底。
  - **Phase B（LLM 后处理）可能并非必需**——整句质量已够好；除非实测发现标点/口头禅问题。

### 4. 测试 mock 方法名必须匹配真实 API
- **现象**：计划里 audio 的测试 mock 写了 `FakeSD.get`，但实现调 `sounddevice.InputStream.read()`（真实 API 是 `read`，返回 `(data, overflowed)`）。
- **修复**：mock 方法改为 `read(self, n) -> (fake, False)`。
- **预防规则**：写 mock 前先 `inspect.signature` 或查真实 API 签名，别凭记忆。

### 5. macOS 全局热键必须在"责任进程"已授权的终端里跑
- **现象**：从 Trae CN（IDE）里经 Claude Code 跑 `python -m whisper_dictation.app`，pynput listener `running=True` 但 **0 事件**；按热键无反应。
- **根因**：macOS TCC 权限按"责任进程"判定。授给主 app（`cn.trae.app`）的 辅助功能/输入监听 **不覆盖** 其 Helper 子进程（`cn.trae.app.helper`），而 python 实际跑在 Helper 下；且 miniconda 的 python 是未签名二进制，更难授权。
- **修复**：用**独立签名终端**（Terminal.app / iTerm）跑，授给它三项权限，重启后生效。责任进程 = 终端 app，授权可靠。
- **预防规则**：涉及全局键鼠监听/CGEvent 的 macOS 工具，永远从已授权的**独立终端**或打包成 **.app** 运行，别指望从 IDE/插件进程内继承权限。
- **诊断方法**：跑 10s pynput Listener 打印每个按键；若 `running=True` 但 0 输出 → 权限没到责任进程。

### 6. fn 键 pynput 收不到；cmd+space 与 Spotlight 冲突
- **现象**：`fn+space` 不可行（`pynput.keyboard.Key` 无 fn 成员，fn 被系统底层拦截）。`cmd+space` 被 Spotlight 抢走。
- **修复**：改用 `control+f5`（pynput 支持 f1-f20）。需在 系统设置→键盘→功能键 开启"将 F1、F2 等用作标准功能键"，否则顶排 F 键默认是多媒体键。
- **预防规则**：选全局热键前先 `pynput.keyboard.Key` 枚举确认键存在，并避开系统保留组合。

## 流程

- 从"用现成 app"转向"自研"（因 SuperWhisper 付费），决策应及时记进 spec，否则计划与现实脱节。
- subagent 抓到计划里的测试 bug 时停下问、而不是硬改——正确行为，应保留这种机制。

## 关键结论

- Apple Silicon 上 ASR 引擎选 **mlx-whisper**（M5 上整句 0.8s）。
- 国内模型分发走 **ModelScope** + 本地目录加载。
- CJK 文本键入：用"剪贴板 + Cmd+V"而非单键事件（Slice 2 待实现）。
