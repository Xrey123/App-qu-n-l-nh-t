; Script Inno Setup để tạo file cài đặt cho ShopFlow

[Setup]
AppName=ShopFlow POS
AppVersion=1.0.0
DefaultDirName={autopf}\ShopFlow
DefaultGroupName=ShopFlow
DisableDirPage=no
DisableProgramGroupPage=no
OutputDir=dist
OutputBaseFilename=ShopFlowSet; Script Inno Setup chuẩn cho ShopFlow

[Setup]
AppName=ShopFlow POS
AppVersion=1.0.0
DefaultDirName={autopf}\ShopFlow
DefaultGroupName=ShopFlow
DisableDirPage=no
DisableProgramGroupPage=no
OutputDir=dist
OutputBaseFilename=ShopFlowSetup
Compression=lzma
SolidCompression=yes
SetupIconFile=..\assets\logo.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\main_gui\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\assets\logo.ico"; DestDir: "{app}"

[Icons]
Name: "{group}\ShopFlow"; Filename: "{app}\main_gui.exe"; IconFilename: "{app}\logo.ico"
Name: "{commondesktop}\ShopFlow"; Filename: "{app}\main_gui.exe"; IconFilename: "{app}\logo.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Run]
Filename: "{app}\main_gui.exe"; Description: "{cm:LaunchProgram,ShopFlow}"; Flags: nowait postinstall skipifsilent
up
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Bao gồm toàn bộ thư mục đã đóng gói bằng PyInstaller
Source: "..\dist\main_gui\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ShopFlow"; Filename: "{app}\main_gui.exe"
Name: "{commondesktop}\ShopFlow"; Filename: "{app}\main_gui.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Run]
Filename: "{app}\main_gui.exe"; Description: "{cm:LaunchProgram,ShopFlow}"; Flags: nowait postinstall skipifsilent



