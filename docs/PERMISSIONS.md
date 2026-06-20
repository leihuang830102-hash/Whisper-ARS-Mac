# macOS 权限配置

本工具常驻运行、要全局热键和模拟键入，需三项系统权限。
**路径：系统设置 → 隐私与安全性**。

| 权限 | 用途 | 加谁 |
|---|---|---|
| **麦克风** | 录音 | 你跑脚本的终端（Terminal / iTerm / VS Code 集成终端） |
| **辅助功能（Accessibility）** | pynput 全局热键监听 + CGEvent 模拟 Cmd+V 键入 | 同上 |
| **输入监听（Input Monitoring）** | pynput 监听键盘事件 | 同上 |

## 操作步骤
1. 打开 系统设置 → 隐私与安全性。
2. 依次进入「麦克风」「辅助功能」「输入监听」，把你用来运行 `python` 的终端 app 打勾（点 `+` 添加）。
3. **重启该终端**（权限变更对已运行进程不生效，必须重启进程）。

## 为什么必须授权
- 不授麦克风 → `sounddevice` 打不开输入流，录音失败。
- 不授辅助功能 → pynput 收不到全局按键、CGEvent 模拟的 Cmd+V 无效。
- 不授输入监听 → pynput 监听器拿不到事件。

## 验证授权是否生效
重启终端后，在仓库根目录：
```bash
source .venv/bin/activate
python -m whisper_dictation.app
```
看到 `听写就绪：mode=ptt hotkey=cmd+space …` 后，切到任意文本框，按 `Cmd+Space` 说一句话，松开 → 文字应出现在光标处。

若按热键无反应 → 多半是辅助功能/输入监听没授或没重启终端。
若按了但没出字 → 检查辅助功能（Cmd+V 模拟键入需要它）。
