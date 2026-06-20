from pynput import keyboard

from whisper_dictation.hotkey import Mode, ModeMachine, _target_key_for


def test_ptt_press_starts_release_stops():
    m = ModeMachine(Mode.PTT)
    assert m.on_press() == "start"     # 按下 → 开始录音
    assert m.is_recording
    assert m.on_release() == "stop"    # 松开 → 停止并转写
    assert not m.is_recording


def test_toggle_first_press_starts_second_press_stops():
    m = ModeMachine(Mode.TOGGLE)
    assert m.on_press() == "start"
    assert m.is_recording
    assert m.on_press() == "stop"      # 再按一次 → 停止
    assert not m.is_recording


def test_toggle_release_is_noop():
    m = ModeMachine(Mode.TOGGLE)
    assert m.on_press() == "start"
    assert m.on_release() == "noop"    # toggle 模式下松开无动作
    assert m.is_recording


def test_target_key_for_f5():
    assert _target_key_for("f5") == keyboard.Key.f5


def test_target_key_for_letter_and_space():
    assert _target_key_for("j") == keyboard.KeyCode.from_char("j")
    assert _target_key_for("space") == keyboard.Key.space
