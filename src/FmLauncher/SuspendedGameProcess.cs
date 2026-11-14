using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections;
using System.Buffers.Binary;
using Microsoft.Win32.SafeHandles;
using System.Security.Cryptography;

namespace FmLauncher;

internal sealed class SuspendedGameProcess : IDisposable
{
    private readonly SafeProcessHandle process;
    private readonly SafeWaitHandle thread;
    private bool resumed;
    internal int ProcessId { get; }
    internal uint LeagueChangesState { get; private set; }
    internal uint PositionBackgroundState { get; private set; }

    internal SuspendedGameProcess(string path, string? arguments = null, bool dpiAware = false)
    {
        var startup = new StartupInfo { Size = Marshal.SizeOf<StartupInfo>() };
        var environment = dpiAware ? BuildDpiEnvironment() : IntPtr.Zero;
        ProcessInformation info;
        try
        {
            if (!CreateProcess(path, new StringBuilder($"\"{path}\" {arguments}".TrimEnd()), IntPtr.Zero, IntPtr.Zero, false,
                0x00000004 | (dpiAware ? 0x00000400u : 0), environment, Path.GetDirectoryName(path)!, ref startup, out info))
                throw NativeError("CreateProcess");
        }
        finally { if (environment != IntPtr.Zero) Marshal.FreeHGlobal(environment); }
        process = new SafeProcessHandle(info.Process, ownsHandle: true);
        thread = new SafeWaitHandle(info.Thread, ownsHandle: true);
        ProcessId = checked((int)info.ProcessId);
    }

    internal RuleHookSession CreateRuleSession(string imageHash)
    {
        using var instance = Process.GetProcessById(ProcessId);
        return new(ProcessId, instance.StartTime.ToUniversalTime().Ticks, imageHash);
    }

    // Compatibility entry for existing native fixtures. Production compiles once in GameLauncher.
    internal void ApplyRuleLimits(IReadOnlyList<RuleSettings> rules, FileStream verifiedGame,
        Action<RuleLimit, RuleHookStatus>? report = null)
    {
        var previous = verifiedGame.Position;
        verifiedGame.Position = 0;
        var imageHash = Convert.ToHexString(SHA256.HashData(verifiedGame));
        verifiedGame.Position = previous;
        ApplyRuleLimits(EffectiveRuleResolver.Compile(rules), verifiedGame, CreateRuleSession(imageHash), report);
    }

    internal AppliedRuleSnapshot ApplyRuleLimits(EffectiveRulePolicy policy, FileStream verifiedGame,
        RuleHookSession session, Action<RuleLimit, RuleHookStatus>? report = null)
    {
        if (session.ProcessId != ProcessId) throw new LauncherException("UnexpectedGameMemory");
        var snapshot = AppliedRuleSnapshot.Begin(session, policy);
        foreach (var limit in Enum.GetValues<RuleLimit>())
        {
            if (!policy.HasOverrides(limit)) continue;
            snapshot = snapshot.WithInstalling(limit);
            report?.Invoke(limit, RuleHookStatus.Installing);
            try
            {
                var receipt = ApplyGetter(policy, verifiedGame, limit);
                snapshot = snapshot.WithVerified(limit, receipt);
                report?.Invoke(limit, RuleHookStatus.Verified);
            }
            catch
            {
                snapshot = snapshot.WithFailed(limit);
                report?.Invoke(limit, RuleHookStatus.Failed);
                throw;
            }
        }
        return snapshot;
    }

    private RuleInstallationReceipt ApplyGetter(EffectiveRulePolicy policy, FileStream verifiedGame, RuleLimit limit)
    {
        // Compare the whole original getter, not only the displaced instruction.
        var getter = MatchRulePatch.GetterAddress(limit);
        var original = new byte[limit == RuleLimit.Substitutions ? 0x80 : 0xB0];
        verifiedGame.Position = MatchRulePatch.GetterFileOffset(limit);
        verifiedGame.ReadExactly(original);
        if (!Read(getter, original.Length).SequenceEqual(original))
            throw new LauncherException("UnexpectedGameMemory");
        var address = Allocate(4096);
        var payload = MatchRulePatch.BuildPayload(address, policy, limit);
        Write(address, payload);
        Protect(address, payload.Length, 0x20);
        Flush(address, payload.Length);
        var jump = MatchRulePatch.BuildEntryJump(address + 64, limit);
        var oldProtection = Protect(getter, jump.Length, 0x40);
        Write(getter, jump);
        Protect(getter, jump.Length, oldProtection);
        Flush(getter, jump.Length);
        // The receipt owns copies, and is created only after the complete readback.
        return RuleInstallationReceipt.CreateVerified(limit, address, payload, jump, Read);
    }

    internal RuleDisplayInstallation? ApplyRuleDisplay(AppliedRuleSnapshot snapshot, FileStream verifiedGame,
        string imageHash)
    {
        var activeCodes = snapshot.ActiveCodesMask29;
        if (!activeCodes.Any(value => value != 0) || imageHash != MatchRulePatch.SupportedHash) return null;
        if (snapshot.Session.ProcessId != ProcessId || snapshot.Session.ImageSha256 != imageHash)
            throw new LauncherException("UnexpectedGameMemory");
        if (!RuleDisplayInstallation.SupportsAppliedState(snapshot))
            throw new LauncherException("UnexpectedGameMemory");
        var fresh = snapshot.Revalidate(CreateRuleSession(imageHash), true, Read);
        // Equal union masks can hide loss of one of two overrides on the same code.
        if (!ReferenceEquals(fresh, snapshot))
            throw new LauncherException("UnexpectedGameMemory");

        // The display ABI has been established only for the primary image hash.
        var original = new byte[GameRuleDisplayPatch.NativeFormatterLength];
        verifiedGame.Position = GameRuleDisplayPatch.EntryAddress - 0x400000;
        verifiedGame.ReadExactly(original);
        if (!original.AsSpan(0, GameRuleDisplayPatch.EntryLength).SequenceEqual(GameRuleDisplayPatch.OriginalEntry)
            || !Read(GameRuleDisplayPatch.EntryAddress, original.Length).SequenceEqual(original))
            throw new LauncherException("UnexpectedGameMemory");
        var address = Allocate(4096);
        var payload = GameRuleDisplayPatch.BuildPayload(address, activeCodes);
        if (payload.Length > 4096) throw new LauncherException("UnexpectedGameMemory");
        Write(address, payload);
        Protect(address, payload.Length, 0x20);
        Flush(address, payload.Length);
        var entry = GameRuleDisplayPatch.BuildEntryJump(address);
        var oldProtection = Protect(GameRuleDisplayPatch.EntryAddress, entry.Length, 0x40);
        Write(GameRuleDisplayPatch.EntryAddress, entry);
        Protect(GameRuleDisplayPatch.EntryAddress, entry.Length, oldProtection);
        Flush(GameRuleDisplayPatch.EntryAddress, entry.Length);
        var receipt = new RuleDisplayInstallation(address, payload, entry);
        if (!receipt.MatchesFreshRead(Read)) throw new LauncherException("UnexpectedGameMemory");
        return receipt;
    }

    internal static void VerifyRuleInstallation(uint address, byte[] payload, byte[] jump, RuleLimit limit,
        Func<uint, int, byte[]> read)
    {
        if (!read(MatchRulePatch.GetterAddress(limit), jump.Length).SequenceEqual(jump)
            || !read(address, payload.Length).SequenceEqual(payload))
            throw new LauncherException("UnexpectedGameMemory");
    }

    internal uint ApplyDisplay(DisplayLaunchSettings settings, FileStream verifiedGame)
    {
        var state = Allocate(GameDisplayPatch.StateSize);
        Write(state, new byte[GameDisplayPatch.StateSize]);
        InstallHook(GameDisplayPatch.OpenAddress, 7, verifiedGame,
            (address, original) => GameDisplayPatch.Open(address, state, settings, original));
        InstallHook(GameDisplayPatch.CreatedAddress, 8, verifiedGame,
            (address, original) => GameDisplayPatch.Created(address, state, settings, original));
        InstallHook(GameDisplayPatch.ExitAddress, 7, verifiedGame,
            (address, original) => GameDisplayPatch.Exit(address, state, original));
        InstallHook(GameDisplayPatch.ResizeAddress, 5, verifiedGame,
            (address, original) => GameDisplayPatch.Resize(address, settings, original));
        if (settings.Mode == DisplayMode.Window)
            InstallHook(GameDisplayPatch.StyleAddress, 10, verifiedGame, GameDisplayPatch.Style);
        return state;
    }

    internal uint ApplyPaGrowth(int chance, FileStream verifiedGame)
    {
        if (chance is < 0 or > 100) throw new LauncherException("InvalidPa");
        return ApplyPaGrowth(new PaGrowthPolicy { BaseChancePercent = chance }, verifiedGame);
    }

    internal uint ApplyPaGrowth(PaGrowthPolicy policy, FileStream verifiedGame)
    {
        policy.Validate();
        if (policy.BaseChancePercent == 0) return 0;
        var state = Allocate(GamePaPatch.StateSize);
        var log = Allocate(GamePaPatch.LogCapacity * GamePaPatch.LogEntrySize);
        Write(state, GamePaPatch.InitialState((uint)RandomNumberGenerator.GetInt32(1, int.MaxValue), log));
        InstallHook(GamePaPatch.HookAddress, GamePaPatch.OriginalEntry.Length, verifiedGame,
            (address, original) => GamePaPatch.BuildPayload(address, state, policy, original));
        return state;
    }

    internal uint ApplyPanelInformation(FileStream verifiedGame, Localizer localizer,
        PlayerProfilePanelOptions? profileOptions = null, bool legacyEnabled = true)
    {
        var integerVtable = new byte[0x70];
        verifiedGame.Position = GamePanelPatch.IntegerVtable - 0x400000;
        verifiedGame.ReadExactly(integerVtable);
        if (!Read(GamePanelPatch.IntegerVtable, integerVtable.Length).SequenceEqual(integerVtable))
            throw new LauncherException("UnexpectedGameMemory");
        profileOptions ??= new();
        uint positionSetRole = 0;
        if (profileOptions.PositionHighlightsEnabled)
        {
            var positionCode = Allocate(4096);
            var positionState = Allocate(GamePositionBackgroundPatch.DataSize);
            var classes = new byte[12 * 47];
            for (var role = 0; role < PositionHighlightModel.Roles.Count; role++)
            for (var attribute = 0; attribute < GamePositionBackgroundPatch.NativeAttributes.Count; attribute++)
                classes[(role + 1) * 47 + attribute] = (byte)PositionHighlightModel.Emphasis(
                    PositionHighlightModel.Roles[role].Code, GamePositionBackgroundPatch.NativeAttributes[attribute]);
            var position = GamePositionBackgroundPatch.Build(positionCode, positionState, classes, true);
            Write(positionState, position.Data); Write(positionCode, position.Code);
            if (!Read(positionState, position.Data.Length).SequenceEqual(position.Data)
                || !Read(positionCode, position.Code.Length).SequenceEqual(position.Code))
                throw new LauncherException("UnexpectedGameMemory");
            Protect(positionCode, position.Code.Length, 0x20); Flush(positionCode, position.Code.Length);
            InstallPanelEntry(GamePositionBackgroundPatch.NumericCreatedAddress,
                GamePositionBackgroundPatch.NumericCreatedOriginal, position.NativeValueCreatedEntry, call: true);
            InstallPanelEntry(GamePositionBackgroundPatch.NameCreatedAddress,
                GamePositionBackgroundPatch.NameCreatedOriginal, position.NativeNameCreatedEntry, call: true);
            InstallPanelEntry(GamePositionBackgroundPatch.DrawAddress,
                GamePositionBackgroundPatch.DrawOriginal, position.LabelDrawEntry);
            InstallPanelEntry(GamePositionBackgroundPatch.RebuildAddress,
                GamePositionBackgroundPatch.RebuildOriginal, position.BeginGenerationHookEntry);
            InstallPanelEntry(GamePositionBackgroundPatch.DestructorAddress,
                GamePositionBackgroundPatch.DestructorOriginal, position.LabelDestructorEntry);
            InstallPanelEntry(GamePositionBackgroundPatch.FontCopyAddress,
                GamePositionBackgroundPatch.FontCopyOriginal, position.FontCopyEntry);
            InstallPanelEntry(GamePositionBackgroundPatch.PopupCommitAddress,
                GamePositionBackgroundPatch.PopupCommitOriginal, position.PopupCommitEntry);
            positionSetRole = position.SetRoleEntry;
            PositionBackgroundState = positionState;
        }
        var code = Allocate(GamePanelPatch.CodeCapacity);
        var data = Allocate(GamePanelPatch.DataCapacity);
        var payload = GamePanelPatch.Build(code, data, integerVtable, localizer, profileOptions, legacyEnabled, positionSetRole);
        Write(data, payload.Data);
        Write(code, payload.Code);
        if (positionSetRole != 0)
        {
            if (payload.ProfileRoleEntry == 0) throw new LauncherException("UnexpectedGameMemory");
            // Written/read back while the main thread remains suspended. Native Fill
            // invokes this only after its rebuild, reading the current popup afresh.
            Write(PositionBackgroundState + (uint)GamePositionBackgroundPatch.RoleSynchronizeOffset, BitConverter.GetBytes(payload.ProfileRoleEntry));
            if (!Read(PositionBackgroundState + (uint)GamePositionBackgroundPatch.RoleSynchronizeOffset, 4)
                .SequenceEqual(BitConverter.GetBytes(payload.ProfileRoleEntry)))
                throw new LauncherException("UnexpectedGameMemory");
        }
        if (!Read(data, payload.Data.Length).SequenceEqual(payload.Data)
            || !Read(code, payload.Code.Length).SequenceEqual(payload.Code))
            throw new LauncherException("UnexpectedGameMemory");
        Protect(code, payload.Code.Length, 0x20);
        Flush(code, payload.Code.Length);
        InstallPanelEntry(GamePanelPatch.PropertyAddress, GamePanelPatch.PropertyOriginal, payload.PropertyEntry);
        InstallPanelEntry(GamePanelPatch.TitleAddress, GamePanelPatch.TitleOriginal, payload.TitleEntry);
        InstallPanelEntry(GamePanelPatch.TrainingAddress, GamePanelPatch.TrainingOriginal, payload.TrainingEntry);
        InstallPanelEntry(GamePanelPatch.LabelAddress, GamePanelPatch.LabelOriginal, payload.LabelEntry);
        if (profileOptions.HiddenAttributesEnabled || profileOptions.PositionHighlightsEnabled)
        {
            InstallPanelEntry(GamePanelPatch.ProfileSetAddress, GamePanelPatch.ProfileSetOriginal, payload.ProfileSetEntry);
            InstallPanelEntry(GamePanelPatch.ProfileEventAddress, GamePanelPatch.ProfileEventOriginal, payload.ProfileEventEntry);
            InstallPanelEntry(GamePanelPatch.ProfileInitAddress, GamePanelPatch.ProfileInitOriginal, payload.ProfileInitEntry);
        }
        return data;

        void InstallPanelEntry(uint site, ReadOnlySpan<byte> expected, uint destination, bool call = false)
        {
            var original = new byte[expected.Length];
            verifiedGame.Position = site - 0x400000;
            verifiedGame.ReadExactly(original);
            if (!original.AsSpan().SequenceEqual(expected) || !Read(site, original.Length).SequenceEqual(original))
                throw new LauncherException("UnexpectedGameMemory");
            var oldProtection = Protect(site, original.Length, 0x40);
            var jump = BuildJump(site, destination, original.Length);
            if (call) jump[0] = 0xE8;
            Write(site, jump);
            Protect(site, original.Length, oldProtection);
            Flush(site, original.Length);
            if (!Read(site, jump.Length).SequenceEqual(jump))
                throw new LauncherException("UnexpectedGameMemory");
        }
    }

    internal void ApplyAgingDelay(FileStream verifiedGame)
    {
        ReplaceVerified(GameAgingPatch.ThresholdAddress, GameAgingPatch.ThresholdOriginal,
            GameAgingPatch.ThresholdDelayed, verifiedGame);
        foreach (var hook in GameAgingPatch.Hooks)
            InstallHook(hook.Address, hook.Original.Length, verifiedGame,
                (address, original) => GameAgingPatch.Build(address, hook, original));
    }

    private void ReplaceVerified(uint site, byte[] expected, byte[] replacement, FileStream verifiedGame)
    {
        var original = new byte[expected.Length];
        verifiedGame.Position = site - 0x400000;
        verifiedGame.ReadExactly(original);
        if (!original.SequenceEqual(expected) || !Read(site, original.Length).SequenceEqual(expected))
            throw new LauncherException("UnexpectedGameMemory");
        var protection = Protect(site, original.Length, 0x40);
        Write(site, replacement);
        Protect(site, original.Length, protection);
        Flush(site, original.Length);
    }

    internal uint ApplyLeagueDiagnostics(FileStream verifiedGame, bool changes = false)
    {
        var state = Allocate(GameLeagueDiagnosticsPatch.StateSize);
        Write(state, new byte[GameLeagueDiagnosticsPatch.StateSize]);
        uint changesCode = 0;
        if (changes)
        {
            LeagueChangesState = Allocate(GameLeagueChangesPatch.StateSize);
            Write(LeagueChangesState, new byte[GameLeagueChangesPatch.StateSize]);
            changesCode = Allocate(4096);
            var payload = GameLeagueChangesPatch.Build(changesCode, LeagueChangesState, state);
            Write(changesCode, payload);
            Protect(changesCode, payload.Length, 0x20);
            Flush(changesCode, payload.Length);
        }
        foreach (var (site, kind) in new[]
        {
            (GameLeagueDiagnosticsPatch.AnnualAddress, LeagueDiagnosticKind.AnnualHistory),
            (GameLeagueDiagnosticsPatch.LoadAddress, LeagueDiagnosticKind.LoadBegin),
            (GameLeagueDiagnosticsPatch.ReturnAddress, LeagueDiagnosticKind.LoadReturn)
        })
            InstallHook(site, 7, verifiedGame,
                (address, original) => GameLeagueDiagnosticsPatch.Build(address, state, kind, original, changesCode));
        if (changes)
            InstallHook(GameLeagueDiagnosticsPatch.SaveAddress, 7, verifiedGame,
                (address, original) => GameLeagueDiagnosticsPatch.Build(address, state,
                    LeagueDiagnosticKind.SaveCompleted, original));
        return state;
    }

    private void InstallHook(uint site, int length, FileStream verifiedGame, Func<uint, byte[], byte[]> build)
    {
        var original = new byte[length];
        verifiedGame.Position = site - 0x400000;
        verifiedGame.ReadExactly(original);
        if (!Read(site, length).SequenceEqual(original)) throw new LauncherException("UnexpectedGameMemory");
        var address = Allocate(4096);
        var payload = build(address, original);
        if (payload.Length > 4096) throw new LauncherException("UnexpectedGameMemory");
        Write(address, payload);
        Protect(address, payload.Length, 0x20);
        Flush(address, payload.Length);
        var oldProtection = Protect(site, length, 0x40);
        Write(site, BuildJump(site, address, length));
        Protect(site, length, oldProtection);
        Flush(site, length);
    }

    private uint Allocate(int size)
    {
        var allocation = VirtualAllocEx(process, IntPtr.Zero, (nuint)size, 0x3000, 0x04);
        if (allocation == IntPtr.Zero) throw NativeError("VirtualAllocEx");
        var address = allocation.ToInt64();
        if (address <= 0 || address > uint.MaxValue - size) throw new LauncherException("UnexpectedGameMemory");
        return (uint)address;
    }

    internal static byte[] BuildJump(uint site, uint destination, int length)
    {
        if (length < 5) throw new ArgumentOutOfRangeException(nameof(length));
        var jump = Enumerable.Repeat((byte)0x90, length).ToArray();
        jump[0] = 0xE9;
        BinaryPrimitives.WriteUInt32LittleEndian(jump.AsSpan(1, 4), unchecked(destination - (site + 5)));
        return jump;
    }

    private static IntPtr BuildDpiEnvironment()
    {
        var values = new SortedDictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (DictionaryEntry entry in Environment.GetEnvironmentVariables())
            values.Add((string)entry.Key, (string?)entry.Value ?? "");
        values.TryGetValue("__COMPAT_LAYER", out var existing);
        var layers = (existing ?? "").Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (!layers.Contains("HIGHDPIAWARE", StringComparer.OrdinalIgnoreCase))
            values["__COMPAT_LAYER"] = string.Join(" ", layers.Append("HIGHDPIAWARE"));
        return Marshal.StringToHGlobalUni(string.Join('\0', values.Select(pair => $"{pair.Key}={pair.Value}")) + "\0\0");
    }
    internal byte[] Read(uint address, int size) => ReadMemory(process, address, size);

    internal static byte[] ReadMemory(SafeProcessHandle process, uint address, int size)
    {
        var bytes = new byte[size];
        if (!ReadProcessMemory(process, Pointer(address), bytes, (nuint)size, out var read))
            throw NativeError("ReadProcessMemory");
        if (read != (nuint)size) throw new LauncherException("UnexpectedGameMemory");
        return bytes;
    }

    private void Write(uint address, byte[] bytes) => WriteMemory(process, address, bytes);

    internal static void WriteMemory(SafeProcessHandle process, uint address, byte[] bytes)
    {
        if (!WriteProcessMemory(process, Pointer(address), bytes, (nuint)bytes.Length, out var written))
            throw NativeError("WriteProcessMemory");
        if (written != (nuint)bytes.Length) throw new LauncherException("UnexpectedGameMemory");
        if (!ReadMemory(process, address, bytes.Length).SequenceEqual(bytes))
            throw new LauncherException("UnexpectedGameMemory");
    }

    private uint Protect(uint address, int size, uint protection)
    {
        if (!VirtualProtectEx(process, Pointer(address), (nuint)size, protection, out var previous))
            throw NativeError("VirtualProtectEx");
        return previous;
    }

    private void Flush(uint address, int size)
    {
        if (!FlushInstructionCache(process, Pointer(address), (nuint)size))
            throw NativeError("FlushInstructionCache");
    }

    internal Process Resume()
    {
        var managed = Process.GetProcessById(ProcessId);
        try
        {
            var previous = ResumeThread(thread);
            if (previous == uint.MaxValue) throw NativeError("ResumeThread");
            if (previous != 1) throw new LauncherException("IntegrationStateError", "ResumeThread", previous);
            resumed = true;
            return managed;
        }
        catch
        {
            managed.Dispose();
            throw;
        }
    }

    private static IntPtr Pointer(uint address) => IntPtr.Size == 8
        ? new IntPtr((long)address) : new IntPtr(unchecked((int)address));

    private static LauncherException NativeError(string operation) =>
        new("IntegrationError", operation, new Win32Exception(Marshal.GetLastWin32Error()).Message);

    public void Dispose()
    {
        if (process.IsClosed) return;
        try
        {
            if (!resumed)
            {
                var existing = WaitForSingleObject(process, 0);
                if (existing == uint.MaxValue) throw NativeError("WaitForSingleObject");
                if (existing == 0) return;
                if (!TerminateProcess(process, 1))
                {
                    var error = NativeError("TerminateProcess");
                    if (WaitForSingleObject(process, 5000) != 0) throw error;
                    return;
                }
                var state = WaitForSingleObject(process, 5000);
                if (state == uint.MaxValue) throw NativeError("WaitForSingleObject");
                if (state != 0) throw new LauncherException("IntegrationStateError", "WaitForSingleObject", state);
            }
        }
        finally
        {
            thread.Dispose();
            process.Dispose();
        }
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct StartupInfo
    {
        public int Size;
        public IntPtr Reserved, Desktop, Title;
        public uint X, Y, XSize, YSize, XCountChars, YCountChars, FillAttribute, Flags;
        public ushort ShowWindow, ReservedSize;
        public IntPtr ReservedBytes, StandardInput, StandardOutput, StandardError;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct ProcessInformation
    {
        public IntPtr Process, Thread;
        public uint ProcessId, ThreadId;
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CreateProcess(string application, StringBuilder commandLine,
        IntPtr processAttributes, IntPtr threadAttributes, [MarshalAs(UnmanagedType.Bool)] bool inheritHandles,
        uint flags, IntPtr environment, string directory, ref StartupInfo startup, out ProcessInformation information);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr VirtualAllocEx(SafeProcessHandle process, IntPtr address, nuint size, uint type, uint protection);
    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool VirtualProtectEx(SafeProcessHandle process, IntPtr address, nuint size, uint protection, out uint previous);
    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool ReadProcessMemory(SafeProcessHandle process, IntPtr address, byte[] buffer, nuint size, out nuint read);
    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool WriteProcessMemory(SafeProcessHandle process, IntPtr address, byte[] buffer, nuint size, out nuint written);
    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool FlushInstructionCache(SafeProcessHandle process, IntPtr address, nuint size);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint ResumeThread(SafeWaitHandle thread);
    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool TerminateProcess(SafeProcessHandle process, uint exitCode);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint WaitForSingleObject(SafeProcessHandle process, uint milliseconds);
}
