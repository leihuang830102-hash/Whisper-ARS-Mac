# 本地语音识别系统设计（Whisper）

- 日期：2026-06-20
- 状态：设计已与用户确认，待评审
- 目标读者：未来实现该系统的自己 / subagent

## 1. 背景与目标

用户（开发者本人）希望在日常与 AI 智能体交流时，用说话代替打字：按下热键说话，松开后转写文字自动输入到当前光标所在处（任意 app）。

硬性约束：

- **全程本地运行，绝不使用 SaaS / 云端**（隐私优先）。
- 机器：Apple M5 / 24GB RAM / Metal 4，已装 Ollama（含 qwen3.5:9b、gemma4:26b， 如有必要可以安装其它模型）。
- 主力模型：**Whisper Large v3 Turbo**。
- 有成熟开源软件时优先用现成的，不够再自研。

## 2. 调研结论（本机 Whisper 引擎选型）

在 Apple Silicon 上，本机跑 Whisper 的引擎对比：

| 引擎 | Apple Silicon 表现 | 结论 |
|---|---|---|
| **mlx-whisper** | 最快（Apple MLX 原生，吃满统一内存） | 本机首选 |
| whisper.cpp | 稍慢（GGML/Metal） | 跨平台才考虑 |
| faster-whisper | CTranslate2，Mac 上不如 MLX | NVIDIA/Intel 才考虑 |

**推荐引擎：mlx-whisper + Whisper Large v3 Turbo（Q8 量化）**。这是 M 系列上目前最快的本地 ASR 路径，且正是用户想用的 V3 Turbo。

> 注意：Ollama 不跑 Whisper ASR，所以转写引擎独立于 Ollama。Ollama 只负责后处理阶段的 LLM 清理。

成熟开源/半开源 macOS 方案：SuperWhisper、MacWhisper（包装好的 app，覆盖热键+本地 Whisper+光标输入）。

## 3. 用户决策记录

经头脑风暴确认的关键决策：

1. **形态**：先调研+装现成的，不够再自己写（务实、分阶段）。
2. **触发模式**（两种均可配，运行时切换）：
   - **push-to-talk（按住说话）**：按住热键收音，松开结束并转写。
   - **toggle（开关式）**：按第一下开始收音，按第二下结束并转写。适合长段输入，手指不用一直按着。
   - 流式/持续听写（VAD 自动断句）放后期（Phase 4）。
3. **语言**：中文为主，偶尔英文术语（用初始 prompt 优化技术词识别）。
4. **后处理**：转写后过一道本地 LLM（Ollama qwen3.5）做清理（加标点、去口头禅、整理成干净句子），再喂给智能体。
5. **验收线**：实战中再调，不预设死值。

## 4. 总体架构（分阶段）

```
Phase 0  现成 app 验收（SuperWhisper/MacWhisper + 本地 Whisper V3 Turbo）
   │     验收点：①中文准确率 ②延迟 ③热键手感 ④能否外挂后处理
   ▼
Phase 1  按需：自研后处理管道（Ollama qwen3.5 清理 raw 文本）
   ▼
Phase 2  极端情况：完全自研（mlx-whisper + 热键 + VAD + 键入）
   ▼
────── 以上是"语音→文字"核心闭环 ──────
   ▼
Phase 3  ASR 生态扩展功能调研（见 §7）
   ▼
Phase 4  自然语言语音对话（见 §8）
```

核心设计原则：**分阶段、每阶段有明确的"达标才继续"门槛**，YAGNI，避免一上来过度工程。

## 5. Phase 0：现成 app 验收

### 5.1 动作

安装 SuperWhisper（或 MacWhisper），配置：

- 模型：本地 Whisper Large v3 Turbo。
- 触发：全局热键，**push-to-talk 与 toggle 两种模式均可配**（见 §3 决策 2）。
- 输出：键入到当前光标处。

### 5.2 验收标准（达标线实战再调，先给初值）

| 验收项 | 初步达标线 | 测试方法 |
|---|---|---|
| 中文准确率 | 日常技术对话 ≥ 90% | 录 10 段不同场景，人工校对错字率 |
| 端到端延迟 | 松开热键到文字出现 ≤ 3 秒 | 时间戳测 |
| 热键手感 | 全局可用、不与常用 app 冲突、单手可按 | VS Code / 浏览器 / 终端各试 5 次 |
| **外挂后处理可行性** | app 能暴露 raw 文本（剪贴板/文件/webhook/命令） | 查 app 文档是否有 post-processing 钩子或剪贴板模式 |
| 隐私 | 全程本地，无云端上传 | 抓包或确认 offline 设置 |

### 5.3 关键决策点

前 3 项预期达标。**真正决定要不要进 Phase 1 的是第 4 项**：若 app 不允许在"转写"和"键入"之间插一脚做后处理，则"过 Ollama 清理"无法实现，需进 Phase 1（外挂管道）或 Phase 2（完全自研）。

## 6. Phase 1：自研后处理管道（按需）

仅当 Phase 0 转写/热键达标、但后处理不能挂时启动。

### 6.1 数据流

```
app 输出 raw 文本
   ▼
[监听层] 剪贴板轮询 / 文件 watch / webhook
   ▼
[清理层] Ollama qwen3.5:9b，prompt：加标点、去口头禅、整理成一句干净中文
   ▼
[输出层] 写回光标处（CGEvent 模拟键入）/ 喂给智能体
```

### 6.2 边界

- 监听层、清理层、输出层各自独立，接口清晰，可单独测试。
- 清理层 prompt 可热替换，不绑定具体 LLM。
- 预估代码量 ~50-150 行脚本。

## 7. Phase 3：ASR 生态扩展功能调研（后期）

目标：调研现有 ASR 软件（SuperWhisper / Whispering / MacWhisper / NVIDIA Parakeet / Assemblyline 等）有哪些额外能力，整理成"功能菜单"，挑需要的纳入本系统。候选功能（非预设，调研后筛选）：

- 多语言自动切换
- 说话人区分（diarization）
- 语音命令/动作触发（说"换行""删除"执行操作）
- 转写历史与检索
- 实时字幕 / 翻译
- 与特定 app 深度集成（VS Code、浏览器）

**产出**：一份功能调研报告 + 选定纳入本系统的功能清单。

## 8. Phase 4：自然语言语音对话（后期）

从"我说你转文字"升级到"像打电话一样双向对话"。需要：

- 流式 ASR：VAD 自动断句，不再按键。
- 流式 TTS：智能体回复用语音播报。
- 本地 LLM（Ollama qwen3.5/gemma）做对话大脑。
- 低延迟回合切换、打断（barge-in）支持。

本质是搭一个本地全双工语音 agent，复用 Phase 0-3 的 ASR 能力。

## 9. 环境与依赖备忘

- macOS 权限（Phase 1/2 自研时需要）：
  - 麦克风访问（TCC）
  - 辅助功能（Accessibility，用于全局热键 + 模拟键入）
  - 输入监听（Input Monitoring，若用键盘事件钩子）
- Ollama 已就绪，后处理直接调用 `ollama run qwen3.5:9b`。
- 引擎（Phase 2 才需要安装）：`mlx-whisper` + Turbo Q8 模型权重。

## 10. 本阶段（Phase 0）范围与非范围

**范围（下一步要做的）**：
- 安装并配置 SuperWhisper / MacWhisper。
- 按 §5.2 跑验收测试。
- 判定是否进 Phase 1。

**非范围（明确不做）**：
- 自研任何代码（除非 Phase 0 不达标）。
- Phase 3 功能调研、Phase 4 语音对话。

## 11. 成功标准（Phase 0）

用户能在一个工作日内：装好 app → 配好本地 Turbo → 在 VS Code/终端/浏览器里按热键说话 → 文字以可接受延迟和准确率出现在光标处 → 并知道下一步该不该进 Phase 1。
