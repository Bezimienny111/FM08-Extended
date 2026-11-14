using System.Buffers.Binary;

namespace FmLauncher;

internal sealed record PaStatistics(uint Rolls, uint Increases, uint InvalidFields);

internal static class GamePaPatch
{
    internal const uint HookAddress = 0x008D3F33;
    internal const int StateSize = 36;
    internal const int LogCapacity = 4096;
    internal const int LogEntrySize = 416;
    internal const int NameCapacity = 96;
    internal const byte CurrentAbilityOffset = 0x14;
    internal const byte PotentialAbilityOffset = 0x16;
    // Relative to PERSON after the native name thunk's vtordisp adjustment.
    internal const byte FirstNameOffset = 0x10C - 0xE0;
    internal const byte LastNameOffset = 0x10C - 0xDC;
    internal static ReadOnlySpan<byte> OriginalEntry => [0x89, 0x4D, 0x04, 0x8B, 0x16];

    internal static byte[] InitialState(uint seed, uint logAddress)
    {
        if (seed == 0) throw new ArgumentOutOfRangeException(nameof(seed));
        var state = new byte[StateSize];
        BinaryPrimitives.WriteUInt32LittleEndian(state, seed);
        BinaryPrimitives.WriteUInt32LittleEndian(state.AsSpan(32), logAddress);
        return state;
    }

    internal static byte[] BuildPayload(uint address, uint state, int chance, byte[] original)
    {
        if (chance is < 0 or > 100) throw new LauncherException("InvalidPa");
        return BuildPayload(address, state, new PaGrowthPolicy { BaseChancePercent = chance }, original);
    }

    internal static byte[] BuildPayload(uint address, uint state, PaGrowthPolicy policy, byte[] original)
    {
        policy.Validate();
        return BuildPayloadCore(address, state, policy, original);
    }

    private static byte[] BuildPayloadCore(uint address, uint state, PaGrowthPolicy policy, byte[] original)
    {
        var chance = policy.BaseChancePercent;
        if (!original.AsSpan().SequenceEqual(OriginalEntry)) throw new LauncherException("UnexpectedGameMemory");
        var code = new List<byte>();
        var labels = new Dictionary<string, int>();
        var branches = new List<(int Offset, string Label)>();
        void Emit(params byte[] bytes) => code.AddRange(bytes);
        void UInt32(uint value)
        {
            var bytes = new byte[4];
            BinaryPrimitives.WriteUInt32LittleEndian(bytes, value);
            code.AddRange(bytes);
        }
        void Branch(byte condition, string label)
        {
            Emit(0x0F, condition);
            branches.Add((code.Count, label));
            UInt32(0);
        }
        void Count(uint offset)
        {
            Emit(0xF0, 0xFF, 0x05);
            UInt32(state + offset);
        }
        if (chance == 0)
        {
            code.AddRange(original);
        }
        else
        {
            Emit(0x9C, 0x60);
            // Execute the native epoch store atomically and retain its previous value.
            Emit(0x8B, 0xC1, 0x87, 0x45, 0x04, 0x3B, 0xC8);
            Branch(0x86, "done");
            Emit(0x0F, 0xB7, 0x4E, CurrentAbilityOffset, 0x83, 0xF9, 0x01);
            Branch(0x82, "invalid");
            Emit(0x81, 0xF9);
            UInt32(200);
            Branch(0x87, "invalid");
            Emit(0x0F, 0xB7, 0x46, PotentialAbilityOffset, 0x83, 0xF8, 0x01);
            Branch(0x82, "invalid");
            Emit(0x3D);
            UInt32(200);
            Branch(0x87, "invalid");
            Branch(0x84, "done");
            Emit(0x8B, 0xD0, 0x2B, 0xD1, 0x83, 0xFA, 0x04);
            Branch(0x87, "done");
            CalculateChance(policy);
            Count(4);
            {
                labels.Add("random", code.Count);
                Emit(0xA1);
                UInt32(state);
                Emit(0x8B, 0xC8, 0x8B, 0xD1, 0xC1, 0xE2, 0x0D, 0x33, 0xCA);
                Emit(0x8B, 0xD1, 0xC1, 0xEA, 0x11, 0x33, 0xCA);
                Emit(0x8B, 0xD1, 0xC1, 0xE2, 0x05, 0x33, 0xCA);
                Emit(0xF0, 0x0F, 0xB1, 0x0D);
                UInt32(state);
                Branch(0x85, "random");
                // xorshift32 emits 1..UINT_MAX; reject the incomplete bucket.
                Emit(0x8B, 0xC1, 0x48, 0x3D);
                UInt32(4294960000);
                Branch(0x83, "random");
                Emit(0x33, 0xD2, 0xB9);
                UInt32(10000);
                Emit(0xF7, 0xF1);
                Emit(0x3B, 0x54, 0x24, 0x0C);
                Branch(0x83, "done");
            }
            labels.Add("increase", code.Count);
            Emit(0x0F, 0xB7, 0x4E, CurrentAbilityOffset, 0x83, 0xF9, 0x01);
            Branch(0x82, "invalid");
            Emit(0x81, 0xF9);
            UInt32(200);
            Branch(0x87, "invalid");
            Emit(0x0F, 0xB7, 0x46, PotentialAbilityOffset, 0x83, 0xF8, 0x01);
            Branch(0x82, "invalid");
            Emit(0x3D);
            UInt32(200);
            Branch(0x87, "invalid");
            Branch(0x84, "done");
            Emit(0x8B, 0xD0, 0x2B, 0xD1, 0x83, 0xFA, 0x04);
            Branch(0x87, "done");
            Emit(0x8D, 0x50, 0x01, 0x66, 0xF0, 0x0F, 0xB1, 0x56, PotentialAbilityOffset);
            Branch(0x85, "increase");
            Count(8);
            // PUSHAD's saved ESP slot is ignored by POPAD; retain the qualifying CA there.
            Emit(0x89, 0x4C, 0x24, 0x0C);
            // Never wait on the launcher or another writer; report lost log entries instead.
            Emit(0x8B, 0xF8, 0x33, 0xC0, 0xB9);
            UInt32(1);
            Emit(0xF0, 0x0F, 0xB1, 0x0D);
            UInt32(state + 16);
            Branch(0x85, "logDropped");
            Emit(0xA1);
            UInt32(state + 20);
            Emit(0x8B, 0xD0, 0x2B, 0x15);
            UInt32(state + 24);
            Emit(0x81, 0xFA);
            UInt32(LogCapacity);
            Branch(0x83, "logFull");
            Emit(0x25);
            UInt32(LogCapacity - 1);
            Emit(0x69, 0xD8);
            UInt32(LogEntrySize);
            Emit(0x03, 0x1D);
            UInt32(state + 32);
            Emit(0x66, 0x89, 0x7B, 0x08, 0x47, 0x66, 0x89, 0x7B, 0x0A);
            // Resolve the shared PERSON base as native training does; player/staff has a different layout.
            Emit(0x8B, 0x46, 0x04, 0x8B, 0x40, 0x04, 0x8D, 0x6C, 0x06, 0x04,
                0x8B, 0x45, 0x14);
            Emit(0x89, 0x03, 0x8B, 0x44, 0x24, 0x18, 0x89, 0x43, 0x04);
            Emit(0x89, 0x73, 0x18, 0x8B, 0x44, 0x24, 0x0C, 0x89, 0x43, 0x1C,
                0x33, 0xC0, 0x89, 0x43, 0x0C);
            CopyName(FirstNameOffset, 16, 32, "firstName");
            CopyName(LastNameOffset, 20, 224, "lastName");
            Count(20);
            labels.Add("logUnlock", code.Count);
            Emit(0x33, 0xC0, 0x87, 0x05);
            UInt32(state + 16);
            Emit(0xE9);
            branches.Add((code.Count, "done"));
            UInt32(0);
            labels.Add("logFull", code.Count);
            Count(28);
            Emit(0xE9);
            branches.Add((code.Count, "logUnlock"));
            UInt32(0);
            labels.Add("logDropped", code.Count);
            Count(28);
            Emit(0xE9);
            branches.Add((code.Count, "done"));
            UInt32(0);
            labels.Add("invalid", code.Count);
            Count(12);
            labels.Add("done", code.Count);
            Emit(0x61, 0x9D);
            code.AddRange(original.AsSpan(3).ToArray());
        }
        code.AddRange(SuspendedGameProcess.BuildJump(address + (uint)code.Count,
            HookAddress + (uint)original.Length, 5));
        var payload = code.ToArray();
        foreach (var branch in branches)
            BinaryPrimitives.WriteInt32LittleEndian(payload.AsSpan(branch.Offset, 4),
                labels[branch.Label] - (branch.Offset + 4));
        return payload;

        void CalculateChance(PaGrowthPolicy model)
        {
            // Native PERSON resolution and its read-only age getter (argument 0 = current game date).
            Emit(0x8B, 0x46, 0x04, 0x8B, 0x40, 0x04, 0x8D, 0x5C, 0x06, 0x04,
                0x8B, 0x03, 0x6A, 0, 0x8B, 0xCB, 0xFF, 0x90);
            UInt32(0x88);
            Emit(0x0F, 0xB6, 0xC0, 0x83, 0xF8, 14);
            Branch(0x82, "invalid");
            Emit(0x83, 0xF8, 100);
            Branch(0x87, "invalid");
            foreach (var (band, index) in model.AgeBands.Select((band, index) => (band, index)))
            {
                Emit(0x83, 0xF8, (byte)band.MaximumAge);
                Branch(0x87, $"ageNext{index}");
                Emit(0xBF);
                UInt32((uint)band.MultiplierPercent);
                Emit(0xE9);
                branches.Add((code.Count, "ageReady"));
                UInt32(0);
                labels.Add($"ageNext{index}", code.Count);
            }
            Branch(0x87, "invalid");
            labels.Add("ageReady", code.Count);
            Emit(0x8B, 0xD3, 0x2B, 0x52, 0xFC, 0x8B, 0x92);
            UInt32(0xCC);
            Emit(0x85, 0xD2);
            Branch(0x84, "invalid");
            Emit(0x0F, 0xBE, 0x42, 0x20);
            AttributeBounds();
            Emit(0x69, 0xC0);
            UInt32((uint)model.ProfessionalismWeight);
            Emit(0x8B, 0xE8, 0x0F, 0xBE, 0x42, 0x1D);
            AttributeBounds();
            Emit(0x69, 0xC0);
            UInt32((uint)model.AmbitionWeight);
            Emit(0x03, 0xE8, 0x8B, 0x96);
            UInt32(0xCC);
            Emit(0x85, 0xD2);
            Branch(0x84, "invalid");
            // Selector 0x4D uses the native 1..100 representation: floor((raw + 2) / 5), clamp 1..20.
            Emit(0x0F, 0xBE, 0x42, 0x69, 0x83, 0xF8, 1);
            Branch(0x82, "invalid");
            Emit(0x83, 0xF8, 100);
            Branch(0x87, "invalid");
            Emit(0x83, 0xC0, 2, 0x33, 0xD2, 0xB9);
            UInt32(5);
            Emit(0xF7, 0xF1, 0x85, 0xC0);
            Branch(0x85, "determinationReady");
            Emit(0x40);
            labels.Add("determinationReady", code.Count);
            Emit(0x69, 0xC0);
            UInt32((uint)model.DeterminationWeight);
            Emit(0x03, 0xC5, 0x05);
            UInt32((uint)model.MentalityOffset);
            Emit(0x0F, 0xAF, 0xC7, 0x69, 0xC0);
            UInt32((uint)model.BaseChancePercent);
            Emit(0x05);
            UInt32((uint)(model.MentalityDivisor / 2));
            Emit(0x33, 0xD2, 0xB9);
            UInt32((uint)model.MentalityDivisor);
            Emit(0xF7, 0xF1, 0x3D);
            UInt32(10000);
            Branch(0x86, "chanceReady");
            Emit(0xB8);
            UInt32(10000);
            labels.Add("chanceReady", code.Count);
            Emit(0x89, 0x44, 0x24, 0x0C);
        }

        void AttributeBounds()
        {
            Emit(0x83, 0xF8, 1);
            Branch(0x82, "invalid");
            Emit(0x83, 0xF8, 20);
            Branch(0x87, "invalid");
        }

        void CopyName(byte personOffset, byte lengthOffset, int textOffset, string label)
        {
            Emit(0xC7, 0x43, lengthOffset);
            UInt32(0);
            Emit(0x8B, 0xD5, 0x2B, 0x52, 0xFC, 0x8B, 0x52, personOffset);
            Emit(0x85, 0xD2);
            Branch(0x84, label + "Missing");
            Emit(0x8B, 0x52, 0x24, 0x85, 0xD2);
            Branch(0x84, label + "Missing");
            Emit(0x0F, 0xB7, 0x4A, 0x04, 0x85, 0xC9);
            Branch(0x84, label + "Missing");
            Emit(0x8B, 0x52, 0x08, 0x85, 0xD2);
            Branch(0x84, label + "Missing");
            Emit(0x83, 0xF9, NameCapacity);
            Branch(0x86, label + "Copy");
            Emit(0xB9);
            UInt32(NameCapacity);
            Emit(0x83, 0x4B, 0x0C, 0x02);
            labels.Add(label + "Copy", code.Count);
            Emit(0x89, 0x4B, lengthOffset, 0x56, 0x8B, 0xF2, 0x8D, 0xBB);
            UInt32((uint)textOffset);
            Emit(0xFC, 0xF3, 0x66, 0xA5, 0x5E, 0xE9);
            branches.Add((code.Count, label + "Done"));
            UInt32(0);
            labels.Add(label + "Missing", code.Count);
            Emit(0x83, 0x4B, 0x0C, 0x01);
            labels.Add(label + "Done", code.Count);
        }
    }
}
