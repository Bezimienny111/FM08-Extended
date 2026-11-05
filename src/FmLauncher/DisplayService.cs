using System.ComponentModel;
using System.Runtime.InteropServices;

namespace FmLauncher;

public static class DisplayService
{
    public static IReadOnlyList<Resolution> Detect() => Detect(DisplayMode.Fullscreen);

    public static IReadOnlyList<Resolution> Detect(DisplayMode mode)
    {
        var screen = Screen.PrimaryScreen ?? throw new LauncherException("NoDisplay");
        var device = screen.DeviceName;
        var current = new DeviceMode { Size = (ushort)Marshal.SizeOf<DeviceMode>() };
        if (!EnumDisplaySettings(device, -1, ref current))
            throw new LauncherException("DisplayError", new Win32Exception(Marshal.GetLastWin32Error()).Message);
        var modes = new HashSet<Resolution>();
        for (var index = 0; ; index++)
        {
            var candidate = new DeviceMode { Size = (ushort)Marshal.SizeOf<DeviceMode>() };
            if (!EnumDisplaySettings(device, index, ref candidate)) break;
            if (candidate.BitsPerPixel == current.BitsPerPixel)
                modes.Add(new Resolution((int)candidate.Width, (int)candidate.Height));
        }
        var desktop = new Resolution((int)current.Width, (int)current.Height);
        var available = FilterAndOrder(modes, desktop);
        return FilterForGame(available, mode, screen.WorkingArea.Size, FrameSize());
    }

    internal static IReadOnlyList<Resolution> FilterForGame(IEnumerable<Resolution> modes, DisplayMode mode,
        Size workArea, Size frame)
    {
        if (!Enum.IsDefined(mode)) throw new LauncherException("InvalidDisplayMode");
        var result = modes.Where(resolution => resolution.Width is >= 640 and <= 1920
            && resolution.Height is >= 480 and <= 1080
            && (mode != DisplayMode.Window || resolution.Width + frame.Width <= workArea.Width
                && resolution.Height + frame.Height <= workArea.Height)).ToList();
        if (result.Count == 0) throw new LauncherException("NoSafeResolution");
        return result;
    }

    internal static Rectangle DesktopBounds() =>
        (Screen.PrimaryScreen ?? throw new LauncherException("NoDisplay")).Bounds;

    internal static Resolution CurrentResolution()
    {
        var screen = Screen.PrimaryScreen ?? throw new LauncherException("NoDisplay");
        var current = new DeviceMode { Size = (ushort)Marshal.SizeOf<DeviceMode>() };
        if (!EnumDisplaySettings(screen.DeviceName, -1, ref current))
            throw new LauncherException("DisplayError", new Win32Exception(Marshal.GetLastWin32Error()).Message);
        return new Resolution((int)current.Width, (int)current.Height);
    }

    private static Size FrameSize()
    {
        var dpi = GetDpiForSystem();
        return new Size(GetSystemMetricsForDpi(7, dpi) * 2,
            GetSystemMetricsForDpi(8, dpi) * 2 + GetSystemMetricsForDpi(4, dpi));
    }

    internal static IReadOnlyList<Resolution> FilterAndOrder(IEnumerable<Resolution> modes, Resolution desktop)
    {
        if (desktop.Width <= 0 || desktop.Height <= 0) throw new LauncherException("NoDisplay");
        var result = modes.Where(mode => mode.Width > 0 && mode.Height > 0
                && mode.Width <= Math.Min(desktop.Width, 1920) && mode.Height <= Math.Min(desktop.Height, 1080))
            .Distinct()
            .OrderBy(mode => Math.Abs((double)mode.Width / mode.Height - (double)desktop.Width / desktop.Height))
            .ThenByDescending(mode => (long)mode.Width * mode.Height).ThenByDescending(mode => mode.Width).ToList();
        if (result.Count == 0) throw new LauncherException("NoSafeResolution");
        return result;
    }

    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool EnumDisplaySettings(string deviceName, int modeNumber, ref DeviceMode mode);
    [DllImport("user32.dll")]
    private static extern uint GetDpiForSystem();
    [DllImport("user32.dll")]
    private static extern int GetSystemMetricsForDpi(int index, uint dpi);

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct DeviceMode
    {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string DeviceName;
        public ushort SpecVersion, DriverVersion, Size, DriverExtra;
        public uint Fields;
        public int PositionX, PositionY;
        public uint DisplayOrientation, DisplayFixedOutput;
        public short Color, Duplex, YResolution, TTOption, Collate;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string FormName;
        public ushort LogPixels;
        public uint BitsPerPixel, Width, Height, DisplayFlags, DisplayFrequency;
        public uint IcmMethod, IcmIntent, MediaType, DitherType, Reserved1, Reserved2, PanningWidth, PanningHeight;
    }
}
