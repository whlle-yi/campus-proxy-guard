# -*- coding: utf-8 -*-
"""配置加载/校验/保存单测。"""

import json

from campus_proxy_guard.config import Config, load_config, save_config


def write(tmp_path, data):
    p = tmp_path / "config.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


def test_defaults_when_missing(tmp_path):
    cfg = load_config(tmp_path / "nope.json")
    assert cfg == Config()
    assert not (tmp_path / "nope.json").exists()


def test_roundtrip(tmp_path):
    p = tmp_path / "config.json"
    cfg = Config()
    cfg.campus_ssids = ["jxufe-wifi"]
    cfg.check_interval_seconds = 5
    save_config(cfg, p)
    loaded = load_config(p)
    assert loaded.campus_ssids == ["jxufe-wifi"]
    assert loaded.check_interval_seconds == 5


def test_unknown_key_ignored(tmp_path):
    cfg = load_config(write(tmp_path, {"campus_ssids": ["x"], "evil_key": 1}))
    assert cfg.campus_ssids == ["x"]
    assert not hasattr(cfg, "evil_key")


def test_wrong_type_falls_back_to_default(tmp_path):
    cfg = load_config(write(tmp_path, {
        "check_interval_seconds": "ten",
        "auto_kill": "yes",
        "campus_ssids": "not-a-list",
    }))
    assert cfg.check_interval_seconds == Config().check_interval_seconds
    assert cfg.auto_kill is False
    assert cfg.campus_ssids == []


def test_zero_or_negative_int_rejected(tmp_path):
    cfg = load_config(write(tmp_path, {"check_interval_seconds": 0}))
    assert cfg.check_interval_seconds == Config().check_interval_seconds


def test_bool_is_not_int(tmp_path):
    # Python 里 bool 是 int 子类, 需显式拒绝
    cfg = load_config(write(tmp_path, {"check_interval_seconds": True}))
    assert cfg.check_interval_seconds == Config().check_interval_seconds


def test_valid_partial_overrides(tmp_path):
    cfg = load_config(write(tmp_path, {
        "campus_ssids": ["jxufe-wifi", "NB的631"],
        "popup_dialog": True,
        "check_interval_seconds": 30,
        "proxy_ports": [7890, 12345],
    }))
    assert cfg.campus_ssids == ["jxufe-wifi", "NB的631"]
    assert cfg.popup_dialog is True
    assert cfg.check_interval_seconds == 30
    assert cfg.proxy_ports == [7890, 12345]  # list[int] 字段同样可覆盖
    # 未提到的字段保持默认
    assert cfg.auto_kill is False


def test_corrupt_file_falls_back_to_defaults(tmp_path):
    p = tmp_path / "config.json"
    p.write_text("{not valid json", encoding="utf-8")
    assert load_config(p) == Config()
