using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using System.Windows.Forms;
using FmLauncher;

internal static class NavigationChecks
{
    [STAThread] public static int Main(string[] args)
    {
        Application.EnableVisualStyles();
        string release=args[0],root=args[1];Directory.CreateDirectory(root);
        foreach(var name in new[]{"FmLauncher.ini","FmLauncher.config.json","FmLauncher.languages.json"})
            File.Copy(Path.Combine(release,name),Path.Combine(root,name));
        int count=0;void Check(bool ok,string title){if(!ok)throw new Exception(title);Console.WriteLine("PASS "+title);count++;}
        string Fingerprint()=>string.Join("\n",Directory.EnumerateFiles(@"J:\FM08dev\Dane\skins","*.xml",SearchOption.AllDirectories)
            .OrderBy(p=>p).Select(p=>p+File.GetLastWriteTimeUtc(p).Ticks+Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(p)))));
        var before=Fingerprint();
        var loc=new Localizer(Path.Combine(root,"FmLauncher.languages.json"));
        using(var form=new MainForm(root,loc,_=>new[]{new Resolution(1920,1080)}))
        {
            form.ShowInTaskbar=false;form.Show();Application.DoEvents();
            T Find<T>(string n)where T:Control=>(T)form.Controls.Find(n,true).Single();
            var tabs=Find<TabControl>("FeatureTabs");var modes=Find<TabControl>("SkinModes");
            foreach(var item in new[]{("TeamTalkFeature","TeamTalkOpenSkins"),("PanelsFeature","PlayerPanelsOpenSkins")})
            {
                modes.SelectedIndex=1;tabs.SelectedTab=tabs.TabPages.Cast<TabPage>().Single(p=>p.Name=="Settings");
                var feature=form.Controls.Find(item.Item1,true).Single();
                typeof(MainForm).GetMethod("ShowFeatureDetails",BindingFlags.NonPublic|BindingFlags.Instance)!.Invoke(form,new object[]{feature});
                Application.DoEvents();var button=Find<Button>(item.Item2);
                Check(button.Visible,item.Item1+" navigation visible");button.PerformClick();Application.DoEvents();
                Check(tabs.SelectedTab!.Name=="SkinGuide" && modes.SelectedIndex==0,item.Item1+" opens Skins Basic without installing");
            }
            form.Close();
        }
        Check(before==Fingerprint(),"navigation preserved all real skin XML hashes and timestamps");
        void Reject(Action action,string key,string title)
        {
            try{action();throw new Exception("Expected rejection: "+title);}
            catch(LauncherException e){Check(e.Key==key,title+" ["+e.Key+"]");}
        }
        var missing=Path.Combine(root,"missing","skins");
        Reject(()=>SkinPanelInstaller.ValidatePanelLanguage(missing,loc),"SkinPanelsNotReady","missing panels rejected read-only");
        Check(!Directory.Exists(Path.GetDirectoryName(missing)),"readiness did not create missing directories");
        var cfg=LauncherConfiguration.CreateDefault(@"J:\FM08dev\fm.exe",new(1920,1080));
        cfg.DisplayOverride=false;cfg.MatchRulesEnabled=false;cfg.UserDataPath=Path.Combine(root,"absent-userdata");
        using(var game=new GameLauncher())
        {
            cfg.PanelInformationEnabled=false;cfg.TeamTalkReactionsEnabled=true;
            Reject(()=>game.Launch(cfg,loc),"SkinPanelsNotReady","team-talk missing panels stops before game creation");
            cfg.TeamTalkReactionsEnabled=false;cfg.PanelInformationEnabled=true;
            Reject(()=>game.Launch(cfg,loc),"SkinPanelsNotReady","information panels missing stops before game creation");
            cfg.PanelInformationEnabled=false;cfg.HiddenAttributesEnabled=true;
            Reject(()=>game.Launch(cfg,loc),"SkinProfileNotReady","hidden panels missing stops before game creation");
            Check(!game.IsRunning,"no game process created");
        }
        string sample=Path.Combine(root,"locale","skins"),receipt=Path.Combine(root,"locale",".fmext","player-panels","installation.json");
        Directory.CreateDirectory(sample);Directory.CreateDirectory(Path.GetDirectoryName(receipt)!);
        string panel=Path.Combine(sample,"fm2008_ext_left","panels","player training.xml");
        Directory.CreateDirectory(Path.GetDirectoryName(panel)!);File.WriteAllText(panel,"<panel />");
        var value=new SkinPanelReceipt(2,"installed",sample,false,false,
            new(){new(panel,null,null,Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(panel))))},PanelLanguage:"en");
        File.WriteAllText(receipt,JsonSerializer.Serialize(value));string receiptBefore=File.ReadAllText(receipt);
        loc.Select("en");SkinPanelInstaller.ValidatePanelLanguage(sample,loc);Check(true,"matching language accepted");
        loc.Select("pl");Reject(()=>SkinPanelInstaller.ValidatePanelLanguage(sample,loc),"SkinPanelsNotReady","language mismatch rejected instead of installing");
        Check(File.ReadAllText(receipt)==receiptBefore && File.ReadAllText(panel)=="<panel />","language check leaves receipt and panels unchanged");
        loc.Select("en");File.WriteAllText(panel,"<edited />");
        Reject(()=>SkinPanelInstaller.ValidatePanelLanguage(sample,loc),"SkinPanelsNotReady","manually changed panel rejected");
        loc.Select("pl");SkinPanelInstaller.ValidatePanelLanguage(@"J:\FM08dev\Dane\skins",loc);
        TeamTalkSkinInstaller.Validate(@"J:\FM08dev\fm.exe",@"J:\FM08dev\Dane\skins");
        Check(before==Fingerprint(),"existing installed panels accepted without writes");
        File.WriteAllText(Path.Combine(root,"RESULT.json"),JsonSerializer.Serialize(new{Status="PASS",Checks=count,GameStarted=false,SkinInstallationPerformed=false}));
        return 0;
    }
}
