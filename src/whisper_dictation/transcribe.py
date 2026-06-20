"""mlx-whisper 封装：audio(float32,16k) → 干净文本。"""
import numpy as np
import mlx_whisper


def transcribe(audio: np.ndarray, model: str, language: str = "zh") -> str:
    """转写音频，返回去除首尾空白的文本。

    audio: float32 mono, 16kHz。
    model: mlx-whisper 模型（HF repo id，如 mlx-community/whisper-large-v3-turbo）。
    """
    if audio.size == 0:
        return ""
    result = mlx_whisper.transcribe(
        audio,
        path_or_hf_repo=model,
        language=language,
    )
    return (result.get("text") or "").strip()
