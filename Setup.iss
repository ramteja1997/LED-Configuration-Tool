[Setup]
AppName=LVGL Font Generator
AppVersion=1.0
DefaultDirName={pf}\LVGLFontGenerator
DefaultGroupName=LVGL Font Generator
OutputBaseFilename=LVGLFontGenerator_Installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; 👇 Use a relative path to the icon folder — works no matter where repo is cloned
SetupIconFile="icons\LVGL_FontGen.ico"

; Output installer to the 'Output' folder relative to this script
OutputDir="Output"

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; 👇 Source exe relative to project folder, inside 'dist' after build
Source: "dist\font2c_lvgl.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\LVGL Font Generator"; Filename: "{app}\font2c_lvgl.exe"
Name: "{commondesktop}\LVGL Font Generator"; Filename: "{app}\font2c_lvgl.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &Desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\font2c_lvgl.exe"; Description: "Launch LVGL Font Generator"; Flags: nowait postinstall skipifsilent
