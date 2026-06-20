# Phase A 验收记录（自研 MVP）

日期：2026-06-20
状态：✅ 通过，端到端可用

## 验收结果

| 验收项 | 结果 |
|---|---|
| 本地 Whisper V3 Turbo（mlx-whisper） | ✅ 离线加载，0.8s/句 |
| 全局热键触发（pynput） | ✅ `ctrl+shift+space` |
| push-to-talk 模式 | ✅ |
| 中文整句准确率 | ✅ 极高（"帮我把这个函数重构一下"等 100% 正确） |
| 英文识别 | ✅（"It's a terrific application" 等） |
| 键入光标处（剪贴板 + Cmd+V） | ✅ 真实文本框中只出现一次，无重复 |
| 静音/过短忽略 | ✅（避免幻觉） |
| 全程本地 / 无云端 / 无订阅 | ✅ |

## 实测样本（用户口述）
- "希望这次能够一次成功" ✅
- "今天的天气真不错我应该出去走走" ✅
- "It's a terrific application, Thank you" ✅
- "Sounds like you repeat twice the same sentence" ✅

用户最终用该工具在与 AI 的对话框里实时听写交流 —— 即真实使用场景验收通过。

## 过程中解决的问题
1. HuggingFace 国内被墙、hf-mirror 重定向回源 → 改走 **ModelScope** + 本地目录加载。
2. 系统 python3=3.9 → venv 用 miniconda 3.13。
3. `fn` 键 pynput 收不到；`cmd+space` 与 Spotlight 冲突；`F5` 是多媒体键（keyCode 176）→ 改用 `ctrl+shift+space`。
4. pynput 在 IDE 内 0 事件（TCC 责任进程 = Helper，非主 app）→ 改用**独立 Terminal** 跑。
5. `event.setFlags` pyobjc 不存在 → `Quartz.CGEventSetFlags`。
6. audio 测试 mock 方法名错（`get`→`read`）。
7. `_start` 防重入 guard 用错字段（`is_recording`→`_stream`）。
8. Whisper 静音幻觉 → 加 `should_transcribe` 能量守卫。

详见 [LESSONS_LEARNED.md](../LESSONS_LEARNED.md)。

## 结论
Phase A（自研 MVP）完成，满足核心目标：**本地、零云、热键说话→光标处出字**。
Phase B（LLM 后处理）暂不需要——原始 Turbo 整句质量已足够。
