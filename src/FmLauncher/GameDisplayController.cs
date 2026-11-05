using System.Buffers.Binary;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

namespace FmLauncher;

internal sealed class GameDisplayController(uint state, DisplayLaunchSettings settings)
{
    private readonly Stopwatch pending = Stopwatch.StartNew();
    internal bool Ready { get; private set; }
    internal bool HasInitialized { get; private set; }
    internal IntPtr Window { get; private set; }
    internal Resolution? RenderResolution { get; private set; }

    internal void Update(Process process)
    {
        var data = SuspendedGameProcess.ReadMemory(process.SafeHandle, state, GameDisplayPatch.StateSize);
        if (UInt32(data, 12) == 0)
        {
            WaitForDisplay();
            return;
        }
        var result = UInt32(data, 8);
        if (result != 0) throw new LauncherException("DisplayNativeError", result);
        if (UInt32(data, 4) == 0) throw new LauncherException("WindowMoveError");
        var hwnd = new IntPtr((long)UInt32(data, 0));
        if (!IsWindow(hwnd))
        {
            if (!HasInitialized) throw new LauncherException("DisplayWindowError");
            WaitForDisplay();
            return;
        }
        GetWindowThreadProcessId(hwnd, out var owner);
        if (owner != process.Id) throw new LauncherException("DisplayWindowError");
        var dpiResult = GetProcessDpiAwareness(process.SafeHandle, out var awareness);
        if (dpiResult != 0 || awareness == 0) throw new LauncherException("DisplayDpiError", dpiResult, awareness);
        if (!GetClientRect(hwnd, out var client)) throw WindowError("GetClientRect");
        var clientResolution = new Resolution(client.Right - client.Left, client.Bottom - client.Top);
        var surface = UInt32(data, 16);
        if (surface == 0) throw new LauncherException("UnexpectedGameMemory");
        var buffer = SuspendedGameProcess.ReadMemory(process.SafeHandle, checked(surface + 0x88), 4);
        var rendered = new Resolution(BinaryPrimitives.ReadUInt16LittleEndian(buffer),
            BinaryPrimitives.ReadUInt16LittleEndian(buffer.AsSpan(2)));
        var minimized = IsIconic(hwnd);
        if (rendered != settings.Resolution || (!minimized && clientResolution != settings.Resolution))
            throw new LauncherException("DisplaySizeMismatch", settings.Resolution, rendered, clientResolution);
        var style = unchecked((uint)GetWindowLong(hwnd, -16));
        if (settings.Mode == DisplayMode.Window)
        {
            if ((style & 0x00C00000) != 0x00C00000 || (style & 0x00050000) != 0)
                throw new LauncherException("DisplayStyleMismatch");
        }
        else if ((style & 0x00C50000) != 0 || (style & 0x80000000) == 0)
            throw new LauncherException("DisplayStyleMismatch");
        if (!Ready && !minimized)
        {
            if (!GetWindowRect(hwnd, out var outer)) throw WindowError("GetWindowRect");
            var rectangle = Rectangle.FromLTRB(outer.Left, outer.Top, outer.Right, outer.Bottom);
            if (settings.Mode == DisplayMode.Borderless)
            {
                var expected = new Rectangle(settings.Desktop.Left + (settings.Desktop.Width - settings.Resolution.Width) / 2,
                    settings.Desktop.Top + (settings.Desktop.Height - settings.Resolution.Height) / 2,
                    settings.Resolution.Width, settings.Resolution.Height);
                if (rectangle != expected) throw new LauncherException("DisplayPositionMismatch");
            }
            if (settings.Mode == DisplayMode.Window
                && !(Screen.PrimaryScreen ?? throw new LauncherException("NoDisplay")).WorkingArea.Contains(rectangle))
                throw new LauncherException("WindowDoesNotFit");
            if (settings.Mode == DisplayMode.Fullscreen && GetForegroundWindow() == hwnd
                && DisplayService.CurrentResolution() != settings.Resolution)
                throw new LauncherException("FullscreenMismatch");
        }
        Window = hwnd;
        RenderResolution = rendered;
        Ready = true;
        HasInitialized = true;
        pending.Stop();
    }

    private void WaitForDisplay()
    {
        Ready = false;
        if (!pending.IsRunning) pending.Restart();
        if (pending.Elapsed > TimeSpan.FromSeconds(60)) throw new LauncherException("DisplayTimeout");
    }

    private static uint UInt32(byte[] data, int offset) =>
        BinaryPrimitives.ReadUInt32LittleEndian(data.AsSpan(offset, 4));
    private static LauncherException WindowError(string operation) =>
        new("DisplayControlError", operation, new Win32Exception(Marshal.GetLastWin32Error()).Message);

    [StructLayout(LayoutKind.Sequential)]
    private struct Rect { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool IsWindow(IntPtr window);
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool IsIconic(IntPtr window);
    [DllImport("user32.dll")]
    private static extern uint GetWindowThreadProcessId(IntPtr window, out uint processId);
    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetClientRect(IntPtr window, out Rect rectangle);
    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetWindowRect(IntPtr window, out Rect rectangle);
    [DllImport("user32.dll", EntryPoint = "GetWindowLongW")]
    private static extern int GetWindowLong(IntPtr window, int index);
    [DllImport("user32.dll")]
    private static extern IntPtr GetForegroundWindow();
    [DllImport("shcore.dll")]
    private static extern int GetProcessDpiAwareness(SafeProcessHandle process, out int awareness);
}
