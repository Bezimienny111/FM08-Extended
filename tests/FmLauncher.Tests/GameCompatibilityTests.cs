using System.Security.Cryptography;
using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    private static string GameFileHash(string path)
    {
        using var stream = File.OpenRead(path);
        return Convert.ToHexString(SHA256.HashData(stream));
    }

    private static void TestGameAllowlist(string path, string directory)
    {
        Assert(MatchRulePatch.IsSupportedHash(MatchRulePatch.SupportedHash));
        Assert(MatchRulePatch.IsSupportedHash(MatchRulePatch.AlternateSupportedHash));
        foreach (var invalid in new[] { "", new string('0', 64), MatchRulePatch.SupportedHash.ToLowerInvariant(),
            MatchRulePatch.AlternateSupportedHash[..63] })
            Assert(!MatchRulePatch.IsSupportedHash(invalid));
        var originalHash = GameFileHash(path);
        using (var verified = MatchRulePatch.OpenVerifiedGame(path))
        {
            Assert(verified.Position == 0 && verified.ReadByte() == 'M');
            Assert(GameFileHash(path) == originalHash);
            try
            {
                using var write = new FileStream(path, FileMode.Open, FileAccess.ReadWrite, FileShare.ReadWrite);
                throw new InvalidOperationException("Verified EXE must remain write-locked.");
            }
            catch (IOException) { }
        }
        var copy = Path.Combine(directory, "unsupported-game-copy.exe");
        try
        {
            var bytes = File.ReadAllBytes(path);
            bytes[^1] ^= 1;
            File.WriteAllBytes(copy, bytes);
            Reject(() => { using var unexpected = MatchRulePatch.OpenVerifiedGame(copy); }, "UnsupportedGame");
            using (var released = new FileStream(copy, FileMode.Open, FileAccess.ReadWrite, FileShare.None))
                Assert(released.Length == bytes.Length);
            File.WriteAllBytes(copy, bytes[..1024]);
            Reject(() => { using var unexpected = MatchRulePatch.OpenVerifiedGame(copy); }, "UnsupportedGame");
            File.WriteAllBytes(copy, []);
            Reject(() => { using var unexpected = MatchRulePatch.OpenVerifiedGame(copy); }, "UnsupportedGame");
        }
        finally { if (File.Exists(copy)) File.Delete(copy); }
        Assert(GameFileHash(path) == originalHash);
    }
}
