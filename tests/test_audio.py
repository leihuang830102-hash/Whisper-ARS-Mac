import numpy as np
from whisper_dictation.audio import record_seconds


def test_record_returns_float32_mono(monkeypatch):
    """record_seconds 应返回 (N, sample_rate*seconds) 形状的 float32 mono。"""
    sr = 16000
    seconds = 1
    fake = np.zeros(sr * seconds, dtype=np.float32)

    class FakeSD:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def stop(self): pass
        def read(self, n):
            return fake, False  # 模拟 sounddevice.InputStream.read 的 (data, overflowed)

    import whisper_dictation.audio as A
    monkeypatch.setattr(A.sd, "InputStream", lambda *a, **k: FakeSD())
    out = record_seconds(seconds=seconds, sample_rate=sr)
    assert out.dtype == np.float32
    assert out.ndim == 1
    assert len(out) == sr * seconds
