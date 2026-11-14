using System.Diagnostics;
using System.Reflection;
using System.Runtime.Loader;
using System.Security.Cryptography;
using System.Text.Json;
namespace FmLauncher.Tests;
internal static class NocheDevInstaller
{
    private const string Root=@"J:\FM08dev";
    private static string Hash(string p)=>Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(p))).ToLowerInvariant();
    private static void Need(bool b,string why){if(!b)throw new InvalidDataException(why);}
    private static void NoGame(){var p=Process.GetProcessesByName("fm");try{Need(p.All(x=>x.HasExited),"STOP: FM is running; no close/kill permitted.");}finally{foreach(var x in p)x.Dispose();}}
    private static Dictionary<string,string> Snapshot(string root)=>Directory.EnumerateFiles(root,"*",SearchOption.AllDirectories).ToDictionary(Path.GetFullPath,Hash,StringComparer.OrdinalIgnoreCase);
    private sealed class Api : IDisposable
    {
        private readonly AssemblyLoadContext context=new("NocheDevReflection-"+Guid.NewGuid(),isCollectible:true);
        internal readonly Assembly Assembly;
        internal Api(string path){Assembly=context.LoadFromAssemblyPath(Path.GetFullPath(path));}
        internal object? Call(string type,string method,params object?[] args)
        {
            try{return Assembly.GetType("FmLauncher."+type,true)!.GetMethod(method,BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic)!.Invoke(null,args);}
            catch(TargetInvocationException e)when(e.InnerException is not null){throw e.InnerException;}
        }
        internal object Options(bool positions,bool hidden)=>Activator.CreateInstance(Assembly.GetType("FmLauncher.PlayerProfilePanelOptions",true)!,[positions,hidden,"DC"])!;
        internal object Locale(string path)=>Activator.CreateInstance(Assembly.GetType("FmLauncher.Localizer",true)!,[path])!;
        public void Dispose()=>context.Unload();
    }
    private static void Atomic(string path,byte[] bytes)
    {
        var temp=path+".noche-"+Guid.NewGuid().ToString("N")+".tmp";
        try{File.WriteAllBytes(temp,bytes);File.Move(temp,path,true);}finally{if(File.Exists(temp))File.Delete(temp);}
    }
    internal static void Run(string mode,string assemblyPath,string game,string skins,string reportPath)
    {
        var research=Path.Combine(Root,"FmLauncher","data","research","NOCHE_EXT_20261113","compat-r2");
        Need(mode is "check" or "install","Explicit check/install mode required.");
        Need(Path.GetFullPath(game)==Path.Combine(Root,"fm.exe")&&Path.GetFullPath(skins)==Path.Combine(Root,"Dane","skins"),"Wrong live target.");
        Need(Path.GetFullPath(assemblyPath)==Path.Combine(research,"candidate","FmLauncher.dll"),"Only reviewed R11 candidate allowed.");
        Need(Path.GetDirectoryName(Path.GetFullPath(reportPath))==research&&!File.Exists(reportPath),"New report in own scope required.");
        NoGame();
        var manifest=JsonDocument.Parse(File.ReadAllBytes(Path.Combine(research,"ready-manifest.json"))).RootElement;
        var candidate=Path.GetDirectoryName(assemblyPath)!;
        foreach(var p in manifest.GetProperty("CandidateFiles").EnumerateObject())
            Need(Hash(Path.Combine(candidate,p.Name))==p.Value.GetProperty("sha256").GetString(),"Candidate pin differs: "+p.Name);
        foreach(var p in manifest.GetProperty("SourceFiles").EnumerateObject())
            Need(Hash(Path.Combine(Root,p.Name))==p.Value.GetString(),"Source pin differs: "+p.Name);
        var r11=Path.Combine(Root,"Launcher_0.1.3_R11");var r10=Path.Combine(Root,"Launcher_0.1.3_R10");
        var config=Path.Combine(r11,"FmLauncher.config.json");Need(File.Exists(config),"Preserved R11 config required.");
        var cfg=JsonDocument.Parse(File.ReadAllBytes(config)).RootElement;
        var positions=cfg.GetProperty("PositionHighlightsEnabled").GetBoolean();var hidden=cfg.GetProperty("HiddenAttributesEnabled").GetBoolean();
        Need(positions&&hidden,"This reviewed plan requires both existing profile options; preserve other settings.");
        using var api=new Api(assemblyPath);using var old=new Api(Path.Combine(r10,"FmLauncher.dll"));
        using var verified=(IDisposable)api.Call("MatchRulePatch","OpenVerifiedGame",game)!;
        var options=api.Options(positions,hidden);var oldOptions=old.Options(positions,hidden);
        var ui=api.Locale(Path.Combine(candidate,"FmLauncher.languages.json"));
        var locale=api.Call("GameLanguageResolver","CreatePanelLocalizer",ui,null)!;
        var code=(string)locale.GetType().GetProperty("Code")!.GetValue(locale)!;
        var fatigue=(string)locale.GetType().GetMethod("Text")!.Invoke(locale,["PanelFatigueTitle",Array.Empty<object>()])!;
        var receiptPath=Path.Combine(Root,"Dane",".fmext","player-panels","installation.json");
        var legacy=JsonDocument.Parse(File.ReadAllBytes(receiptPath)).RootElement;
        Need(legacy.GetProperty("PanelLanguage").GetString()==code,"Language differs from protected four-skin baseline; stop for root review.");
        foreach(var f in legacy.GetProperty("Files").EnumerateArray())
        {
            var actual=f.GetProperty("Path").GetString()!;
            var expected=Path.Combine(research,"clone-run3","private-user","skins",Path.GetRelativePath(skins,actual));
            Need(File.Exists(expected)&&Hash(actual)==Hash(expected),"Live four-skin content differs from tested clone: "+actual);
        }
        old.Call("SkinPanelInstaller","ValidateProfileReadiness",skins,oldOptions);
        var protectedFiles=Snapshot(r10);
        foreach(var p in Snapshot(Path.Combine(skins,"noche")))protectedFiles.Add(p.Key,p.Value);
        foreach(var name in new[]{"fm2008_ext_left","fm2008_ext_right","steklo_black_ext_left","steklo_black_ext_right"})
            foreach(var p in Snapshot(Path.Combine(skins,name)))protectedFiles.Add(p.Key,p.Value);
        foreach(var p in Snapshot(Path.Combine(Path.GetDirectoryName(receiptPath)!,"backups")))protectedFiles.Add(p.Key,p.Value);
        protectedFiles.Add(config,Hash(config));
        var result=new Dictionary<string,object?>{{"Mode",mode},{"Status","PRECHECK_PASS"},{"CandidateDLL",Hash(assemblyPath)},{"PanelLanguage",code},{"ProtectedFiles",protectedFiles},{"R10ActualReadiness",true},{"FMStarted",false},{"GUIStarted",false},{"ClosedProcesses",false}};
        if(mode=="check"){File.WriteAllText(reportPath,JsonSerializer.Serialize(result,new JsonSerializerOptions{WriteIndented=true}));Console.WriteLine("PASS: precheck, actual R10 readiness, protected four-skin clone parity; game stopped.");return;}
        NoGame();
        var launchers=Process.GetProcessesByName("FmLauncher");
        try{Need(launchers.All(p=>p.HasExited),"STOP: launcher open; do not close/restart without root.");}finally{foreach(var p in launchers)p.Dispose();}
        var backup=Path.Combine(research,"live-backup-"+DateTime.UtcNow.ToString("yyyyMMddTHHmmssfff"));Directory.CreateDirectory(backup);
        var r11Before=Directory.EnumerateFiles(r11).ToDictionary(Path.GetFullPath,File.ReadAllBytes,StringComparer.OrdinalIgnoreCase);
        foreach(var p in r11Before)File.WriteAllBytes(Path.Combine(backup,Path.GetFileName(p.Key)),p.Value);
        File.Copy(receiptPath,Path.Combine(backup,"legacy-installation.json"));
        var written=new List<string>();
        try
        {
            foreach(var file in Directory.EnumerateFiles(candidate))
            {
                if(Path.GetFileName(file)=="FmLauncher.config.json")continue;
                NoGame();var target=Path.Combine(r11,Path.GetFileName(file));Atomic(target,File.ReadAllBytes(file));written.Add(target);Need(Hash(target)==Hash(file),"R11 publication readback failed.");
            }
            NoGame();
            result["ChangedSkinFiles"]=api.Call("SkinPanelInstaller","InstallExt",game,skins,fatigue,options,locale);
            api.Call("SkinPanelInstaller","ValidateProfileReadiness",skins,options);
            old.Call("SkinPanelInstaller","ValidateProfileReadiness",skins,oldOptions);
            foreach(var p in protectedFiles)Need(File.Exists(p.Key)&&Hash(p.Key)==p.Value,"Protected file changed: "+p.Key);
            var nocheRoot=Path.Combine(skins,"NocheExt");Need(Directory.EnumerateFiles(nocheRoot,"*",SearchOption.AllDirectories).Count()==6,"Unexpected child assets.");
            var receipts=new Dictionary<string,object>();
            foreach(var group in new[]{("player-panels",20),("player-panels-noche",6)})
            {
                var rp=Path.Combine(Root,"Dane",".fmext",group.Item1,"installation.json");var doc=JsonDocument.Parse(File.ReadAllBytes(rp)).RootElement;
                var files=doc.GetProperty("Files").EnumerateArray().ToArray();Need(files.Length==group.Item2,"Unexpected receipt size.");
                foreach(var f in files)
                {
                    var path=f.GetProperty("Path").GetString()!;Need(Hash(path).Equals(f.GetProperty("AfterHash").GetString(),StringComparison.OrdinalIgnoreCase),"Target readback differs.");
                    if(f.GetProperty("Backup").ValueKind!=JsonValueKind.Null)Need(Hash(f.GetProperty("Backup").GetString()!).Equals(f.GetProperty("BeforeHash").GetString(),StringComparison.OrdinalIgnoreCase),"Backup readback differs.");
                }
                receipts[rp]=new{Sha256=Hash(rp),Files=files.Length};
            }
            result["Receipts"]=receipts;result["Status"]="PASS_LIVE_INSTALL_READBACK";result["Backup"]=backup;result["VisualAcceptance"]="PENDING";
            result["NocheFiles"]=Snapshot(nocheRoot);result["R11Files"]=Snapshot(r11);
        }
        catch(Exception error)
        {
            result["Status"]="FAILED_INSTALL_OR_READBACK";result["Error"]=error.ToString();
            // Launcher publication rollback only; skin changes are owned by the checked installer transaction.
            foreach(var path in written.AsEnumerable().Reverse())
                if(r11Before.TryGetValue(path,out var bytes))Atomic(path,bytes);else File.Delete(path);
            throw;
        }
        finally{File.WriteAllText(reportPath,JsonSerializer.Serialize(result,new JsonSerializerOptions{WriteIndented=true}));}
        Console.WriteLine("PASS: R11 published with config preserved; six Noche XML installed; actual R10/R11 readiness and protected hashes verified. Visual PENDING.");
    }
}
