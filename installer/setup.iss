; Inno Setup Script for MATLAB MCP Server
; Requires Inno Setup 6.0 or later: https://jrsoftware.org/isinfo.php

#define MyAppName "MATLAB MCP Server"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "MATLAB MCP Project"
#define MyAppURL "https://github.com/yourusername/matlab-mcp-server"
#define MyAppExeName "matlab-mcp-server.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
AppId={{8F3D9A2B-C1E4-4B5A-9D3E-2F1A8B7C6D5E}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE
InfoBeforeFile=..\installer\INSTALL_INFO.txt
OutputDir=..\dist\installer
OutputBaseFilename=matlab-mcp-server-setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\matlab-mcp-server\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\.env.example"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\README.md"; Description: "View README"; Flags: postinstall shellexec skipifsilent unchecked

[Code]
var
  MatlabPathPage: TInputDirWizardPage;
  ConfigFilePath: String;

procedure InitializeWizard;
begin
  { Create custom page for MATLAB path }
  MatlabPathPage := CreateInputDirPage(wpSelectDir,
    'Select MATLAB Installation',
    'Where is MATLAB installed?',
    'Please select the folder where MATLAB is installed, then click Next.' + #13#10 + #13#10 +
    'Example paths:' + #13#10 +
    '  C:\Program Files\MATLAB\R2024b' + #13#10 +
    '  C:\Program Files\MATLAB\R2023b',
    False, '');

  MatlabPathPage.Add('MATLAB Installation Path:');

  { Try to find MATLAB automatically }
  if DirExists('C:\Program Files\MATLAB\R2024b') then
    MatlabPathPage.Values[0] := 'C:\Program Files\MATLAB\R2024b'
  else if DirExists('C:\Program Files\MATLAB\R2023b') then
    MatlabPathPage.Values[0] := 'C:\Program Files\MATLAB\R2023b';
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  MatlabPath: String;
begin
  Result := True;

  if CurPageID = MatlabPathPage.ID then
  begin
    MatlabPath := MatlabPathPage.Values[0];

    { Validate MATLAB path }
    if not DirExists(MatlabPath) then
    begin
      MsgBox('The specified MATLAB path does not exist. Please select a valid MATLAB installation folder.', mbError, MB_OK);
      Result := False;
    end
    else if not FileExists(MatlabPath + '\bin\matlab.exe') then
    begin
      MsgBox('The selected folder does not appear to contain a valid MATLAB installation. Please select the correct folder.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvContent: TStringList;
  MatlabPath: String;
  ClaudeConfigPath: String;
  ClaudeConfig: String;
  AppPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    { Create .env file with MATLAB path }
    MatlabPath := MatlabPathPage.Values[0];
    AppPath := ExpandConstant('{app}');

    EnvContent := TStringList.Create;
    try
      EnvContent.Add('# MATLAB installation path');
      EnvContent.Add('MATLAB_PATH=' + MatlabPath);
      EnvContent.Add('');
      EnvContent.Add('# Optional: Directory for saving MATLAB scripts and outputs');
      EnvContent.Add('MATLAB_WORKSPACE_DIR=' + AppPath + '\matlab_workspace');
      EnvContent.Add('');
      EnvContent.Add('# Optional: Default figure export resolution (DPI)');
      EnvContent.Add('MATLAB_FIGURE_DPI=300');

      EnvContent.SaveToFile(AppPath + '\.env');
    finally
      EnvContent.Free;
    end;

    { Show configuration instructions }
    ClaudeConfigPath := ExpandConstant('{%APPDATA}\Claude\claude_desktop_config.json');
    ClaudeConfig := '{'#13#10 +
      '  "mcpServers": {'#13#10 +
      '    "matlab": {'#13#10 +
      '      "command": "' + AppPath + '\matlab-mcp-server.exe",'#13#10 +
      '      "env": {'#13#10 +
      '        "MATLAB_PATH": "' + MatlabPath + '"'#13#10 +
      '      }'#13#10 +
      '    }'#13#10 +
      '  }'#13#10 +
      '}';

    { Save configuration example to file }
    EnvContent := TStringList.Create;
    try
      EnvContent.Text := ClaudeConfig;
      EnvContent.SaveToFile(AppPath + '\claude_config_example.json');
    finally
      EnvContent.Free;
    end;

    MsgBox('Installation complete!' + #13#10 + #13#10 +
           'Next steps:' + #13#10 +
           '1. Add the configuration from claude_config_example.json to:' + #13#10 +
           '   ' + ClaudeConfigPath + #13#10 + #13#10 +
           '2. Restart Claude Desktop' + #13#10 + #13#10 +
           '3. The MATLAB MCP Server will be available as the "matlab" server',
           mbInformation, MB_OK);
  end;
end;
