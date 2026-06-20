# 候选 App 选型

调研日期：2026-06-20

| 能力 | SuperWhisper | MacWhisper | 来源 |
|---|---|---|---|
| 本地 Whisper V3 Turbo | 支持。基于 whisper.cpp 在 Apple Silicon 上运行 large-v3-turbo，pro tier 提供 "Ultra V3 Turbo" 本地档；社区与官方均将其列为最佳本地 Whisper 模型。 | 支持。基于 whisper.cpp 本地运行，可下载 large/large-v3 模型（官网 App Store 说明支持 on-device/offline 模型下载）。 | [superwhisper.com](https://superwhisper.com/)；[getvoibe.com](https://www.getvoibe.com/resources/best-local-whisper-model-superwhisper/)；[macwhisper.helpscoutdocs.com](https://macwhisper.helpscoutdocs.com/article/52-keeping-transcriptions-private) |
| push-to-talk + toggle 双模式 | 支持。官网 "What's inside" 列出 "Push to talk"（Hold, speak, release，标 New）与 toggle 式 ⌥+space 启动听写。 | 支持 toggle 式：Dictation 模式在 Settings > Dictation 配置快捷键，按下即可在任意文本框听写。未明确宣传 press-and-hold push-to-talk，主要面向 toggle/快捷键触发。 | [superwhisper.com](https://superwhisper.com/)；[macwhisper.helpscoutdocs.com](https://macwhisper.helpscoutdocs.com/article/14-how-to-use-the-dictation-feature) |
| 键入到光标处 | 支持。Clipboard integration 与 "Works anywhere you can type" 直接将处理后文本输入到 Slack/Cursor/Notion 等任意应用光标处。 | 支持。Dictation 功能明确说明可将音频转写文本直接键入任意文本字段（type by speaking to your Mac）。 | [superwhisper.com](https://superwhisper.com/)；[macwhisper.helpscoutdocs.com](https://macwhisper.helpscoutdocs.com/article/14-how-to-use-the-dictation-feature) |
| 离线运行（无云端） | 支持。官网 "Duh, yes online too — Works offline"；FAQ 也说明离线模型仅在 Apple Silicon 上运行良好，V3 Turbo 全本地。 | 支持。所有转写模型本地下载运行，无云端上传。 | [superwhisper.com](https://superwhisper.com/)；[macwhisper.helpscoutdocs.com](https://macwhisper.helpscoutdocs.com/article/52-keeping-transcriptions-private) |
| 后处理可外挂（命令/剪贴板/webhook/内置本地 LLM 接 Ollama） | 支持且可配置：内置 "Custom Mode" 允许编写任意 AI Instructions；Models 面板支持 "+ Custom Model" 填写自定义 endpoint + API key，可指向 Ollama 的 OpenAI 兼容端点 `http://localhost:11434`（社区 r/superwhisper + YouTube 教程验证可用）。此外 Context Awareness 支持 Clipboard/Selected Text/Application Context 注入。无原生 shell/webhook 钩子，但通过自定义本地 LLM 端点已满足"外挂后处理"需求。 | 部分支持：Dictation 内置 "AI Dictation" 允许自定义 prompt（清理/翻译/扩写）并支持 App-Specific Prompts，但官方文档明确要求 OpenAI API key，"Support for Anthropic and other AI providers will be added soon"——目前不支持自定义本地 LLM 端点（如 Ollama）。无 shell/webhook 钩子。 | [superwhisper.com/docs/modes/custom](https://superwhisper.com/docs/modes/custom)；[superwhisper.com/docs/enterprise/models](https://superwhisper.com/docs/enterprise/models)；[reddit.com/r/superwhisper](https://www.reddit.com/r/superwhisper/comments/1sn1m5b/)；[ollama.com/blog/openai-compatibility](https://ollama.com/blog/openai-compatibility)；[macwhisper.helpscoutdocs.com](https://macwhisper.helpscoutdocs.com/article/14-how-to-use-the-dictation-feature) |

## 详细说明

**SuperWhisper**
- 安装：`brew install --cask superwhisper`（cask 已验证存在，版本 2.16.1，auto_updates，要求 macOS >= 13）。
- 收费/开源：闭源，订阅制 Free / Pro（$8.49/月，学生 6 折）/ Yearly / Lifetime；Pro 解锁自定义 API key、本地大模型、翻译、文件转写。Free 档可永久使用小模型 + 听写。
- 中文支持：宣称 100+ 语言；whisper.cpp large-v3-turbo 中文识别质量好；Vocabulary 自定义词条可纠正专有名词/术语。
- 后处理机制细节：核心是 "Modes" 体系。Custom Mode 允许写完整 AI Instructions（支持 XML 标签结构化 prompt、Few-shot 示例、Context Awareness 注入 Clipboard/Selected Text/Application Context）。Language Models 面板的 "+ Custom Model" 可选 provider 下拉的 "Custom"，填自定义 base URL + key —— 指向本地 Ollama `http://localhost:11434/v1`（OpenAI 兼容），即可让任意本地 LLM（如 qwen、llama3）对原始转写做润色/纠错/术语规范化。这是无需任何代码改动、纯 UI 配置即可把本地 LLM 接入后处理链路的最干净方案。注意：社区反馈部分弱本地模型会原样输出，需选用指令跟随能力强的模型。

**MacWhisper**
- 安装：`brew install --cask macwhisper`（cask 已验证存在，版本 13.22.0,1432，auto_updates，要求 macOS >= 14）。注意 Dictation 功能仅 www.macwhisper.com 直购版可用，App Store 版因沙盒限制不含 Dictation——brew cask 版应来自官网发行。
- 收费/开源：闭源，独立开发者 Jordi Bruin（Goodsnooze），一次性买断（Pro 约 $30），无订阅。
- 中文支持：whisper.cpp large 模型中文识别良好，原生多语言。
- 后处理机制细节：Dictation 模式内置 "AI Dictation"，可在 Settings > Dictation 创建自定义 prompt（清理语法、翻译、扩写），并支持 App-Specific Prompts（按当前应用切换不同 prompt）。但官方文档明确：该功能当前**只支持 OpenAI API key**，且 "Support for Anthropic and other AI providers will be added soon"——尚无法指向 Ollama 等本地 LLM 端点，也无法跑 shell/webhook。因此"后处理外挂本地 LLM"在 MacWhisper 上目前不可行，只能靠 OpenAI 云端或先用 Dictation 键入后再手工调用 Ollama 二次处理。

## 选定：SuperWhisper

## 理由：SuperWhisper 的 Custom Mode + "+ Custom Model" 可直接将本地 Ollama 的 OpenAI 兼容端点配置为后处理 LLM，实现"原始转写 → 本地 LLM 润色/术语纠正 → 键入光标"的纯本地闭环；而 MacWhisper 的 AI 后处理当前仅绑定 OpenAI API key，不支持自定义本地端点，无法满足"完全本地、后处理可外挂"的决定性指标。

## 安装命令
brew install --cask superwhisper
