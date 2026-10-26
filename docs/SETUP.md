# Installing Far Far West VR

This beta adds PC VR support to the Steam version of Far Far West. UEVR loads
the VR support into the running game; this project supplies the game’s profile,
scripts, and controls. You need a Windows PC capable of PC VR, your own game,
SteamVR, and a connected headset. A Quest must be connected to the PC for PC VR;
copying these files onto the headset will not install it.

**This release does not include UEVR.** The matching custom runtime is not
publicly downloadable yet, pending redistribution permission. Installation
currently requires an existing copy of that runtime. First-time users must wait
for runtime availability; [ask about installation or availability](https://github.com/brifl/FarFarWestVR/issues/new?template=installation.yml)
if unsure. Stock UEVR lacks our required compatibility changes.
Keep the complete runtime folder together, including its injector and companion
DLLs. The installer checks its backend before replacing your profile.

## Install with the Windows script

1. Launch Far Far West normally once, then close it.
2. From the [beta release page](https://github.com/brifl/FarFarWestVR/releases/tag/v0.1.0-beta.1),
   download **`FarFarWestVR-0.1.0-beta.1-Setup.zip`** under **Assets**. Use this
   asset rather than GitHub’s automatically generated Source code ZIP.
3. Right-click the ZIP → **Properties → Unblock → Apply**, if Unblock is shown.
   Then use **Extract All** to extract the whole ZIP.
4. Open the extracted folder and double-click **`Install-FarFarWestVR.cmd`**.
   Keep its accompanying PowerShell script, `manifest.json`, and `payload` folder together.
5. Select the matching custom UEVR folder containing `UEVRInjector.exe`. Steam
   libraries are detected automatically. If asked for the game folder, select
   the folder Steam opens through Far Far West → **Manage → Browse local files**.
6. Approve the Windows administrator prompt for the game-log link and game
   configuration. The installer retains the playing account’s resolved paths.
7. Wait for the green **Installed Far Far West VR** message. Errors remain in
   the command window. Elevated runs also log to
   `%LOCALAPPDATA%\FarFarWestVR\install.log` for the playing account.

No Python, Git, WSL, Epic account, or development tools are needed. Installation
works offline once you have the Setup ZIP and matching runtime. It does not
download DLLs or replace the selected runtime.

The profile installs here:

```text
%APPDATA%\UnrealVRMod\FarFarWest-Win64-Shipping\
```

Updates preserve `data\tuning.ini`, use clean beta UEVR settings, and remove
obsolete scripts from the active profile. The previous profile and original
game configuration remain in a timestamped folder here:

```text
%APPDATA%\UnrealVRMod\FarFarWestVR-Backups\
```

Development Git checkouts are protected: continue using Git/WSL deployment there.

## Start playing

1. Connect the headset for PC VR and start **SteamVR**. The tested setup is Quest 3
   with Virtual Desktop connected to the PC.
2. Start Far Far West through Steam.
3. Open the **Far Far West VR** desktop shortcut, or `UEVRInjector.exe` in the
   matching custom runtime folder. If the injector requests a Microsoft .NET
   runtime, follow its Microsoft link and install the **Desktop Runtime** version
   it requests; you do not need the developer SDK.
4. Select **FarFarWest-Win64-Shipping**, choose **OpenVR**, and click **Inject**.
5. Press **Insert** to close the UEVR panel. Keep the desktop game window focused.
   Point in menus with the right controller and click with its trigger. In
   gameplay, aiming is independent of where you look. **B** pauses and resumes.

For map/horse shortcuts, open UEVR with **Insert**, enable **D-pad Shifting**, and
select **Gesture (Head) + Left Joystick**. The [controls table](https://github.com/brifl/FarFarWestVR#quest-controls)
lists the directions. Adjust HUD size/margins, aiming stabilization, steering,
and graphics in the installed `data\tuning.ini`; numeric edits reload during play.

Use a normal game relaunch after installing updates. Avoid **Reset scripts**,
which can disrupt the current session.

## Download and Windows warnings

The ZIPs contain plugin DLLs; you do not need to download them individually.
Browsers may warn about uncommon downloads, and Windows may warn about unsigned
scripts or executables. A warning alone does not prove a file safe or unsafe.
Microsoft explains [how SmartScreen checks downloads](https://support.microsoft.com/en-us/edge/how-can-smartscreen-help-protect-me-in-microsoft-edge).

- Download from **github.com/brifl/FarFarWestVR/releases**. For an uncommon-download
  warning, review the source in the browser’s Downloads list and use **Keep** or
  **Keep anyway** if offered and you trust this beta. Wording varies by browser.
- Before extraction, right-click the ZIP → **Properties → Unblock → Apply**, if
  present. This is Windows’ [per-file unblock procedure](https://support.microsoft.com/en-us/windows/security/information-about-the-attachment-manager-in-microsoft-windows).
- For an unsigned-app reputation warning, review **More info** and the publisher
  before deciding whether to use **Run anyway**, if Windows offers it.
- If antivirus reports a specific threat or Windows offers no way to proceed,
  stop and [open an installation issue](https://github.com/brifl/FarFarWestVR/issues/new?template=installation.yml)
  with the detection name and affected file. Do not turn off antivirus, SmartScreen,
  or global PowerShell protections to install this beta.

The CMD launcher permits its accompanying PowerShell script for that process
only; it does not change your saved execution policy. The installer validates
the profile ZIP and every file before activating it. For an optional download
integrity check, compare this output with `SHA256SUMS.txt` on the release page:

```powershell
Get-FileHash .\FarFarWestVR-0.1.0-beta.1-Setup.zip -Algorithm SHA256
```

## If installation or play fails

[Open an installation-help issue](https://github.com/brifl/FarFarWestVR/issues/new?template=installation.yml)
or [report a gameplay/UI bug](https://github.com/brifl/FarFarWestVR/issues/new?template=bug_report.yml).
Include the beta/game versions, headset/PC VR connection, the failing step, and
the exact error. A screenshot helps; remove private information from attached logs.

- **Wrong backend:** obtain the matching custom runtime. Renaming a stock DLL
  does not add the required changes.
- **Game log missing:** launch the game once normally, then close it before installing.
- **Game not found:** select Steam’s Browse local files folder, not an inner Binaries folder.
- **No controller input:** focus the game window and close the UEVR panel with Insert.
- **A new patch breaks scripts:** report the new game version; the backend may need an update.

## Manual profile ZIP for experienced users

`FarFarWestVR-0.1.0-beta.1-Profile.zip` has `config.txt` at its root. It omits
the installer, runtime, development caches, and captures. The Setup ZIP is
recommended because copying a profile alone does not configure the log connection.

To install manually, close the game, back up the old profile, and extract the
Profile ZIP’s contents into the AppData profile folder above. The included
`data\controller_aim_backend.txt` enables aiming. Merge this into the game’s
**FarFarWest\Config\UserEngine.ini** beneath its Steam folder, preserving other settings:

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

The last line removes the heat distortion and other custom post-process materials.
The game’s generated AppData Engine.ini is not the persistent configuration location.
Then create the link in administrator Windows PowerShell under the playing account:

```powershell
$profileData = Join-Path $env:APPDATA 'UnrealVRMod\FarFarWest-Win64-Shipping\data'
$gameLog = Join-Path $env:LOCALAPPDATA 'FarFarWest\Saved\Logs\FarFarWest.log'
New-Item -ItemType SymbolicLink -Path (Join-Path $profileData 'FarFarWest.log') -Target $gameLog
```

If a file already occupies that link path, inspect and back it up first. Copying
a log manually will not keep the helper connected across game launches.
