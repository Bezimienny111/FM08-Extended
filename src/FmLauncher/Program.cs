namespace FmLauncher;

internal static class Program
{
    [STAThread]
    private static void Main(string[] args)
    {
        if(args.Length>0)
        {
            if(args.Length!=4 || args[0]!="--teamtalk-skins-stage")
                throw new ArgumentException("Skin installation is available only in Skins > Basic.");
            int count=TeamTalkSkinInstaller.Stage(args[1],args[2],args[3]);
            Console.WriteLine("TEAMTALK_PANELS "+count);return;
        }
        ApplicationConfiguration.Initialize();
        var localizer = new Localizer(Path.Combine(AppContext.BaseDirectory, "FmLauncher.languages.json"));
        Application.ThreadException += (_, args) =>
            MessageBox.Show(localizer.Text("UnexpectedError", args.Exception.Message),
                localizer.Text("ErrorTitle"), MessageBoxButtons.OK, MessageBoxIcon.Error);
        Application.Run(new MainForm(AppContext.BaseDirectory, localizer, DisplayService.Detect));
    }
}
