"""冒烟测试：录 3 秒 → 用真实 Turbo 模型转写 → 打印结果。

用途：确认 mlx-whisper + Turbo 在本机能跑、中文识别可用。
模型需先用 scripts/download_model.py 从 ModelScope 下到本地 models/whisper-large-v3-turbo/
（HuggingFace 在国内被墙，走 ModelScope 镜像）。

运行（在仓库根目录）：
    source .venv/bin/activate
    python scripts/smoke_transcribe.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from whisper_dictation.audio import record_seconds  # noqa: E402
from whisper_dictation.transcribe import transcribe  # noqa: E402

MODEL = str(Path(__file__).resolve().parent.parent / "models" / "whisper-large-v3-turbo")


def main():
    sr = 16000
    print("准备录音 3 秒，请说话…", flush=True)
    audio = record_seconds(seconds=3, sample_rate=sr)
    print("转写中…", flush=True)
    text = transcribe(audio, model=MODEL, language="zh")
    print(f"结果：{text!r}")


if __name__ == "__main__":
    main()
