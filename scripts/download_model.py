"""从 ModelScope（国内可直连）下载 MLX 版 Whisper Large v3 Turbo 到本地目录。

为什么用 ModelScope：HuggingFace 在国内被墙，hf-mirror.com 又会重定向回
huggingface.co。ModelScope（魔搭，阿里）镜像了 mlx-community 的模型，可直连。
下载到本地目录后，mlx_whisper 检测到目录存在就跳过 HF hub，直接本地加载
（见 mlx_whisper/load_models.py: load_model 第一步判断 path.exists()）。

用法：
    source .venv/bin/activate   # 仅为了用 venv 的 python
    python scripts/download_model.py

默认下载到 models/whisper-large-v3-turbo/（已 .gitignore，不入库）。
"""
import sys
import urllib.request
from pathlib import Path

MODEL_ID = "mlx-community/whisper-large-v3-turbo"
DEST = Path(__file__).resolve().parent.parent / "models" / "whisper-large-v3-turbo"
FILES = ["config.json", "weights.safetensors"]
BASE = f"https://modelscope.cn/api/v1/models/{MODEL_ID}/repo?Revision=master&FilePath="


def _download(url: str, dest: Path) -> None:
    # 流式下载，避免 1.6GB 一次性读进内存；支持断点续传（HTTP Range）。
    mode = "ab" if dest.exists() else "wb"
    have = dest.stat().st_size if dest.exists() else 0
    req = urllib.request.Request(url)
    if have:
        req.add_header("Range", f"bytes={have}-")
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, mode) as f:
        while True:
            chunk = r.read(1024 * 1024)  # 1MB
            if not chunk:
                break
            f.write(chunk)
    print(f"  ✓ {dest.name} ({dest.stat().st_size} bytes)")


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    print(f"下载 {MODEL_ID} → {DEST}")
    for name in FILES:
        url = BASE + name
        dest = DEST / name
        print(f"  下载 {name} …")
        try:
            _download(url, dest)
        except Exception as e:
            print(f"  ✗ {name} 失败：{e}", file=sys.stderr)
            return 1
    print("完成。config.yaml 的 model 应指向：", DEST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
