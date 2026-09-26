# -*- coding: utf-8 -*-
"""违规处置动作(apply_actions)单测, 全部 mock, 不触碰真实系统。"""

from campus_proxy_guard import notifier
from campus_proxy_guard.config import Config


def make(**overrides) -> Config:
    cfg = Config()
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


def test_no_actions_configured(monkeypatch):
    called = {"disable": 0, "kill": 0}
    monkeypatch.setattr("campus_proxy_guard.detector.disable_system_proxy",
                        lambda: called.__setitem__("disable", 1))
    monkeypatch.setattr("campus_proxy_guard.detector.kill_proxy_processes",
                        lambda cfg: (called.__setitem__("kill", 1), [])[:2])
    taken = notifier.apply_actions(make())
    assert taken == []
    assert called == {"disable": 0, "kill": 0}


def test_disable_system_proxy_action(monkeypatch):
    calls = []
    monkeypatch.setattr("campus_proxy_guard.detector.disable_system_proxy",
                        lambda: calls.append(1))
    taken = notifier.apply_actions(make(auto_disable_system_proxy=True))
    assert calls == [1]
    assert any("系统代理" in t for t in taken)


def test_kill_action_reports_killed_and_failed(monkeypatch):
    monkeypatch.setattr("campus_proxy_guard.detector.kill_proxy_processes",
                        lambda cfg: (["clash.exe (PID 1)", "v2ray.exe (PID 2)"],
                                     ["svc.exe (PID 3): 权限不足"]))
    taken = notifier.apply_actions(make(auto_kill=True))
    assert any("clash.exe" in t for t in taken)
    assert any("v2ray.exe" in t for t in taken)
    assert any("权限不足" in t for t in taken)


def test_disable_failure_recorded(monkeypatch):
    def boom():
        raise OSError("denied")

    monkeypatch.setattr("campus_proxy_guard.detector.disable_system_proxy", boom)
    taken = notifier.apply_actions(make(auto_disable_system_proxy=True))
    assert any("失败" in t for t in taken)


def test_actions_combined(monkeypatch):
    monkeypatch.setattr("campus_proxy_guard.detector.disable_system_proxy", lambda: None)
    monkeypatch.setattr("campus_proxy_guard.detector.kill_proxy_processes",
                        lambda cfg: (["x.exe (PID 9)"], []))
    taken = notifier.apply_actions(
        make(auto_disable_system_proxy=True, auto_kill=True))
    assert len(taken) == 2


def test_warn_includes_actions_in_body(monkeypatch):
    seen = {}
    monkeypatch.setattr("campus_proxy_guard.detector.disable_system_proxy", lambda: None)
    monkeypatch.setattr(notifier, "send_toast", lambda t, b, app_id="": seen.update(body=b) or True)
    cfg = make(popup_dialog=False, auto_disable_system_proxy=True)
    notifier.warn(["系统代理已开启: 127.0.0.1:7890"], cfg)
    assert "已采取措施" in seen["body"]
