[Setup]
AppName=LVGL Font Generator
AppVersion=1.0
DefaultDirName={pf}\LVGLFontGenerator
DefaultGroupName=LVGL Font Generator
OutputBaseFilename=LVGLFontGenerator_Installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile="D:\Digicomm Daily ACT\LED Zone Digicomm\LVGL_FontGen.ico"

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\font2c_lvgl.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\LVGL Font Generator"; Filename: "{app}\font2c_lvgl.exe"
Name: "{commondesktop}\LVGL Font Generator"; Filename: "{app}\font2c_lvgl.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &Desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\font2c_lvgl.exe"; Description: "Launch LVGL Font Generator"; Flags: nowait postinstall skipifsilent