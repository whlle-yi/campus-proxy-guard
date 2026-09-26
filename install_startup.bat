@echo off
rem 注册开机自启(当前用户注册表 Run 键, 无需管理员): 登录时后台启动托盘 GUI
rem 卸载: reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v CampusProxyGuard /f
setlocal
cd /d "%~dp0"
for /f "delims=" %%i in ('where pythonw 2^>nul') do if not defined PYTHONW set PYTHONW=%%i
if not defined PYTHONW for /f "delims=" %%i in ('where python') do set PYTHONW=%%i
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v CampusProxyGuard /t REG_SZ /d "\"%PYTHONW%\" -m campus_proxy_guard" /f
if %errorlevel%==0 (
  echo 已开启开机自启, 下次登录自动启动托盘
  echo ^(注: 需已 pip install -e ., 否则请改用托盘右键菜单里的开关^)
) else (
  echo 注册失败
)
pause
