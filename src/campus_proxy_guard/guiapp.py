#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""系统托盘图形界面: 三态图标 + 主窗口(状态展示 + 可视化配置) + 单实例锁。"""

from __future__ import annotations

import ctypes
import logging
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    pystray = None
    Image = None

from . import __version__
from .autostart import autostart_enabled, autostart_set
from .config import load_config, save_config
from .detector import detect_proxy, on_campus
from .netinfo import get_default_gateway, get_local_ips, get_wifi_ssid
from .notifier import log_dir, setup_logging, warn

logger = logging.getLogger(__name__)

MUTEX_NAME = "CampusProxyGuardSingleInstance"
ERROR_ALREADY_EXISTS = 183

COLOR_OK = "#27ae60"
COLOR_ALERT = "#e74c3c"
COLOR_PAUSE = "#95a5a6"


def make_icon(color: str) -> "Image.Image":
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([16, 16, 240, 240], fill=color)
    d.ellipse([72, 72, 184, 184], fill=(255, 255, 255, 235))
    d.ellipse([108, 108, 148, 148], fill=color)
    return img


class GuardApp:
    def __init__(self) -> None:
        self.state = {"campus": None, "hits": [], "why": "", "paused": False}
        self.stop_event = threading.Event()
        self.root = tk.Tk()
        self.root.withdraw()
        self.window: tk.Toplevel | None = None
        self.icon: "pystray.Icon | None" = None
        self._icons = {
            "ok": make_icon(COLOR_OK),
            "alert": make_icon(COLOR_ALERT),
            "pause": make_icon(COLOR_PAUSE),
        } if Image else {}

    # --- 监测循环 ---
    def monitor_loop(self) -> None:
        last_warn = 0.0
        while not self.stop_event.is_set():
            try:
                cfg = load_config()  # 每轮重读, 设置保存后即时生效
                if not self.state["paused"]:
                    campus, why = on_campus(cfg)
                    hits = detect_proxy(cfg) if campus else []
                    self.state.update(campus=campus, hits=hits, why=why)
                    if campus and hits and time.time() - last_warn >= cfg.warn_interval_seconds:
                        warn(hits, cfg)
                        last_warn = time.time()
            except Exception:
                logger.exception("监测轮询异常(继续运行)")
            self.refresh_ui()
            self.stop_event.wait(load_config().check_interval_seconds)
        logger.info("监测线程退出")

    # --- 状态 ---
    def status_text(self) -> tuple[str, str]:
        if self.state["paused"]:
            return "监测已暂停", COLOR_PAUSE
        if self.state["campus"] is None:
            return "检测中…", COLOR_PAUSE
        if self.state["campus"] and self.state["hits"]:
            return "⚠ 校园网 + 代理 = 违规!", COLOR_ALERT
        if self.state["campus"]:
            return "校园网, 未检测到代理", COLOR_OK
        return "非校园网, 不监测", COLOR_OK

    def tray_title(self) -> str:
        return f"校园网代理卫士 v{__version__}: {self.status_text()[0]}"

    def icon_key(self) -> str:
        if self.state["paused"]:
            return "pause"
        if self.state["campus"] and self.state["hits"]:
            return "alert"
        return "ok"

    # --- UI 刷新 ---
    def refresh_ui(self) -> None:
        if self.icon:
            self.icon.icon = self._icons[self.icon_key()]
            self.icon.title = self.tray_title()

        def apply() -> None:
            if self.window and self.window.winfo_exists():
                self.update_window_labels()

        try:
            self.root.after(0, apply)
        except RuntimeError:
            pass

    # --- 主窗口 ---
    def show_window(self) -> None:
        if self.window and self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            return
        self.window = tk.Toplevel(self.root)
        self.window.title(f"校园网代理卫士 v{__version__}")
        self.window.geometry("540x660")
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.window.withdraw)
        self.build_window(self.window)
        self.update_window_labels()
        self.load_settings_fields()

    def build_window(self, w: tk.Toplevel) -> None:
        pad = {"padx": 14, "pady": 4}

        self.lbl_status = tk.Label(w, text="", font=("Microsoft YaHei", 15, "bold"))
        self.lbl_status.pack(pady=(14, 2))
        self.lbl_detail = tk.Label(w, text="", font=("Microsoft YaHei", 9),
                                   justify="left", anchor="w", fg="#555555")
        self.lbl_detail.pack(fill="x", padx=14)

        ttk.Separator(w).pack(fill="x", pady=8)

        box = ttk.LabelFrame(
            w, text="校园网识别特征 (逗号分隔, 任一命中即算校园网; 全空=任意网络都监测)")
        box.pack(fill="x", **pad)
        self.var_ssids = tk.StringVar()
        self.var_gw = tk.StringVar()
        self.var_ip = tk.StringVar()
        for row, (label, var) in enumerate([
                ("Wi-Fi SSID 关键词", self.var_ssids),
                ("网关 IP 前缀", self.var_gw),
                ("本机 IP 前缀", self.var_ip)]):
            ttk.Label(box, text=label + ":").grid(row=row, column=0, sticky="w",
                                                  padx=8, pady=3)
            ttk.Entry(box, textvariable=var, width=38).grid(row=row, column=1,
                                                            padx=6, pady=3)

        box2 = ttk.LabelFrame(w, text="代理识别信号")
        box2.pack(fill="x", **pad)
        self.var_sys = tk.BooleanVar()
        self.var_env = tk.BooleanVar()
        self.var_proc = tk.BooleanVar()
        self.var_port = tk.BooleanVar()
        for col, (text, var) in enumerate([
                ("系统代理/PAC", self.var_sys), ("环境变量", self.var_env),
                ("代理进程", self.var_proc), ("代理端口", self.var_port)]):
            ttk.Checkbutton(box2, text=text, variable=var).grid(
                row=0, column=col, padx=8, pady=5)

        box3 = ttk.LabelFrame(w, text="行为")
        box3.pack(fill="x", **pad)
        ttk.Label(box3, text="检测间隔(秒):").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.var_interval = tk.IntVar()
        ttk.Spinbox(box3, from_=1, to=3600, textvariable=self.var_interval, width=7)\
            .grid(row=0, column=1, sticky="w")
        ttk.Label(box3, text="警告间隔(秒):").grid(row=0, column=2, sticky="w", padx=8)
        self.var_warn_interval = tk.IntVar()
        ttk.Spinbox(box3, from_=5, to=86400, textvariable=self.var_warn_interval, width=7)\
            .grid(row=0, column=3, sticky="w")
        self.var_popup = tk.BooleanVar()
        ttk.Checkbutton(box3, text="额外弹出阻塞式对话框", variable=self.var_popup)\
            .grid(row=1, column=0, columnspan=2, sticky="w", padx=8)
        self.var_kill = tk.BooleanVar()
        ttk.Checkbutton(box3, text="自动结束代理进程 (慎用!)", variable=self.var_kill)\
            .grid(row=1, column=2, columnspan=2, sticky="w", padx=8)

        btns = tk.Frame(w)
        btns.pack(pady=12)
        tk.Button(btns, text="保存设置", width=12, command=self.save_settings).pack(
            side="left", padx=6)
        tk.Button(btns, text="立即检测", width=12, command=self.check_now).pack(
            side="left", padx=6)
        tk.Button(btns, text="打开日志", width=12, command=self.open_log).pack(
            side="left", padx=6)

        self.lbl_msg = tk.Label(w, text="", fg="#2980b9", font=("Microsoft YaHei", 9))
        self.lbl_msg.pack()

    def update_window_labels(self) -> None:
        if not (self.window and self.window.winfo_exists()):
            return
        text, color = self.status_text()
        self.lbl_status.config(text=text, fg=color)
        lines = [
            f"Wi-Fi SSID : {get_wifi_ssid() or '(无)'}",
            f"默认网关   : {get_default_gateway() or '(无)'}",
            f"本机 IP    : {', '.join(get_local_ips()) or '(无)'}",
        ]
        if self.state["hits"]:
            lines.append("代理信号:")
            lines += [f"  - {h}" for h in self.state["hits"]]
        elif self.state["campus"] is not None:
            lines.append("代理信号: 未检测到")
        self.lbl_detail.config(text="\n".join(lines))

    def load_settings_fields(self) -> None:
        cfg = load_config()
        self.var_ssids.set(", ".join(cfg.campus_ssids))
        self.var_gw.set(", ".join(cfg.campus_gateway_prefixes))
        self.var_ip.set(", ".join(cfg.campus_local_ip_prefixes))
        self.var_sys.set(cfg.check_system_proxy)
        self.var_env.set(cfg.check_env_proxy)
        self.var_proc.set(cfg.check_processes)
        self.var_port.set(cfg.check_ports)
        self.var_interval.set(cfg.check_interval_seconds)
        self.var_warn_interval.set(cfg.warn_interval_seconds)
        self.var_popup.set(cfg.popup_dialog)
        self.var_kill.set(cfg.auto_kill)

    def flash_msg(self, text: str) -> None:
        if self.window and self.window.winfo_exists():
            self.lbl_msg.config(text=text)
            self.window.after(4000, lambda: self.lbl_msg.config(text=""))

    # --- 按钮动作 ---
    def save_settings(self) -> None:
        def split(s: str) -> list[str]:
            return [x.strip() for x in s.split(",") if x.strip()]

        cfg = load_config()
        try:
            cfg.campus_ssids = split(self.var_ssids.get())
            cfg.campus_gateway_prefixes = split(self.var_gw.get())
            cfg.campus_local_ip_prefixes = split(self.var_ip.get())
            cfg.check_system_proxy = self.var_sys.get()
            cfg.check_env_proxy = self.var_env.get()
            cfg.check_processes = self.var_proc.get()
            cfg.check_ports = self.var_port.get()
            cfg.check_interval_seconds = int(self.var_interval.get())
            cfg.warn_interval_seconds = int(self.var_warn_interval.get())
            cfg.popup_dialog = self.var_popup.get()
            cfg.auto_kill = self.var_kill.get()
            save_config(cfg)
        except (OSError, ValueError) as e:
            messagebox.showerror("保存失败", str(e), parent=self.window)
            return
        self.flash_msg("设置已保存, 下一轮检测生效")

    def check_now(self) -> None:
        if self.state["paused"]:
            self.flash_msg("监测已暂停, 先恢复监测")
            return
        cfg = load_config()
        campus, _why = on_campus(cfg)
        hits = detect_proxy(cfg) if campus else []
        self.state.update(campus=campus, hits=hits)
        self.update_window_labels()
        self.refresh_ui()
        if campus and hits:
            warn(hits, cfg)
        self.flash_msg("已重新检测" + (", 发现违规!" if campus and hits else ""))

    def toggle_pause(self, _item=None, _icon=None) -> None:
        self.state["paused"] = not self.state["paused"]
        self.refresh_ui()

    def open_log(self, _item=None, _icon=None) -> None:
        log_dir().mkdir(parents=True, exist_ok=True)
        subprocess.Popen(["notepad.exe", str(log_dir() / "guard.log")])

    # --- 托盘 ---
    def run_tray(self) -> None:
        menu = pystray.Menu(
            pystray.MenuItem("打开主窗口",
                             lambda: self.root.after(0, self.show_window), default=True),
            pystray.MenuItem(
                lambda item: "恢复监测" if self.state["paused"] else "暂停监测",
                self.toggle_pause),
            pystray.MenuItem("立即检测一次", lambda: self.root.after(0, self.check_now)),
            pystray.MenuItem(
                lambda item: "开机自启: 已开启" if autostart_enabled() else "开机自启: 已关闭",
                self.on_autostart_click),
            pystray.MenuItem("打开日志", self.open_log),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self.on_quit),
        )
        self.icon = pystray.Icon("campus-proxy-guard", self._icons["pause"],
                                 self.tray_title(), menu)
        self.icon.run_detached()

    def on_autostart_click(self, _item, _icon) -> None:
        msg = autostart_set(not autostart_enabled())

        def apply() -> None:
            self.show_window()
            self.flash_msg(msg)

        self.root.after(0, apply)

    def on_quit(self, _item, icon) -> None:
        self.stop_event.set()
        icon.stop()
        self.root.after(0, self.root.destroy)

    # --- 入口 ---
    def run(self) -> None:
        self.run_tray()
        threading.Thread(target=self.monitor_loop, daemon=True).start()
        self.root.after(500, self.show_window)
        self.root.mainloop()


def _single_instance() -> bool:
    """命名互斥锁防止同时开多个托盘实例。"""
    ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    return ctypes.windll.kernel32.GetLastError() != ERROR_ALREADY_EXISTS


def run_gui() -> int:
    if pystray is None:
        print("缺少 GUI 依赖: pip install pystray Pillow")
        return 1
    if not _single_instance():
        logger.warning("已有托盘实例在运行, 本次启动退出")
        return 0
    GuardApp().run()
    return 0


if __name__ == "__main__":
    setup_logging()
    sys.exit(run_gui())
