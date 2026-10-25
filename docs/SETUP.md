# Required one-time Windows setup

Follow this after installing the matching beta runtime and copying the profile
as described in the [README](../README.md#installation). Launch the game once in
desktop mode, then close it before continuing. No WSL, Python, or development
tools are needed for these steps.

## 1. Configure the game

In Steam, right-click **Far Far West → Manage → Browse local files**. Open the
`FarFarWest` folder inside that location, then its `Config` folder.

Create a text file named **`UserEngine.ini`** there. If you use Notepad, choose
**Save as type: All files** so it does not become `UserEngine.ini.txt`.
If the file already exists, keep its other settings and merge the sections below.

```ini
[SectionsToSave]
+Section=Core.Log
+Section=SectionsToSave
+Section=SystemSettings

[Core.Log]
LogViewport=VeryVerbose
LogConfig=Verbose

[SystemSettings]
r.PostProcessing.DisableMaterials=1
```

The logging settings let the extension distinguish menus, loading screens, and
gameplay. The last setting applies the heat-distortion workaround. It also
disables other custom post-process materials; remove that line if you prefer
the game's original effects. Changes to this file require a game restart.

Use the game's `Config\UserEngine.ini` location above. The game rewrites its
generated settings under AppData, so edits there may not persist.

## 2. Connect the profile to the game log and enable aiming

Open **Windows PowerShell as administrator**, using the same Windows account you
use to play. Administrator access is used to create a Windows file link. Paste
this block and press Enter:

```powershell
$ErrorActionPreference = 'Stop'
$ffwProfile = Join-Path $env:APPDATA 'UnrealVRMod\FarFarWest-Win64-Shipping'
$ffwData = Join-Path $ffwProfile 'data'
$ffwLog = Join-Path $env:LOCALAPPDATA 'FarFarWest\Saved\Logs\FarFarWest.log'
$ffwLink = Join-Path $ffwData 'FarFarWest.log'

if (-not (Test-Path -LiteralPath $ffwLog)) {
    throw 'Start Far Far West once in desktop mode, close it, then retry.'
}
New-Item -ItemType Directory -Path $ffwData -Force | Out-Null
$ffwExisting = Get-Item -LiteralPath $ffwLink -Force -ErrorAction SilentlyContinue
if ($ffwExisting -and $ffwExisting.LinkType -ne 'SymbolicLink') {
    throw 'The profile already contains a regular FarFarWest.log file. Move that file elsewhere, then retry.'
}
if (-not $ffwExisting) {
    New-Item -ItemType SymbolicLink -Path $ffwLink -Target $ffwLog | Out-Null
}
[IO.File]::WriteAllText(
    (Join-Path $ffwData 'controller_aim_backend.txt'),
    "ue5-camera-aim-pose-v1`n",
    [Text.UTF8Encoding]::new($false)
)
Write-Host 'Far Far West VR setup complete.'
```

The file link keeps the profile connected to the current game log across launches.
Copying a log into the profile manually will not keep it up to date. The small
aiming file enables the controller bridge in the matching custom backend.

## 3. Check the first launch

Return to the [launch instructions](../README.md#installation). After injection,
press **Insert** to close the UEVR settings panel if it is covering the game.
You should be able to point at menus with the right controller and click with its
trigger. In gameplay, looking around and aiming should work independently.

For map and horse shortcuts, enable **D-pad Shifting → Gesture (Head) + Left
Joystick** in UEVR. Keep the game window focused for input.

If controller aiming is missing or menus remain in the wrong mode, check that
both setup steps completed and that you are running the matching beta runtime.
Relaunch the game after correcting the setup. Use a normal relaunch rather than
**Reset scripts**.

For everyday adjustments, use [data/tuning.ini](../data/tuning.ini), as explained
in the [README configuration section](../README.md#configuration). Those numeric
settings reload during play.
