from whisper_dictation.transcribe import transcribe


def test_transcribe_passes_language_and_returns_text(monkeypatch):
    captured = {}

    def fake_transcribe(audio, *, path_or_hf_repo, language, **kw):  # noqa: ARG001
        captured["lang"] = language
        captured["repo"] = path_or_hf_repo
        return {"text": "  你好世界。  "}

    import whisper_dictation.transcribe as T
    monkeypatch.setattr(T.mlx_whisper, "transcribe", fake_transcribe)

    text = transcribe(audio=__import__("numpy").zeros(16000, dtype="float32"),
                      model="mlx-community/whisper-large-v3-turbo", language="zh")
    assert text == "你好世界。"          # 去掉首尾空白
    assert captured["lang"] == "zh"
    assert captured["repo"].startswith("mlx-community/")


def test_transcribe_empty_audio_returns_empty(monkeypatch):
    import whisper_dictation.transcribe as T
    import numpy as np
    monkeypatch.setattr(T.mlx_whisper, "transcribe",
                        lambda *a, **k: {"text": ""})
    assert transcribe(np.zeros(0, dtype="float32"), "m", "zh") == ""
