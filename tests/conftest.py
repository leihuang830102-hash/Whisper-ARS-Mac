"""共享测试夹具。"""
import numpy as np
import pytest


@pytest.fixture
def sample_rate() -> int:
    """mlx-whisper 期望 16kHz。"""
    return 16000


@pytest.fixture
def silence_audio(sample_rate):
    """1 秒静音音频（全零 float32），用于测试转写/录音接口形状。"""
    return np.zeros(sample_rate, dtype=np.float32)
