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
2. 依次进入「麦克风」「辅助功能」「输入监听」，把**你实际跑 `python` 的那个程序**打勾。
   - ⚠️ 注意：`python -m whisper_dictation.app` 里的 `whisper_dictation.app` 是 **Python 模块路径**，不是要授权的对象。要授权的是**宿主程序**：在 VS Code 终端跑→给 `Visual Studio Code`；在 Trae CN 跑→给 `Trae CN`；Terminal→`Terminal`；iTerm→`iTerm`。
   - 判断方法：`echo $__CFBundleIdentifier`（如 `cn.trae.app` 即 Trae CN）。
3. **完全退出该程序再重开**（权限变更对已运行进程不生效——重启终端面板不够，要重启整个宿主 app）。

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
