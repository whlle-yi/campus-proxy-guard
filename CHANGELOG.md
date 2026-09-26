# 更新日志

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.4] - 2026-09-26

### 新增
- **安装包分发**: Inno Setup 构建的 `CampusProxyGuard-Setup-x.y.z.exe`, 提供安装向导/桌面与开始菜单快捷方式/可选开机自启/控制面板卸载; 绿色 zip 保留作为便携版
- 卸载前自动结束运行中的程序; 卸载保留用户配置(%APPDATA%)
- 默认安装位置: 有 D 盘时为 `D:\CampusProxyGuard`(D 盘根目录普通权限可写; D:\Program Files 受系统保护), 无 D 盘回退 `%LOCALAPPDATA%\Programs`; 向导中可自行修改

## [1.0.3] - 2026-09-26

### 修复
- **exe 启动即崩溃**: PyInstaller 入口误用含相对导入的 __main__.py, 导致 v1.0.0~v1.0.2 的发布包全部无法使用; 改用绝对导入的 launcher.py 作为打包入口
- 上述三个版本的发布附件已撤下

## [1.0.2] - 2026-09-25

### 新增
- 违规处置动作: `auto_disable_system_proxy` 自动关闭 Windows 系统代理并即时生效(新增, 对系统代理模式最有效)
- 警告通知与日志中写明已采取的处置措施及失败原因

### 修复
- `auto_kill` 结束进程失败(权限不足/超时)此前被静默吞掉, 现在完整记录并在警告中提示

## [1.0.1] - 2026-09-25

### 修复
- GUI 保存设置时兼容中文逗号/顿号/分号分隔(此前 `jxufe-wifi，501` 会被当成一个条目)
- 配置校验遗漏 `list[int]` 类型字段, `proxy_ports` 自定义值被误忽略
- 第二次启动托盘时不再静默退出, 改为唤起已运行实例弹出主窗口

## [1.0.0] - 2026-09-25

首个正式版本。

### 新增
- 校园网识别: Wi-Fi SSID 关键词 / 默认网关 IP 前缀 / 本机 IP 前缀, 任一命中即生效
- 代理识别: 系统代理与 PAC / 环境变量 / 代理客户端进程(分词匹配防误报) / 常见本地监听端口
- 系统托盘 GUI: 绿/红/灰三态图标, 主窗口可视化配置, 一键开关开机自启, 单实例锁
- CLI: `--status` / `--once` / `--test-toast` / `--daemon`, 便于脚本化使用
- 配置保存于 `%APPDATA%\CampusProxyGuard`, 首次运行自动迁移旧版程序目录配置
- 轮转日志(%APPDATA%\CampusProxyGuard\logs, 1MB x 3)
- `python push_via_api.py`: github.com 直连受阻时经 API 推送快照提交
- CI: pytest + ruff 自动检查; 打 v* 标签自动构建 exe 并发布 GitHub Release
