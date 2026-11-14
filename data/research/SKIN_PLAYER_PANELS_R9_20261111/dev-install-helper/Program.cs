using System.Diagnostics;
using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Xml.Linq;

string root=@"J:\FM08dev", app=Path.Combine(root,"Launcher_0.1.3_R9");
string exe=Path.Combine(app,"FmLauncher.exe"), game=Path.Combine(root,"fm.exe");
string user=Path.Combine(root,"Dane"), skins=Path.Combine(user,"skins");
string batch=Path.Combine(root,"FmLauncher","data","research","SKIN_PLAYER_PANELS_R9_20261111","dev-install-20261111");
Directory.CreateDirectory(batch);
void Check(bool ok,string text){if(!ok)throw new InvalidOperationException(text);}
string Hash(string p)=>Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(p))).ToLowerInvariant();
Check(args.SequenceEqual(new[]{"--apply"}),"Explicit --apply required.");
string output=Path.Combine(batch,"installation-report.json");
Check(!File.Exists(output),"Installation report already exists; do not replay.");
var manifest=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"FmLauncher","data","research","SKIN_PLAYER_PANELS_R9_20261111","manifest.json")))!;
var assets=manifest["candidate_files"]!.AsObject().ToDictionary(x=>x.Key,x=>x.Value!["sha256"]!.GetValue<string>());
Check(assets.All(x=>Hash(Path.Combine(app,x.Key))==x.Value),"Frozen R9 assets differ.");
Check(!Process.GetProcessesByName("fm").Any(p=>!p.HasExited),"FM08 is running; game was not closed.");
var status=new JsonObject{["status"]="running",["game_started"]=false,["game_modified"]=false};
bool closed=false, ready=false;
try
{
    string oldApp=Path.Combine(root,"Launcher_0.1.3_R8");
    string oldExe=Path.Combine(oldApp,"FmLauncher.exe");
    var launchers=Process.GetProcessesByName("FmLauncher").Where(p=>
        string.Equals(p.MainModule!.FileName,exe,StringComparison.OrdinalIgnoreCase)
        ||string.Equals(p.MainModule!.FileName,oldExe,StringComparison.OrdinalIgnoreCase)).ToArray();
    Check(launchers.GroupBy(p=>p.MainModule!.FileName,StringComparer.OrdinalIgnoreCase).All(g=>g.Count()==1),
        "Multiple dev instances; no forced close.");
    var closing=new JsonArray();
    foreach(var launcher in launchers)
    {
        using(launcher)
        {
            closing.Add(new JsonObject{["pid"]=launcher.Id,["path"]=launcher.MainModule!.FileName});
            Check(launcher.CloseMainWindow(),"Graceful close refused; no forced kill.");
            Check(launcher.WaitForExit(10000),"Launcher close timed out; no forced kill.");
        }
    }
    closed=true;status["closed_dev_launchers"]=closing;
    var file=Path.Combine(app,"FmLauncher.config.json");
    if(!File.Exists(file))
    {
        var previous=Path.Combine(oldApp,"FmLauncher.config.json");
        Check(File.Exists(previous),"No saved dev config to preserve.");
        File.Copy(previous,file,false);
        status["config_seeded_from_fresh_saved_R8"]=true;
    }
    var before=File.ReadAllBytes(file);File.WriteAllBytes(Path.Combine(batch,"config-before.json"),before);
    var beforeJson=JsonNode.Parse(before)!;
    var assembly=Assembly.LoadFrom(Path.Combine(app,"FmLauncher.dll"));
    var flags=BindingFlags.Public|BindingFlags.NonPublic;
    var st=assembly.GetType("FmLauncher.ConfigurationStore",true)!;
    var store=Activator.CreateInstance(st,[file])!;
    var config=st.GetMethod("Load")!.Invoke(store,null)!;var ct=config.GetType();
    ct.GetProperty("Language")!.SetValue(config,"en");ct.GetProperty("UserDataPath")!.SetValue(config,user);
    ct.GetProperty("PositionHighlightsEnabled")!.SetValue(config,true);ct.GetProperty("HiddenAttributesEnabled")!.SetValue(config,true);
    st.GetMethod("Save")!.Invoke(store,[config]);st.GetMethod("Load")!.Invoke(store,null);
    var afterJson=JsonNode.Parse(File.ReadAllBytes(file))!;
    var left=beforeJson.DeepClone();var right=afterJson.DeepClone();
    foreach(var key in new[]{"Language","UserDataPath","PositionHighlightsEnabled","HiddenAttributesEnabled"})
    {left.AsObject().Remove(key);right.AsObject().Remove(key);}
    Check(JsonNode.DeepEquals(left,right),"Unrelated config changed.");
    Check(afterJson["Language"]!.GetValue<string>()=="en"&&afterJson["UserDataPath"]!.GetValue<string>()==user
        &&afterJson["PositionHighlightsEnabled"]!.GetValue<bool>()&&afterJson["HiddenAttributesEnabled"]!.GetValue<bool>(),"Config readback failed.");
    File.WriteAllBytes(Path.Combine(batch,"config-after.json"),File.ReadAllBytes(file));
    string[] ext=["fm2008_ext_left","fm2008_ext_right","steklo_black_ext_left","steklo_black_ext_right"];
    bool Target(string p)=>ext.Any(n=>Path.GetFullPath(p).StartsWith(Path.Combine(skins,n)+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase));
    var parents=Directory.EnumerateFiles(skins,"*.xml",SearchOption.AllDirectories).Where(p=>!Target(p)).ToDictionary(p=>p,Hash);
    File.WriteAllText(Path.Combine(batch,"parent-pins-before.json"),JsonSerializer.Serialize(parents,new JsonSerializerOptions{WriteIndented=true}));
    var lt=assembly.GetType("FmLauncher.Localizer",true)!;
    var localizer=Activator.CreateInstance(lt,flags|BindingFlags.Instance,null,[Path.Combine(app,"FmLauncher.languages.json")],null)!;
    lt.GetMethod("Select",flags|BindingFlags.Instance)!.Invoke(localizer,["en"]);
    var ot=assembly.GetType("FmLauncher.PlayerProfilePanelOptions",true)!;
    var options=Activator.CreateInstance(ot,flags|BindingFlags.Instance,null,[true,true,"DC"],null)!;
    var installer=assembly.GetType("FmLauncher.SkinPanelInstaller",true)!;
    var install=installer.GetMethods(flags|BindingFlags.Static).Single(m=>m.Name=="InstallExt"&&m.GetParameters().Length==5);
    var fatigueTitle=(string)lt.GetMethod("Text",flags|BindingFlags.Instance)!.Invoke(localizer,["PanelFatigueTitle",Array.Empty<object>()])!;
    int changed=(int)install.Invoke(null,[game,skins,fatigueTitle,options,localizer])!;
    installer.GetMethod("ValidateProfileReadiness",flags|BindingFlags.Static)!.Invoke(null,[skins,options]);
    var receiptPath=Path.Combine(user,".fmext","player-panels","installation.json");
    var receipt=JsonNode.Parse(File.ReadAllBytes(receiptPath))!;
    Check(receipt["Status"]!.GetValue<string>()=="installed"&&receipt["PositionHighlights"]!.GetValue<bool>()
        &&receipt["HiddenAttributes"]!.GetValue<bool>(),"Receipt options/status invalid.");
    foreach(var row in receipt["Files"]!.AsArray())
    {
        var p=row!["Path"]!.GetValue<string>();Check(Target(p),"NonExt target in receipt.");
        Check(Hash(p)==row["AfterHash"]!.GetValue<string>().ToLowerInvariant(),"Installed hash mismatch.");
        if(row["Backup"]is JsonNode backup)
            Check(Hash(backup.GetValue<string>())==row["BeforeHash"]!.GetValue<string>().ToLowerInvariant(),"Backup mismatch.");
    }
    string[] ids=["FhAd","FhAm","FhLo","FhPr","FhPf","FhSp","FhTe","FhCo","FhIm","FhIn","FhDi","FhCt"];
    var profiles=new JsonArray();
    foreach(var name in ext)
    {
        var p=Path.Combine(skins,name,"panels","player profile.xml");var xml=XDocument.Load(p);
        Check(xml.Descendants("widget").Count(x=>(string?)x.Attribute("id")=="Fpos"&&(string?)x.Attribute("selection")=="Fpn0")==1,"Unique Fpos missing.");
        Check(xml.Descendants("container").Count(x=>(string?)x.Attribute("id")=="Fhid")==1,"Unique Fhid missing.");
        foreach(var id in ids)Check(xml.Descendants("widget").Count(x=>(string?)x.Attribute("id")==id)==1,"Hidden field missing:"+id);
        foreach(var id in new[]{"Fhp1","Fhp2","Fhp3"})
            Check(xml.Descendants("widget").Count(x=>(string?)x.Attribute("id")==id&&(string?)x.Attribute("class")=="table")==1,"Missing split table:"+id);
        Check(!xml.Descendants().Any(x=>(string?)x.Attribute("id")=="FhSt"),"Obsolete own-club message remains.");
        foreach(var id in new[]{"Fhp1","Fhp2","Fhp3"})
            Check(xml.Descendants("widget").Single(x=>(string?)x.Attribute("id")==id).Descendants("widget")
                .Count(x=>ids.Contains((string?)x.Attribute("id")))==4,"Hidden table must have4fields:"+id);
        var popup=xml.Descendants("widget").Single(x=>(string?)x.Attribute("id")=="Fpos");
        Check((string?)popup.Attribute("fixed")=="false" && (string?)popup.Attribute("auto_tick_exclusive")=="true",
            "Native caption/exclusive checkmark properties missing.");
        var legend=xml.Descendants("container").Single(x=>(string?)x.Attribute("id")=="Flgb");
        Check(legend.Ancestors("container").Any(x=>(string?)x.Attribute("id")=="Fpsi")
            && !legend.Ancestors("container").Any(x=>(string?)x.Attribute("id")=="attr"),"Legend must be under portrait.");
        Check(legend.Attribute("class") is null && (string?)legend.Attribute("height")=="88","Legend must be plain with height88.");
        Check(legend.Elements("layout").Any(x=>(string?)x.Attribute("inset")=="0"),"Legend must have zero outer inset.");
        var legendTable=legend.Descendants("widget").Single(x=>(string?)x.Attribute("id")=="Fltb");
        Check((string?)legendTable.Attribute("class")=="table" && legendTable.Descendants("widget")
            .Count(x=>new[]{"Fleg","Flg2","Flg3"}.Contains((string?)x.Attribute("id")))==3,"Legend must have3 native rows.");
        Check((string?)xml.Descendants("container").Single(x=>(string?)x.Attribute("id")=="Faur")
            .Attribute("height")=="304","Native skills height must keep hidden rows adjacent.");
        Check(xml.Descendants("container").Single(x=>(string?)x.Attribute("id")=="attr").Elements("layout")
            .Any(x=>(string?)x.Attribute("class")=="arrange_vertical_attachment" && (string?)x.Attribute("alignment")=="top"),
            "Attribute section must align at top.");
        Check((string?)xml.Descendants("container").Single(x=>(string?)x.Attribute("id")=="Fhid").Attribute("height")=="112",
            "Compact hidden block height missing.");
        foreach(var kind in new[]{"technical","mental","physical"})
            Check(xml.Descendants("container").Count(x=>(string?)x.Attribute("file")=="player profile "+kind+" attributes")==1,"Duplicate native container.");
        var model=assembly.GetType("FmLauncher.PositionHighlightModel",true)!;
        var roleList=(System.Collections.IEnumerable)model.GetProperty("Roles",flags|BindingFlags.Static)!.GetValue(null)!;
        int roleCount=0;
        foreach(var role in roleList)
        {
            var expectedName=(string)role!.GetType().GetMethod("Name",flags|BindingFlags.Instance)!.Invoke(role,["en"])!;
            var id="Fp"+(++roleCount).ToString("00");
            Check((string?)popup.Descendants("record").Single(x=>(string?)x.Attribute("id")==id).Attribute("name")==expectedName,
                "English role name missing:"+id);
        }
        Check(roleCount==11,"Expected11 English roles.");
        var fieldType=assembly.GetType("FmLauncher.PlayerProfileFields",true)!;
        foreach(var field in (System.Collections.IEnumerable)fieldType.GetProperty("Hidden",flags|BindingFlags.Static)!.GetValue(null)!)
        {
            var expected=(string)field!.GetType().GetProperty("English")!.GetValue(field)!;
            Check(xml.Descendants("container").Single(x=>(string?)x.Attribute("id")=="Fhid").Descendants("widget")
                .Count(x=>(string?)x.Attribute("col")=="0" && (string?)x.Attribute("text")==expected)==1,"English hidden label missing:"+expected);
        }
        var expectedTitle=(string)lt.GetMethod("Text",flags|BindingFlags.Instance)!.Invoke(localizer,["ProfilePanelLegendTitle",Array.Empty<object>()])!;
        Check(legendTable.Descendants("record").Any(x=>(string?)x.Attribute("text")==expectedTitle),"English legend title missing.");
        var expectedLegend=(string)lt.GetMethod("Text",flags|BindingFlags.Instance)!.Invoke(localizer,["ProfilePanelLegend",Array.Empty<object>()])!;
        var lines=expectedLegend.Split(". ",StringSplitOptions.RemoveEmptyEntries).Select(x=>x.EndsWith('.')?x:x+".").ToArray();
        var actualLines=legendTable.Elements("widget").Select(x=>(string?)x.Attribute("text")).ToArray();
        Check(actualLines.SequenceEqual(lines),"English legend lines differ.");
        profiles.Add(new JsonObject{["skin"]=name,["path"]=p,["sha256"]=Hash(p),["hidden_fields"]=12,["unique_Fpos"]=true,
            ["language"]="en",["english_role_names"]=11,["english_hidden_labels"]=12,["english_legend_verified"]=true});
    }
    Check(parents.All(x=>Hash(x.Key)==x.Value),"Parent XML modified.");
    Check(assets.All(x=>Hash(Path.Combine(app,x.Key))==x.Value),"Frozen assets modified.");
    File.WriteAllBytes(Path.Combine(batch,"installation-receipt-copy.json"),File.ReadAllBytes(receiptPath));
    ready=true;status["status"]="PASS";status["changed_files"]=changed;status["receipt"]=receiptPath;status["profiles"]=profiles;
    status["parent_xml_unchanged"]=true;status["parent_xml_count"]=parents.Count;status["transaction_backups_verified"]=true;
    status["frozen_assets_unchanged"]=true;status["unrelated_config_preserved"]=true;
    status["config_before_sha256"]=Hash(Path.Combine(batch,"config-before.json"));status["config_after_sha256"]=Hash(file);
    status["UserDataPath"]=user;status["language"]="en";status["both_options"]=true;
}
catch(Exception e)
{
    var actual=e is TargetInvocationException t&&t.InnerException is not null?t.InnerException:e;
    status["status"]="FAILED";status["error"]=actual.ToString();throw;
}
finally
{
    status["launcher_ready_for_reopen"]=closed;
    if(closed&&ready&&!Process.GetProcessesByName("fm").Any(p=>!p.HasExited))
    {
        var opened=Process.Start(new ProcessStartInfo(exe){UseShellExecute=true,WorkingDirectory=app});
        status["launcher_reopened_interactive"]=opened is not null;status["launcher_pid"]=opened?.Id;
    }
    status["completed_utc"]=DateTimeOffset.UtcNow.ToString("O");
    File.WriteAllText(output,status.ToJsonString(new JsonSerializerOptions{WriteIndented=true}));
    Console.WriteLine(status.ToJsonString(new JsonSerializerOptions{WriteIndented=true}));
}
