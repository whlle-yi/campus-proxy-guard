# -*- coding: utf-8 -*-
"""netinfo 解析函数单测, 样本取自中文 Windows 实际输出。"""

from campus_proxy_guard.netinfo import parse_gateway, parse_ssid

NETSH_ZH = """
                状态                   : 已连接
                SSID                   : jxufe-wifi
                BSSID                  : aa:bb:cc:dd:ee:ff
                接收速率(Mbps)          : 866.7
"""

NETSH_BLANK = """
                状态                   : 已断开
                SSID                   :
"""

ROUTE_ZH = """
===========================================================================
接口列表
 12...xx xx Intel(R) Wi-Fi 6 AX201 160MHz ...... 
  1...........................Software Loopback Interface 1
===========================================================================
IPv4 路由表
===========================================================================
活动路由:
网络目标        网络掩码          网关       接口   跃点数
          0.0.0.0          0.0.0.0     192.168.1.1    192.168.1.7     35
         10.11.12.0    255.255.255.0         在链路上      10.11.12.5     281
        127.0.0.0        255.0.0.0         在链路上         127.0.0.1    331
===========================================================================
永久路由:
  无
"""

ROUTE_MULTI_DEFAULT = """
活动路由:
网络目标        网络掩码          网关       接口   跃点数
          0.0.0.0          0.0.0.0      10.20.0.1      10.20.3.9     25
          0.0.0.0          0.0.0.0     172.30.1.1    172.30.1.44     10
          0.0.0.0          0.0.0.0         在链路上     169.254.9.36     15
"""


def test_parse_ssid_chinese_windows():
    assert parse_ssid(NETSH_ZH) == "jxufe-wifi"


def test_parse_ssid_ignores_bssid_line():
    # BSSID 行形如 "BSSID 1 : ..." 不应被当成 SSID
    text = NETSH_ZH.replace("SSID ", "BSSID 1                : fake\n                SSID ")
    assert parse_ssid(text) == "jxufe-wifi"


def test_parse_ssid_disconnected_returns_none():
    assert parse_ssid(NETSH_BLANK) is None


def test_parse_gateway_basic():
    assert parse_gateway(ROUTE_ZH) == "192.168.1.1"


def test_parse_gateway_prefers_lowest_metric():
    assert parse_gateway(ROUTE_MULTI_DEFAULT) == "172.30.1.1"


def test_parse_gateway_skips_onlink_and_zero():
    # 唯一合法网关是 10.20.0.1; "在链路上" 与 0.0.0.0 都要跳过
    text = """活动路由:
          0.0.0.0          0.0.0.0         在链路上     169.254.9.36      1
          0.0.0.0          0.0.0.0         0.0.0.0      192.168.1.7      1
          0.0.0.0          0.0.0.0      10.20.0.1      10.20.3.9     25
"""
    assert parse_gateway(text) == "10.20.0.1"


def test_parse_gateway_none_when_absent():
    assert parse_gateway("永久路由:\n  无\n") is None
