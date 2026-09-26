#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本机网络信息采集: Wi-Fi SSID / 默认网关 / 本机 IP。

解析函数(parse_ssid/parse_gateway)与命令执行分离, 便于单元测试。
"""

from __future__ import annotations

import re
import socket
import subprocess

try:
    import psutil
except ImportError:
    psutil = None


def _run_decode(cmd: list[str]) -> str | None:
    """运行命令并解码输出(中文 Windows 控制台工具输出 GBK, 需自动识别)。"""
    try:
        import sys
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        r = subprocess.run(cmd, capture_output=True, timeout=10,
                           creationflags=creationflags)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None
    for enc in ("utf-8", "gbk"):
        try:
            return r.stdout.decode(enc)
        except UnicodeDecodeError:
            continue
    return r.stdout.decode("utf-8", errors="replace")


def parse_ssid(netsh_output: str) -> str | None:
    """从 `netsh wlan show interfaces` 输出解析当前 SSID, 非 Wi-Fi 返回 None。"""
    m = re.search(r"^\s*SSID\s*:\s*(\S.*?)\s*$", netsh_output, re.MULTILINE)
    return m.group(1) if m else None


def parse_gateway(route_output: str) -> str | None:
    """从 `route print -4` 输出解析默认网关, 取跃点数最小的一条。"""
    best: tuple[str, int] | None = None
    for line in route_output.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[0] == "0.0.0.0" and parts[1] == "0.0.0.0":
            gw = parts[2]
            if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", gw) or gw == "0.0.0.0":
                continue
            try:
                metric = int(parts[4])
            except ValueError:
                metric = 1 << 30
            if best is None or metric < best[1]:
                best = (gw, metric)
    return best[0] if best else None


def get_wifi_ssid() -> str | None:
    out = _run_decode(["netsh", "wlan", "show", "interfaces"])
    return parse_ssid(out) if out else None


def get_default_gateway() -> str | None:
    out = _run_decode(["route", "print", "-4"])
    return parse_gateway(out) if out else None


def get_local_ips() -> list[str]:
    ips: list[str] = []
    if psutil:
        for addrs in psutil.net_if_addrs().values():
            for a in addrs:
                if a.family == socket.AF_INET and not a.address.startswith("127."):
                    ips.append(a.address)
    else:
        try:
            hostname = socket.gethostname()
            for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
                ip = info[4][0]
                if not ip.startswith("127.") and ip not in ips:
                    ips.append(ip)
        except OSError:
            pass
    return ips
