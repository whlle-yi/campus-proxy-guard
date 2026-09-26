#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日志与用户警告: 轮转日志 / Windows Toast / 置顶对话框。"""

from __future__ import annotations

import base64
import ctypes
import logging
import logging.handlers
import subprocess
import sys

from .config import Config, log_dir

logger = logging.getLogger(__name__)

PS_TOAST_TEMPLATE = r"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$texts = $xml.GetElementsByTagName('text')
$texts.Item(0).AppendChild($xml.CreateTextNode('{title}')) | Out-Null
$texts.Item(1).AppendChild($xml.CreateTextNode('{body}')) | Out-Null
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{appid}').Show($toast)
"""


def setup_logging(verbose: bool = False) -> None:
    """轮转文件日志(1MB x 3) + 控制台输出; 所有模块共用。"""
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    try:
        log_dir().mkdir(parents=True, exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(
            log_dir() / "guard.log", maxBytes=1_000_000, backupCount=3,
            encoding="utf-8")
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except OSError as e:
        root.warning("日志文件不可用, 仅输出到控制台: %s", e)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    sh.setLevel(logging.DEBUG if verbose else logging.INFO)
    root.addHandler(sh)


def send_toast(title: str, body: str, app_id: str = "campus-proxy-guard") -> bool:
    """通过 PowerShell 发送 Windows 通知, 失败返回 False(调用方回退对话框)。"""
    if sys.platform != "win32":
        return False
    ps = (PS_TOAST_TEMPLATE.replace("{title}", title)
                          .replace("{body}", body)
                          .replace("{appid}", app_id))
    encoded = base64.b64encode(ps.encode("utf-16-le")).decode("ascii")
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-EncodedCommand", encoded],
            capture_output=True, timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW)
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired) as e:
        logger.debug("toast 发送异常: %s", e)
        return False


def send_messagebox(title: str, body: str) -> None:
    """阻塞式置顶警告对话框。"""
    if sys.platform != "win32":
        return
    flags = 0x00000040 | 0x00040000 | 0x00010000  # MB_ICONWARNING | TOPMOST | SETFOREGROUND
    ctypes.windll.user32.MessageBoxW(0, body, title, flags)


def apply_actions(cfg: Config) -> list[str]:
    """执行已启用的违规处置动作, 返回结果描述列表(写入警告与日志)。"""
    from .detector import disable_system_proxy, kill_proxy_processes
    taken: list[str] = []
    if cfg.auto_disable_system_proxy:
        try:
            disable_system_proxy()
            taken.append("已自动关闭系统代理")
        except OSError as e:
            logger.error("关闭系统代理失败: %s", e)
            taken.append("关闭系统代理失败(见日志)")
    if cfg.auto_kill:
        killed, failed = kill_proxy_processes(cfg)
        if killed:
            logger.warning("auto_kill: 已结束进程 -> %s", ", ".join(killed))
            taken.append("已结束进程: " + ", ".join(k.split(" (")[0] for k in killed))
        for f in failed:
            logger.warning("auto_kill: %s", f)
            taken.append("未能结束: " + f)
    return taken


def warn(triggers: list[str], cfg: Config, app_id: str = "campus-proxy-guard") -> None:
    """发出警告: 记日志 + 通知(或对话框); 按配置执行处置动作。"""
    title = "【校园网代理警告】"
    body = "检测到您正在校园网中使用代理:\n" + "\n".join(triggers[:5])
    logger.warning("%s %s", title, " | ".join(triggers))
    actions = apply_actions(cfg)
    if actions:
        body += "\n\n已采取措施:\n" + "\n".join(actions)
    if cfg.popup_dialog:
        send_messagebox(title, body)
    elif not send_toast(title, body, app_id):
        send_messagebox(title, body)
