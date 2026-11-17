using System;
using System.IO;
using System.Reflection;
using System.Windows.Forms;
using FmLauncher;
internal static class StartChecks
{
    [STAThread] public static int Main(string[] args)
    {
        Application.EnableVisualStyles();string root=args[0];Directory.CreateDirectory(root);
        foreach(var name in new[]{"FmLauncher.ini","FmLauncher.config.json","FmLauncher.languages.json"})
            File.Copy(Path.Combine(AppContext.BaseDirectory,name),Path.Combine(root,name));
        using var form=new MainForm(root,new Localizer(Path.Combine(root,"FmLauncher.languages.json")),_=>new[]{new Resolution(1920,1080)});
        form.LoadConfiguration();
        int starts=0;
        form.LaunchGame(config=>
        {
            if(!File.Exists(Path.Combine(root,"FmLauncher.ini")))throw new Exception("Settings not saved");
            var saved=new ConfigurationStore(Path.Combine(root,"FmLauncher.config.json")).Load();
            if(saved?.GamePath!=config.GamePath)throw new Exception("Saved settings differ");
            starts++;
        });
        if(starts!=1)throw new Exception("Expected one direct launch");
        Console.WriteLine("PASS direct launch invokes start exactly once, without confirmation; settings saved");
        try{form.LaunchGame(_=>throw new LauncherException("AlreadyRunning"));throw new Exception("Launch failure ignored");}
        catch(LauncherException e)when(e.Key=="AlreadyRunning"){Console.WriteLine("PASS actual launch errors still propagate to UI error handling");}
        typeof(MainForm).GetField("configurationBlocked",BindingFlags.Instance|BindingFlags.NonPublic)!.SetValue(form,true);
        try{form.LaunchGame(_=>starts++);throw new Exception("Blocked config launched");}
        catch(LauncherException e)when(e.Key=="ConfigBlocked"){Console.WriteLine("PASS blocked configuration prevents launch");}
        if(starts!=1)throw new Exception("Unexpected extra launch");
        File.WriteAllText(Path.Combine(root,"RESULT.json"),"{\"Status\":\"PASS\",\"Checks\":3,\"GameStarted\":false}");return 0;
    }
}
