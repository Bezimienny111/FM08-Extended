namespace FmLauncher;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        ApplicationConfiguration.Initialize();
        var localizer = new Localizer(Path.Combine(AppContext.BaseDirectory, "FmLauncher.languages.json"));
        Application.ThreadException += (_, args) =>
            MessageBox.Show(localizer.Text("UnexpectedError", args.Exception.Message),
                localizer.Text("ErrorTitle"), MessageBoxButtons.OK, MessageBoxIcon.Error);
        Application.Run(new MainForm(AppContext.BaseDirectory, localizer, DisplayService.Detect));
    }
}
