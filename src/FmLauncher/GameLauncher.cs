using System.ComponentModel;
using System.Diagnostics;
using System.Buffers.Binary;

namespace FmLauncher;

public sealed class GameLauncher : IDisposable
{
    private Process? process;
    private Mutex? launchLock;
    private GameDisplayController? display;
    private uint paState;
    private uint panelState;
    public bool IsRunning => process is not null && !process.HasExited;
    public bool IsDisplayReady => display is null || display.Ready;
    internal IntPtr GameWindow => display?.Window ?? IntPtr.Zero;
    internal int GameProcessId => process?.Id ?? 0;
    internal Resolution? RenderResolution => display?.RenderResolution;
    internal PaStatistics? PaStatistics { get; private set; }
    internal PanelStatistics? PanelStatistics { get; private set; }
    internal GamePaJournal PaJournal { get; } = new();
    internal LeagueDiagnostics LeagueDiagnostics { get; } = new();
    internal LeagueChanges LeagueChanges { get; } = new();

    public void Launch(string path) => Launch(path, null);

    public void Launch(LauncherConfiguration config, Localizer? localizer = null)
    {
        ConfigurationValidator.Validate(config);
        if (config.DisplayOverride)
            ConfigurationValidator.ValidateDisplay(config, DisplayService.Detect(config.DisplayMode));
        var settings = config.DisplayOverride
            ? new DisplayLaunchSettings(config.DisplayMode, config.Resolution, DisplayService.DesktopBounds())
            {
                WorkArea = (Screen.PrimaryScreen ?? throw new LauncherException("NoDisplay")).WorkingArea
            } : null;
        Localizer? panels = null;
        if (config.PanelInformationEnabled)
        {
            panels = localizer ?? new Localizer(Path.Combine(AppContext.BaseDirectory, "FmLauncher.languages.json"));
            panels.Select(config.Language);
        }
        Launch(config.GamePath, config.MatchRulesEnabled ? config.Rules : null, settings, config.PaEnabled ? PaGrowthPolicy.Default : null, panels,
            config.LeagueDiagnosticsEnabled || config.LeagueChangesEnabled, config.AgingDelayEnabled,
            config.LeagueChangesEnabled);
    }

    private void Launch(string path, IReadOnlyList<RuleSettings>? rules, DisplayLaunchSettings? settings = null,
        PaGrowthPolicy? paPolicy = null, Localizer? panels = null, bool leagueDiagnostics = false, bool agingDelay = false,
        bool leagueChanges = false)
    {
        if (IsRunning) throw new LauncherException("AlreadyRunning");
        Release();
        PaStatistics = null;
        PanelStatistics = null;
        PaJournal.Reset();
        LeagueDiagnostics.Reset();
        if (!Path.IsPathFullyQualified(path) || !File.Exists(path)
            || !string.Equals(Path.GetExtension(path), ".exe", StringComparison.OrdinalIgnoreCase))
            throw new LauncherException("InvalidGamePath", path);
        launchLock = new Mutex(false, @"Local\FmLauncher.GameStart");
        bool acquired;
        try { acquired = launchLock.WaitOne(0); }
        catch (AbandonedMutexException) { acquired = true; }
        if (!acquired)
        {
            launchLock.Dispose();
            launchLock = null;
            throw new LauncherException("AlreadyRunning");
        }
        try
        {
            // Treat inaccessible same-name processes conservatively; never risk a second start.
            var candidates = Process.GetProcessesByName(Path.GetFileNameWithoutExtension(path));
            try
            {
                if (candidates.Any(candidate => !candidate.HasExited))
                    throw new LauncherException("AlreadyRunning");
            }
            finally { foreach (var candidate in candidates) candidate.Dispose(); }
            if (agingDelay || leagueDiagnostics || panels is not null || settings is not null || paPolicy is not null
                || (rules is not null && rules.Any(rule => rule.Override || rule.BenchOverride)))
            {
                using var verified = MatchRulePatch.OpenVerifiedGame(path);
                using var suspended = new SuspendedGameProcess(path,
                    settings is null ? null : GameDisplayPatch.Arguments(settings.Mode), dpiAware: settings is not null);
                if (rules is not null) suspended.ApplyRuleLimits(rules, verified);
                if (agingDelay) suspended.ApplyAgingDelay(verified);
                if (settings is not null) display = new GameDisplayController(suspended.ApplyDisplay(settings, verified), settings);
                if (paPolicy is not null)
                {
                    paState = suspended.ApplyPaGrowth(paPolicy, verified);
                    PaStatistics = new PaStatistics(0, 0, 0);
                }
                if (panels is not null)
                {
                    panelState = suspended.ApplyPanelInformation(verified, panels);
                    PanelStatistics = new PanelStatistics(0, 0, 0, 0);
                }
                if (leagueDiagnostics)
                {
                    var state = suspended.ApplyLeagueDiagnostics(verified, leagueChanges);
                    LeagueDiagnostics.Begin(state,
                        (address, size) => SuspendedGameProcess.ReadMemory(
                            (process ?? throw new LauncherException("LeagueGameRequired")).SafeHandle, address, size),
                        Path.Combine(AppContext.BaseDirectory, "league-diagnostics"), suspended.ProcessId);
                    if (leagueChanges)
                        LeagueChanges.Begin(suspended.LeagueChangesState,
                            (address, size) => SuspendedGameProcess.ReadMemory(
                                (process ?? throw new LauncherException("LeagueGameRequired")).SafeHandle, address, size),
                            (address, bytes) => SuspendedGameProcess.WriteMemory(
                                (process ?? throw new LauncherException("LeagueGameRequired")).SafeHandle, address, bytes),
                            LeagueDiagnostics, Path.Combine(AppContext.BaseDirectory, "league-changes"), suspended.ProcessId);
                }
                process = suspended.Resume();
            }
            else
            {
                process = Process.Start(new ProcessStartInfo
                {
                    FileName = path,
                    WorkingDirectory = Path.GetDirectoryName(path)!,
                    UseShellExecute = false
                }) ?? throw new LauncherException("ProcessStartError", path);
            }
        }
        catch (Exception ex) when (ex is Win32Exception or InvalidOperationException or IOException or UnauthorizedAccessException)
        {
            Release();
            throw new LauncherException("ProcessStartError", ex.Message);
        }
        catch (LauncherException)
        {
            Release();
            throw;
        }
    }

    public bool CheckExited()
    {
        if (process is null) return false;
        if (process.HasExited)
        {
            var startupFailed = display is not null && !display.HasInitialized;
            var exitCode = process.ExitCode;
            Release();
            if (startupFailed) throw new LauncherException("DisplayStartupExited", exitCode);
            return true;
        }
        LeagueDiagnostics.Update();
        LeagueChanges.Update();
        if (display is not null || paState != 0 || panelState != 0)
        {
            try
            {
                display?.Update(process);
                if (panelState != 0)
                {
                    var state = SuspendedGameProcess.ReadMemory(process.SafeHandle, panelState, GamePanelPatch.StateSize);
                    PanelStatistics = new PanelStatistics(BinaryPrimitives.ReadUInt32LittleEndian(state),
                        BinaryPrimitives.ReadUInt32LittleEndian(state.AsSpan(4)),
                        BinaryPrimitives.ReadUInt32LittleEndian(state.AsSpan(8)),
                        BinaryPrimitives.ReadUInt32LittleEndian(state.AsSpan(12)));
                }
                if (paState != 0)
                {
                    try
                    {
                        PaJournal.Update(paState,
                            (address, size) => SuspendedGameProcess.ReadMemory(process.SafeHandle, address, size),
                            (address, bytes) => SuspendedGameProcess.WriteMemory(process.SafeHandle, address, bytes));
                    }
                    catch (LauncherException ex)
                    {
                        PaJournal.Error = ex;
                    }
                    var state = SuspendedGameProcess.ReadMemory(process.SafeHandle, paState, GamePaPatch.StateSize);
                    var confirmed = SuspendedGameProcess.ReadMemory(process.SafeHandle, paState + 4, 12);
                    if (state.AsSpan(4, 12).SequenceEqual(confirmed))
                        PaStatistics = new PaStatistics(BinaryPrimitives.ReadUInt32LittleEndian(confirmed),
                            BinaryPrimitives.ReadUInt32LittleEndian(confirmed.AsSpan(4)),
                            BinaryPrimitives.ReadUInt32LittleEndian(confirmed.AsSpan(8)));
                }
            }
            catch (LauncherException) when (process.HasExited)
            {
                var startupFailed = display is not null && !display.HasInitialized;
                var exitCode = process.ExitCode;
                Release();
                if (startupFailed) throw new LauncherException("DisplayStartupExited", exitCode);
                return true;
            }
            catch (LauncherException)
            {
                try
                {
                    if (!process.HasExited)
                    {
                        process.Kill();
                        if (!process.WaitForExit(5000)) throw new LauncherException("DisplayStopTimeout");
                    }
                }
                finally { Release(); }
                throw;
            }
        }
        return false;
    }

    private void Release()
    {
        LeagueChanges.End(process is not null && !process.HasExited);
        LeagueDiagnostics.End();
        process?.Dispose();
        process = null;
        display = null;
        paState = 0;
        panelState = 0;
        if (launchLock is not null)
        {
            launchLock.ReleaseMutex();
            launchLock.Dispose();
            launchLock = null;
        }

    }

    public void Dispose() => Release();

    internal LeagueSnapshot CaptureLeagueSnapshot(Process candidate)
    {
        if (LeagueDiagnostics.Installed)
        {
            if (process is null || process.HasExited || candidate.Id != process.Id)
                throw new LauncherException("LeagueGameRequired");
            return LeagueDiagnostics.Capture(() =>
            {
                byte[] Read(uint address, int size) => SuspendedGameProcess.ReadMemory(candidate.SafeHandle, address, size);
                var identity = LeagueChanges.Installed ? CareerIdentity.Read(Read) : null;
                var snapshot = LeagueMemoryReader.Capture(candidate);
                if (identity is not null && identity != CareerIdentity.Read(Read))
                    throw new LauncherException("LeagueHistoryChanged");
                return snapshot with { Identity = identity };
            });
        }
        return LeagueMemoryReader.Capture(candidate);
    }

    internal LeagueSnapshot CaptureCurrentLeagueSnapshot() =>
        CaptureLeagueSnapshot(process is not null && !process.HasExited ? process
            : throw new LauncherException("LeagueGameRequired"));

    internal (CareerIdentity Identity, DateOnly Date) CaptureCurrentCareer() =>
        LeagueDiagnostics.CaptureStable(() =>
        {
            if (process is null || process.HasExited) throw new LauncherException("LeagueGameRequired");
            byte[] Read(uint address, int size) => SuspendedGameProcess.ReadMemory(process.SafeHandle, address, size);
            var identity = CareerIdentity.Read(Read);
            var calendar = Read(0x1B1EE14, 4);
            var day = BinaryPrimitives.ReadUInt16LittleEndian(calendar);
            var year = BinaryPrimitives.ReadUInt16LittleEndian(calendar.AsSpan(2));
            if (year is < 1900 or > 9998 || day >= (DateTime.IsLeapYear(year) ? 366 : 365))
                throw new LauncherException("LeagueInvalidData");
            if (identity != CareerIdentity.Read(Read) || !calendar.SequenceEqual(Read(0x1B1EE14, 4)))
                throw new LauncherException("LeagueHistoryChanged");
            return (identity, new DateOnly(year, 1, 1).AddDays(day));
        });
}

internal sealed record PanelStatistics(uint Reads, uint Hidden, uint Invalid, uint TrainingUpdates);
