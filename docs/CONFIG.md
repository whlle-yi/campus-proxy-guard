# 配置参考

配置文件位于 `%APPDATA%\CampusProxyGuard\config.json`(UTF-8 JSON), 也可在托盘主窗口中
可视化编辑并保存, 两者等效; 保存后下一轮检测(默认 10 秒内)生效。

## 字段说明

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `campus_ssids` | string[] | `[]` | 校园网 Wi-Fi SSID 关键词(子串匹配, 不区分大小写) |
| `campus_gateway_prefixes` | string[] | `[]` | 默认网关 IP 前缀, 如 `["10."]` |
| `campus_local_ip_prefixes` | string[] | `[]` | 本机内网 IP 前缀 |
| `check_system_proxy` | bool | `true` | 检测 Windows 系统代理与 PAC 脚本 |
| `check_env_proxy` | bool | `true` | 检测 `http_proxy` 等环境变量 |
| `check_processes` | bool | `true` | 检测已知代理客户端进程 |
| `check_ports` | bool | `true` | 检测常见本地代理监听端口 |
| `proxy_process_names` | string[] | Clash/v2ray 等常见项 | 代理进程名关键词(分词匹配) |
| `proxy_ports` | int[] | 7890/1080/10808 等 | 常见本地代理端口 |
| `check_interval_seconds` | int | `10` | 检测间隔(1~3600) |
| `warn_interval_seconds` | int | `60` | 警告最小间隔, 防止刷屏 |
| `popup_dialog` | bool | `false` | 额外弹出阻塞式对话框(不依赖通知服务) |
| `auto_disable_system_proxy` | bool | `false` | 违规时自动关闭 Windows 系统代理 |
| `auto_kill` | bool | `false` | 违规时自动结束代理进程(慎用) |
| `check_school_sites` | bool | `true` | 启用学校网站保护(与所在网络无关) |
| `school_domains` | string[] | `["jxufe.edu.cn"]` | 受保护的学校域名(含子域) |
| `school_site_disable_proxy` | bool | `true` | 检测到经代理访问学校域名时自动关闭系统代理 |
| `clash_api_url` | string | `http://127.0.0.1:9090` | Clash/Mihomo 外部控制 API, 留空禁用该检测 |
| `clash_api_secret` | string | `""` | API 鉴权密钥(外部控制器设置了才有) |

> 三组校园网特征**全部留空 = 不监测**(首次安装的默认状态, 程序不会产生任何警告),
> 填写任一特征后开始工作。

## 怎么确定该填什么

1. 连上校园网后双击托盘图标, 在窗口上部查看「Wi-Fi SSID / 默认网关 / 本机 IP」;
2. 把 SSID 名称(或其关键词)填入 `campus_ssids`; 若校园网使用 `10.x` 网段,
   在网关/IP 前缀里填 `10.`;
3. 保存, 等下一轮检测确认判定结果。

## 学校网站保护

检测两路信号, 任一命中即警告(标题为「代理访问学校网站警告」):

1. **系统代理接管**: 系统代理开启且学校域名未被 `ProxyOverride` 绕过——
   此时浏览器访问学校网站必然经过代理;
2. **实时连接**(Clash/Mihomo 客户端): 轮询 `external-controller` 的 `/connections`
   接口, 对经过代理的活动连接按学校域名匹配——TUN 模式同样有效。

命中后按 `school_site_disable_proxy` 自动关闭系统代理(学校网站在国内, 直连即可)。
TUN 模式下系统代理开关无效, 需依赖客户端的分流规则把学校域名加入 DIRECT, 或使用
`auto_kill` 结束代理进程。

## 数据与日志

| 位置 | 内容 |
| --- | --- |
| `%APPDATA%\CampusProxyGuard\config.json` | 用户配置(升级覆盖程序不影响) |
| `%APPDATA%\CampusProxyGuard\logs\guard.log` | 运行日志, 轮转保留 1MB x 3 |
| 安装目录(默认 `D:\CampusProxyGuard`) | 程序本体, 只读 |

## 命令行

```
campus-proxy-guard              # 等价于 python -m campus_proxy_guard, 启动托盘
  --status                      # 打印当前网络与代理判定
  --once                        # 单次检测, 校园网+代理时退出码为 2(适合接脚本)
  --daemon                      # CLI 常驻监测
  --test-toast                  # 测试 Windows 通知
  --version / -v                # 版本与调试日志
```

## 卸载与升级

- **卸载**: 设置 → 应用 → 校园网代理卫士; 会先结束运行中的程序并清理自启项,
  但保留 `%APPDATA%` 下的配置与日志;
- **升级**: 直接运行新版安装包覆盖; 便携版替换 exe 即可, 配置不受影响。
