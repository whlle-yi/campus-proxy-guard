#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核心检测逻辑: 校园网判定 + 代理信号识别。"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

from .config import Config
from .netinfo import get_default_gateway, get_local_ips, get_wifi_ssid

logger = logging.getLogger(__name__)

SYSTEM_PROXY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"


# ---------------------------------------------------------------------------
# 校园网判定
# ---------------------------------------------------------------------------

def on_campus(cfg: Config, ssid: str | None = None, gateway: str | None = None,
              ips: list[str] | None = None) -> tuple[bool, str]:
    """判断当前是否处于校园网, 返回 (是否命中, 依据)。

    ssid/gateway/ips 可注入以便测试; 缺省时实时采集。
    """
    ssids = [s.lower() for s in cfg.campus_ssids]
    gw_prefixes = tuple(cfg.campus_gateway_prefixes)
    ip_prefixes = tuple(cfg.campus_local_ip_prefixes)

    if not (ssids or gw_prefixes or ip_prefixes):
        return True, "未配置校园网特征, 按任意网络均监测处理"

    if ssid is None:
        ssid = get_wifi_ssid()
    if ssid and ssids and any(s in ssid.lower() for s in ssids):
        return True, f"Wi-Fi SSID 命中: {ssid}"

    if gateway is None:
        gateway = get_default_gateway()
    if gateway and gw_prefixes and gateway.startswith(gw_prefixes):
        return True, f"默认网关命中: {gateway}"

    if ips is None:
        ips = get_local_ips()
    for ip in ips:
        if ip_prefixes and ip.startswith(ip_prefixes):
            return True, f"本机 IP 命中: {ip}"

    return False, ""


# ---------------------------------------------------------------------------
# 代理识别
# ---------------------------------------------------------------------------

def match_proc(stem: str, keywords: list[str]) -> bool:
    """进程名匹配: 按非字母数字分词后做全等/前缀匹配。

    避免 NisSrv(含 'ssr') 这类子串误报, 同时兼容 clash-verge / v2rayn 等连写名。
    """
    tokens = [t for t in re.split(r"[^a-z0-9]+", stem.lower()) if t]
    candidates = set(tokens) | {"-".join(tokens)}
    return any(c == k or c.startswith(k) for k in keywords for c in candidates)


def check_system_proxy() -> list[str]:
    """检查 Windows 系统代理与 PAC 自动配置脚本。"""
    hits: list[str] = []
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, SYSTEM_PROXY_KEY) as k:
            enabled, _ = winreg.QueryValueEx(k, "ProxyEnable")
            if enabled:
                try:
                    server, _ = winreg.QueryValueEx(k, "ProxyServer")
                except FileNotFoundError:
                    server = "(未读取到地址)"
                hits.append(f"系统代理已开启: {server}")
            try:
                pac, _ = winreg.QueryValueEx(k, "AutoConfigURL")
                if pac:
                    hits.append(f"PAC 自动配置脚本: {pac}")
            except FileNotFoundError:
                pass
    except OSError:
        pass
    return hits


def check_env_proxy() -> list[str]:
    hits = []
    for name in ("http_proxy", "https_proxy", "all_proxy",
                 "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        val = os.environ.get(name)
        if val:
            hits.append(f"环境变量 {name}={val}")
    return hits


def check_processes(cfg: Config) -> list[str]:
    if not psutil:
        return []
    keywords = [k.lower() for k in cfg.proxy_process_names]
    hits, seen = [], set()
    for p in psutil.process_iter(["name"]):
        try:
            name = (p.info["name"] or "").lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if match_proc(Path(name).stem, keywords) and name not in seen:
            seen.add(name)
            hits.append(f"代理进程: {p.info['name']} (PID {p.pid})")
    return hits


def _is_local_listen(ip: str, port: int, status: str, targets: set[int]) -> bool:
    """纯函数: 判定一个连接是否算代理监听端口, 便于测试。"""
    return (status == psutil.CONN_LISTEN
            and port in targets
            and ip in ("127.0.0.1", "0.0.0.0", "::1", "::"))


def check_ports(cfg: Config) -> list[str]:
    if not psutil:
        return []
    targets = set(cfg.proxy_ports)
    hits: list[str] = []
    seen: set[tuple[int, int | None]] = set()
    try:
        conns = psutil.net_connections(kind="inet")
    except (psutil.AccessDenied, OSError) as e:
        logger.debug("端口扫描失败: %s", e)
        return []
    for c in conns:
        if c.laddr is None or not _is_local_listen(c.laddr.ip, c.laddr.port,
                                                   c.status, targets):
            continue
        key = (c.laddr.port, c.pid)
        if key in seen:
            continue
        seen.add(key)
        pname = "?"
        if c.pid:
            try:
                pname = psutil.Process(c.pid).name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pname = f"PID {c.pid}"
        hits.append(f"代理端口监听: :{c.laddr.port} ({pname})")
    return hits


def detect_proxy(cfg: Config) -> list[str]:
    """汇总所有代理信号, 返回命中列表。"""
    hits: list[str] = []
    if cfg.check_system_proxy:
        hits += check_system_proxy()
    if cfg.check_env_proxy:
        hits += check_env_proxy()
    if cfg.check_processes:
        hits += check_processes(cfg)
    if cfg.check_ports:
        hits += check_ports(cfg)
    return hits


def kill_proxy_processes(cfg: Config) -> tuple[list[str], list[str]]:
    """结束所有匹配的代理进程, 返回 (已结束, 失败原因列表)。"""
    if not psutil:
        return [], []
    keywords = [k.lower() for k in cfg.proxy_process_names]
    killed: list[str] = []
    failed: list[str] = []
    for p in psutil.process_iter(["name"]):
        try:
            name = p.info["name"] or ""
            if not match_proc(Path(name).stem, keywords):
                continue
            try:
                p.kill()
                p.wait(timeout=5)
                killed.append(f"{name} (PID {p.pid})")
            except psutil.AccessDenied:
                failed.append(f"{name} (PID {p.pid}): 权限不足, 请以管理员运行本程序")
            except psutil.TimeoutExpired:
                failed.append(f"{name} (PID {p.pid}): 结束超时")
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
    return killed, failed


def disable_system_proxy() -> None:
    """关闭 Windows 系统代理(ProxyEnable=0)并通知系统立即生效。"""
    import ctypes
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, SYSTEM_PROXY_KEY, 0,
                        winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, "ProxyEnable", 0, winreg.REG_DWORD, 0)
    # 通知 WinINet 设置已变更并刷新, 免重启浏览器
    internet_set_option = ctypes.windll.wininet.InternetSetOptionW
    internet_set_option(None, 39, None, 0)  # INTERNET_OPTION_SETTINGS_CHANGED
    internet_set_option(None, 37, None, 0)  # INTERNET_OPTION_REFRESH
