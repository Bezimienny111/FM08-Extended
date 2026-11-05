using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using FmLauncher;
using Microsoft.Win32.SafeHandles;

internal sealed class PanelRemoteProcess : IDisposable
{
    private readonly SuspendedGameProcess game;
    private readonly SafeProcessHandle process;

    internal PanelRemoteProcess(string path)
    {
        game = new SuspendedGameProcess(path);
        process = OpenProcess(0x1FFFFF, false, game.ProcessId);
        if (process.IsInvalid)
        {
            game.Dispose();
            throw new Win32Exception(Marshal.GetLastWin32Error());
        }
    }

    internal IntPtr Allocate(int address, uint size)
    {
        var result = VirtualAllocEx(process, new IntPtr(address), (nuint)size, 0x3000, 0x40);
        if (result != new IntPtr(address)) throw new Win32Exception(Marshal.GetLastWin32Error());
        return result;
    }

    internal byte[] Read(IntPtr address, int count)
    {
        var bytes = new byte[count];
        if (!ReadProcessMemory(process, address, bytes, (nuint)count, out var actual) || actual != (nuint)count)
            throw new Win32Exception(Marshal.GetLastWin32Error());
        return bytes;
    }

    internal void Write(IntPtr address, byte[] bytes)
    {
        if (!VirtualProtectEx(process, address, (nuint)bytes.Length, 0x40, out var old))
            throw new Win32Exception(Marshal.GetLastWin32Error());
        try
        {
            if (!WriteProcessMemory(process, address, bytes, (nuint)bytes.Length, out var actual)
                || actual != (nuint)bytes.Length || !FlushInstructionCache(process, address, (nuint)bytes.Length))
                throw new Win32Exception(Marshal.GetLastWin32Error());
        }
        finally
        {
            if (!VirtualProtectEx(process, address, (nuint)bytes.Length, old, out _))
                throw new Win32Exception(Marshal.GetLastWin32Error());
        }
    }

    internal int Call(int address, params int[] arguments)
    {
        var bytes = new List<byte>();
        foreach (var argument in arguments.Reverse())
        {
            bytes.Add(0x68);
            bytes.AddRange(BitConverter.GetBytes(argument));
        }
        bytes.Add(0xB8);
        bytes.AddRange(BitConverter.GetBytes(address));
        bytes.AddRange([0xFF, 0xD0, 0x83, 0xC4, checked((byte)(arguments.Length * 4)), 0xA3]);
        bytes.AddRange(BitConverter.GetBytes(0x1200F100));
        bytes.AddRange([0x33, 0xC0, 0xC2, 0x04, 0]);
        Write(new IntPtr(0x1200F000), bytes.ToArray());
        using var thread = CreateRemoteThread(process, IntPtr.Zero, 0, new IntPtr(0x1200F000),
            IntPtr.Zero, 0, out _);
        if (thread.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
        if (WaitForSingleObject(thread, 10000) != 0)
            throw new InvalidOperationException("Native panel test thread timed out.");
        if (!GetExitCodeThread(thread, out var exitCode)) throw new Win32Exception(Marshal.GetLastWin32Error());
        if (exitCode != 0) throw new InvalidOperationException($"Native panel test at {address:X8} crashed: {exitCode:X8}.");
        return BitConverter.ToInt32(Read(new IntPtr(0x1200F100), 4));
    }

    public void Dispose()
    {
        process.Dispose();
        game.Dispose();
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern SafeProcessHandle OpenProcess(uint access, bool inherit, int id);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr VirtualAllocEx(SafeProcessHandle process, IntPtr address, nuint size, uint type, uint protection);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool ReadProcessMemory(SafeProcessHandle process, IntPtr address, byte[] bytes, nuint count, out nuint actual);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool WriteProcessMemory(SafeProcessHandle process, IntPtr address, byte[] bytes, nuint count, out nuint actual);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool VirtualProtectEx(SafeProcessHandle process, IntPtr address, nuint count, uint protection, out uint old);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool FlushInstructionCache(SafeProcessHandle process, IntPtr address, nuint count);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern SafeWaitHandle CreateRemoteThread(SafeProcessHandle process, IntPtr attributes, nuint stack,
        IntPtr start, IntPtr argument, uint flags, out uint id);
    [DllImport("kernel32.dll")]
    private static extern uint WaitForSingleObject(SafeWaitHandle thread, uint milliseconds);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GetExitCodeThread(SafeWaitHandle thread, out uint exitCode);
}

internal static class PanelRemoteMemory
{
    internal static PanelRemoteProcess Process { get; set; } = null!;
    internal static int ReadInt32(IntPtr address, int offset = 0) =>
        BitConverter.ToInt32(Process.Read(IntPtr.Add(address, offset), 4));
    internal static short ReadInt16(IntPtr address, int offset = 0) =>
        BitConverter.ToInt16(Process.Read(IntPtr.Add(address, offset), 2));
    internal static void WriteInt32(IntPtr address, int value) => WriteInt32(address, 0, value);
    internal static void WriteInt32(IntPtr address, int offset, int value) =>
        Process.Write(IntPtr.Add(address, offset), BitConverter.GetBytes(value));
    internal static void WriteInt16(IntPtr address, int offset, short value) =>
        Process.Write(IntPtr.Add(address, offset), BitConverter.GetBytes(value));
    internal static void WriteByte(IntPtr address, byte value) => Process.Write(address, [value]);
    internal static void WriteByte(IntPtr address, int offset, byte value) => WriteByte(IntPtr.Add(address, offset), value);
    internal static void Copy(byte[] source, int start, IntPtr target, int count) =>
        Process.Write(target, source.AsSpan(start, count).ToArray());
    internal static void Copy(int[] source, int start, IntPtr target, int count) =>
        Process.Write(target, source.Skip(start).Take(count).SelectMany(BitConverter.GetBytes).ToArray());
    internal static void Copy(IntPtr source, byte[] target, int start, int count) =>
        Process.Read(source, count).CopyTo(target, start);
    internal static string PtrToStringUni(IntPtr address, int count) =>
        Encoding.Unicode.GetString(Process.Read(address, checked(count * 2)));
}
