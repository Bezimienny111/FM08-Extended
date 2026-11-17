using System.Security.Cryptography;

namespace FmLauncher;

// Read-only evidence of the startup display adapter; never a saved configuration.
internal sealed class RuleDisplayInstallation
{
    private readonly byte[] payload;
    private readonly byte[] entry;
    internal uint PayloadAddress { get; }
    internal string PayloadSha256 { get; }
    internal string EntrySha256 { get; }

    internal RuleDisplayInstallation(uint payloadAddress, byte[] payload, byte[] entry)
    {
        PayloadAddress = payloadAddress;
        this.payload = payload.ToArray();
        this.entry = entry.ToArray();
        PayloadSha256 = Convert.ToHexString(SHA256.HashData(this.payload));
        EntrySha256 = Convert.ToHexString(SHA256.HashData(this.entry));
    }

    internal static bool SupportsAppliedState(AppliedRuleSnapshot snapshot) =>
        snapshot.SessionAlive && snapshot.HasActiveOverrides
        && Enum.GetValues<RuleLimit>().All(limit => snapshot.Status(limit) ==
            (snapshot.Policy.HasOverrides(limit) ? AppliedRuleStatus.Verified : AppliedRuleStatus.Disabled));

    internal bool MatchesFreshRead(Func<uint, int, byte[]> read) =>
        read(GameRuleDisplayPatch.EntryAddress, entry.Length).SequenceEqual(entry)
        && read(PayloadAddress, payload.Length).SequenceEqual(payload);
}
