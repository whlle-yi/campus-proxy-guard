<div align="center">

# campus-proxy-guard 校园网代理卫士

**连接校园网时一旦开启代理(梯子), 立即弹窗警告 —— 帮你管住自己**

[![CI](https://github.com/whlle-yi/campus-proxy-guard/actions/workflows/ci.yml/badge.svg)](https://github.com/whlle-yi/campus-proxy-guard/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/whlle-yi/campus-proxy-guard)](https://github.com/whlle-yi/campus-proxy-guard/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[下载安装](https://github.com/whlle-yi/campus-proxy-guard/releases) · [配置参考](docs/CONFIG.md) · [问题反馈](https://github.com/whlle-yi/campus-proxy-guard/issues)

</div>

仅用于**本机自查与提醒**, 不监控他人, 也不做任何绕过检测的行为。支持 Windows 10/11。

## 功能

- **校园网识别**: Wi-Fi SSID / 网关 IP / 内网 IP 三路特征, 任一命中即生效(未配置 = 不监测);
- **代理识别**: 系统代理与 PAC、环境变量、代理客户端进程、常见监听端口, 四路信号并行;
- **警告**: Windows 通知 + 日志, 可选阻塞式对话框; 按间隔节流不刷屏;
- **可选处置**: 违规时自动关闭系统代理 / 自动结束代理进程;
- **常驻**: 系统托盘三态图标(绿=正常 / 红=违规 / 灰=暂停), 开机自启, 单实例。

## 快速开始

1. 从 [Releases](https://github.com/whlle-yi/campus-proxy-guard/releases) 下载 `CampusProxyGuard-Setup-x.y.z.exe` 并安装(绿色便携版 zip 亦提供; 开发者可 `pip install campus-proxy-guard`);
2. 双击托盘图标, 把学校 Wi-Fi 名称填入「校园网识别特征」并保存;
3. 完成。之后后台自动工作: 在校园网挂梯子就会弹警告。

> 首次运行若被 SmartScreen / 浏览器提示"无法识别的应用": 点 **更多信息 → 仍要运行 /
> 保留**。本程序开源且未购买代码签名证书, 独立软件首次分发均有此提示, 与病毒无关。

## 常见问题

| 问题 | 处理 |
| --- | --- |
| 通知不弹出 | 检查系统"专注助手"是否开启; 或在配置中启用 `popup_dialog` 改用对话框 |
| TUN/增强模式代理没被警告 | 正常——TUN 无系统代理痕迹, 请确保"代理进程/端口"两项检测开启 |
| 判定不准(误报/漏报) | 按 [docs/CONFIG.md](docs/CONFIG.md) 校准三组校园网特征; 仍异常请带日志提 Issue |
| 想让它自动关掉梯子 | 托盘主窗口「行为」区勾选处置动作; 说明见 [docs/CONFIG.md](docs/CONFIG.md) |

## 从源码运行

```bat
pip install -e .[dev]
python -m campus_proxy_guard --status   # 手动检测
pytest --cov=campus_proxy_guard         # 测试(42 例)
ruff check . && mypy src                # lint 与类型检查
```

提交与发布规范见 [CONTRIBUTING.md](CONTRIBUTING.md); 安全问题见 [SECURITY.md](SECURITY.md)。

## License

[MIT](LICENSE)
