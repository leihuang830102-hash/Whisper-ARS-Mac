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


def test_should_transcribe_rejects_silence_and_short():
    import numpy as np
    from whisper_dictation.audio import should_transcribe
    sr = 16000
    # pure silence (1s) -> False
    assert should_transcribe(np.zeros(sr, dtype=np.float32), sr) is False
    # too short (<0.25s) -> False
    assert should_transcribe(np.ones(100, dtype=np.float32) * 0.1, sr) is False
    # real-ish signal (1s, rms high) -> True
    sig = (np.random.RandomState(0).randn(sr) * 0.1).astype(np.float32)
    assert should_transcribe(sig, sr) is True
