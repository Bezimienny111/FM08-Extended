using System.Reflection;
using System.Runtime.Loader;
using System.Security.Cryptography;
using System.Text.Json;
using FmLauncher;

namespace FmLauncher.Tests;
internal static partial class Program
{
    private static void TestNocheR10Compatibility(string dummyExe,string skins,string gamePath,
        Localizer pl,Localizer en,PlayerProfilePanelOptions options)
    {
        en.Select("en");pl.Select("pl");
        var data=Path.GetDirectoryName(skins)!;
        var legacy=Path.Combine(data,".fmext","player-panels","installation.json");
        var extra=Path.Combine(data,".fmext","player-panels-noche","installation.json");
        SkinPanelReceipt Receipt(string path)=>JsonSerializer.Deserialize<SkinPanelReceipt>(File.ReadAllBytes(path))!;
        string Hash(string path)=>Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)));
        var oldDll=Path.Combine(Path.GetDirectoryName(gamePath)!,"Launcher_0.1.3_R10","FmLauncher.dll");
        var context=new AssemblyLoadContext("R10SkinCompatibility",isCollectible:true);
        var assembly=context.LoadFromAssemblyPath(Path.GetFullPath(oldDll));
        var installer=assembly.GetType("FmLauncher.SkinPanelInstaller",true)!;
        var optType=assembly.GetType("FmLauncher.PlayerProfilePanelOptions",true)!;
        var localeType=assembly.GetType("FmLauncher.Localizer",true)!;
        var oldOptions=Activator.CreateInstance(optType,[true,true,"DC"])!;
        var oldEnglish=Activator.CreateInstance(localeType,[Path.Combine(Path.GetDirectoryName(oldDll)!,"FmLauncher.languages.json")])!;
        localeType.GetMethod("Select")!.Invoke(oldEnglish,["en"]);
        object? Old(string method,params object[] args)
        {
            try{return installer.GetMethod(method,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args);}
            catch(TargetInvocationException e)when(e.InnerException is not null){throw e.InnerException;}
        }
        // Optional Noche parent absent: a four-only private clone remains a valid installation.
        var fourData=Path.Combine(Path.GetDirectoryName(data)!,"four-only");
        var fourSkins=Path.Combine(fourData,"skins");
        foreach(var path in Directory.EnumerateFiles(skins,"*.xml",SearchOption.AllDirectories))
        {
            var relative=Path.GetRelativePath(skins,path);
            var folder=relative.Split(Path.DirectorySeparatorChar)[0];
            if(folder.Equals("NocheExt",StringComparison.OrdinalIgnoreCase)||folder.Equals("noche",StringComparison.OrdinalIgnoreCase))continue;
            var target=Path.Combine(fourSkins,relative);Directory.CreateDirectory(Path.GetDirectoryName(target)!);File.Copy(path,target);
        }
        var fourReceiptRoot=Path.Combine(fourData,".fmext","player-panels");
        var oldRoot=Path.GetDirectoryName(legacy)!;
        foreach(var path in Directory.EnumerateFiles(oldRoot,"*",SearchOption.AllDirectories))
        {
            var target=Path.Combine(fourReceiptRoot,Path.GetRelativePath(oldRoot,path));Directory.CreateDirectory(Path.GetDirectoryName(target)!);File.Copy(path,target);
        }
        var fourReceipt=Receipt(legacy)with{SkinsRoot=fourSkins,Files=Receipt(legacy).Files.Select(f=>f with
        {
            Path=Path.Combine(fourSkins,Path.GetRelativePath(skins,f.Path)),
            Backup=f.Backup is null?null:Path.Combine(fourReceiptRoot,Path.GetRelativePath(oldRoot,f.Backup))
        }).ToList()};
        File.WriteAllBytes(Path.Combine(fourReceiptRoot,"installation.json"),JsonSerializer.SerializeToUtf8Bytes(fourReceipt));
        SkinPanelInstaller.InstallExt(dummyExe,fourSkins,pl.Text("PanelFatigueTitle"),options,pl);
        Assert(!Directory.Exists(Path.Combine(fourSkins,"NocheExt"))&&!File.Exists(Path.Combine(fourData,".fmext","player-panels-noche","installation.json")));
        SkinPanelInstaller.ValidateProfileReadiness(fourSkins,options);Old("ValidateProfileReadiness",fourSkins,oldOptions);
        // Invoke the ACTUAL protected R10 assembly, not a reimplementation of its validator.
        Old("ValidateProfileReadiness",skins,oldOptions);
        SkinPanelInstaller.InstallExt(dummyExe,skins,pl.Text("PanelFatigueTitle"),options,pl);
        var nocheProfile=Path.Combine(skins,"NocheExt","panels","player profile.xml");
        var nochePL=Hash(nocheProfile);
        Old("EnsurePanelLanguage",dummyExe,skins,oldOptions,oldEnglish);
        Assert(Receipt(legacy).PanelLanguage=="en" && Receipt(extra).PanelLanguage=="pl" && Hash(nocheProfile)==nochePL);
        Assert(SkinPanelInstaller.EnsurePanelLanguage(dummyExe,skins,options,en)>0);
        Assert(Receipt(legacy).PanelLanguage=="en" && Receipt(extra).PanelLanguage=="en" && Hash(nocheProfile)!=nochePL);
        Old("ValidateProfileReadiness",skins,oldOptions);
        // R10 may change only its four feature switches. Language synchronization preserves each part's options.
        var oldPartial=Activator.CreateInstance(optType,[false,true,"DC"])!;
        Old("InstallExt",dummyExe,skins,en.Text("PanelFatigueTitle"),oldPartial,oldEnglish);
        Assert(!Receipt(legacy).PositionHighlights && Receipt(extra).PositionHighlights);
        var partial=new PlayerProfilePanelOptions(false,true);
        SkinPanelInstaller.EnsurePanelLanguage(dummyExe,skins,partial,pl);
        Assert(!Receipt(legacy).PositionHighlights && Receipt(legacy).HiddenAttributes && Receipt(extra).PositionHighlights && Receipt(extra).HiddenAttributes);
        SkinPanelInstaller.ValidateProfileReadiness(skins,partial);
        Old("ValidateProfileReadiness",skins,oldPartial);
        SkinPanelInstaller.InstallExt(dummyExe,skins,pl.Text("PanelFatigueTitle"),options,pl);
        // A failure writing the SECOND receipt restores the first receipt AND every changed panel.
        var paths=Receipt(legacy).Files.Concat(Receipt(extra).Files).Select(f=>f.Path).Append(legacy).Append(extra).ToArray();
        var before=paths.ToDictionary(p=>p,Hash);
        using(var locked=new FileStream(extra,FileMode.Open,FileAccess.Read,FileShare.Read))
        {
            try{SkinPanelInstaller.EnsurePanelLanguage(dummyExe,skins,options,en);throw new InvalidOperationException("Expected second-receipt failure");}
            catch(LauncherException e){Assert(e.Key=="SkinInstallError");}
        }
        Assert(before.All(p=>Hash(p.Key)==p.Value));
        var saved=File.ReadAllBytes(legacy);var rec=Receipt(legacy);
        void Rejected(SkinPanelReceipt bad)
        {
            File.WriteAllBytes(legacy,JsonSerializer.SerializeToUtf8Bytes(bad));
            try{SkinPanelInstaller.InstallExt(dummyExe,skins,pl.Text("PanelFatigueTitle"),options,pl);throw new InvalidOperationException("Invalid receipt accepted");}
            catch(LauncherException e){Assert(e.Key=="SkinInstallError");}
            File.WriteAllBytes(legacy,saved);
            Assert(before.All(p=>Hash(p.Key)==p.Value));
        }
        Rejected(rec with{Files=rec.Files.Concat([rec.Files[0]]).ToList()});
        Rejected(rec with{Files=rec.Files.Concat([Receipt(extra).Files[0]]).ToList()});
        var f=rec.Files.First(f=>f.Backup is not null);
        Rejected(rec with{Files=rec.Files.Select(v=>v==f?v with{Backup=Path.Combine(data,"outside-backup.xml")}:v).ToList()});
        Old("ValidateProfileReadiness",skins,oldOptions);
        context.Unload();
        Console.WriteLine("PASS: actual R10 readiness, PL->R10 EN->R11 EN stale Noche refresh, independent options, two-receipt rollback and scope guards.");
    }
}
