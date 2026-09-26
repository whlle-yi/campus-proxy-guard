# 贡献指南

感谢关注 campus-proxy-guard!欢迎以 Issue / Pull Request 的形式参与。

## 开发环境

```bat
git clone https://github.com/whlle-yi/campus-proxy-guard.git
cd campus-proxy-guard
pip install -e .[dev]
```

## 开发流程

1. 从 `main` 拉出功能分支(`feat/xxx`、`fix/xxx`);
2. 改动需同步更新:
   - 新配置项 → `src/campus_proxy_guard/config.py` 的 `Config` + README 配置表;
   - 用户可见变化 → `CHANGELOG.md`(遵循 Keep a Changelog 格式);
3. 提交前确保本地全绿:

```bat
ruff check .
mypy src
pytest --cov=campus_proxy_guard
```

4. 提交 PR,CI 通过后由维护者合并。提交信息使用中文, 格式 `type: 摘要`
   (type 取 feat/fix/docs/refactor/test/chore)。

## 发布流程(维护者)

1. 更新 `src/campus_proxy_guard/__init__.py` 的 `__version__` 与 `CHANGELOG.md`;
2. 提交并推送, 打 `vX.Y.Z` 标签;
3. CI 自动构建 exe/安装包并发布 GitHub Release;
4. 本机 `github.com` 直连受阻时, 推送与打标签使用 `python scripts/push_via_api.py`
   与 GitHub API(见脚本内注释)。

## 代码约定

- 面向 Windows 10/11, 纯标准库 + psutil/pystray/Pillow, 不引入重量级依赖;
- 命令输出解析(如 netsh/route)必须与命令执行分离, 且附带真实输出样本的单测;
- 任何检测/处置失败都不能让常驻进程退出: 记录日志、继续运行。
