using System.Buffers.Binary;

namespace FmLauncher;

internal sealed record CareerIdentity(uint Token, ushort Day, ushort Year, byte Marker)
{
    internal uint DateWord => (uint)(Day | Year << 16);

    internal void Validate(string key = "LeagueProfileInvalid")
    {
        if (Token >= 10000000 || Year is < 1900 or > 9998
            || Day >= (DateTime.IsLeapYear(Year) ? 366 : 365))
            throw new LauncherException(key);
    }

    internal static CareerIdentity Read(Func<uint, int, byte[]> read)
    {
        var data = read(0x1911160, 20);
        if (BinaryPrimitives.ReadUInt32LittleEndian(data.AsSpan(4)) != 0x121A5BC
            || BinaryPrimitives.ReadUInt32LittleEndian(data.AsSpan(16)) != 117931)
            throw new LauncherException("LeagueInvalidData");
        var result = new CareerIdentity(BinaryPrimitives.ReadUInt32LittleEndian(data),
            BinaryPrimitives.ReadUInt16LittleEndian(data.AsSpan(8)),
            BinaryPrimitives.ReadUInt16LittleEndian(data.AsSpan(10)), data[12]);
        result.Validate("LeagueInvalidData");
        return result;
    }
}
