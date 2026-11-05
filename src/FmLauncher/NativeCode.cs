using System.Buffers.Binary;
using System.Runtime.InteropServices;

namespace FmLauncher;

internal sealed class NativeCode(uint address)
{
    private readonly List<byte> bytes = [];
    private readonly Dictionary<string, int> labels = [];
    private readonly List<(int Offset, string Label)> fixups = [];
    internal void Emit(params byte[] value) => bytes.AddRange(value);
    internal void Dword(uint value) => bytes.AddRange(BitConverter.GetBytes(value));
    internal void Mark(string label) => labels.Add(label, bytes.Count);
    internal void Jump(uint target) { Emit(0xE9); Relative(target); }
    internal void Call(uint target) { Emit(0xE8); Relative(target); }
    internal void Jump(string label) { Emit(0xE9); Reference(label); }
    internal void Branch(byte condition, string label) { Emit(0x0F, condition); Reference(label); }
    internal void Branch(byte condition, uint target) { Emit(0x0F, condition); Relative(target); }
    private void Relative(uint target) => Dword(unchecked(target - address - (uint)bytes.Count - 4));
    private void Reference(string label)
    {
        fixups.Add((bytes.Count, label));
        Dword(0);
    }
    internal byte[] Finish()
    {
        foreach (var (offset, label) in fixups)
            BinaryPrimitives.WriteInt32LittleEndian(CollectionsMarshal.AsSpan(bytes).Slice(offset, 4),
                labels[label] - offset - 4);
        return bytes.ToArray();
    }
}
