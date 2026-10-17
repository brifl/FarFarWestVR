# Read-only, bounded lookup of reticle/HUD objects in the supported game build.
# No injection, function calls inside the game, or process-memory writes.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;

public sealed class FfwReticleReader : IDisposable {
    [DllImport("kernel32.dll", SetLastError=true)]
    private static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
    [DllImport("kernel32.dll", SetLastError=true)]
    private static extern bool CloseHandle(IntPtr process);
    [DllImport("kernel32.dll", SetLastError=true)]
    private static extern bool ReadProcessMemory(IntPtr process, IntPtr address,
        byte[] data, UIntPtr count, out UIntPtr read);

    private readonly IntPtr handle;
    private readonly long moduleBase, moduleEnd;
    private readonly Stopwatch timer = Stopwatch.StartNew();
    private readonly Dictionary<uint, string> names = new Dictionary<uint, string>();
    private readonly Dictionary<long, string> classes = new Dictionary<long, string>();
    private long bytesRead;
    private int calls;
    private const long PoolRva = 0xac9b900;
    private const long ArrayRva = 0xad3d980;

    public FfwReticleReader(uint pid, long start, int size) {
        moduleBase = start; moduleEnd = start + size;
        // PROCESS_QUERY_INFORMATION | PROCESS_VM_READ. Never request VM_WRITE.
        handle = OpenProcess(0x410, false, pid);
        if (handle == IntPtr.Zero) throw new Exception("Cannot open game for reading.");
    }
    public void Dispose() { CloseHandle(handle); }

    private byte[] Read(long address, int size) {
        if (++calls > 1000000 || bytesRead + size > 33554432 || timer.Elapsed.TotalSeconds > 20)
            throw new Exception("Read-only probe budget reached; no game state changed.");
        if (address < 0x10000 || address > 0x7fffffffffff - size || size < 1 || size > 4096)
            return null;
        byte[] data = new byte[size]; UIntPtr read;
        if (!ReadProcessMemory(handle, new IntPtr(address), data, (UIntPtr)size, out read)
            || read.ToUInt64() != (ulong)size) return null;
        bytesRead += size;
        return data;
    }

    private string Name(uint id) {
        string cached;
        if (names.TryGetValue(id, out cached)) return cached;
        uint block = id >> 16;
        if (block >= 8192) return "";
        byte[] ptr = Read(moduleBase + PoolRva + 16 + block * 8L, 8);
        if (ptr == null) return "";
        long entry = BitConverter.ToInt64(ptr, 0) + (id & 65535) * 2L;
        byte[] header = Read(entry, 2);
        if (header == null) return "";
        ushort bits = BitConverter.ToUInt16(header, 0);
        int length = bits >> 6;
        if (length < 1 || length > 1023) return "";
        bool wide = (bits & 1) != 0;
        byte[] text = Read(entry + 2, length * (wide ? 2 : 1));
        if (text == null) return "";
        cached = (wide ? Encoding.Unicode : Encoding.UTF8).GetString(text);
        names[id] = cached;
        return cached;
    }
    private string ObjectName(byte[] data) {
        string name = Name(BitConverter.ToUInt32(data, 24));
        uint number = BitConverter.ToUInt32(data, 28);
        return number == 0 || name.Length == 0 ? name : name + "_" + (number - 1);
    }
    private string ClassName(long address) {
        string name;
        if (classes.TryGetValue(address, out name)) return name;
        byte[] data = Read(address, 40);
        name = data == null ? "" : ObjectName(data);
        classes[address] = name;
        return name;
    }
    private static string Hex(long address) { return "0x" + address.ToString("x"); }
    private static bool Relevant(string name) {
        string n = name.ToLowerInvariant();
        return n.Contains("crosshair") || n.Contains("reticle") || n.Contains("reticule")
            || n.Contains("wbp_hud") || n.Contains("w_hud") || n.Contains("playerhud")
            || n == "ui_player_c";
    }

    private object DescribeWidgetClass(long klass) {
        var result = new List<object>();
        var seenClasses = new HashSet<long>();
        for (int depth = 0; klass != 0 && depth < 8 && seenClasses.Add(klass); ++depth) {
            byte[] prefix = Read(klass, 96);
            if (prefix == null) break;
            var fields = new List<object>();
            var seenFields = new HashSet<long>();
            // Observed UStruct layout; keep the raw field header to verify its
            // type/offset interpretation before using any field in a fix.
            long field = BitConverter.ToInt64(prefix, 80);
            for (int i = 0; field != 0 && i < 256 && seenFields.Add(field); ++i) {
                byte[] data = Read(field, 112);
                if (data == null) break;
                long vt = BitConverter.ToInt64(data, 0);
                if (vt < moduleBase || vt >= moduleEnd) break;
                string name = Name(BitConverter.ToUInt32(data, 32));
                long type = BitConverter.ToInt64(data, 8);
                byte[] typeData = Read(type, 32);
                string typeName = "";
                if (typeData != null) {
                    for (int n = 0; n < 32; n += 8) {
                        string candidate = Name(BitConverter.ToUInt32(typeData, n));
                        if (candidate.EndsWith("Property")) { typeName = candidate; break; }
                    }
                }
                fields.Add(new { address = Hex(field), name = name, type = typeName,
                    header = BitConverter.ToString(data) });
                field = BitConverter.ToInt64(data, 24);
            }
            result.Add(new { address = Hex(klass), name = ObjectName(prefix), fields = fields });
            klass = BitConverter.ToInt64(prefix, 64);
        }
        return result;
    }

    public object Scan() {
        if (Name(0) != "None") throw new Exception("Name-pool validation failed; nothing changed.");
        byte[] h = Read(moduleBase + ArrayRva, 24);
        if (h == null) throw new Exception("Object-array header unreadable.");
        long chunks = BitConverter.ToInt64(h, 0);
        int count = BitConverter.ToInt32(h, 8), capacity = BitConverter.ToInt32(h, 12);
        int numChunks = BitConverter.ToInt32(h, 16), maxChunks = BitConverter.ToInt32(h, 20);
        if (count < 2 || count > 250000 || numChunks < 1 || numChunks > 4
            || maxChunks < numChunks || maxChunks > 1024 || capacity != maxChunks * 65536
            || count > numChunks * 65536)
            throw new Exception("Object-array layout differs from the verified build.");
        byte[] chunkData = Read(chunks, numChunks * 8);
        if (chunkData == null) throw new Exception("Chunk pointers unreadable.");
        var matches = new List<object>();
        var classHeaders = new Dictionary<string, string>();
        var widgetClasses = new HashSet<long>();
        for (int i = 0; i < count; ++i) {
            long chunk = BitConverter.ToInt64(chunkData, (i / 65536) * 8);
            byte[] item = Read(chunk + (i % 65536) * 24L, 24);
            if (item == null) continue;
            long address = BitConverter.ToInt64(item, 8);
            byte[] data = Read(address, 40);
            if (data == null || BitConverter.ToInt32(data, 12) != i) continue;
            long vtable = BitConverter.ToInt64(data, 0);
            if (vtable < moduleBase || vtable >= moduleEnd) continue;
            string name = ObjectName(data);
            if (i < 2 && name != (i == 0 ? "/Script/CoreUObject" : "Object"))
                throw new Exception("UObject/FName layout validation failed.");
            long klass = BitConverter.ToInt64(data, 16);
            string className = ClassName(klass);
            if (!Relevant(name) && !Relevant(className)) continue;
            if (className == "Image" || className == "UI_Player_C") widgetClasses.Add(klass);
            if (matches.Count >= 128) throw new Exception("Too many HUD matches; narrow the filter.");
            long outer = BitConverter.ToInt64(data, 32);
            byte[] outerData = Read(outer, 40);
            if (!classHeaders.ContainsKey(Hex(klass))) {
                byte[] prefix = Read(klass, 256);
                classHeaders[Hex(klass)] = prefix == null ? "" : BitConverter.ToString(prefix);
            }
            matches.Add(new { index = i, address = Hex(address), name = name,
                classAddress = Hex(klass), className = className,
                outer = Hex(outer), outerName = outerData == null ? "" : ObjectName(outerData),
                item = BitConverter.ToString(item) });
        }
        var widgetProperties = new List<object>();
        foreach (long klass in widgetClasses) widgetProperties.Add(DescribeWidgetClass(klass));
        return new { objectCount = count, bytesRead = bytesRead, readCalls = calls,
            seconds = timer.Elapsed.TotalSeconds, matches = matches, classHeaders = classHeaders,
            widgetProperties = widgetProperties };
    }
}
'@

$game = Get-Process -Name 'FarFarWest-Win64-Shipping' -ErrorAction SilentlyContinue
if (@($game).Count -ne 1) { throw 'Leave one Far Far West instance open in the saloon.' }
$module = $game.MainModule
$binary = New-Object System.IO.BinaryReader([System.IO.File]::OpenRead($module.FileName))
try {
    $binary.BaseStream.Position = 0x3c
    $pe = $binary.ReadUInt32()
    $binary.BaseStream.Position = $pe + 8
    $timestamp = $binary.ReadUInt32()
    $binary.BaseStream.Position = $pe + 24 + 56
    $imageSize = $binary.ReadUInt32()
} finally { $binary.Dispose() }
if ($timestamp -ne 907750432 -or $imageSize -ne 203960320 -or $module.ModuleMemorySize -ne $imageSize) {
    throw 'Executable differs from the verified 0.2.0.20 build; nothing changed.'
}
$reader = New-Object FfwReticleReader -ArgumentList @([uint32]$game.Id, $module.BaseAddress.ToInt64(), [int]$imageSize)
try {
    $result = $reader.Scan()
    [ordered]@{processId=$game.Id; gameBase=('0x{0:x}' -f $module.BaseAddress.ToInt64());
        timestamp=$timestamp; imageSize=$imageSize; result=$result} | ConvertTo-Json -Depth 8
} finally { $reader.Dispose() }
