; Script Inno Setup per ToulMap
; Richiede Inno Setup 6.x — https://jrsoftware.org/isinfo.php
; Compilare con: iscc toulmap_installer.iss

#define MyAppName      "ToulMap"
#define MyAppVersion   "1.0"
#define MyAppPublisher "Antonio Vigilante"
#define MyAppURL       "https://antonio-vigilante.github.io/toulmap"
#define MyAppExeName   "ToulMap.exe"
#define MyAppDir       "dist\ToulMap"

[Setup]
AppId={{A3F2C1D4-7B8E-4F2A-9C1D-E5F6A7B8C9D0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Compressione massima
Compression=lzma2/ultra64
SolidCompression=yes
; Icona del programma di installazione (opzionale)
; SetupIconFile=toulmap.ico
WizardStyle=modern
WizardSizePercent=110
; L'installer non richiede privilegi di amministratore
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=installer_output
OutputBaseFilename=ToulMap_Setup_v{#MyAppVersion}
; Lingua
ShowLanguageDialog=no

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon";    Description: "Crea un'icona sul Desktop"; GroupDescription: "Icone aggiuntive:"
Name: "quicklaunchicon"; Description: "Crea un'icona nella barra Avvio rapido"; GroupDescription: "Icone aggiuntive:"; Flags: unchecked

[Files]
; Copia l'intera cartella dist\ToulMap generata da PyInstaller
Source: "{#MyAppDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}";                  Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Disinstalla {#MyAppName}";      Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}";          Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
// Controlla se una versione precedente è installata e la rimuove
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    // nessuna azione speciale necessaria
  end;
end;
