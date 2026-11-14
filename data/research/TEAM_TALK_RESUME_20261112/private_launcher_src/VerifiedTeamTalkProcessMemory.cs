using System.ComponentModel;
using System.Reflection.PortableExecutable;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Win32.SafeHandles;

namespace FmLauncher;

// Not enabled by the private UI. Opening requires an explicitly pinned request.
internal sealed class VerifiedTeamTalkProcessMemory : ITeamTalkReadMemory
{
    private const string SupportedHash = "157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d";
    private readonly SafeProcessHandle handle;
    private readonly TeamTalkProcess expected;
    private readonly byte[] image;
    private readonly PEHeaders headers;
    private readonly string imagePath;
    internal VerifiedTeamTalkProcessMemory(TeamTalkReadRequest request)
    {
        expected=request.Process;
        if(expected.Pid<=0 || expected.Sha256!=SupportedHash)
            throw new InvalidDataException("Unpinned target/hash.");
        handle=OpenProcess(0x410,false,expected.Pid);
        if(handle.IsInvalid)throw new Win32Exception(Marshal.GetLastWin32Error());
        try
        {
            imagePath=QueryPath();
            if(!string.Equals(Path.GetFileName(imagePath),"fm.exe",StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Target is not fm.exe.");
            image=File.ReadAllBytes(imagePath);
            if(Convert.ToHexString(SHA256.HashData(image)).ToLowerInvariant()!=SupportedHash)
                throw new InvalidDataException("Executable hash rejected.");
            using var pe=new PEReader(new MemoryStream(image,false));
            headers=pe.PEHeaders;
            if(headers.PEHeader is null || headers.PEHeader.ImageBase!=0x400000 ||
                headers.PEHeader.Magic!=PEMagic.PE32 || ((int)headers.PEHeader.DllCharacteristics&0x40)!=0)
                throw new InvalidDataException("Image base/architecture/ASLR rejected.");
            if(!Read(0x400000,64).SequenceEqual(image.AsSpan(0,64).ToArray()) || ReadIdentity()!=expected)
                throw new InvalidDataException("Runtime mapping/generation rejected.");
        }
        catch {handle.Dispose();throw;}
    }
    private string QueryPath()
    {
        var path=new StringBuilder(32768);uint length=(uint)path.Capacity;
        if(!QueryFullProcessImageName(handle,0,path,ref length))
            throw new Win32Exception(Marshal.GetLastWin32Error());
        return path.ToString();
    }
    public TeamTalkProcess ReadIdentity()
    {
        if(!GetProcessTimes(handle,out long creation,out _,out _,out _))
            throw new Win32Exception(Marshal.GetLastWin32Error());
        if(!string.Equals(QueryPath(),imagePath,StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Process image path changed.");
        return new(expected.Pid,creation,SupportedHash);
    }
    public byte[] Read(uint address,int bytes)
    {
        if(address<0x10000 || bytes<1 || bytes>4096 || (ulong)address+(uint)bytes>0x100000000UL)
            throw new InvalidDataException("Unbounded read.");
        byte[] buffer=new byte[bytes];
        if(!ReadProcessMemory(handle,(nint)(long)address,buffer,(nuint)bytes,out nuint got) || got!=(nuint)bytes)
            throw new InvalidDataException("ReadProcessMemory incomplete.");
        return buffer;
    }
    public uint VerifiedFileU32(uint address)
    {
        if(address<0x400000)throw new InvalidDataException("File VA outside supported image.");
        long rva=address-0x400000;
        foreach(var section in headers.SectionHeaders)
        {
            long relative=rva-section.VirtualAddress;
            if(relative>=0 && relative+4<=section.SizeOfRawData)
            {
                long offset=section.PointerToRawData+relative;
                if(offset<0 || offset+4>image.Length)break;
                return System.Buffers.Binary.BinaryPrimitives.ReadUInt32LittleEndian(image.AsSpan((int)offset,4));
            }
        }
        throw new InvalidDataException("Verified image does not contain getter.");
    }
    public void Dispose()=>handle.Dispose();
    [DllImport("kernel32.dll",SetLastError=true)]
    private static extern SafeProcessHandle OpenProcess(uint access,bool inherit,int pid);
    [DllImport("kernel32.dll",SetLastError=true)]
    private static extern bool ReadProcessMemory(SafeProcessHandle process,nint address,[Out]byte[] buffer,nuint size,out nuint bytesRead);
    [DllImport("kernel32.dll",SetLastError=true,CharSet=CharSet.Unicode,EntryPoint="QueryFullProcessImageNameW")]
    private static extern bool QueryFullProcessImageName(SafeProcessHandle process,uint flags,StringBuilder path,ref uint size);
    [DllImport("kernel32.dll",SetLastError=true)]
    private static extern bool GetProcessTimes(SafeProcessHandle process,out long creation,out long exit,out long kernel,out long user);
}
