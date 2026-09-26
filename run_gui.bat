@echo off
rem 启动托盘 GUI(开发环境, 已 pip install -e . 时也可直接运行 campus-proxy-guard)
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
python -m campus_proxy_guard
