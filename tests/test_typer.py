from whisper_dictation.typer import type_text


def test_type_text_writes_clipboard_and_pastes(monkeypatch):
    calls = []

    class FakePasteboard:
        def clearContents(self): calls.append("clear")
        def setString_forType_(self, s, t): calls.append(("set", s, t))

    def fake_post_key(mods_flags, key_code, down):
        calls.append(("post", mods_flags, key_code, down))

    import whisper_dictation.typer as Ty
    monkeypatch.setattr(Ty, "_new_pasteboard", lambda: FakePasteboard())
    monkeypatch.setattr(Ty, "_post_key", fake_post_key)

    type_text("你好")

    assert ("set", "你好", "public.utf8-plain-text") in calls
    # should be one cmd-down on V, then one V release without cmd flag
    posts = [c for c in calls if isinstance(c, tuple) and c[0] == "post"]
    assert any(p[2] == 9 and p[3] is True and p[1] != 0 for p in posts)   # V key-down WITH cmd flag
    assert any(p[2] == 9 and p[3] is False for p in posts)                # V key-up


def test_type_text_empty_does_nothing(monkeypatch):
    calls = []
    import whisper_dictation.typer as Ty

    class FakePB:
        def clearContents(self): calls.append("clear")
        def setString_forType_(self, s, t): calls.append(("set", s, t))
    monkeypatch.setattr(Ty, "_new_pasteboard", lambda: FakePB())
    monkeypatch.setattr(Ty, "_post_key", lambda *a: calls.append("post"))
    type_text("")
    assert calls == []
