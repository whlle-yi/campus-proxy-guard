# -*- coding: utf-8 -*-
"""进程匹配与校园网判定单测。"""

import os

from campus_proxy_guard.config import Config
from campus_proxy_guard.detector import _is_local_listen, match_proc, on_campus


def make(**overrides) -> Config:
    cfg = Config()
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


class TestMatchProc:
    keywords = ["clash", "v2ray", "sing-box", "ssr", "trojan"]

    def test_positive_simple(self):
        assert match_proc("clash", self.keywords)

    def test_positive_hyphenated(self):
        assert match_proc("clash-verge", self.keywords)

    def test_positive_concat(self):
        assert match_proc("v2rayn", self.keywords)

    def test_positive_multi_token(self):
        assert match_proc("sing-box", self.keywords)

    def test_negative_nissrv(self):
        # NisSrv 含 "ssr" 子串, 分词后不应误报
        assert not match_proc("nissrv", self.keywords)

    def test_negative_unrelated(self):
        assert not match_proc("chrome", self.keywords)

    def test_negative_substring_inside_word(self):
        # "password" 含 "ssr"? 否, 但含 "sswo"; 用 "assr" 验证不分子串
        assert not match_proc("assr", self.keywords)


class TestOnCampus:
    cfg = make(campus_ssids=["jxufe-wifi", "NB的631"],
               campus_gateway_prefixes=["10."],
               campus_local_ip_prefixes=["10."])

    def test_ssid_hit(self):
        hit, why = on_campus(self.cfg, ssid="JXUFE-WiFi", gateway="192.168.1.1", ips=[])
        assert hit and "SSID" in why

    def test_gateway_hit(self):
        hit, why = on_campus(self.cfg, ssid="other", gateway="10.20.0.1", ips=[])
        assert hit and "网关" in why

    def test_local_ip_hit(self):
        hit, why = on_campus(self.cfg, ssid="other", gateway="192.168.1.1",
                             ips=["169.254.1.2", "10.30.5.6"])
        assert hit and "IP" in why

    def test_no_hit(self):
        hit, _ = on_campus(self.cfg, ssid="501", gateway="192.168.1.1",
                           ips=["192.168.1.7"])
        assert not hit

    def test_empty_config_matches_nothing(self):
        # 未配置特征 = 不监测(首次安装不应误报)
        hit, why = on_campus(make(), ssid="anything", gateway="1.2.3.4", ips=[])
        assert not hit and "未配置" in why


class TestIsLocalListen:
    def _targets(self):
        return {7890, 1080}

    def test_loopback_listen_hit(self):
        import psutil
        assert _is_local_listen("127.0.0.1", 7890, psutil.CONN_LISTEN, self._targets())

    def test_wildcard_listen_hit(self):
        import psutil
        assert _is_local_listen("0.0.0.0", 1080, psutil.CONN_LISTEN, self._targets())

    def test_established_ignored(self):
        import psutil
        assert not _is_local_listen("127.0.0.1", 7890, psutil.CONN_ESTABLISHED,
                                    self._targets())

    def test_unlisted_port_ignored(self):
        import psutil
        assert not _is_local_listen("127.0.0.1", 3389, psutil.CONN_LISTEN,
                                    self._targets())

    def test_lan_ip_ignored(self):
        import psutil
        assert not _is_local_listen("10.1.2.3", 7890, psutil.CONN_LISTEN,
                                    self._targets())


def test_env_proxy_detection(monkeypatch):
    from campus_proxy_guard.detector import check_env_proxy
    monkeypatch.setenv("http_proxy", "http://127.0.0.1:7890")
    monkeypatch.delenv("https_proxy", raising=False)
    hits = check_env_proxy()
    assert any("http_proxy" in h for h in hits)


def test_system_proxy_detection():
    """真实注册表环境: 未开系统代理时应返回空列表(不抛异常)。"""
    from campus_proxy_guard.detector import check_system_proxy
    if os.name != "nt":
        return
    assert isinstance(check_system_proxy(), list)


def test_on_campus_uses_live_network_when_not_injected():
    """不注入参数时走真实采集路径(仅验证不抛异常)。"""
    cfg = make(campus_ssids=["definitely-not-this-ssid"])
    hit, _ = on_campus(cfg)
    assert isinstance(hit, bool)


def test_match_proc_turkish_i_not_crash():
    assert isinstance(match_proc("naive", ["naive"]), bool)
