#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""命令行入口: python -m campus_proxy_guard [选项]

不带参数时启动托盘图形界面。
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

from . import __version__
from .config import Config, load_config
from .detector import detect_proxy, on_campus
from .netinfo import get_default_gateway, get_local_ips, get_wifi_ssid
from .notifier import setup_logging, warn

logger = logging.getLogger(__name__)


def report_status(cfg: Config) -> int:
    """打印当前网络与代理判定。校园网+代理时退出码为 2。"""
    campus, why = on_campus(cfg)
    print(f"校园网判定: {'是' if campus else '否'}  ({why})")
    print(f"Wi-Fi SSID   : {get_wifi_ssid() or '(无)'}")
    print(f"默认网关     : {get_default_gateway() or '(无)'}")
    print(f"本机 IP      : {', '.join(get_local_ips()) or '(无)'}")
    hits = detect_proxy(cfg)
    if hits:
        print("代理信号:")
        for h in hits:
            print(f"  - {h}")
    else:
        print("代理信号: 未检测到")
    if campus and hits:
        print("\n结论: 在校园网且开启代理 —— 违规!")
        return 2
    return 0


def run_daemon(cfg: Config) -> int:
    """常驻监测循环(CLI 模式)。"""
    logger.info("守护模式启动: 检测间隔 %ss, 警告间隔 %ss",
                cfg.check_interval_seconds, cfg.warn_interval_seconds)
    last_warn = 0.0
    while True:
        try:
            campus, why = on_campus(cfg)
            hits = detect_proxy(cfg) if campus else []
            if campus and hits:
                if time.time() - last_warn >= cfg.warn_interval_seconds:
                    warn(hits, cfg)
                    last_warn = time.time()
                else:
                    logger.info("再次检测到代理(警告已节流): %s", " | ".join(hits))
            elif campus:
                logger.info("正常: 校园网(%s), 无代理", why)
        except KeyboardInterrupt:
            logger.info("手动退出")
            return 0
        except Exception:
            # 常驻进程不能因偶发错误退出, 但必须完整记录异常栈
            logger.exception("检测异常(继续运行)")
        time.sleep(cfg.check_interval_seconds)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="campus-proxy-guard",
        description="校园网代理卫士: 连接校园网时检测到本机开启代理立即警告")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--status", action="store_true", help="单次检测并打印结果")
    parser.add_argument("--once", action="store_true",
                        help="单次检测, 校园网+代理时退出码为 2(适合接脚本)")
    parser.add_argument("--test-toast", action="store_true", help="测试 Windows 通知")
    parser.add_argument("--daemon", action="store_true", help="CLI 常驻监测(默认启动 GUI)")
    parser.add_argument("-v", "--verbose", action="store_true", help="调试日志")
    args = parser.parse_args(argv)

    setup_logging(verbose=args.verbose)
    cfg = load_config()

    if args.test_toast:
        from .notifier import send_messagebox, send_toast
        ok = send_toast("campus-proxy-guard", "通知测试: 通道正常")
        print("Toast 发送", "成功" if ok else "失败(回退对话框)")
        if not ok:
            send_messagebox("campus-proxy-guard", "通知测试: Toast 失败, 已回退对话框")
        return 0

    if args.status or args.once:
        return report_status(cfg)

    if args.daemon:
        if sys.platform != "win32":
            print("本工具依赖 Windows(netsh/注册表/Toast), 当前系统不受支持")
            return 1
        return run_daemon(cfg)

    # 默认: 启动托盘 GUI
    if sys.platform != "win32":
        print("本工具仅支持 Windows")
        return 1
    from .guiapp import run_gui
    return run_gui()


if __name__ == "__main__":
    sys.exit(main())
