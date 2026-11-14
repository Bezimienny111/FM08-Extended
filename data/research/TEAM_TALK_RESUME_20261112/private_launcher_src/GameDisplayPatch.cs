using System.Buffers.Binary;

namespace FmLauncher;

internal sealed record DisplayLaunchSettings(DisplayMode Mode, Resolution Resolution, Rectangle Desktop)
{
    internal Rectangle WorkArea { get; init; } = Desktop;
}

internal static class GameDisplayPatch
{
    internal const uint OpenAddress = 0x0104D560;
    internal const uint CreatedAddress = 0x0104DCEA;
    internal const uint ExitAddress = 0x0104E037;
    internal const uint StyleAddress = 0x0104D8BE;
    internal const uint ResizeAddress = 0x0104D260;
    internal const int StateSize = 24;

    internal static string Arguments(DisplayMode mode) =>
        mode == DisplayMode.Fullscreen ? "--fullscreen --small_screen" : "--windowed --small_screen";

    internal static byte[] Open(uint address, uint state, DisplayLaunchSettings settings, byte[] original)
    {
        Validate(settings);
        var code = new List<byte>();
        StoreAbsolute(code, state + 12, 0);
        StoreAbsolute(code, state + 8, uint.MaxValue);
        StoreStack(code, 0x0C, settings.Resolution.Width);
        StoreStack(code, 0x10, settings.Resolution.Height);
        code.AddRange([0x80, 0x64, 0x24, 0x14, 0xF0]); // clear native mode/maximize/restore flags
        code.AddRange([0x80, 0x4C, 0x24, 0x14, settings.Mode == DisplayMode.Window ? (byte)1 : (byte)4]);
        StoreStack(code, 0x18, settings.Resolution.Height);
        StoreStack(code, 0x1C, settings.Resolution.Height);
        StoreStack(code, 0x20, settings.Resolution.Width);
        StoreStack(code, 0x24, settings.Resolution.Width);
        code.AddRange(original);
        ReturnTo(code, address, OpenAddress + (uint)original.Length);
        return code.ToArray();
    }

    internal static byte[] Created(uint address, uint state, DisplayLaunchSettings settings, byte[] original)
    {
        Validate(settings);
        var code = new List<byte> { 0x9C, 0x60 }; // preserve flags and registers across MoveWindow
        code.AddRange([0x8B, 0x86, 0xB4, 0, 0, 0]); // native render-window HWND
        code.Add(0xA3);
        UInt32(code, state);
        code.AddRange([0x89, 0x35]); // retain the render-surface object for exact buffer verification
        UInt32(code, state + 16);
        if (settings.Mode != DisplayMode.Fullscreen)
        {
            Push(code, 0);
            if (settings.Mode == DisplayMode.Window)
            {
                // Native creation omits the fixed frame from the outer size.
                code.AddRange([0x0F, 0xB7, 0x8E, 0xAA, 0, 0, 0, 0x0F, 0xB7, 0x96, 0xAE, 0, 0, 0, 0x03, 0xCA]);
                AddImmediate(code, 0xC1, settings.Resolution.Height);
                code.Add(0x51);
                code.AddRange([0x0F, 0xB7, 0x96, 0xAC, 0, 0, 0, 0x03, 0xD2]);
                AddImmediate(code, 0xC2, settings.Resolution.Width);
                code.Add(0x52);
                CenterCoordinate(code, settings.WorkArea.Height, settings.WorkArea.Top, 0xD9);
                CenterCoordinate(code, settings.WorkArea.Width, settings.WorkArea.Left, 0xDA);
            }
            else
            {
                Push(code, settings.Resolution.Height);
                Push(code, settings.Resolution.Width);
                Push(code, settings.Desktop.Top + (settings.Desktop.Height - settings.Resolution.Height) / 2);
                Push(code, settings.Desktop.Left + (settings.Desktop.Width - settings.Resolution.Width) / 2);
            }
            code.Add(0x50);
            code.AddRange([0xFF, 0x15]);
            UInt32(code, 0x0121A3B0); // verified FM08 MoveWindow import
            code.Add(0xA3);
            UInt32(code, state + 4);
        }
        else StoreAbsolute(code, state + 4, 1);
        code.AddRange([0x61, 0x9D]);
        if (settings.Mode == DisplayMode.Borderless)
        {
            // Use native popup geometry, but do not enter the exclusive display-switch branch.
            code.AddRange([0x80, 0xA4, 0x24, 0x28, 0x02, 0, 0, 0xF0]);
            code.AddRange([0x80, 0x8C, 0x24, 0x28, 0x02, 0, 0, 1]);
        }
        code.AddRange(original);
        ReturnTo(code, address, CreatedAddress + (uint)original.Length);
        return code.ToArray();
    }

    internal static byte[] Exit(uint address, uint state, byte[] original)
    {
        var code = new List<byte> { 0x50, 0x0F, 0xB7, 0xC0, 0xA3 };
        UInt32(code, state + 8);
        code.Add(0x58);
        StoreAbsolute(code, state + 12, 1);
        code.AddRange(original);
        ReturnTo(code, address, ExitAddress + (uint)original.Length);
        return code.ToArray();
    }

    internal static byte[] Style(uint address, byte[] original)
    {
        var code = new List<byte>();
        StoreStack(code, 0x14, 0x00CA0000); // caption, system menu and minimize; no resizing/maximize
        code.AddRange(original);
        ReturnTo(code, address, StyleAddress + (uint)original.Length);
        return code.ToArray();
    }

    internal static byte[] Resize(uint address, DisplayLaunchSettings settings, byte[] original)
    {
        Validate(settings);
        var code = new List<byte>();
        StoreStack(code, 4, settings.Resolution.Width);
        StoreStack(code, 8, settings.Resolution.Height);
        code.AddRange(original);
        ReturnTo(code, address, ResizeAddress + (uint)original.Length);
        return code.ToArray();
    }

    private static void Validate(DisplayLaunchSettings settings)
    {
        if (!Enum.IsDefined(settings.Mode) || settings.Resolution.Width is < 640 or > 1920
            || settings.Resolution.Height is < 480 or > 1080
            || settings.Resolution.Width > settings.Desktop.Width || settings.Resolution.Height > settings.Desktop.Height)
            throw new LauncherException("InvalidGameResolution");
    }

    private static void StoreAbsolute(List<byte> code, uint address, uint value)
    {
        code.AddRange([0xC7, 0x05]);
        UInt32(code, address);
        UInt32(code, value);
    }
    private static void StoreStack(List<byte> code, byte offset, int value)
    {
        code.AddRange([0xC7, 0x44, 0x24, offset]);
        UInt32(code, unchecked((uint)value));
    }
    private static void Push(List<byte> code, int value)
    {
        code.Add(0x68);
        UInt32(code, unchecked((uint)value));
    }
    private static void AddImmediate(List<byte> code, byte operand, int value)
    {
        code.AddRange([0x81, operand]);
        UInt32(code, unchecked((uint)value));
    }
    private static void CenterCoordinate(List<byte> code, int extent, int origin, byte subtract)
    {
        code.Add(0xBB);
        UInt32(code, (uint)extent);
        code.AddRange([0x2B, subtract, 0xD1, 0xFB]);
        AddImmediate(code, 0xC3, origin);
        code.Add(0x53);
    }
    private static void UInt32(List<byte> code, uint value)
    {
        var bytes = new byte[4];
        BinaryPrimitives.WriteUInt32LittleEndian(bytes, value);
        code.AddRange(bytes);
    }
    private static void ReturnTo(List<byte> code, uint address, uint destination) =>
        code.AddRange(SuspendedGameProcess.BuildJump(address + (uint)code.Count, destination, 5));
}
