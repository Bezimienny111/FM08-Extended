namespace FmLauncher;

internal sealed record PaAgeBand(int MaximumAge, int MultiplierPercent);

internal sealed class PaGrowthPolicy
{
    internal static PaGrowthPolicy Default { get; } = new();
    internal int BaseChancePercent { get; init; } = 8;
    internal int ProfessionalismWeight { get; init; } = 60;
    internal int AmbitionWeight { get; init; } = 25;
    internal int DeterminationWeight { get; init; } = 15;
    internal int MentalityOffset { get; init; } = 850;
    internal int MentalityDivisor { get; init; } = 1900;
    internal IReadOnlyList<PaAgeBand> AgeBands { get; init; } = Array.AsReadOnly(new[]
    {
        new PaAgeBand(18, 125), new PaAgeBand(21, 110), new PaAgeBand(24, 100),
        new PaAgeBand(27, 70), new PaAgeBand(30, 40), new PaAgeBand(33, 15), new PaAgeBand(100, 5)
    });

    internal void Validate()
    {
        if (BaseChancePercent is < 0 or > 100
            || ProfessionalismWeight < 0 || AmbitionWeight < 0 || DeterminationWeight < 0
            || (long)ProfessionalismWeight + AmbitionWeight + DeterminationWeight != 100
            || MentalityOffset is < 0 or > 10000 || MentalityDivisor is < 1 or > 100000
            || AgeBands.Count == 0 || AgeBands[^1].MaximumAge != 100
            || AgeBands.Any(band => band.MaximumAge is < 14 or > 100 || band.MultiplierPercent is < 1 or > 200)
            || !AgeBands.Select(band => band.MaximumAge).SequenceEqual(
                AgeBands.Select(band => band.MaximumAge).Distinct().Order()))
            throw new LauncherException("InvalidPaPolicy");
    }

    internal int ChanceBasisPoints(int age, int professionalism, int ambition, int determination)
    {
        Validate();
        if (age is < 14 or > 100 || professionalism is < 1 or > 20
            || ambition is < 1 or > 20 || determination is < 1 or > 20)
            throw new LauncherException("InvalidPaInputs");
        var weighted = ProfessionalismWeight * professionalism + AmbitionWeight * ambition
            + DeterminationWeight * determination;
        var ageFactor = AgeBands.First(band => age <= band.MaximumAge).MultiplierPercent;
        // Basis points, rounded half up; the native payload uses the same integer expression.
        return Math.Min(10000, (BaseChancePercent * ageFactor * (weighted + MentalityOffset)
            + MentalityDivisor / 2) / MentalityDivisor);
    }
}
