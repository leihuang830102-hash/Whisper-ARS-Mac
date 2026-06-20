"""配置加载与热键描述解析。"""
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# 允许的修饰键别名 → 标准名
_MOD_ALIASES = {
    "cmd": "cmd", "command": "cmd", "⌘": "cmd",
    "ctrl": "ctrl", "control": "ctrl", "⌃": "ctrl",
    "option": "option", "alt": "option", "opt": "option", "⌥": "option",
    "shift": "shift", "⇧": "shift",
}


@dataclass
class Config:
    """运行时配置。"""
    mode: str = "ptt"                       # "ptt" | "toggle"
    hotkey: str = "cmd+space"
    model: str = "mlx-community/whisper-large-v3-turbo"
    language: str = "zh"                    # 传给 mlx-whisper 的 language 参数
    sample_rate: int = 16000
    silence_threshold: float = 0.01         # 预留：toggle 未来自动停用
    record_dir: str = ""                    # 调试用：保存录音目录，空=不存


def parse_hotkey(desc: str) -> tuple[list[str], str]:
    """'cmd+space' → (['cmd'], 'space')。末段为按键，前面为修饰键。"""
    parts = [p.strip().lower() for p in desc.split("+")]
    if not parts:
        raise ValueError(f"empty hotkey: {desc!r}")
    mods = [_MOD_ALIASES[p] for p in parts[:-1] if p in _MOD_ALIASES]
    key = parts[-1]
    return mods, key


def load_config(path: str) -> Config:
    """从 yaml 加载配置，缺失项用 Config 默认值补齐。"""
    data = yaml.safe_load(Path(path).read_text()) or {}
    return Config(**{k: v for k, v in data.items() if k in Config.__dataclass_fields__})
