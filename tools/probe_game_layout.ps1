# Read-only discovery of the compact object array and FName pool after a game update.
# Scans only the main executable's .data section; never writes process memory.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
public sealed class FfwLayoutReader : IDisposable {
    [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(uint access,bool inherit,uint pid);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll")] static extern bool ReadProcessMemory(IntPtr handle,IntPtr address,byte[] data,UIntPtr size,out UIntPtr read);
    readonly IntPtr handle; readonly long start,end;
    readonly Stopwatch timer=Stopwatch.StartNew();
    int calls; long bytes;
    public FfwLayoutReader(uint pid,long address,int size) {
        start=address;end=start+size;handle=OpenProcess(0x410,false,pid);
        if(handle==IntPtr.Zero) throw new Exception("Cannot open game for reading");
    }
    public void Dispose(){CloseHandle(handle);}
    byte[] Read(long address,int size) {
        if(++calls>100000 || bytes+size>33554432 || timer.Elapsed.TotalSeconds>20)
            throw new Exception("Read-only probe budget reached");
        if(address<65536 || address>0x7fffffffffff-size || size<1 || size>8388608)return null;
        var data=new byte[size]; UIntPtr read;
        if(!ReadProcessMemory(handle,new IntPtr(address),data,(UIntPtr)size,out read) || read.ToUInt64()!=(ulong)size)return null;
        bytes+=size;return data;
    }
    string Name(long pool,uint id) {
        uint block=id>>16;if(block>=8192)return "";
        var p=Read(pool+16+8L*block,8);if(p==null)return "";
        long entry=BitConverter.ToInt64(p,0)+(id&65535)*2L;
        var h=Read(entry,2);if(h==null)return "";
        ushort bits=BitConverter.ToUInt16(h,0);int len=bits>>6;
        if(len<1 || len>1023)return "";
        bool wide=(bits&1)!=0;var data=Read(entry+2,len*(wide?2:1));
        return data==null ? "" : (wide?Encoding.Unicode:Encoding.UTF8).GetString(data);
    }
    public object Scan(int rva,int size) {
        if(size<24 || size>8388608 || start+rva+size>end)throw new Exception("Unexpected .data extent");
        var data=Read(start+rva,size);if(data==null)throw new Exception("Unreadable .data section");
        var arrays=new List<long>();var pools=new List<long>();
        for(int i=0;i<=data.Length-24;i+=8) {
            int count=BitConverter.ToInt32(data,i+8),capacity=BitConverter.ToInt32(data,i+12);
            int chunks=BitConverter.ToInt32(data,i+16),max=BitConverter.ToInt32(data,i+20);
            if(count>=4 && count<=250000 && chunks>=1 && chunks<=4 && max>=chunks && max<=1024
                && capacity==max*65536 && count<=chunks*65536) {
                var pointers=Read(BitConverter.ToInt64(data,i),chunks*8);
                var items=pointers==null?null:Read(BitConverter.ToInt64(pointers,0),24*4);
                bool valid=items!=null;
                for(int n=0;valid && n<4;n++) {
                    var obj=Read(BitConverter.ToInt64(items,n*24+8),40);
                    valid=obj!=null && BitConverter.ToInt32(obj,12)==n
                        && BitConverter.ToInt64(obj,0)>=start && BitConverter.ToInt64(obj,0)<end;
                }
                if(valid)arrays.Add(start+rva+i);
            }
            uint block=BitConverter.ToUInt32(data,i+8),cursor=BitConverter.ToUInt32(data,i+12);
            if(block<8192 && cursor>0 && cursor<=131072) {
                var first=Read(BitConverter.ToInt64(data,i+16),6);
                if(first!=null && (BitConverter.ToUInt16(first,0)>>6)==4
                    && Encoding.ASCII.GetString(first,2,4)=="None")pools.Add(start+rva+i);
            }
        }
        if(arrays.Count!=1 || pools.Count!=1)throw new Exception("Expected unique array/pool; found "+arrays.Count+"/"+pools.Count);
        long array=arrays[0],pool=pools[0];var header=Read(array,24);
        int total=BitConverter.ToInt32(header,8);var list=Read(BitConverter.ToInt64(header,0),BitConverter.ToInt32(header,16)*8);
        var samples=new List<object>();
        foreach(int index in new[]{0,1,2,3,1023,65535,65536,total-1}) {
            if(index>=total)continue;
            long chunk=BitConverter.ToInt64(list,index/65536*8);
            var item=Read(chunk+index%65536*24L,24);var obj=item==null?null:Read(BitConverter.ToInt64(item,8),40);
            if(obj==null)continue;
            if(BitConverter.ToInt32(obj,12)!=index)throw new Exception("Object index mismatch at "+index);
            string name=Name(pool,BitConverter.ToUInt32(obj,24));
            if(index==0 && name!="/Script/CoreUObject" || index==1 && name!="Object")throw new Exception("Name/object identity mismatch");
            samples.Add(new{index=index,name=name,address="0x"+BitConverter.ToInt64(item,8).ToString("x")});
        }
        return new{arrayRva="0x"+(array-start).ToString("x"),poolRva="0x"+(pool-start).ToString("x"),
            objectCount=total,header=BitConverter.ToString(header),samples=samples,bytesRead=bytes,readCalls=calls,seconds=timer.Elapsed.TotalSeconds};
    }
}
'@
$game=Get-Process -Name FarFarWest-Win64-Shipping -ErrorAction Stop
if(@($game).Count -ne 1){throw 'Leave exactly one game instance open.'}
$module=$game.MainModule
$binary=[IO.BinaryReader]::new([IO.File]::OpenRead($module.FileName))
try {
    $binary.BaseStream.Position=0x3c;$pe=$binary.ReadUInt32()
    $binary.BaseStream.Position=$pe+6;$count=$binary.ReadUInt16();$timestamp=$binary.ReadUInt32()
    $binary.BaseStream.Position=$pe+20;$optional=$binary.ReadUInt16()
    $binary.BaseStream.Position=$pe+24+56;$imageSize=$binary.ReadUInt32()
    if($imageSize -ne $module.ModuleMemorySize){throw 'Image size mismatch.'}
    $section=$null
    for($i=0;$i -lt $count;$i++) {
        $binary.BaseStream.Position=$pe+24+$optional+$i*40
        $name=[Text.Encoding]::ASCII.GetString($binary.ReadBytes(8)).Trim([char]0)
        $size=$binary.ReadUInt32();$rva=$binary.ReadUInt32()
        if($name -eq '.data'){$section=@{size=$size;rva=$rva}}
    }
    if(!$section){throw 'Missing .data section.'}
} finally {$binary.Dispose()}
$reader=[FfwLayoutReader]::new([uint32]$game.Id,$module.BaseAddress.ToInt64(),[int]$imageSize)
try {
    @{processId=$game.Id;timestamp=$timestamp;imageSize=$imageSize;result=$reader.Scan($section.rva,$section.size)}|ConvertTo-Json -Depth 6
} finally {$reader.Dispose()}
