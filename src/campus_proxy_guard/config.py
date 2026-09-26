#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配置模型与读写。

配置文件位置: %APPDATA%\\CampusProxyGuard\\config.json (安装级软件规范)。
首次运行时自动迁移旧版程序目录下的 config.json。
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

APP_DIR_NAME = "CampusProxyGuard"


def app_dir() -> Path:
    """用户数据目录: %APPDATA%\\CampusProxyGuard (无 APPDATA 时回退 ~/CampusProxyGuard)。"""
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / APP_DIR_NAME


def config_path() -> Path:
    return app_dir() / "config.json"


def log_dir() -> Path:
    return app_dir() / "logs"


def _legacy_candidates() -> list[Path]:
    """旧版本把 config.json 放在程序目录, 依次检查这些位置。"""
    here = Path(__file__).resolve()
    return [here.parents[2] / "config.json", here.parents[3] / "config.json"]


@dataclass
class Config:
    """全部配置项, 与 config.json 字段一一对应。"""

    # 校园网识别: 任一条件命中即认为在校园网; 全部留空则任何网络都监测
    campus_ssids: list[str] = field(default_factory=list)
    campus_gateway_prefixes: list[str] = field(default_factory=list)
    campus_local_ip_prefixes: list[str] = field(default_factory=list)
    # 代理识别开关
    check_system_proxy: bool = True
    check_env_proxy: bool = True
    check_processes: bool = True
    check_ports: bool = True
    proxy_process_names: list[str] = field(default_factory=lambda: [
        "clash", "mihomo", "verge", "v2ray", "v2rayn", "xray",
        "sing-box", "singbox", "shadowsocks", "ssr", "trojan",
        "hysteria", "naive", "nekoray", "nekobox", "leaf",
        "tun2socks", "privoxy", "gost", "brook",
    ])
    proxy_ports: list[int] = field(default_factory=lambda: [
        7890, 7891, 7892, 7893, 7894, 7895, 7897,
        1080, 1081,
        2080, 2081,
        8118,
        10808, 10809,
        20170, 20171, 20172,
    ])
    # 行为
    check_interval_seconds: int = 10
    warn_interval_seconds: int = 60
    popup_dialog: bool = False
    # 违规处置(可叠加)
    auto_disable_system_proxy: bool = False  # 自动关闭 Windows 系统代理
    auto_kill: bool = False                  # 自动结束代理进程(慎用)

    def to_dict(self) -> dict:
        return asdict(self)


def _validate(data: dict) -> tuple[dict, list[str]]:
    """逐字段校验: 类型不符的字段丢弃并告警, 未知字段忽略并告警。"""
    import typing

    warnings: list[str] = []
    valid: dict = {}
    hints = typing.get_type_hints(Config)
    str_lists = {n for n, t in hints.items()
                 if typing.get_origin(t) is list and typing.get_args(t) == (str,)}
    int_lists = {n for n, t in hints.items()
                 if typing.get_origin(t) is list and typing.get_args(t) == (int,)}
    int_fields = {n for n, t in hints.items() if t is int}
    bool_fields = {n for n, t in hints.items() if t is bool}
    for key, value in data.items():
        if key not in hints:
            warnings.append(f"未知配置项 '{key}' 已忽略")
        elif key in str_lists:
            if isinstance(value, list) and all(isinstance(v, str) for v in value):
                valid[key] = value
            else:
                warnings.append(f"配置项 '{key}' 应为字符串列表, 已恢复默认值")
        elif key in int_lists:
            if isinstance(value, list) and all(
                    isinstance(v, int) and not isinstance(v, bool) for v in value):
                valid[key] = value
            else:
                warnings.append(f"配置项 '{key}' 应为整数列表, 已恢复默认值")
        elif key in int_fields:
            if isinstance(value, int) and not isinstance(value, bool) and value > 0:
                valid[key] = value
            else:
                warnings.append(f"配置项 '{key}' 应为正整数, 已恢复默认值")
        elif key in bool_fields:
            if isinstance(value, bool):
                valid[key] = value
            else:
                warnings.append(f"配置项 '{key}' 应为 true/false, 已恢复默认值")
        else:
            warnings.append(f"未知配置项 '{key}' 已忽略")
    return valid, warnings


def load_config(path: Path | None = None) -> Config:
    """加载配置; 文件缺失/损坏时返回默认值。

    仅当使用默认路径(未显式传 path)且文件缺失时, 才尝试从旧版程序目录迁移。
    """
    explicit = path is not None
    path = path or config_path()
    data: dict = {}
    if not path.exists() and not explicit:
        for legacy in _legacy_candidates():
            if legacy.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(legacy, path)
                logger.info("已从旧位置迁移配置: %s -> %s", legacy, path)
                break
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except (OSError, json.JSONDecodeError) as e:
            logger.error("配置文件解析失败(%s), 使用默认配置: %s", e, path)
    valid, warnings = _validate(data)
    for w in warnings:
        logger.warning("配置: %s", w)
    cfg = Config()
    for key, value in valid.items():
        setattr(cfg, key, value)
    return cfg


def save_config(cfg: Config, path: Path | None = None) -> Path:
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg.to_dict(), ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return path
