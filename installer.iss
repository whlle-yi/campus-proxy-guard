; Inno Setup 脚本 —— 校园网代理卫士安装包
; CI 中以 iscc /DAPP_VERSION=vX.Y.Z 编译, 版本号取自 git 标签

#ifndef APP_VERSION
#define APP_VERSION "0.0.0"
#endif

#define MyAppName "校园网代理卫士"
#define MyAppExeName "CampusProxyGuard.exe"

[Setup]
AppId={{7E3B9C42-5A1D-4F6E-9C8A-2B4D6E8F1A3C}
AppName={#MyAppName}
AppVersion={#APP_VERSION}
AppPublisher=whlle-yi
AppPublisherURL=https://github.com/whlle-yi/campus-proxy-guard
DefaultDirName={code:GetDefaultDir}
DisableDirPage=no
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=CampusProxyGuard-Setup-{#APP_VERSION}
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"
Name: "autostart"; Description: "开机自动启动(后台托盘运行)"; GroupDescription: "附加任务:"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Code]
// 默认装 D 盘根目录(D:\Program Files 受 TrustedInstaller 保护, 普通权限写不进);
// 无 D 盘或不可写时回退用户目录下的标准位置。向导中用户可自行修改。
function GetDefaultDir(Param: string): string;
begin
  if DirExists('D:\') then
    Result := 'D:\CampusProxyGuard'
  else
    Result := ExpandConstant('{localappdata}\Programs\CampusProxyGuard');
end;

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Registry]
; 开机自启(用户级 Run 键, 卸载时自动删除)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; \
    ValueName: "CampusProxyGuard"; ValueData: """{app}\{#MyAppExeName}"""; \
    Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; \
    Flags: nowait postinstall skipifsilent

[UninstallRun]
; 卸载前先结束正在运行的实例
Filename: "{cmd}"; Parameters: "/C taskkill /F /IM {#MyAppExeName}"; Flags: runhidden; RunOnceId: "KillApp"
