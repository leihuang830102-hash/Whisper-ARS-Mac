import pytest
from whisper_dictation.config import load_config, parse_hotkey


def test_parse_hotkey_cmd_space():
    mods, key = parse_hotkey("cmd+space")
    assert "cmd" in mods
    assert key == "space"


def test_parse_hotkey_option_with_letter():
    mods, key = parse_hotkey("option+j")
    assert mods == ["option"]
    assert key == "j"


def test_load_config_defaults(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        "mode: ptt\nhotkey: cmd+space\nmodel: mlx-community/whisper-large-v3-turbo\nlanguage: zh\n"
    )
    cfg = load_config(str(cfg_file))
    assert cfg.mode == "ptt"
    assert cfg.language == "zh"
    assert cfg.model.startswith("mlx-community/")
