using System.Buffers.Binary;

namespace FmLauncher;

internal enum LeagueDiagnosticKind { AnnualHistory = 1, LoadBegin = 2, LoadReturn = 3, SaveCompleted = 4 }

internal static class GameLeagueDiagnosticsPatch
{
    internal const uint AnnualAddress = 0x00E26113;
    internal const uint LoadAddress = 0x00465210;
    internal const uint ReturnAddress = 0x00466978;
    internal const uint SaveAddress = 0x00467F23;
    internal const int HeaderSize = 20;
    internal const int EntrySize = 40;
    internal const int Capacity = 4096;
    internal const int StateSize = HeaderSize + Capacity * EntrySize;

    internal static readonly byte[] AnnualOriginal = [0x8B, 0xCE, 0xE8, 0x26, 0xD3, 0xFF, 0xFF];
    internal static readonly byte[] LoadOriginal = [0x6A, 0xFF, 0x68, 0x98, 0x74, 0x14, 0x01];
    internal static readonly byte[] ReturnOriginal = [0x8B, 0x8C, 0x24, 0x4C, 0x0C, 0, 0];
    internal static readonly byte[] SaveOriginal = [0x8B, 0x8C, 0x24, 0xEC, 0x02, 0, 0];

    internal static byte[] Build(uint address, uint state, LeagueDiagnosticKind kind, byte[] original,
        uint changes = 0)
    {
        var (site, expected) = kind switch
        {
            LeagueDiagnosticKind.AnnualHistory => (AnnualAddress, AnnualOriginal),
            LeagueDiagnosticKind.LoadBegin => (LoadAddress, LoadOriginal),
            LeagueDiagnosticKind.LoadReturn => (ReturnAddress, ReturnOriginal),
            LeagueDiagnosticKind.SaveCompleted => (SaveAddress, SaveOriginal),
            _ => throw new ArgumentOutOfRangeException(nameof(kind))
        };
        if (!original.SequenceEqual(expected)) throw new LauncherException("UnexpectedGameMemory");
        var code = new List<byte> { 0x9C, 0x60 };
        var jumps = new List<(int Position, string Label)>();
        var labels = new Dictionary<string, int>();
        void U32(uint value)
        {
            var bytes = new byte[4];
            BinaryPrimitives.WriteUInt32LittleEndian(bytes, value);
            code.AddRange(bytes);
        }
        void Jump(byte condition, string label)
        {
            code.AddRange([0x0F, condition]);
            jumps.Add((code.Count, label));
            U32(0);
        }
        void Absolute(byte operand, uint target)
        {
            code.AddRange([0xF0, 0xFF, operand]);
            U32(target);
        }
        void StoreImmediate(byte offset, uint value)
        {
            code.AddRange([0xC7, 0x47, offset]);
            U32(value);
        }
        if (kind == LeagueDiagnosticKind.LoadBegin)
        {
            Absolute(0x05, state + 16);
            Absolute(0x05, state + 12);
        }
        if (kind == LeagueDiagnosticKind.LoadReturn) Absolute(0x0D, state + 16);
        code.Add(0xB8); U32(1);
        code.AddRange([0x87, 0x05]); U32(state);
        code.AddRange([0x85, 0xC0]);
        Jump(0x85, "dropped");
        code.Add(0xA1); U32(state + 4);
        code.Add(0x3D); U32(Capacity);
        Jump(0x83, "full");
        code.AddRange([0x6B, 0xF8, EntrySize, 0x81, 0xC7]); U32(state + HeaderSize);
        StoreImmediate(0, (uint)kind);
        code.AddRange([0x64, 0xA1]); U32(0x24);
        code.AddRange([0x89, 0x47, 4]);
        code.Add(0xA1); U32(state + 12);
        code.AddRange([0x89, 0x47, 8, 0x0F, 0xB7, 0x05]); U32(0x01B1EE14);
        code.AddRange([0x89, 0x47, 12, 0x0F, 0xB7, 0x05]); U32(0x01B1EE16);
        code.AddRange([0x89, 0x47, 16]);
        // PUSHAD offsets: saved ECX +24, ESI +4, EAX +28; original stack is +36.
        code.AddRange([0x8B, 0x44, 0x24, kind == LeagueDiagnosticKind.AnnualHistory ? (byte)4
            : kind == LeagueDiagnosticKind.SaveCompleted ? (byte)0 : (byte)24,
            0x89, 0x47, 20]);
        if (kind == LeagueDiagnosticKind.LoadBegin)
            code.AddRange([0x0F, 0xB6, 0x44, 0x24, 44, 0x89, 0x47, 24]);
        else if (kind == LeagueDiagnosticKind.SaveCompleted)
        {
            code.Add(0xA1); U32(0x1911160);
            code.AddRange([0x89,0x47,24]);
        }
        else StoreImmediate(24, uint.MaxValue);
        if (kind == LeagueDiagnosticKind.LoadReturn)
            code.AddRange([0x0F, 0xB6, 0x44, 0x24, 28, 0x89, 0x47, 28]);
        else StoreImmediate(28, kind == LeagueDiagnosticKind.SaveCompleted ? 1u : uint.MaxValue);
        if (kind == LeagueDiagnosticKind.AnnualHistory)
        {
            code.AddRange([0x0F, 0xB7, 0x46, 0x1C, 0x89, 0x47, 32,
                0x0F, 0xB7, 0x46, 0x1E, 0x89, 0x47, 36]);
        }
        else if (kind == LeagueDiagnosticKind.SaveCompleted)
        {
            // Save-only slots carry the persistent identity, not an annual schedule.
            code.Add(0xA1); U32(0x1911168);
            code.AddRange([0x89,0x47,32,0x0F,0xB6,0x05]); U32(0x191116C);
            code.AddRange([0x89,0x47,36]);
        }
        else
        {
            StoreImmediate(32, uint.MaxValue);
            StoreImmediate(36, uint.MaxValue);
        }
        Absolute(0x05, state + 4);
        labels["unlock"] = code.Count;
        code.AddRange([0x31, 0xC0, 0xA3]); U32(state);
        code.AddRange([0x61, 0x9D]);
        labels["original"] = code.Count;
        if (kind == LeagueDiagnosticKind.AnnualHistory)
        {
            code.AddRange([0x8B, 0xCE, 0xE8]);
            U32(unchecked(0x00E23440 - (address + (uint)code.Count + 4)));
            if (changes != 0)
            {
                code.Add(0xE8);
                U32(unchecked(changes - (address + (uint)code.Count + 4)));
            }
        }
        else code.AddRange(original);
        code.Add(0xE9);
        U32(unchecked(site + (uint)original.Length - (address + (uint)code.Count + 4)));
        labels["full"] = code.Count;
        Absolute(0x05, state + 8);
        code.Add(0xE9); var unlock = code.Count; U32(0);
        BinaryPrimitives.WriteInt32LittleEndian(CollectionsMarshalSpan(code, unlock), labels["unlock"] - (unlock + 4));
        labels["dropped"] = code.Count;
        Absolute(0x05, state + 8);
        code.AddRange([0x61, 0x9D]);
        code.Add(0xE9);
        U32(unchecked(address + (uint)labels["original"] - (address + (uint)code.Count + 4)));
        // The dropped path must skip the unlock store owned by another producer.
        foreach (var (position, label) in jumps)
            BinaryPrimitives.WriteInt32LittleEndian(CollectionsMarshalSpan(code, position), labels[label] - (position + 4));
        return code.ToArray();
    }

    private static Span<byte> CollectionsMarshalSpan(List<byte> code, int offset) =>
        System.Runtime.InteropServices.CollectionsMarshal.AsSpan(code).Slice(offset, 4);
}
