#!/bin/bash
# 把 whisper_dictation 打包成可双击的 macOS .app（薄壳：启动器指向项目 venv）。
#
# 为什么是薄壳而非 PyInstaller 全量打包：
#   - venv 含 torch+mlx（2GB+），全打包会得到 2-3GB 巨型 .app，且 mlx 原生库易打坏。
#   - 薄壳只有一个启动脚本，复用已装好的 venv，体积几 KB、稳定。
#   - 代价：.app 依赖项目目录存在（PROJECT_DIR 不能删/移动）。
#
# 输出位置默认 ~/Applications/WhisperDictation.app（用户级，与项目源码分离）。
# 用法： scripts/build_app.sh [输出目录]

set -euo pipefail

# ---- 配置（按实际环境）----
PROJECT_DIR="/Users/lei/AI_Projects/Whisper"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
APP_NAME="WhisperDictation"
BUNDLE_ID="local.whisper.dictation"
VERSION="0.1.0"
LOG_FILE="$HOME/Library/Logs/whisper_dictation.log"

OUT_ROOT="${1:-$HOME/Applications}"
APP_DIR="$OUT_ROOT/$APP_NAME.app"

# ---- 前置检查 ----
[ -x "$VENV_PYTHON" ] || { echo "✗ 找不到 venv python: $VENV_PYTHON"; exit 1; }
[ -d "$PROJECT_DIR/src/whisper_dictation" ] || { echo "✗ 找不到源码: $PROJECT_DIR/src/whisper_dictation"; exit 1; }

# ---- 组装 .app 包结构 ----
echo "构建 $APP_DIR …"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/Contents/MacOS"

# Info.plist：LSUIElement=false（显示 Dock 图标，方便右键退出；以后可改菜单栏常驻）
cat > "$APP_DIR/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Whisper Dictation</string>
  <key>CFBundleDisplayName</key><string>Whisper Dictation</string>
  <key>CFBundleIdentifier</key><string>${BUNDLE_ID}</string>
  <key>CFBundleVersion</key><string>${VERSION}</string>
  <key>CFBundleShortVersionString</key><string>${VERSION}</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleExecutable</key><string>launch</string>
  <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
  <key>NSMicrophoneUsageDescription</key><string>本地语音听写需要使用麦克风录音。</string>
  <key>LSMinimumSystemVersion</key><string>13.0</string>
</dict>
</plist>
PLIST

# 启动器脚本：双击 → 打开 Terminal 运行听写。
# 关键：复用 Terminal 已有的 麦克风/辅助功能/输入监听 权限，.app 自身无需授权、听写代码不改。
cat > "$APP_DIR/Contents/MacOS/launch" <<LAUNCH
#!/bin/bash
# .app 薄壳：只负责在 Terminal 里跑听写命令，然后自身退出。
# osascript 单引号串里用双引号包住 do script 的 shell 命令；\$PROJECT_DIR 已在构建时展开为字面路径。
osascript -e 'tell application "Terminal" to activate' \
          -e 'tell application "Terminal" to do script "cd $PROJECT_DIR && source .venv/bin/activate && exec python -m whisper_dictation.app"'
exit 0
LAUNCH
chmod +x "$APP_DIR/Contents/MacOS/launch"

# ---- ad-hoc 签名（让 .app 被 macOS 识别为合法 app；本 .app 不需 TCC 权限，签名仅求干净）----
echo "ad-hoc 签名…"
codesign --force --deep --sign - "$APP_DIR" >/dev/null 2>&1 || echo "⚠️ codesign 警告（不影响功能）"

echo
echo "✅ 完成：$APP_DIR"
echo
echo "下一步："
echo "  1. Finder 打开 $OUT_ROOT ，双击 $APP_NAME —— 会弹出一个 Terminal 窗口跑听写。"
echo "  2. 无需再授权（复用 Terminal 已有权限）。看到 '听写就绪…' 即可。"
echo "  3. 退出：那个 Terminal 窗口里 Ctrl-C，或 pkill -f whisper_dictation.app"
echo "  注意：项目目录不能移动/删除（.app 依赖它）。"
