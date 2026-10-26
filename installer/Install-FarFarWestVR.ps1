#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$GamePath,
    [string]$UEVRPath,
    [string]$ProfilePath = (Join-Path $env:APPDATA 'UnrealVRMod\FarFarWest-Win64-Shipping'),
    [string]$GameLog = (Join-Path $env:LOCALAPPDATA 'FarFarWest\Saved\Logs\FarFarWest.log'),
    [string]$PackagePath = $PSScriptRoot,
    [string]$DesktopPath = ([Environment]::GetFolderPath('Desktop')),
    [string]$InstallLog = (Join-Path $env:LOCALAPPDATA 'FarFarWestVR\install.log'),
    [switch]$NonInteractive,
    [switch]$NoShortcut
)

$ErrorActionPreference = 'Stop'
$ffwUtf8 = New-Object Text.UTF8Encoding($false)

function Get-FileSha([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Select-Folder([string]$Message) {
    if ($NonInteractive) { throw "$Message Supply the corresponding path parameter." }
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object Windows.Forms.FolderBrowserDialog
    $dialog.Description = $Message
    $dialog.ShowNewFolderButton = $false
    try {
        if ($dialog.ShowDialog() -ne [Windows.Forms.DialogResult]::OK) { throw 'Installation cancelled.' }
        return $dialog.SelectedPath
    } finally { $dialog.Dispose() }
}

function Find-Game {
    $roots = @()
    foreach ($key in @('HKCU:\Software\Valve\Steam', 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam')) {
        $steam = Get-ItemProperty -LiteralPath $key -ErrorAction SilentlyContinue
        if ($steam.SteamPath) { $roots += $steam.SteamPath }
        if ($steam.InstallPath) { $roots += $steam.InstallPath }
    }
    foreach ($root in @($roots)) {
        $vdf = Join-Path $root 'steamapps\libraryfolders.vdf'
        if (Test-Path -LiteralPath $vdf) {
            foreach ($m in [regex]::Matches([IO.File]::ReadAllText($vdf), '"path"\s+"([^"]+)"')) {
                $roots += $m.Groups[1].Value.Replace('\\', '\')
            }
        }
    }
    foreach ($root in ($roots | Select-Object -Unique)) {
        $candidate = Join-Path $root 'steamapps\common\FarFarWest'
        if (Test-Path -LiteralPath (Join-Path $candidate 'FarFarWest\Binaries\Win64\FarFarWest-Win64-Shipping.exe')) {
            return $candidate
        }
    }
    return Select-Folder 'Select the FarFarWest game folder (Steam: Manage > Browse local files).'
}

function Assert-NoGitCheckout([string]$Path) {
    $cursor = [IO.DirectoryInfo][IO.Path]::GetFullPath($Path)
    while ($cursor) {
        if (Test-Path -LiteralPath (Join-Path $cursor.FullName '.git')) {
            throw 'This is a Git development checkout. Use git pull and the existing development workflow instead of this installer.'
        }
        $cursor = $cursor.Parent
    }
}

function Assert-Closed {
    if (Get-Process -Name 'FarFarWest-Win64-Shipping' -ErrorAction SilentlyContinue) {
        throw 'Close Far Far West before installing or updating. No files have been replaced.'
    }
}

function Test-Administrator {
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-GameConfig([string]$Original) {
    $clean = [regex]::Replace($Original, '(?ms)^; BEGIN FarFarWestVR\r?\n.*?^; END FarFarWestVR(?:\r?\n|$)', '')
    $block = @'
; BEGIN FarFarWestVR
[SectionsToSave]
+Section=Core.Log
+Section=SectionsToSave
+Section=SystemSettings

[Core.Log]
LogViewport=VeryVerbose
LogConfig=Verbose

[SystemSettings]
r.PostProcessing.DisableMaterials=1
; END FarFarWestVR
'@
    return $clean.TrimEnd() + "`r`n`r`n" + $block.Replace("`r`n", "`n").Replace("`n", "`r`n") + "`r`n"
}

function Expand-CheckedProfile([string]$ZipPath, [string]$Destination, $Manifest) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [IO.Compression.ZipFile]::OpenRead($ZipPath)
    $seen = @{}
    try {
        foreach ($entry in $zip.Entries) {
            $name = $entry.FullName
            if ($name -match '(^[/\\]|\\|:|(^|/)\.\.(/|$))' -or $seen.ContainsKey($name)) {
                throw "Unsafe or duplicate archive entry: $name"
            }
            $property = $Manifest.files.PSObject.Properties[$name]
            if (-not $property) { throw "File not listed in package manifest: $name" }
            $seen[$name] = $true
            $target = Join-Path $Destination $name
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target)) | Out-Null
            $inputStream = $entry.Open()
            $outputStream = [IO.File]::Create($target)
            try { $inputStream.CopyTo($outputStream) } finally { $inputStream.Dispose(); $outputStream.Dispose() }
            if ((Get-FileSha $target) -ne $property.Value) { throw "Package integrity check failed: $name" }
        }
        if ($seen.Count -ne @($Manifest.files.PSObject.Properties).Count) { throw 'The profile ZIP is incomplete.' }
    } finally { $zip.Dispose() }
}

function New-GameLogLink([string]$Link, [string]$Target) {
    New-Item -ItemType SymbolicLink -Path $Link -Target $Target | Out-Null
}

function Write-GameConfig([string]$Path, [string]$Text) {
    $temporary = Join-Path (Split-Path -Parent $Path) ('.ffw-config-' + [guid]::NewGuid().ToString('N') + '.tmp')
    try {
        [IO.File]::WriteAllText($temporary, $Text, $ffwUtf8)
        if ([IO.File]::Exists($Path)) { [IO.File]::Replace($temporary,$Path,$null) }
        else { [IO.File]::Move($temporary,$Path) }
    } finally {
        if ([IO.File]::Exists($temporary)) { [IO.File]::Delete($temporary) }
    }
}

function Invoke-ProfileInstall([string]$Profile, [string]$LogPath, [string]$GameRoot, [string]$Package) {
    Assert-Closed
    Assert-NoGitCheckout $Profile
    $manifest = Get-Content -LiteralPath (Join-Path $Package 'manifest.json') -Raw | ConvertFrom-Json
    $zipPath = Join-Path $Package 'payload\profile.zip'
    if ((Get-FileSha $zipPath) -ne $manifest.profile_sha256) { throw 'The downloaded profile ZIP failed its checksum. Download the Setup ZIP again.' }
    if (-not (Test-Path -LiteralPath $LogPath -PathType Leaf)) { throw 'Launch Far Far West once normally, close it, then run the installer again.' }
    $configFolder = Join-Path $GameRoot 'FarFarWest\Config'
    if (-not (Test-Path -LiteralPath (Join-Path $GameRoot 'FarFarWest\Binaries\Win64\FarFarWest-Win64-Shipping.exe'))) {
        throw 'The selected game folder does not contain FarFarWest\Binaries\Win64\FarFarWest-Win64-Shipping.exe.'
    }
    $configPath = Join-Path $configFolder 'UserEngine.ini'
    $oldConfig = $null
    if (Test-Path -LiteralPath $configPath) { $oldConfig = [IO.File]::ReadAllBytes($configPath) }
    $original = if ($null -ne $oldConfig) { [IO.File]::ReadAllText($configPath) } else { '' }
    $newConfig = Get-GameConfig $original
    $parent = Split-Path -Parent $Profile
    [IO.Directory]::CreateDirectory($parent) | Out-Null
    $id = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
    $staging = Join-Path $parent ('.ffw-install-' + $id)
    $backup = Join-Path $parent ('FarFarWestVR-Backups\' + $id)
    $hadProfile = Test-Path -LiteralPath $Profile
    $movedOld = $false; $installedNew = $false; $configTouched = $false
    try {
        [IO.Directory]::CreateDirectory($staging) | Out-Null
        Expand-CheckedProfile $zipPath $staging $manifest
        $oldTuning = Join-Path $Profile 'data\tuning.ini'
        if (Test-Path -LiteralPath $oldTuning -PathType Leaf) {
            Copy-Item -LiteralPath $oldTuning -Destination (Join-Path $staging 'data\tuning.ini')
        }
        New-GameLogLink (Join-Path $staging 'data\FarFarWest.log') $LogPath
        Assert-Closed
        [IO.Directory]::CreateDirectory($backup) | Out-Null
        if ($null -ne $oldConfig) { [IO.File]::WriteAllBytes((Join-Path $backup 'UserEngine.ini'), $oldConfig) }
        @{ profile=$Profile; game_config=$configPath; game_config_existed=($null -ne $oldConfig); version=$manifest.version } |
            ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backup 'install.json') -Encoding UTF8
        if ($hadProfile) { Move-Item -LiteralPath $Profile -Destination (Join-Path $backup 'profile'); $movedOld=$true }
        Move-Item -LiteralPath $staging -Destination $Profile; $installedNew=$true
        [IO.Directory]::CreateDirectory($configFolder) | Out-Null
        $configTouched=$true
        Write-GameConfig $configPath $newConfig
        Write-Host "Installed Far Far West VR $($manifest.version)." -ForegroundColor Green
        Write-Host "Profile: $Profile"
        Write-Host "Backup:  $backup"
        Write-Host 'Your tuning.ini was preserved if present. UEVR profile settings use the new beta defaults.'
        return $backup
    } catch {
        if (Test-Path -LiteralPath $backup) { Write-Warning "Installation failed; retained backups: $backup" }
        try {
            if ($configTouched) {
                if ($null -ne $oldConfig) { [IO.File]::WriteAllBytes($configPath,$oldConfig) }
                elseif (Test-Path -LiteralPath $configPath) { Remove-Item -LiteralPath $configPath }
            }
        } finally {
            # Restore the profile even if restoring the game file encounters an I/O error.
            if ($installedNew) { Remove-Item -LiteralPath $Profile -Recurse -Force }
            if ($movedOld) { Move-Item -LiteralPath (Join-Path $backup 'profile') -Destination $Profile }
        }
        throw
    } finally {
        if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force }
    }
}

function Invoke-Installer {
    Write-Host 'Far Far West VR - beta profile installer'
    Write-Host 'The matching custom UEVR runtime is supplied separately; no runtime download or replacement occurs.'
    Assert-Closed
    Assert-NoGitCheckout $ProfilePath
    if (-not $UEVRPath) { $script:UEVRPath = Select-Folder 'Select the matching custom UEVR folder supplied by the maintainer (contains UEVRInjector.exe).' }
    $manifest = Get-Content -LiteralPath (Join-Path $PackagePath 'manifest.json') -Raw | ConvertFrom-Json
    if (-not (Test-Path -LiteralPath (Join-Path $UEVRPath 'UEVRInjector.exe') -PathType Leaf) -or
        -not (Test-Path -LiteralPath (Join-Path $UEVRPath 'UEVRBackend.dll') -PathType Leaf)) {
        throw 'The selected UEVR folder is incomplete. Keep the matching runtime files together.'
    }
    if ((Get-FileSha (Join-Path $UEVRPath 'UEVRBackend.dll')) -ne $manifest.backend_sha256) {
        throw 'This UEVR backend does not match this beta. Obtain the matching custom runtime from the maintainer; stock UEVR is insufficient.'
    }
    if (-not $GamePath) { $script:GamePath = Find-Game }
    if (-not (Test-Path -LiteralPath $GameLog -PathType Leaf)) {
        throw 'Launch Far Far West once normally, close it, then run the installer again.'
    }
    if (-not (Test-Administrator)) {
        if ($NonInteractive) { throw 'Administrator access is needed to create the game-log link and update game configuration.' }
        # Preserve the playing account's resolved paths even when UAC uses another account.
        $arguments = @{
            GamePath=$GamePath; UEVRPath=$UEVRPath; ProfilePath=$ProfilePath;
            GameLog=$GameLog; PackagePath=$PackagePath; DesktopPath=$DesktopPath; InstallLog=$InstallLog
        }
        $command = "& '" + $PSCommandPath.Replace("'","''") + "'"
        foreach ($key in $arguments.Keys) { $command += " -$key '" + $arguments[$key].Replace("'","''") + "'" }
        if ($NoShortcut) { $command += ' -NoShortcut' }
        $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
        Write-Host 'Windows will ask for administrator permission for the log link and game configuration.'
        $child = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -Verb RunAs -Wait -PassThru -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-EncodedCommand',$encoded)
        if ($child.ExitCode -ne 0) { throw "The elevated installer did not finish. Error details: $InstallLog" }
        Write-Host "Installed Far Far West VR $($manifest.version)." -ForegroundColor Green
        Write-Host "Installation details: $InstallLog"
        Write-Host 'Next: connect PC VR/SteamVR, start the game, and open the selected UEVRInjector.exe.'
        return
    }
    $null = Invoke-ProfileInstall $ProfilePath $GameLog $GamePath $PackagePath
    if (-not $NoShortcut) {
        try {
            $shell = New-Object -ComObject WScript.Shell
            $shortcut = $shell.CreateShortcut((Join-Path $DesktopPath 'Far Far West VR.lnk'))
            $shortcut.TargetPath = Join-Path $UEVRPath 'UEVRInjector.exe'
            $shortcut.WorkingDirectory = $UEVRPath
            $shortcut.Save()
        } catch { Write-Warning 'Profile installed, but the desktop shortcut could not be created. Open UEVRInjector.exe manually.' }
    }
    Write-Host 'Next: connect PC VR/SteamVR, start Far Far West, open UEVRInjector.exe, choose OpenVR, then Inject.'
    Write-Host 'Press Insert to close the UEVR panel. Installation help: https://github.com/brifl/FarFarWestVR/issues/new/choose'
}

# Dot-sourcing exposes helpers for isolated Windows tests without running installation.
if ($MyInvocation.InvocationName -ne '.') {
    $transcript = $false
    try {
        if (Test-Administrator) {
            [IO.Directory]::CreateDirectory((Split-Path -Parent $InstallLog)) | Out-Null
            Start-Transcript -LiteralPath $InstallLog -Append | Out-Null
            $transcript=$true
        }
        Invoke-Installer
        if ($transcript) { Stop-Transcript | Out-Null }
        exit 0
    }
    catch {
        Write-Host "Installation stopped: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host 'Help: https://github.com/brifl/FarFarWestVR/issues/new/choose'
        if ($transcript) { Stop-Transcript | Out-Null }
        exit 1
    }
}
