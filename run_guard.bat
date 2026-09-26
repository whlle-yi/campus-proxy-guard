@echo off
rem CLI 常驻监测(开发环境)
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
python -m campus_proxy_guard --daemon
