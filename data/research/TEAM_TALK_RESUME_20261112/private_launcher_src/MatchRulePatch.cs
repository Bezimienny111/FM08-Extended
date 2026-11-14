using System.Buffers.Binary;
using System.Security.Cryptography;

namespace FmLauncher;

internal enum RuleLimit { Substitutions, Bench }

internal static class MatchRulePatch
{
    internal static uint GetterAddress(RuleLimit limit) => limit switch
    {
        RuleLimit.Substitutions => 0x00AFE0D0,
        RuleLimit.Bench => 0x00AFE150,
        _ => throw new ArgumentOutOfRangeException(nameof(limit))
    };
    internal static int GetterFileOffset(RuleLimit limit) => checked((int)GetterAddress(limit) - 0x400000);
    internal static bool Enabled(RuleSettings rule, RuleLimit limit) =>
        limit == RuleLimit.Substitutions ? rule.Override : rule.BenchOverride;
    internal const string SupportedHash = "157F484BE2EAD4AB27006D1002C2C666A7228197B88B14C8D026E76F31B1D62D";
    internal const string AlternateSupportedHash = "32046D2AC71459036B60E72321DFFEEB39A1A8E1A63E6CCBEE6220680E9BC4F4";
    internal static bool IsSupportedHash(string hash) => hash is SupportedHash or AlternateSupportedHash;
    internal static ReadOnlySpan<byte> OriginalEntry => [0x0F, 0xBE, 0x44, 0x24, 0x04];

    internal static FileStream OpenVerifiedGame(string path)
    {
        var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
        try
        {
            if (!IsSupportedHash(Convert.ToHexString(SHA256.HashData(stream))))
                throw new LauncherException("UnsupportedGame");
            stream.Position = 0;
            return stream;
        }
        catch
        {
            stream.Dispose();
            throw;
        }
    }

    internal static byte[] BuildPayload(uint address, IReadOnlyList<RuleSettings> rules, RuleLimit limit)
    {
        if (rules.Count != 29 || rules.Select(rule => rule.Code).Distinct().Count() != 29
            || rules.Any(rule => rule.Code is < 0 or > 28))
            throw new LauncherException("InvalidRules");
        var getter = GetterAddress(limit);
        if (rules.Any(rule => Enabled(rule, limit) && Value(rule, limit) is < 0 or > 12))
            throw new LauncherException(limit == RuleLimit.Substitutions ? "InvalidSubstitutionLimit" : "InvalidBenchLimit");

        // Tables precede the code; unsigned bounds checking also rejects negative signed-byte codes.
        var payload = new byte[96];
        foreach (var rule in rules)
        {
            var enabled = Enabled(rule, limit);
            payload[rule.Code] = enabled ? (byte)1 : (byte)0;
            payload[32 + rule.Code] = enabled ? checked((byte)Value(rule, limit)) : (byte)0;
        }
        byte[] code =
        [
            0x0F, 0xBE, 0x44, 0x24, 0x04, // movsx eax, byte ptr [esp+4]
            0x83, 0xF8, 0x1C,             // cmp eax, 28
            0x77, 0x10,                   // ja original
            0x80, 0xB8, 0, 0, 0, 0, 0,   // cmp byte ptr [eax+enabled], 0
            0x74, 0x07,                   // je original
            0x8A, 0x80, 0, 0, 0, 0,      // mov al, byte ptr [eax+values]
            0xC3,                         // ret
            0xE9, 0, 0, 0, 0             // jmp original getter+5
        ];
        BinaryPrimitives.WriteUInt32LittleEndian(code.AsSpan(12, 4), address);
        BinaryPrimitives.WriteUInt32LittleEndian(code.AsSpan(21, 4), checked(address + 32));
        BinaryPrimitives.WriteUInt32LittleEndian(code.AsSpan(27, 4),
            unchecked(getter + 5 - (address + 64 + (uint)code.Length)));
        code.CopyTo(payload, 64);
        return payload;
    }

    private static int Value(RuleSettings rule, RuleLimit limit) =>
        limit == RuleLimit.Substitutions ? rule.Substitutions : rule.Bench;

    internal static byte[] BuildEntryJump(uint destination, RuleLimit limit)
    {
        var jump = new byte[] { 0xE9, 0, 0, 0, 0 };
        BinaryPrimitives.WriteUInt32LittleEndian(jump.AsSpan(1),
            unchecked(destination - (GetterAddress(limit) + 5)));
        return jump;
    }
}
