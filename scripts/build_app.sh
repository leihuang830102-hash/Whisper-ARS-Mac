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

# 启动器脚本：进项目目录，用 venv python 跑 app，输出重定向到日志文件（.app 无终端）
cat > "$APP_DIR/Contents/MacOS/launch" <<LAUNCH
#!/bin/bash
# 薄壳启动器：由 .app 调用，指向项目 venv 运行听写服务。
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/opt/miniconda3/bin:\$PATH"
cd "$PROJECT_DIR" || exit 11
mkdir -p "\$(dirname "$LOG_FILE")"
exec "$VENV_PYTHON" -m whisper_dictation.app >> "$LOG_FILE" 2>&1
LAUNCH
chmod +x "$APP_DIR/Contents/MacOS/launch"

# ---- ad-hoc 签名（个人使用无需公证；签名后 TCC 权限才能稳定挂到 .app）----
echo "ad-hoc 签名…"
codesign --force --deep --sign - "$APP_DIR" >/dev/null 2>&1 || echo "⚠️ codesign 警告（可能影响权限，注意测试）"

echo
echo "✅ 完成：$APP_DIR"
echo
echo "下一步："
echo "  1. 在 Finder 里打开 $OUT_ROOT ，双击 $APP_NAME 。"
echo "  2. 系统设置 → 隐私与安全性，给 'Whisper Dictation' 授："
echo "     - 辅助功能  - 输入监听  - 麦克风（首次录音会弹窗）"
echo "  3. 日志：tail -f $LOG_FILE"
echo "  4. 退出：Dock 里右键 Whisper Dictation → 退出；或 pkill -f whisper_dictation.app"
