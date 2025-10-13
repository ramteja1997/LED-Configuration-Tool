[Setup]
AppName=Centum Configuration Tool
AppVersion=1.0
DefaultDirName={pf}\CentumConfigurationTool
DefaultGroupName=Centum Configuration Tool
OutputBaseFilename=CentumConfigurationTool
Compression=lzma
SolidCompression=yes
WizardStyle=modern

SetupIconFile="icons\CentumTool.ico"
OutputDir="Output"

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\CentumConfigurationTool.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Centum Configuration Tool"; Filename: "{app}\CentumConfigurationTool.exe"
Name: "{commondesktop}\Centum Configuration Tool"; Filename: "{app}\CentumConfigurationTool.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &Desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\CentumConfigurationTool.exe"; Description: "Launch Centum Configuration Tool"; Flags: nowait postinstall skipifsilent
