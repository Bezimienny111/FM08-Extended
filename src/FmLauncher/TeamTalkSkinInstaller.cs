using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Xml.Linq;

namespace FmLauncher;

internal sealed record TeamTalkSkinFile(string Path,byte[] Original,byte[] Updated,string? BeforeHash);
internal static class TeamTalkSkinInstaller
{
    internal const string Panel="match team stats short.xml";
    private static string Hash(byte[] value)=>Convert.ToHexString(SHA256.HashData(value)).ToLowerInvariant();
    internal static byte[] Transform(byte[] original)
    {
        using var input=new MemoryStream(original);var xml=XDocument.Load(input,LoadOptions.PreserveWhitespace);
        var table=xml.Descendants("widget").Single(e=>(string?)e.Attribute("id")=="mtst");
        var columns=table.Elements("list").Single(e=>(string?)e.Attribute("id")=="column_display_properties");
        var name=columns.Elements("record").Single(e=>(string?)e.Attribute("id")=="match_stats_name");
        var existing=columns.Elements("record").Where(e=>(string?)e.Attribute("id")=="Frtt").ToArray();
        if(existing.Length>1)throw new InvalidDataException("Duplicate team-talk column.");
        if(existing.Length==0)
        {
            var extra=new XElement("record",new XAttribute("id","Frtt"),new XAttribute("width","200"),
                new XElement("flags",new XAttribute("id","sort_disabled"),new XAttribute("value","true")),
                new XElement("flags",new XAttribute("id","box_style"),new XAttribute("value","no_border")),
                new XElement("record",new XAttribute("id","column_properties"),
                    new XElement("flags",new XAttribute("id","alignment"),new XAttribute("value","left,centre_y")),
                    new XElement("flags",new XAttribute("id","spec"),new XAttribute("value","control,small"))));
            name.AddAfterSelf(new XText("\n"),extra);
        }
        using var output=new MemoryStream();
        using(var writer=System.Xml.XmlWriter.Create(output,new(){Encoding=new UTF8Encoding(false),Indent=false,
            OmitXmlDeclaration=xml.Declaration is null}))xml.Save(writer);
        return output.ToArray();
    }
    internal static IReadOnlyList<TeamTalkSkinFile> Plan(string gamePath,string skinsPath)
    {
        var resolver=new SkinResourceResolver(gamePath,skinsPath);var result=new List<TeamTalkSkinFile>();
        foreach(var skin in ExtSkinCatalog.All)
        {
            if(!Directory.Exists(System.IO.Path.Combine(skinsPath,skin.DirectoryName)))continue;
            var target=System.IO.Path.Combine(skinsPath,skin.DirectoryName,"panels",Panel);
            var original=resolver.Get(skin.DirectoryName,Panel);
            result.Add(new(target,original,Transform(original),File.Exists(target)?Hash(File.ReadAllBytes(target)):null));
        }
        if(result.Count==0)throw new InvalidDataException("No supported Ext skins found.");
        return result;
    }
    internal static void Validate(string gamePath,string skinsPath)
    {
        foreach(var file in Plan(gamePath,skinsPath))
        {
            if(!File.Exists(file.Path))throw new LauncherException("TeamTalkSkinNotReady");
            using var input=new MemoryStream(File.ReadAllBytes(file.Path));var xml=XDocument.Load(input);
            if(xml.Descendants("record").Count(e=>(string?)e.Attribute("id")=="Frtt")!=1)
                throw new LauncherException("TeamTalkSkinNotReady");
        }
    }
    internal static int Stage(string gamePath,string skinsPath,string destination)
    {
        var plan=Plan(gamePath,skinsPath);
        if(Directory.Exists(destination) || File.Exists(destination))throw new IOException("Stage must be a new directory.");
        Directory.CreateDirectory(destination);int i=0;
        foreach(var file in plan)
        {
            var path=System.IO.Path.Combine(destination,$"{i++:00}-"+Panel);
            using var output=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.Read);output.Write(file.Updated);
        }
        File.WriteAllText(System.IO.Path.Combine(destination,"PLAN.json"),JsonSerializer.Serialize(plan.Select(f=>new{
            f.Path,f.BeforeHash,OriginalHash=Hash(f.Original),AfterHash=Hash(f.Updated)}),new JsonSerializerOptions{WriteIndented=true}));
        return plan.Count;
    }
    internal static int Install(string gamePath,string skinsPath,string backupRoot)
    {
        using var mutex=new Mutex(false,@"Local\FmLauncher.GameStart");bool acquired;
        try{acquired=mutex.WaitOne(0);}catch(AbandonedMutexException){acquired=true;}
        if(!acquired)throw new LauncherException("AlreadyRunning");
        try
        {
            var games=Process.GetProcessesByName(System.IO.Path.GetFileNameWithoutExtension(gamePath));
            try{if(games.Any(p=>!p.HasExited))throw new LauncherException("AlreadyRunning");}
            finally{foreach(var p in games)p.Dispose();}
            using var verified=MatchRulePatch.OpenVerifiedGame(gamePath);
            var plan=Plan(gamePath,skinsPath);
            var backup=System.IO.Path.Combine(backupRoot,DateTime.UtcNow.ToString("yyyyMMddTHHmmssfffffffZ"));
            Directory.CreateDirectory(backup);
            for(int i=0;i<plan.Count;i++)
                File.WriteAllBytes(System.IO.Path.Combine(backup,$"{i:00}-before.xml"),plan[i].Original);
            var touched=new List<TeamTalkSkinFile>();
            try
            {
                foreach(var file in plan)
                {
                    string? before=File.Exists(file.Path)?Hash(File.ReadAllBytes(file.Path)):null;
                    if(before!=file.BeforeHash)throw new IOException("Skin changed after preparation: "+file.Path);
                    Directory.CreateDirectory(System.IO.Path.GetDirectoryName(file.Path)!);
                    touched.Add(file);File.WriteAllBytes(file.Path,file.Updated);
                    if(!File.ReadAllBytes(file.Path).SequenceEqual(file.Updated))throw new IOException("Skin readback failed.");
                }
            }
            catch
            {
                // No deletion, even on rollback. A newly-created override receives
                // its inherited baseline XML instead of restoring file absence.
                foreach(var file in touched)File.WriteAllBytes(file.Path,file.Original);
                throw;
            }
            File.WriteAllText(System.IO.Path.Combine(backup,"RECEIPT.json"),JsonSerializer.Serialize(new{
                Status="installed",Files=plan.Select(f=>new{f.Path,f.BeforeHash,AfterHash=Hash(f.Updated)}),
                NoDeletion=true,RollbackOfNewFile="preserves inherited baseline as an override"},new JsonSerializerOptions{WriteIndented=true}));
            return plan.Count;
        }
        finally{mutex.ReleaseMutex();}
    }
}
