using System.Reflection;
using System.Security.Cryptography;
using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    // R13 withdrawal regression. Private files only; no live skin installation or cleanup.
    private static void TestNocheExt(string gamePath, string actualSkins, string output)
    {
        Assert(!Directory.Exists(output));
        Directory.CreateDirectory(output);
        Assert(ExtSkinCatalog.All.Select(s => s.DirectoryName).SequenceEqual(new[] {
            "fm2008_ext_left", "fm2008_ext_right", "steklo_black_ext_left", "steklo_black_ext_right" }));
        Assert(SkinPanelInstaller.ExtSkins.Count == 4 && !ExtSkinCatalog.All.Any(s => s.CreateWhenParentPresent));
        var skins = Path.Combine(output, "private-data", "skins");
        var parent = Path.Combine(skins, "noche");
        var child = Path.Combine(skins, "NocheExt");
        Directory.CreateDirectory(parent); Directory.CreateDirectory(child);
        File.WriteAllText(Path.Combine(parent, "noche.xml"), "<properties />");
        File.WriteAllText(Path.Combine(child, "NocheExt.xml"), "<properties />");
        var receipt = Path.Combine(output, "private-data", ".fmext", "player-panels-noche", "installation.json");
        Directory.CreateDirectory(Path.GetDirectoryName(receipt)!);
        File.WriteAllText(receipt, "historical Noche receipt deliberately unreadable");
        string Hash(string path) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)));
        var before = Directory.EnumerateFiles(output, "*", SearchOption.AllDirectories).ToDictionary(p => p, Hash);
        var validate = typeof(SkinPanelInstaller).GetMethod("ValidateDestination", BindingFlags.NonPublic | BindingFlags.Static)!;
        foreach (var skin in ExtSkinCatalog.All)
            validate.Invoke(null, new object[] { skins, Path.Combine(skins, skin.DirectoryName, "panels", "player profile.xml") });
        try
        {
            validate.Invoke(null, new object[] { skins, Path.Combine(child, "panels", "player profile.xml") });
            throw new InvalidOperationException("NocheExt write scope remained enabled.");
        }
        catch (TargetInvocationException error) when (error.InnerException is InvalidDataException) { }
        var read = typeof(SkinPanelInstaller).GetMethod("ReadReceipt", BindingFlags.NonPublic | BindingFlags.Static)!;
        Assert(read.Invoke(null, new object[] { skins }) is null);
        Assert(before.All(pair => File.Exists(pair.Key) && Hash(pair.Key) == pair.Value));
        Assert(Directory.EnumerateFiles(output, "*", SearchOption.AllDirectories).Count() == before.Count);
        Console.WriteLine("PASS: four supported skins, NocheExt writes rejected, historical Noche receipt ignored, private fixtures unchanged.");
    }
}
