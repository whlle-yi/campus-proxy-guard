#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""开机自启: HKCU Run 注册表键(用户级, 无需管理员)。"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
TASK_NAME = "CampusProxyGuard"


def _command() -> str:
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    exe = pythonw if pythonw.exists() else Path(sys.executable)
    # 打包成 exe 后 sys.executable 即程序自身, 无需再跟模块参数
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    script = Path(__file__).resolve().parent / "guiapp.py"
    return f'"{exe}" "{script}"'


def autostart_enabled() -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, TASK_NAME)
            return True
    except OSError:
        return False


def autostart_set(on: bool) -> str:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as k:
            if on:
                winreg.SetValueEx(k, TASK_NAME, 0, winreg.REG_SZ, _command())
                return "已开启开机自启"
            try:
                winreg.DeleteValue(k, TASK_NAME)
            except FileNotFoundError:
                pass
            return "已关闭开机自启"
    except OSError as e:
        logger.error("开机自启设置失败: %s", e)
        return f"开机自启设置失败({e})"
