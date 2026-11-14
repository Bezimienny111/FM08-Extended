using System.Buffers.Binary;
using System.Text;

namespace FmLauncher;

internal sealed record PaGrowthEvent(int PlayerId, uint Epoch, int CurrentAbility, int Before, int After,
    string FirstName, string LastName, bool NameIncomplete);

internal sealed class GamePaJournal
{
    private readonly List<PaGrowthEvent> entries = [];
    private static readonly Encoding Unicode = new UnicodeEncoding(false, false, true);
    internal IReadOnlyList<PaGrowthEvent> Entries => entries;
    internal uint Dropped { get; private set; }
    internal LauncherException? Error { get; set; }
    private uint consumed;

    internal void Reset()
    {
        entries.Clear();
        consumed = Dropped = 0;
        Error = null;
    }

    internal void Update(uint state, Func<uint, int, byte[]> read, Action<uint, byte[]> write)
    {
        if (Error is not null) return;
        var header = read(state + 20, 16);
        var published = BinaryPrimitives.ReadUInt32LittleEndian(header);
        var available = unchecked(published - consumed);
        var address = BinaryPrimitives.ReadUInt32LittleEndian(header.AsSpan(12));
        Dropped = BinaryPrimitives.ReadUInt32LittleEndian(header.AsSpan(8));
        if (available > GamePaPatch.LogCapacity || address == 0
            || address > uint.MaxValue - GamePaPatch.LogCapacity * GamePaPatch.LogEntrySize)
            throw new LauncherException("PaLogInvalid");
        if (available == 0) return;
        var batch = new List<PaGrowthEvent>((int)available);
        var next = consumed;
        while (next != published)
        {
            var index = next % GamePaPatch.LogCapacity;
            var length = (int)Math.Min(unchecked(published - next), GamePaPatch.LogCapacity - index);
            var bytes = read(checked(address + index * GamePaPatch.LogEntrySize), length * GamePaPatch.LogEntrySize);
            for (var i = 0; i < length; i++)
                batch.Add(Decode(bytes.AsSpan(i * GamePaPatch.LogEntrySize, GamePaPatch.LogEntrySize)));
            next = unchecked(next + (uint)length);
        }
        var acknowledgement = new byte[4];
        BinaryPrimitives.WriteUInt32LittleEndian(acknowledgement, published);
        write(state + 24, acknowledgement);
        entries.AddRange(batch);
        consumed = published;
    }

    internal static PaGrowthEvent Decode(ReadOnlySpan<byte> entry)
    {
        if (entry.Length != GamePaPatch.LogEntrySize) throw new LauncherException("PaLogInvalid");
        var before = BinaryPrimitives.ReadUInt16LittleEndian(entry[8..]);
        var after = BinaryPrimitives.ReadUInt16LittleEndian(entry[10..]);
        var firstLength = BinaryPrimitives.ReadUInt32LittleEndian(entry[16..]);
        var lastLength = BinaryPrimitives.ReadUInt32LittleEndian(entry[20..]);
        var flags = BinaryPrimitives.ReadUInt32LittleEndian(entry[12..]);
        var ca = BinaryPrimitives.ReadUInt32LittleEndian(entry[28..]);
        if (before is < 1 or >= 200 || after != before + 1
            || ca is < 1 or > 200 || ca > before || before - ca > 4
            || firstLength > GamePaPatch.NameCapacity || lastLength > GamePaPatch.NameCapacity || flags > 3)
            throw new LauncherException("PaLogInvalid");
        var incomplete = flags != 0 || firstLength == 0 || lastLength == 0;
        var first = Name(entry.Slice(32, (int)firstLength * 2), ref incomplete);
        var last = Name(entry.Slice(224, (int)lastLength * 2), ref incomplete);
        return new PaGrowthEvent(BinaryPrimitives.ReadInt32LittleEndian(entry),
            BinaryPrimitives.ReadUInt32LittleEndian(entry[4..]), (int)ca, before, after, first, last, incomplete);
    }

    private static string Name(ReadOnlySpan<byte> bytes, ref bool incomplete)
    {
        // A truncated surrogate or malformed text must not masquerade as a valid name.
        try
        {
            var value = Unicode.GetString(bytes);
            if (value.Any(char.IsControl)) { incomplete = true; return ""; }
            return value;
        }
        catch (DecoderFallbackException) { incomplete = true; return ""; }
    }
}
