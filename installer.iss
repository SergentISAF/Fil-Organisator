; ================================================================
;  Fil-Organisator  –  Inno Setup installationsscript
;  Kør via: byg_installer.bat
; ================================================================

[Setup]
AppName=Fil-Organisator
AppVersion=3.8
AppPublisher=Danho
AppPublisherURL=
DefaultDirName={autopf}\Fil-Organisator
DefaultGroupName=Fil-Organisator
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=FilOrganisator_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\FilOrganisator.exe
UninstallDisplayName=Fil-Organisator

; Vis et velkomstbillede i installationsguiden
WizardImageStretch=yes

[Languages]
; Brug dansk hvis tilgængeligt, ellers engelsk
Name: "danish";  MessagesFile: "compiler:Languages\Danish.isl"

[Tasks]
Name: "desktopicon"; Description: "Opret genvej på skrivebordet"; GroupDescription: "Genveje:"
Name: "startmenu";   Description: "Opret genvej i Startmenuen";   GroupDescription: "Genveje:"

[Files]
; Kopier hele PyInstaller-mappen til installationsmappen
Source: "dist\FilOrganisator\*"; \
    DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Startmenu
Name: "{group}\Fil-Organisator"; \
    Filename: "{app}\FilOrganisator.exe"; \
    Tasks: startmenu

Name: "{group}\Afinstaller Fil-Organisator"; \
    Filename: "{uninstallexe}"; \
    Tasks: startmenu

; Skrivebord
Name: "{commondesktop}\Fil-Organisator"; \
    Filename: "{app}\FilOrganisator.exe"; \
    Tasks: desktopicon

[Run]
; Tilbyd at starte programmet med det samme efter installation
Filename: "{app}\FilOrganisator.exe"; \
    Description: "Start Fil-Organisator nu"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Ryd evt. cache-filer når programmet afinstalleres
Type: filesandordirs; Name: "{app}"
