#requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SetupZip, [switch]$RequireRealLinks)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$temp = Join-Path ([IO.Path]::GetTempPath()) ('ffw-installer-tests-' + [guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($temp) | Out-Null
$checks=0
function Check([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
    $script:checks++;Write-Host "PASS $Message"
}
function Must-Fail([scriptblock]$Action,[string]$Message) {
    $failed=$false
    try { & $Action | Out-Null } catch { $failed=$true }
    Check $failed $Message
}
try {
    $package=Join-Path $temp 'package'
    [IO.Compression.ZipFile]::ExtractToDirectory((Resolve-Path -LiteralPath $SetupZip),$package)
    . (Join-Path $package 'Install-FarFarWestVR.ps1')
    $realLinks=Test-Administrator
    if (-not $realLinks) {
        if ($RequireRealLinks) { throw 'This test requires an administrator Windows token for real symbolic links.' }
        function New-GameLogLink([string]$Link,[string]$Target) { [IO.File]::WriteAllText($Link,'TEST LINK PLACEHOLDER') }
        Write-Host 'NOTE: log-link creation is simulated in this non-admin test run.'
    }
    $game=Join-Path $temp 'game';$profile=Join-Path $temp 'profiles\FarFarWest-Win64-Shipping';$log=Join-Path $temp 'FarFarWest.log'
    $config=Join-Path $game 'FarFarWest\Config\UserEngine.ini'
    [IO.Directory]::CreateDirectory((Split-Path -Parent $config)) | Out-Null
    $exe=Join-Path $game 'FarFarWest\Binaries\Win64\FarFarWest-Win64-Shipping.exe'
    [IO.Directory]::CreateDirectory((Split-Path -Parent $exe)) | Out-Null
    [IO.File]::WriteAllText($exe,'TEST EXE');[IO.File]::WriteAllText($log,'first log')
    [IO.File]::WriteAllText($config,"[Custom]`r`nKeepMe=42`r`n")
    $merged=Get-GameConfig ([IO.File]::ReadAllText($config))
    Check ($merged.Contains('KeepMe=42') -and $merged.Contains('LogViewport=VeryVerbose')) 'INI merge preserves unrelated settings and enables menu logging'
    Check ((Get-GameConfig $merged) -ceq $merged) 'INI merge is idempotent'
    $backup=Invoke-ProfileInstall $profile $log $game $package
    Check (Test-Path -LiteralPath (Join-Path $profile 'scripts\controller_aim.lua')) 'Fresh installation creates the complete profile'
    Check ([IO.File]::ReadAllText((Join-Path $profile 'data\controller_aim_backend.txt')) -ceq "ue5-camera-aim-pose-v1`n") 'Controller marker retains exact LF encoding'
    Check (Test-Path -LiteralPath (Join-Path $backup 'UserEngine.ini')) 'Original game configuration is backed up'
    if ($realLinks) {
        $link=Join-Path $profile 'data\FarFarWest.log'
        Check ((Get-Item -LiteralPath $link).LinkType -eq 'SymbolicLink') 'Installer creates a real Windows game-log link'
        Move-Item -LiteralPath $log -Destination ($log+'.old')
        [IO.File]::WriteAllText($log,'rotated log')
        Check ([IO.File]::ReadAllText($link) -ceq 'rotated log') 'Log link follows game-log replacement across launches'
    }
    $tuning=Join-Path $profile 'data\tuning.ini'
    [IO.File]::AppendAllText($tuning,"`n; PERSONAL TUNING`n")
    [IO.File]::WriteAllText((Join-Path $profile 'scripts\obsolete.lua'),'old script')
    $oldTuning=[IO.File]::ReadAllText($tuning)
    $backup2=Invoke-ProfileInstall $profile $log $game $package
    Check ([IO.File]::ReadAllText($tuning) -ceq $oldTuning) 'Updates preserve personal tuning'
    Check (-not (Test-Path -LiteralPath (Join-Path $profile 'scripts\obsolete.lua'))) 'Clean staging removes obsolete scripts from the active install'
    Check (Test-Path -LiteralPath (Join-Path $backup2 'profile\scripts\obsolete.lua')) 'Previous profile remains intact in backup'
    $before=[IO.File]::ReadAllText($config)
    $writer=(Get-Command Write-GameConfig).ScriptBlock
    function Write-GameConfig([string]$Path,[string]$Text) {
        [IO.File]::WriteAllText($Path,'SIMULATED PARTIAL WRITE')
        throw 'SIMULATED GAME CONFIG WRITE FAILURE'
    }
    Must-Fail { Invoke-ProfileInstall $profile $log $game $package } 'Game-configuration write failures abort installation'
    Set-Item Function:\Write-GameConfig $writer
    Check ((Test-Path -LiteralPath $tuning) -and [IO.File]::ReadAllText($tuning) -ceq $oldTuning) 'Failed installation restores the previous profile'
    Check ([IO.File]::ReadAllText($config) -ceq $before) 'Failed installation restores the previous game configuration'
    $zipPath=Join-Path $package 'payload\profile.zip';$zipBytes=[IO.File]::ReadAllBytes($zipPath)
    [IO.File]::WriteAllText($zipPath,'CORRUPT ZIP')
    Must-Fail { Invoke-ProfileInstall $profile $log $game $package } 'Corrupt profile payload is rejected before replacing files'
    [IO.File]::WriteAllBytes($zipPath,$zipBytes)
    [IO.File]::WriteAllText((Join-Path $profile '.git'),'gitdir: development')
    Must-Fail { Invoke-ProfileInstall $profile $log $game $package } 'Development Git checkouts are protected from the end-user installer'
    Remove-Item -LiteralPath (Join-Path $profile '.git')
    function Get-Process { return [pscustomobject]@{ProcessName='FarFarWest-Win64-Shipping'} }
    Must-Fail { Invoke-ProfileInstall $profile $log $game $package } 'A running game prevents installation'
    Remove-Item Function:\Get-Process
    $script:UEVRPath=Join-Path $temp 'wrong-runtime';[IO.Directory]::CreateDirectory($UEVRPath) | Out-Null
    [IO.File]::WriteAllText((Join-Path $UEVRPath 'UEVRInjector.exe'),'TEST INJECTOR')
    [IO.File]::WriteAllText((Join-Path $UEVRPath 'UEVRBackend.dll'),'STOCK OR WRONG BACKEND')
    $script:PackagePath=$package;$script:ProfilePath=$profile;$script:NonInteractive=$true
    Must-Fail { Invoke-Installer } 'Stock or mismatched UEVR is rejected instead of producing an apparently successful install'
    Check ([IO.File]::ReadAllText($tuning) -ceq $oldTuning) 'Rejected runtime leaves the installed profile unchanged'
    $output = & (Join-Path $PSHOME 'powershell.exe') -NoProfile -NonInteractive -ExecutionPolicy Bypass `
        -File (Join-Path $package 'Install-FarFarWestVR.ps1') -UEVRPath $UEVRPath `
        -GamePath $game -GameLog $log -ProfilePath $profile -PackagePath $package `
        -InstallLog (Join-Path $temp 'entrypoint.log') -NoShortcut
    Check ($LASTEXITCODE -eq 1 -and ($output -join "`n").Contains('does not match this beta')) 'Real script entrypoint reports runtime mismatch with a nonzero exit code'
    # A valid outer ZIP hash is insufficient if an inner file differs from its manifest.
    $manifestPath=Join-Path $package 'manifest.json';$manifestBytes=[IO.File]::ReadAllBytes($manifestPath)
    $z=[IO.Compression.ZipFile]::Open($zipPath,[IO.Compression.ZipArchiveMode]::Update)
    try {
        $z.GetEntry('config.txt').Delete();$entry=$z.CreateEntry('config.txt')
        $stream=New-Object IO.StreamWriter($entry.Open());$stream.Write('ALTERED CONFIG');$stream.Dispose()
    } finally { $z.Dispose() }
    $manifest=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $manifest.profile_sha256=Get-FileSha $zipPath
    [IO.File]::WriteAllText($manifestPath,($manifest | ConvertTo-Json -Depth 10),$ffwUtf8)
    Must-Fail { Invoke-ProfileInstall $profile $log $game $package } 'Per-file hashes reject altered content even when the outer checksum matches'
    Check ([IO.File]::ReadAllText($tuning) -ceq $oldTuning) 'Payload staging failure leaves the prior installation intact'
    Write-Host "$checks Windows installer checks passed. Real log links: $realLinks"
} finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}
