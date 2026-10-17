# Read-only probe of the candidates UEVR already logged for this game instance.
# Run from WSL with Windows PowerShell while Far Far West is in the saloon.
# Emits JSON; does not write process memory, change settings, or enumerate objects.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class FfwProcessMemory {
    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern IntPtr OpenProcess(uint access, bool inherit, uint processId);
    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll", SetLastError=true)]
    private static extern bool ReadProcessMemory(IntPtr process, IntPtr address,
        byte[] buffer, UIntPtr size, out UIntPtr read);
    public static byte[] Read(IntPtr process, long address, int count) {
        if (address < 0x10000 || address > 0x7fffffffffff || count < 1 || count > 4096)
            return null;
        byte[] data = new byte[count];
        UIntPtr read;
        if (!ReadProcessMemory(process, new IntPtr(address), data, (UIntPtr)count, out read)
            || read.ToUInt64() != (ulong)count) return null;
        return data;
    }
}
'@

$game = Get-Process -Name 'FarFarWest-Win64-Shipping' -ErrorAction SilentlyContinue
if (@($game).Count -ne 1) { throw 'Expected one running Far Far West instance; leave it open in the saloon.' }
$module = $game.MainModule
$gameBase = $module.BaseAddress.ToInt64()
$gameEnd = $gameBase + $module.ModuleMemorySize
# Restrict the logged candidates to writable PE sections, where globals live.
$binary = New-Object System.IO.BinaryReader([System.IO.File]::OpenRead($module.FileName))
$writable = @()
try {
    $binary.BaseStream.Position = 0x3c
    $peOffset = $binary.ReadUInt32()
    $binary.BaseStream.Position = $peOffset + 8
    $timestamp = $binary.ReadUInt32()
    $binary.BaseStream.Position = $peOffset + 24 + 56
    $imageSize = $binary.ReadUInt32()
    $binary.BaseStream.Position = $peOffset + 6
    $sectionCount = $binary.ReadUInt16()
    $binary.BaseStream.Position = $peOffset + 20
    $optionalSize = $binary.ReadUInt16()
    $binary.BaseStream.Position = $peOffset + 24 + $optionalSize
    for ($i = 0; $i -lt $sectionCount; $i++) {
        $section = $binary.ReadBytes(40)
        if (([BitConverter]::ToUInt32($section, 36) -band 0x80000000L) -ne 0) {
            $start = $gameBase + [BitConverter]::ToUInt32($section, 12)
            $size = [Math]::Max([BitConverter]::ToUInt32($section, 8), [BitConverter]::ToUInt32($section, 16))
            $writable += @{start=$start; end=$start+$size}
        }
    }
} finally { $binary.Dispose() }
$logPath = 'C:\Users\brian\AppData\Roaming\UnrealVRMod\FarFarWest-Win64-Shipping\log.txt'
if ((Get-Item $logPath).LastWriteTime -lt $game.StartTime) {
    throw 'UEVR log predates this game instance; wait for injection before probing.'
}
$candidates = New-Object 'System.Collections.Generic.HashSet[long]'
$stream = [System.IO.File]::Open($logPath, 'Open', 'Read', 'ReadWrite, Delete')
$reader = New-Object System.IO.StreamReader($stream)
try {
    $characters = 0
    while (($line = $reader.ReadLine()) -ne $null -and $characters -lt 4194304) {
        $characters += $line.Length
        if ($line -match '(?:potential GUObjectArray|Found GUObjectArray) at (?:0x)?([0-9a-fA-F]+)') {
            $address = [Convert]::ToInt64($Matches[1], 16)
            if (($address -band 7) -eq 0 -and
                @($writable | Where-Object { $address -ge $_.start -and $address -le $_.end - 128 }).Count) {
                $null = $candidates.Add($address)
            }
        }
        if ($line.Contains('Failed to find GUObjectArray')) { break }
    }
} finally { $reader.Dispose() }
if ($candidates.Count -eq 0) { throw 'No current-module object-array candidates found in the UEVR log.' }
if ($candidates.Count -gt 512) { throw 'More than 512 writable candidates; narrow the probe before reading.' }

# PROCESS_QUERY_INFORMATION | PROCESS_VM_READ only.
$handle = [FfwProcessMemory]::OpenProcess(0x410, $false, $game.Id)
if ($handle -eq [IntPtr]::Zero) { throw 'Cannot open this game instance for read-only memory access.' }
$results = @()
try {
    foreach ($address in ($candidates | Sort-Object)) {
        [byte[]]$header = [FfwProcessMemory]::Read($handle, $address, 128)
        if ($null -eq $header) { continue }
        $layouts = @()
        # Find the chunked array header without assuming the surrounding GC fields.
        foreach ($offset in (0..8 | ForEach-Object { $_ * 8 })) {
          foreach ($variant in ('legacy', 'compact')) {
            $objects = [BitConverter]::ToInt64($header, $offset)
            if ($variant -eq 'legacy') {
                $capacity = [BitConverter]::ToInt32($header, $offset + 16)
                $count = [BitConverter]::ToInt32($header, $offset + 20)
                $maxChunks = [BitConverter]::ToInt32($header, $offset + 24)
                $numChunks = [BitConverter]::ToInt32($header, $offset + 28)
            } else {
                $count = [BitConverter]::ToInt32($header, $offset + 8)
                $capacity = [BitConverter]::ToInt32($header, $offset + 12)
                $numChunks = [BitConverter]::ToInt32($header, $offset + 16)
                $maxChunks = [BitConverter]::ToInt32($header, $offset + 20)
            }
            if ($count -le 0 -or $capacity -lt $count -or $capacity -gt 67108864 -or
                $numChunks -lt 1 -or $maxChunks -lt $numChunks -or $maxChunks -gt 4096 -or
                $capacity -ne $maxChunks * 65536 -or $count -gt $numChunks * 65536) { continue }
            [byte[]]$chunkPointers = [FfwProcessMemory]::Read($handle, $objects, 16)
            if ($null -eq $chunkPointers) { continue }
            $firstChunk = [BitConverter]::ToInt64($chunkPointers, 0)
            [byte[]]$items = [FfwProcessMemory]::Read($handle, $firstChunk, 256)
            if ($null -eq $items) { continue }
            $samples = @()
            foreach ($itemOffset in (0, 8, 16, 24, 32, 48, 56, 64, 72, 80, 96)) {
                $object = [BitConverter]::ToInt64($items, $itemOffset)
                [byte[]]$objectData = [FfwProcessMemory]::Read($handle, $object, 48)
                if ($null -eq $objectData) { continue }
                $vtable = [BitConverter]::ToInt64($objectData, 0)
                if ($vtable -ge $gameBase -and $vtable -lt $gameEnd) {
                    $samples += [ordered]@{itemOffset=$itemOffset; address=('0x{0:x}' -f $object);
                        objectIndex=[BitConverter]::ToInt32($objectData, 12);
                        vtableRva=('0x{0:x}' -f ($vtable-$gameBase)); bytes=([BitConverter]::ToString($objectData))}
                }
            }
            $layouts += [ordered]@{variant=$variant; offset=$offset; capacity=$capacity; count=$count;
                maxChunks=$maxChunks; numChunks=$numChunks; firstChunk=('0x{0:x}' -f $firstChunk);
                items=([BitConverter]::ToString($items)); samples=$samples}
          }
        }
        $results += [ordered]@{rva=('0x{0:x}' -f ($address-$gameBase));
            header=([BitConverter]::ToString($header)); layouts=$layouts}
    }
} finally { $null = [FfwProcessMemory]::CloseHandle($handle) }
[ordered]@{processId=$game.Id; gameBase=('0x{0:x}' -f $gameBase);
    executable=$module.FileName; timestamp=$timestamp; imageSize=$imageSize;
    candidates=$results} | ConvertTo-Json -Depth 8 -Compress
