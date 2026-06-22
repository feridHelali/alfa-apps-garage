; ===========================================================================
; Inno Setup — Gestion Réparation Voiture v1.0.0
; Alfa Computers Apps
;
; Build via build.ps1 or manually:
;   iscc /DArch=x64 /DAppVersion=1.0.0 installer\setup.iss
;   iscc /DArch=x86 /DAppVersion=1.0.0 installer\setup.iss
; ===========================================================================

; ---- Defaults (overridden by build.ps1 CLI defines) ----------------------
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#ifndef Arch
  #define Arch "x64"
#endif

; ---- Application constants -----------------------------------------------
#define AppName        "Gestion Réparation Voiture"
#define AppPublisher   "Alfa Computers Apps"
#define AppURL         "https://alfa-computers.com"
#define AppContact     "Ferid HELALI — helaliferid@gmail.com — +216 22 45 79 16"
#define AppExeName     "GarageReparation.exe"
#define DistDir        "..\dist\" + Arch + "\GarageReparation"
#define DBBrowserDir   "tools\DBBrowserForSQLite"

; ---- Architecture-dependent defaults -------------------------------------
#if Arch == "x86"
  #define ArchLabel    "32-bit"
  #define OutSuffix    "x86"
#else
  #define ArchLabel    "64-bit"
  #define OutSuffix    "x64"
#endif

; ==========================================================================
[Setup]
AppId={{A1F4C0DE-DEAD-BEEF-C0FE-GARAGE2025001}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion} ({#ArchLabel})
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppPublisher}\{#AppName}
DefaultGroupName={#AppPublisher}\{#AppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=GarageReparationSetup_{#AppVersion}_{#OutSuffix}
SetupIconFile=..\assets\icons\app_icon.ico
WizardImageFile=wizard_image.bmp
WizardSmallImageFile=wizard_small_image.bmp
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ChangesAssociations=no
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName}
AppComments={#AppContact}

#if Arch == "x64"
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
#endif

; ==========================================================================
[Languages]
Name: "french";  MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

; ==========================================================================
[Types]
Name: "full";    Description: "Installation complète"
Name: "compact"; Description: "Application uniquement"
Name: "custom";  Description: "Installation personnalisée"; Flags: iscustom

[Components]
Name: "main";      Description: "Application Gestion Réparation Voiture"; Types: full compact custom; Flags: fixed
Name: "dbbrowser"; Description: "DB Browser for SQLite (outil d''administration)"; Types: full; ExtraDiskSpaceRequired: 20971520

; ==========================================================================
[Tasks]
Name: "desktopicon";        Description: "{cm:CreateDesktopIcon}";            GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon";        Description: "Lancer au démarrage de Windows";    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "dbbrowser_shortcut"; Description: "Raccourci bureau pour DB Browser";   GroupDescription: "DB Browser for SQLite"; Components: dbbrowser; Flags: unchecked

; ==========================================================================
[Files]
; Main application
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: main

; DB Browser for SQLite (portable) — optional, place at installer\tools\DBBrowserForSQLite\
Source: "{#DBBrowserDir}\*"; DestDir: "{app}\tools\DBBrowserForSQLite"; \
  Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; Components: dbbrowser

; ==========================================================================
[Icons]
Name: "{group}\{#AppName}";                          Filename: "{app}\{#AppExeName}"; Components: main
Name: "{group}\{cm:UninstallProgram,{#AppName}}";    Filename: "{uninstallexe}";       Components: main
Name: "{autodesktop}\{#AppName}";                    Filename: "{app}\{#AppExeName}";  Tasks: desktopicon; Components: main

Name: "{group}\DB Browser for SQLite";               Filename: "{app}\tools\DBBrowserForSQLite\DB Browser for SQLite.exe"; Components: dbbrowser
Name: "{autodesktop}\DB Browser for SQLite";         Filename: "{app}\tools\DBBrowserForSQLite\DB Browser for SQLite.exe"; Tasks: dbbrowser_shortcut; Components: dbbrowser

; ==========================================================================
[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "{#AppName}"; ValueData: """{app}\{#AppExeName}"""; \
  Tasks: startupicon; Flags: uninsdeletevalue

; ==========================================================================
[Run]
Filename: "{app}\{#AppExeName}"; \
  Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; \
  Flags: nowait postinstall skipifsilent; Components: main

; ==========================================================================
[Code]

var
  LicencePage:  TInputQueryWizardPage;
  DataDirPage:  TInputDirWizardPage;

// ---------------------------------------------------------------------------
// CRC32 checksum — mirrors Python zlib.crc32 for offline key validation
// ---------------------------------------------------------------------------
function Crc32Byte(Crc: LongWord; B: Byte): LongWord;
var
  I: Integer;
begin
  Crc := Crc xor B;
  for I := 0 to 7 do
  begin
    if (Crc and 1) <> 0 then
      Crc := (Crc shr 1) xor $EDB88320
    else
      Crc := Crc shr 1;
  end;
  Result := Crc;
end;

function Crc32Str(S: String): LongWord;
var
  I: Integer;
begin
  Result := $FFFFFFFF;
  for I := 1 to Length(S) do
    Result := Crc32Byte(Result, Ord(S[I]));
  Result := Result xor $FFFFFFFF;
end;

function HexChar(N: Byte): Char;
const
  HEX: String = '0123456789ABCDEF';
begin
  Result := HEX[N + 1];
end;

function DWordToHex8(D: LongWord): String;
begin
  Result :=
    HexChar((D shr 28) and $F) +
    HexChar((D shr 24) and $F) +
    HexChar((D shr 20) and $F) +
    HexChar((D shr 16) and $F) +
    HexChar((D shr 12) and $F) +
    HexChar((D shr  8) and $F) +
    HexChar((D shr  4) and $F) +
    HexChar( D         and $F);
end;

// ---------------------------------------------------------------------------
// Validate key:  ALFA-G1-G2-G3-CHCK
// Returns True when format and CRC checksum are correct.
// ---------------------------------------------------------------------------
function IsValidLicenceKey(Key: String): Boolean;
var
  Parts:    TStringList;
  G1, G2, G3, Chk, Expected: String;
  Crc:      LongWord;
begin
  Result := False;
  Parts := TStringList.Create;
  try
    Parts.Delimiter := '-';
    Parts.StrictDelimiter := True;
    Parts.DelimitedText := Uppercase(Key);
    if Parts.Count <> 5 then Exit;
    if Parts[0] <> 'ALFA' then Exit;
    G1  := Parts[1];
    G2  := Parts[2];
    G3  := Parts[3];
    Chk := Parts[4];
    if (Length(G1) <> 4) or (Length(G2) <> 4) or
       (Length(G3) <> 4) or (Length(Chk) <> 4) then Exit;
    Crc := Crc32Str(G1 + G2 + G3);
    Expected := Copy(DWordToHex8(Crc), 5, 4);   // last 4 chars of 8-char hex
    Result := (Chk = Expected);
  finally
    Parts.Free;
  end;
end;

// ---------------------------------------------------------------------------
// Wizard setup
// ---------------------------------------------------------------------------
procedure InitializeWizard();
var
  DefaultDataDir: String;
begin
  // --- Licence key page (appears before wpSelectDir) ---
  LicencePage := CreateInputQueryPage(
    wpWelcome,
    'Clé de licence',
    'Entrez votre clé de licence pour activer le logiciel',
    'Votre clé de licence est fournie par Alfa Computers Apps.' + #13#10
    + 'Format : ALFA-XXXX-XXXX-XXXX-XXXX' + #13#10 + #13#10
    + 'Contact : helaliferid@gmail.com  |  +216 22 45 79 16' + #13#10
    + 'Site    : https://alfa-computers.com'
  );
  LicencePage.Add('Clé de licence :', False);

  // --- Data directory page (appears after wpSelectDir) ---
  DefaultDataDir := ExpandConstant('{%USERPROFILE}') + '\.garage_reparation';
  DataDirPage := CreateInputDirPage(
    wpSelectDir,
    'Répertoire des données',
    'Choisissez où stocker la base de données et les sauvegardes',
    'Le dossier sélectionné sera utilisé pour la base de données (garage.db) '
    + 'et les sauvegardes automatiques.' + #13#10
    + 'Vous pouvez conserver le répertoire par défaut ou en choisir un autre '
    + '(ex. un dossier synchronisé ou sauvegardé automatiquement).',
    False,
    'garage_reparation'
  );
  DataDirPage.Add('');
  DataDirPage.Values[0] := DefaultDataDir;
end;

// ---------------------------------------------------------------------------
// Per-page validation on Next
// ---------------------------------------------------------------------------
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;

  if CurPageID = LicencePage.ID then
  begin
    if not IsValidLicenceKey(LicencePage.Values[0]) then
    begin
      MsgBox(
        'Clé de licence invalide.' + #13#10 + #13#10 +
        'Vérifiez la clé et réessayez.' + #13#10 +
        'Format attendu : ALFA-XXXX-XXXX-XXXX-XXXX',
        mbError, MB_OK
      );
      Result := False;
      Exit;
    end;
  end;

  if CurPageID = DataDirPage.ID then
  begin
    if DataDirPage.Values[0] = '' then
    begin
      MsgBox('Veuillez sélectionner un répertoire de données.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not ForceDirectories(DataDirPage.Values[0]) then
    begin
      MsgBox(
        'Impossible de créer le répertoire :' + #13#10 + DataDirPage.Values[0]
        + #13#10 + 'Vérifiez les permissions et réessayez.',
        mbError, MB_OK
      );
      Result := False;
    end;
  end;
end;

// ---------------------------------------------------------------------------
// Write config files after installation
// ---------------------------------------------------------------------------
procedure CurStepChanged(CurStep: TSetupStep);
var
  DataDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Write licence.key so the app skips its own activation dialog
    SaveStringToFile(
      ExpandConstant('{app}') + '\licence.key',
      Uppercase(LicencePage.Values[0]),
      False
    );

    // Write data_dir.cfg so the app uses the chosen data directory
    DataDir := DataDirPage.Values[0];
    if DataDir <> '' then
    begin
      SaveStringToFile(ExpandConstant('{app}') + '\data_dir.cfg', DataDir, False);
      ForceDirectories(DataDir);
      ForceDirectories(DataDir + '\snapshots');
    end;
  end;
end;
