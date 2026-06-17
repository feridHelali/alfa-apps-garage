; Inno Setup script — Gestion Réparation Voiture
; Alfa Computers Apps
; Run with: iscc installer\setup.iss
;
; Optional: place DB Browser for SQLite portable in installer\tools\DBBrowserForSQLite\
; Download: https://sqlitebrowser.org/dl/  →  "DB Browser for SQLite - PortableApp"

#define AppName "Gestion Réparation Voiture"
#define AppVersion "0.1.0"
#define AppPublisher "Alfa Computers Apps"
#define AppURL "https://alfa-computers.com"
#define AppExeName "GarageReparation.exe"
#define DistDir "..\dist\garage_reparation"
#define DBBrowserDir "tools\DBBrowserForSQLite"

[Setup]
AppId={{A1F4C0DE-DEAD-BEEF-C0FE-GARAGE2025001}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppPublisher}\{#AppName}
DefaultGroupName={#AppPublisher}\{#AppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=GarageReparationSetup_{#AppVersion}_x64
SetupIconFile=..\assets\icons\app_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
ChangesAssociations=no

[Languages]
Name: "french";  MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Types]
Name: "full";    Description: "Installation complète"
Name: "compact"; Description: "Application uniquement"
Name: "custom";  Description: "Installation personnalisée"; Flags: iscustom

[Components]
Name: "main";       Description: "Application Gestion Réparation Voiture"; Types: full compact custom; Flags: fixed
Name: "dbbrowser"; Description: "DB Browser for SQLite (outil d''administration BDD)"; Types: full; ExtraDiskSpaceRequired: 20971520

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "dbbrowser_shortcut"; Description: "Raccourci bureau pour DB Browser for SQLite"; GroupDescription: "DB Browser for SQLite"; Components: dbbrowser; Flags: unchecked

[Files]
; Main application
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: main

; DB Browser for SQLite (portable) — place folder at installer\tools\DBBrowserForSQLite\
; Download portable ZIP from https://sqlitebrowser.org/dl/ and extract to installer\tools\DBBrowserForSQLite\
Source: "{#DBBrowserDir}\*"; DestDir: "{app}\tools\DBBrowserForSQLite"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Components: dbbrowser

[Icons]
; Main app
Name: "{group}\{#AppName}";                            Filename: "{app}\{#AppExeName}"; Components: main
Name: "{group}\{cm:UninstallProgram,{#AppName}}";      Filename: "{uninstallexe}"; Components: main
Name: "{autodesktop}\{#AppName}";                      Filename: "{app}\{#AppExeName}"; Tasks: desktopicon; Components: main

; DB Browser for SQLite
Name: "{group}\DB Browser for SQLite";                 Filename: "{app}\tools\DBBrowserForSQLite\DB Browser for SQLite.exe"; Components: dbbrowser
Name: "{autodesktop}\DB Browser for SQLite";           Filename: "{app}\tools\DBBrowserForSQLite\DB Browser for SQLite.exe"; Tasks: dbbrowser_shortcut; Components: dbbrowser

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent; Components: main

[Code]
// Show a hint about the DB path when setup finishes
procedure CurStepChanged(CurStep: TSetupStep);
var
  DbPath: String;
begin
  if CurStep = ssDone then
  begin
    DbPath := ExpandConstant('{userappdata}') + '\..\' + 'garage_reparation\garage.db';
    MsgBox('La base de données sera créée au premier lancement :' + #13#10 + DbPath, mbInformation, MB_OK);
  end;
end;
