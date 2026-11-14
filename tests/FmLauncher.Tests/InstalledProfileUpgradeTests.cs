using System.Reflection;
using System.Runtime.Loader;
using System.Security.Cryptography;
using System.Text.Json;
using System.Xml.Linq;
using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    private static void TestInstalledProfileUpgrade(string gamePath, string userData, string output, bool includeEnglish = true, string firstLanguage = "pl", bool gameLanguageSync = false)
    {
        var oldSkins=Path.Combine(userData,"skins");
        var oldReceiptRoot=Path.Combine(userData,".fmext","player-panels");
        var receiptPath=Path.Combine(oldReceiptRoot,"installation.json");
        var receipt=File.Exists(receiptPath) ? JsonSerializer.Deserialize<SkinPanelReceipt>(File.ReadAllBytes(receiptPath)) : null;
        Assert(receipt is null || receipt.Schema==2 && receipt.Status=="installed" && receipt.HiddenAttributes);
        var originals=Directory.EnumerateFiles(oldSkins,"*.xml",SearchOption.AllDirectories)
            .Concat(Directory.Exists(oldReceiptRoot) ? Directory.EnumerateFiles(oldReceiptRoot,"*",SearchOption.AllDirectories) : [])
            .ToDictionary(p=>p,p=>SHA256.HashData(File.ReadAllBytes(p)));
        var temp=Path.Combine(Path.GetTempPath(),"FmLauncher.InstalledUpgrade."+Guid.NewGuid().ToString("N"));
        try
        {
            var fakeGame=Path.Combine(temp,"game");
            var exe=Path.Combine(fakeGame,"R2UpgradeFixture.exe");
            Directory.CreateDirectory(fakeGame);File.WriteAllBytes(exe,[0x4D,0x5A]);
            foreach(var relative in new[]{"data/panels.fmf","data/skins.fmf","data/updates/update-802/data/panels.fmf"})
            {
                var dest=Path.Combine(fakeGame,relative);Directory.CreateDirectory(Path.GetDirectoryName(dest)!);
                File.Copy(Path.Combine(Path.GetDirectoryName(gamePath)!,relative),dest);
            }
            var clonedData=Path.Combine(temp,"user");
            var skins=Path.Combine(clonedData,"skins");
            var root=Path.Combine(clonedData,".fmext","player-panels");
            foreach(var p in Directory.EnumerateFiles(oldSkins,"*.xml",SearchOption.AllDirectories))
            {
                var dest=Path.Combine(skins,Path.GetRelativePath(oldSkins,p));
                Directory.CreateDirectory(Path.GetDirectoryName(dest)!);File.Copy(p,dest);
            }
            foreach(var p in Directory.Exists(oldReceiptRoot) ? Directory.EnumerateFiles(oldReceiptRoot,"*",SearchOption.AllDirectories) : [])
            {
                var dest=Path.Combine(root,Path.GetRelativePath(oldReceiptRoot,p));
                Directory.CreateDirectory(Path.GetDirectoryName(dest)!);File.Copy(p,dest);
            }
            if (receipt is not null)
            {
                var moved=receipt with { SkinsRoot=skins,Files=receipt.Files.Select(f=>f with
                {
                    Path=Path.Combine(skins,Path.GetRelativePath(oldSkins,f.Path)),
                    Backup=f.Backup is null ? null : Path.Combine(root,Path.GetRelativePath(oldReceiptRoot,f.Backup))
                }).ToList()};
                File.WriteAllBytes(Path.Combine(root,"installation.json"),JsonSerializer.SerializeToUtf8Bytes(moved));
            }
            else
            {
                // No installed receipt exists in actual Dane. Exercise the real older
                // candidate installer on this clone, without inventing installation history.
                var oldFolder=Path.Combine(Path.GetDirectoryName(gamePath)!,"FmLauncher","data","research",
                    "SKIN_PLAYER_PANELS_IMPLEMENTATION_20261111","build","candidate-0.1.3");
                var alc=new AssemblyLoadContext("OldSkinInstaller."+Guid.NewGuid().ToString("N"),true);
                try
                {
                    var assembly=alc.LoadFromAssemblyPath(Path.Combine(oldFolder,"FmLauncher.dll"));
                    var flags=BindingFlags.Public|BindingFlags.NonPublic;
                    var lt=assembly.GetType("FmLauncher.Localizer",true)!;
                    var opt=assembly.GetType("FmLauncher.PlayerProfilePanelOptions",true)!;
                    var installer=assembly.GetType("FmLauncher.SkinPanelInstaller",true)!;
                    var loc=Activator.CreateInstance(lt,flags|BindingFlags.Instance,null,
                        [Path.Combine(oldFolder,"FmLauncher.languages.json")],null)!;
                    lt.GetMethod("Select",flags|BindingFlags.Instance)!.Invoke(loc,["pl"]);
                    var oldOptions=Activator.CreateInstance(opt,flags|BindingFlags.Instance,null,[false,true,"DC"],null)!;
                    var install=installer.GetMethods(flags|BindingFlags.Static).Single(m=>m.Name=="InstallExt"&&m.GetParameters().Length==5);
                    install.Invoke(null,[exe,skins,"Zmęczenie sezonowe",oldOptions,loc]);
                }
                finally { alc.Unload(); }
                Assert(File.Exists(Path.Combine(root,"installation.json")));
            }
            var options=new PlayerProfilePanelOptions(true,true);
            var localizer=PanelLocalizer();
            localizer.Select(firstLanguage);
            Assert(SkinPanelInstaller.InstallExt(exe,skins,localizer.Text("PanelFatigueTitle"),options,localizer)>0);
            SkinPanelInstaller.ValidateProfileReadiness(skins,options);
            Assert(SkinPanelInstaller.InstallExt(exe,skins,localizer.Text("PanelFatigueTitle"),options,localizer)==0);
            var upgraded=JsonSerializer.Deserialize<SkinPanelReceipt>(File.ReadAllBytes(Path.Combine(root,"installation.json")))!;
            foreach(var file in upgraded.Files)
                if(file.Backup is not null)
                    Assert(Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(file.Backup)))==file.BeforeHash);
            foreach(var name in SkinPanelInstaller.ExtSkins)
            {
                var xml=XDocument.Load(Path.Combine(skins,name,"panels","player profile.xml"));
                Assert(xml.Descendants("widget").Count(e=>(string?)e.Attribute("id")=="Fpos"
                    && (string?)e.Attribute("selection")=="Fpn0")==1);
                foreach(var field in PlayerProfileFields.Hidden)
                    Assert(xml.Descendants("widget").Count(e=>(string?)e.Attribute("id")==field.Id)==1);
                var popup=xml.Descendants("widget").Single(e=>(string?)e.Attribute("id")=="Fpos");
                Assert((string?)popup.Attribute("fixed")=="false" && (string?)popup.Attribute("auto_tick_exclusive")=="true");
                foreach(var id in new[]{"Fhp1","Fhp2","Fhp3"})
                    Assert(xml.Descendants("widget").Single(e=>(string?)e.Attribute("id")==id)
                        .Descendants("widget").Count(e=>PlayerProfileFields.Hidden.Any(f=>f.Id==(string?)e.Attribute("id")))==4);
                Assert(xml.Descendants("container").Single(e=>(string?)e.Attribute("id")=="Flgb")
                    .Ancestors("container").Any(e=>(string?)e.Attribute("id")=="Fpsi"));
                Assert((string?)xml.Descendants("container").Single(e=>(string?)e.Attribute("id")=="Fhid").Attribute("height")=="112");
                Assert((string?)xml.Descendants("container").Single(e=>(string?)e.Attribute("id")=="Faur").Attribute("height")=="304");
                var legend=xml.Descendants("container").Single(e=>(string?)e.Attribute("id")=="Flgb");
                Assert(legend.Attribute("class") is null && (string?)legend.Attribute("height")=="88"
                    && legend.Descendants("widget").Count(e=>(string?)e.Attribute("id")=="Fltb")==1);
                if(localizer.Code=="en")
                {
                    var hidden=xml.Descendants("container").Single(e=>(string?)e.Attribute("id")=="Fhid");
                    foreach(var field in PlayerProfileFields.Hidden)
                        Assert(hidden.Descendants("widget").Count(e=>(string?)e.Attribute("col")=="0"
                            && PanelXmlText(e,"text")==field.English)==1);
                    for(var index=0;index<PositionHighlightModel.Roles.Count;index++)
                        Assert(PanelXmlText(popup.Descendants("record").Single(e=>(string?)e.Attribute("id")==PlayerProfileXml.RoleItemId(index)),
                            "name")==PositionHighlightModel.Roles[index].Name("en"));
                    var table=legend.Descendants("widget").Single(e=>(string?)e.Attribute("id")=="Fltb");
                    Assert(table.Descendants("record").Any(e=>PanelXmlText(e,"text")==localizer.Text("ProfilePanelLegendTitle")));
                    var expected=localizer.Text("ProfilePanelLegend").Split(". ",StringSplitOptions.RemoveEmptyEntries)
                        .Select(e=>e.EndsWith('.')?e:e+".");
                    Assert(table.Elements("widget").Select(e=>PanelXmlText(e,"text")).SequenceEqual(expected));
                }
            }
            if(gameLanguageSync)
            {
                var preference=Path.Combine(temp,"current_language.xml");
                var ui=PanelLocalizer();ui.Select("en");
                foreach(var (native,expected) in new[]{("polish","pl"),("german","en"),("polish","pl"),("english","en")})
                {
                    File.WriteAllText(preference,"<record><string id='valu' value='"+native+"'/></record>");
                    var prefHash=SHA256.HashData(File.ReadAllBytes(preference));
                    var panels=GameLanguageResolver.CreatePanelLocalizer(ui,preference);
                    Assert(panels.Code==expected && ui.Code=="en");
                    Assert(SkinPanelInstaller.EnsurePanelLanguage(exe,skins,options,panels)>0);
                    SkinPanelInstaller.ValidateProfileReadiness(skins,options);
                    var current=JsonSerializer.Deserialize<SkinPanelReceipt>(File.ReadAllBytes(Path.Combine(root,"installation.json")))!;
                    Assert(current.PanelLanguage==expected && current.PositionHighlights && current.HiddenAttributes);
                    var receiptBytes=File.ReadAllBytes(Path.Combine(root,"installation.json"));
                    Assert(SkinPanelInstaller.EnsurePanelLanguage(exe,skins,options,panels)==0);
                    Assert(File.ReadAllBytes(Path.Combine(root,"installation.json")).SequenceEqual(receiptBytes));
                    Assert(SHA256.HashData(File.ReadAllBytes(preference)).SequenceEqual(prefHash));
                    foreach(var name in SkinPanelInstaller.ExtSkins)
                    {
                        var xml=XDocument.Load(Path.Combine(skins,name,"panels","player profile.xml"));
                        var hidden=xml.Descendants("container").Single(e=>(string?)e.Attribute("id")=="Fhid");
                        foreach(var field in PlayerProfileFields.Hidden)
                            Assert(hidden.Descendants("widget").Count(e=>(string?)e.Attribute("col")=="0"
                                && PanelXmlText(e,"text")==(expected=="pl"?field.Polish:field.English))==1);
                        foreach(var element in hidden.Descendants().Where(e=>e.Elements("string").Any(x=>(string?)x.Attribute("id")=="text_not_translated")))
                            Assert(element.Elements("string").Where(e=>(string?)e.Attribute("id")=="text_not_translated")
                                .All(e=>(string?)e.Attribute("translate")=="false"));
                        var training=XDocument.Load(Path.Combine(skins,name,"panels","player training.xml"));
                        var fatigue=training.Descendants("widget").Single(e=>(string?)e.Attribute("id")=="Fmjd");
                        var fatigueLabel=fatigue.Parent!.Elements("widget").Single(e=>(string?)e.Attribute("col")=="0"
                            && (string?)e.Attribute("row")==(string?)fatigue.Attribute("row"));
                        Assert(PanelXmlText(fatigueLabel,"text")==panels.Text("PanelFatigueTitle"));
                        Assert(fatigueLabel.Elements("string").Single(e=>(string?)e.Attribute("id")=="text_not_translated")
                            .Attribute("translate")!.Value=="false");
                        var registry=XDocument.Load(Path.Combine(skins,name,"panels","person list table.xml"));
                        foreach(var id in new[]{"Fjad","Fcab","Fpab"})
                        {
                            var definition=registry.Descendants("record").Single(e=>e.Elements("flags").Any(f=>(string?)f.Attribute("id")=="id" && (string?)f.Attribute("value")==id));
                            var heading=definition.Elements("record").Single(e=>(string?)e.Attribute("id")=="column_heading");
                            Assert(heading.Elements("string").Count(e=>(string?)e.Attribute("translate")=="false"
                                && (string?)e.Attribute("id") is "text_not_translated" or "hint_not_translated")==2);
                        }
                        var squad=XDocument.Load(Path.Combine(skins,name,"panels","team squad.xml"));
                        var edit=squad.Descendants("record").Single(e=>(string?)e.Attribute("id")==SkinPanelInstaller.EditViewId);
                        Assert((PanelXmlText(edit,"name")??PanelXmlText(edit,"text"))==(expected=="pl"?"Edycja":"Edit"));
                    }
                }
                var receiptFile=Path.Combine(root,"installation.json");
                var legacy=JsonSerializer.Deserialize<SkinPanelReceipt>(File.ReadAllBytes(receiptFile))! with {PanelLanguage=null};
                File.WriteAllBytes(receiptFile,JsonSerializer.SerializeToUtf8Bytes(legacy));
                var english=GameLanguageResolver.CreatePanelLocalizer(ui,preference);
                Assert(SkinPanelInstaller.EnsurePanelLanguage(exe,skins,options,english)==0);
                Assert(JsonSerializer.Deserialize<SkinPanelReceipt>(File.ReadAllBytes(receiptFile))!.PanelLanguage=="en");
                using(var start=new Mutex(false,@"Local\FmLauncher.GameStart"))
                {
                    Assert(start.WaitOne(0));
                    try{Assert(SkinPanelInstaller.EnsurePanelLanguage(exe,skins,options,english)==0);}
                    finally{start.ReleaseMutex();}
                }
                var target=legacy.Files[0].Path;var saved=File.ReadAllBytes(target);
                try
                {
                    File.WriteAllBytes(target,saved.Concat(new byte[]{0}).ToArray());
                    bool rejected=false;
                    try{SkinPanelInstaller.EnsurePanelLanguage(exe,skins,options,english);}
                    catch(LauncherException){rejected=true;}
                    Assert(rejected && File.ReadAllBytes(target).SequenceEqual(saved.Concat(new byte[]{0})));
                }
                finally{File.WriteAllBytes(target,saved);}
                var absent=Path.Combine(temp,"uninstalled","skins");Directory.CreateDirectory(absent);
                Assert(SkinPanelInstaller.EnsurePanelLanguage(exe,absent,options,english)==0
                    && !Directory.Exists(Path.Combine(temp,"uninstalled",".fmext")));
            }
            if(includeEnglish)
            {
            localizer.Select("en");
            Assert(SkinPanelInstaller.InstallExt(exe,skins,localizer.Text("PanelFatigueTitle"),options,localizer)>0);
            SkinPanelInstaller.ValidateProfileReadiness(skins,options);
            Assert(SkinPanelInstaller.InstallExt(exe,skins,localizer.Text("PanelFatigueTitle"),options,localizer)==0);
            foreach(var name in SkinPanelInstaller.ExtSkins)
            {
                var xml=XDocument.Load(Path.Combine(skins,name,"panels","player profile.xml"));
                var table=xml.Descendants("widget").Single(e=>(string?)e.Attribute("id")=="Fltb");
                Assert(table.Descendants("record").Any(e=>PanelXmlText(e,"text")==localizer.Text("ProfilePanelLegendTitle")));
            }
            }
            Directory.CreateDirectory(output);
            File.WriteAllText(Path.Combine(output,"installed-upgrade.json"),JsonSerializer.Serialize(new {
                Status="PASS",SourceReceipt=receiptPath,SourceModule=receipt?.ModuleVersion ?? "0.1.3",
                SourceReceiptActuallyPresent=receipt is not null,SourcePreparedWithRealOldInstaller=receipt is null,
                SourcePosition=receipt?.PositionHighlights ?? false,TargetBothOn=true,Profiles=upgraded.Files.Count(f=>Path.GetFileName(f.Path)=="player profile.xml"),ManagedLanguages=includeEnglish ? new[]{"pl","en"} : new[]{firstLanguage},
                Idempotent=true,OriginalBackupChainPreserved=true,ActualUserDataWritten=false,GameLanguageSyncTested=gameLanguageSync
            },new JsonSerializerOptions{WriteIndented=true}));
            Assert(SkinPanelInstaller.Uninstall(exe,skins)>0);
            foreach(var file in upgraded.Files)
                Assert(file.BeforeHash is null ? !File.Exists(file.Path)
                    : Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(file.Path)))==file.BeforeHash);
        }
        finally
        {
            if(Directory.Exists(temp))
            {
                Assert(Path.GetFullPath(temp).StartsWith(Path.GetFullPath(Path.GetTempPath()),StringComparison.OrdinalIgnoreCase)
                    && Path.GetFileName(temp).StartsWith("FmLauncher.InstalledUpgrade.",StringComparison.Ordinal));
                foreach(var file in Directory.EnumerateFiles(temp,"*",SearchOption.AllDirectories))
                    File.SetAttributes(file,File.GetAttributes(file)&~FileAttributes.ReadOnly);
                Directory.Delete(temp,true);
            }
        }
        foreach(var (p,hash)in originals)Assert(SHA256.HashData(File.ReadAllBytes(p)).SequenceEqual(hash));
        Console.WriteLine(receipt is not null
            ? "PASS: actual installed4Ext receipt upgraded on clone; idempotent, original backups and Undo preserved; actual user data unchanged."
            : "PASS: real older hidden-only installer/receipt upgraded on clone; idempotent, original backups and Undo preserved; actual user data unchanged.");
    }
}
