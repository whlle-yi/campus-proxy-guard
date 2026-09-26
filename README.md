# campus-proxy-guard 校园网代理卫士

> **连接校园网时一旦检测到本机开启代理(梯子), 立即弹 Windows 系统通知警告并记录日志。**
> 帮你管住自己: 校园网环境下不挂代理, 避免校内认证异常 / 触发风控 / 流量审计问题。

仅用于**本机自查与提醒**, 不涉及任何监控他人的功能, 也不做任何绕过或对抗检测的行为。
支持 Windows 10/11。

## 给使用者

### 安装(两种方式任选)

**方式 A: 安装包(推荐)**

1. 打开 [Releases](https://github.com/whlle-yi/campus-proxy-guard/releases) 页面;
2. 下载最新的 `CampusProxyGuard-Setup-vX.X.X.exe`;
3. 双击安装: 可勾选创建桌面快捷方式、开机自启, 支持在控制面板正常卸载;
4. 安装即完成——托盘出现绿/灰色圆点图标, 开始工作。

> 首次运行如出现"Windows 已保护你的电脑": 点 **更多信息 → 仍要运行**。
> 本程序开源、未购买代码签名证书, 独立软件首次分发均有此提示, 与病毒无关。

**方式 B: 绿色便携版**: 下载 `CampusProxyGuard-vX.X.X-win64.zip` 解压即用, 不写注册表。

**方式 B: Python 安装(适合开发者)**

```bat
pip install campus-proxy-guard   # 或从源码: pip install -e .
campus-proxy-guard               # 启动托盘
```

### 日常使用

程序常驻系统托盘(右下角, 可能收进 `^` 折叠区):

- **图标变色**: 绿 = 正常; 红 = 校园网 + 代理违规; 灰 = 已暂停。悬停显示状态。
- **双击图标**打开主窗口: 实时显示校园网判定 / SSID / 网关 / 代理信号; 全部配置可视化编辑, 点「保存设置」即时生效。
- **右键图标**: 立即检测一次 / 暂停监测 / 开机自启开关 / 打开日志 / 退出。

**第一次用必须做的一步**: 双击托盘图标, 在「校园网识别特征」里填入你们学校的 Wi-Fi 名称(如 `jxufe-wifi`)或校园网网关前缀(如 `10.`), 点保存。全部留空 = 任何网络都监测。

配置与日志保存在 `%APPDATA%\CampusProxyGuard\`, 重装/升级不影响你的配置。

## 给开发者

### 项目结构

```
src/campus_proxy_guard/     包源码
├── config.py               配置模型(dataclass)+校验+读写
├── netinfo.py              SSID/网关/IP 采集(解析函数与命令执行分离, 可测)
├── detector.py             校园网判定 + 代理信号识别(核心逻辑)
├── notifier.py             轮转日志 / Toast / 对话框 / 警告动作
├── autostart.py            开机自启(HKCU Run 键, 免管理员)
├── cli.py                  命令行入口(python -m campus_proxy_guard)
└── guiapp.py               托盘 GUI(单实例锁)
tests/                      pytest 单元测试
.github/workflows/ci.yml    push 自动跑测试+lint; 打 v* 标签自动发 Release(exe)
```

### 本地开发

```bat
pip install -e .[dev]
pytest            # 运行测试
ruff check .      # 代码检查
python -m campus_proxy_guard --status   # 手动检测
```

### 命令行参数

```
python -m campus_proxy_guard              # 启动托盘 GUI
python -m campus_proxy_guard --status     # 打印当前网络与代理判定
python -m campus_proxy_guard --once       # 单次检测, 校园网+代理时退出码为 2(适合接脚本)
python -m campus_proxy_guard --daemon     # CLI 常驻监测
python -m campus_proxy_guard --test-toast # 测试 Windows 通知
```

### 发布新版本

```bat
:: 1. 更新 CHANGELOG.md 与 src/campus_proxy_guard/__init__.py 中的版本号
:: 2. 提交并推送
git add -A && git commit -m "release: vX.X.X" && python push_via_api.py
:: 3. 打标签(本机无法直连 github.com 时可用 API 建标签引用)
git tag vX.X.X && git push origin vX.X.X
```

标签推送后, CI 自动跑测试并用 PyInstaller 构建 exe, 附到 GitHub Release。

### 推送更新(github.com 被阻断的环境)

本机若无法直连 `github.com:443` 但 `api.github.com` 可用:

```bat
git add -A && git commit -m "..." && python push_via_api.py
```

它把本地最新提交的完整内容作为快照提交追加到远端 main 之上(凭据取自 Git 凭据管理器)。

## 配置说明(%APPDATA%\CampusProxyGuard\config.json)

| 字段 | 说明 | 默认 |
| --- | --- | --- |
| `campus_ssids` | 校园网 Wi-Fi SSID 关键词(子串匹配) | `[]` |
| `campus_gateway_prefixes` | 默认网关 IP 前缀, 如 `["10."]` | `[]` |
| `campus_local_ip_prefixes` | 本机内网 IP 前缀 | `[]` |
| `check_system_proxy` / `check_env_proxy` / `check_processes` / `check_ports` | 各类代理信号开关 | `true` |
| `proxy_process_names` | 代理进程名关键词 | Clash/v2ray 等常见项 |
| `proxy_ports` | 常见本地代理端口 | 7890/1080/10808 等 |
| `check_interval_seconds` | 检测间隔 | `10` |
| `warn_interval_seconds` | 警告通知最小间隔(防刷屏) | `60` |
| `popup_dialog` | 额外弹出阻塞式对话框 | `false` |
| `auto_disable_system_proxy` | 违规时自动关闭 Windows 系统代理 | `false` |
| `auto_kill` | 违规时自动结束代理进程(**慎用**) | `false` |

> **怎么知道该填什么?** 连上校园网后运行 `python -m campus_proxy_guard --status`(或看 GUI 主窗口), 把显示的 SSID / 网关 / 本机 IP 填进配置即可。三组条件全部留空 = 任何网络都监测(最严格)。

## 违规处置(可选)

默认只警告; 可在 GUI「行为」区(或配置文件)启用处置动作, 可叠加:

- **自动关闭系统代理**(`auto_disable_system_proxy`): 把 Windows 系统代理关掉并立即生效, 流量不再走代理——对绝大多数"系统代理模式"梯子最有效, 且不动对方进程;
- **自动结束代理进程**(`auto_kill`, 慎用): 直接杀掉 Clash/v2ray 等进程。TUN/管理员权限运行的进程可能杀不掉, 失败原因会写进警告和日志, 建议管理员身份运行本程序。

两个动作都开启 = 双保险。警告通知里会写明具体采取了哪些措施。

## 工作原理

```
┌ 每 check_interval_seconds 轮询 ─────────────────────────────┐
│ 1. netsh wlan show interfaces → SSID                        │
│    route print -4 → 默认网关                                 │
│    psutil → 本机内网 IP        ── 三者任一命中校园网特征?      │
│ 2. 命中后检测代理信号:                                        │
│    注册表(系统代理/PAC) + 环境变量 + 进程名 + 监听端口           │
│ 3. 有信号 → Windows Toast 警告 + 写日志(按 warn_interval 节流) │
└─────────────────────────────────────────────────────────────┘
```

- TUN/增强模式代理没有系统代理痕迹, 依赖**进程名/端口**信号识别, 请保留这两项开启。

## 已知限制

- 进程与端口特征基于常见代理客户端, 自定义端口且改名的客户端识别不到;
- Toast 通知依赖 Windows 通知服务, 系统开了专注助手(勿扰)时可能不弹, 可改用 `popup_dialog: true`;
- 仅支持 Windows 10/11。

## License

[MIT](LICENSE)
