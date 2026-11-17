using System.Runtime.InteropServices;
using System.Security;
using System.Text;
using System.Xml.Linq;

namespace FmLauncher;

internal sealed class SkinGuidePage : TabPage
{
    private readonly Localizer localizer;
    private readonly Func<bool> isDarkMode;
    private readonly Func<string> gamePath,userDataPath;
    private readonly Func<PlayerProfilePanelOptions> profileOptions;
    private readonly Action<Action> execute;
    private readonly ThemedTabControl modes=new(){Name="SkinModes",Dock=DockStyle.Fill,SizeMode=TabSizeMode.Fixed,ItemSize=new Size(180,44),ProminentTabs=true};
    private readonly TabPage basic=new(){Name="SkinBasic",Padding=new Padding(10)};
    private readonly TabPage advanced=new(){Name="SkinAdvanced",Padding=new Padding(10)};
    private readonly Label heading=new(){Name="SkinBasicHeading",AutoSize=true,Dock=DockStyle.Top,Font=new Font("Segoe UI",12,FontStyle.Bold)};
    private readonly Label notice=new(){Name="SkinBasicNotice",AutoSize=true,Dock=DockStyle.Top};
    private readonly Label folder=new(){Name="SkinFolder",AutoSize=true,Dock=DockStyle.Top};
    private readonly Button detect=ActionButton("DetectSkins");
    private readonly Button install=ActionButton("InstallSkinPanels");
    private readonly DataGridView families=new()
    {
        Name="DetectedSkinFamilies",Dock=DockStyle.Top,Height=200,ReadOnly=true,AllowUserToAddRows=false,
        AllowUserToDeleteRows=false,AllowUserToResizeRows=false,RowHeadersVisible=false,
        AutoSizeColumnsMode=DataGridViewAutoSizeColumnsMode.Fill,AutoSizeRowsMode=DataGridViewAutoSizeRowsMode.AllCells,
        ColumnHeadersHeightSizeMode=DataGridViewColumnHeadersHeightSizeMode.AutoSize,
        SelectionMode=DataGridViewSelectionMode.FullRowSelect,MultiSelect=false
    };
    private readonly TextBox instructions=new(){Name="SkinInstructions",Multiline=true,ReadOnly=true,ScrollBars=ScrollBars.Vertical,Dock=DockStyle.Fill};
    private readonly ComboBox snippets=new ThemedComboBox{Name="SkinSnippetChoice",DropDownStyle=ComboBoxStyle.DropDownList,Width=390};
    private readonly TextBox xml=new(){Name="SkinSnippet",Multiline=true,ReadOnly=true,WordWrap=false,ScrollBars=ScrollBars.Both,Dock=DockStyle.Fill,Font=new Font("Consolas",9)};
    private readonly Label destination=new(){Name="SkinSnippetDestination",AutoSize=true,Dock=DockStyle.Top};
    private readonly Button copy=ActionButton("CopySkinSnippet");
    private readonly Label result=new(){Name="SkinInstallResult",AutoSize=true,Dock=DockStyle.Top};
    private readonly Label runtime=new(){Name="PanelRuntimeStatus",AutoSize=true,Dock=DockStyle.Bottom,Padding=new Padding(6)};
    private IReadOnlyList<ExtSkinDetection> detection=[];
    private PanelStatistics? statistics;
    private bool running,changingLanguage;

    internal SkinGuidePage(Localizer localizer,Func<string> gamePath,Func<string> userDataPath,Action<Action> execute,
        Func<bool>? isDarkMode=null,Func<PlayerProfilePanelOptions>? profileOptions=null)
    {
        this.localizer=localizer;this.gamePath=gamePath;this.userDataPath=userDataPath;this.execute=execute;
        this.isDarkMode=isDarkMode??(()=>false);this.profileOptions=profileOptions??(()=>new());
        Name="SkinGuide";Padding=new Padding(10);
        var basicScroll=new Panel{Dock=DockStyle.Fill,AutoScroll=true};var body=Stack();
        body.Controls.Add(heading);body.Controls.Add(notice);body.Controls.Add(folder);
        var actions=new FlowLayoutPanel{Dock=DockStyle.Top,AutoSize=true,Margin=new Padding(0,8,0,8)};
        actions.Controls.AddRange([install,detect]);body.Controls.Add(actions);
        families.Columns.Add(new DataGridViewTextBoxColumn{Name="Family",FillWeight=22,MinimumWidth=100});
        families.Columns.Add(new DataGridViewTextBoxColumn{Name="Detected",FillWeight=25,MinimumWidth=150});
        families.Columns.Add(new DataGridViewTextBoxColumn{Name="Variants",FillWeight=53,MinimumWidth=230});
        families.DefaultCellStyle.WrapMode=DataGridViewTriState.True;families.DefaultCellStyle.Padding=new Padding(6,8,6,8);
        families.RowHeightChanged+=(_,_)=>FitFamilyTable();families.ColumnHeadersHeightChanged+=(_,_)=>FitFamilyTable();
        body.Controls.Add(families);body.Controls.Add(result);basicScroll.Controls.Add(body);basic.Controls.Add(basicScroll);
        var layout=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=1,RowCount=4,Margin=Padding.Empty};
        layout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent,42));layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));layout.RowStyles.Add(new RowStyle(SizeType.Percent,58));
        layout.Controls.Add(instructions,0,0);
        snippets.Margin=new Padding(0,7,8,0);
        var snippetActions=new FlowLayoutPanel{Dock=DockStyle.Top,AutoSize=true,WrapContents=true};snippetActions.Controls.AddRange([snippets,copy]);
        layout.Controls.Add(snippetActions,0,1);layout.Controls.Add(destination,0,2);layout.Controls.Add(xml,0,3);advanced.Controls.Add(layout);
        modes.TabPages.AddRange([basic,advanced]);Controls.Add(modes);Controls.Add(runtime);
        for(int i=0;i<7;i++)snippets.Items.Add("");snippets.SelectedIndex=0;
        snippets.SelectedIndexChanged+=(_,_)=>{if(!changingLanguage)UpdateSnippet();};
        copy.Click+=(_,_)=>execute(()=>
        {
            try{Clipboard.SetText(xml.Text);}catch(ExternalException error){throw new LauncherException("SkinClipboardError",error.Message);}
            result.Text=localizer.Text("SkinCopied");
        });
        detect.Click+=(_,_)=>execute(()=>RefreshDetection(true));
        install.Click+=(_,_)=>execute(()=>
        {
            int count=CreateExt();result.Text=localizer.Text("SkinBasicInstalled",count,CurrentSkinDirectory);
        });
        Enter+=(_,_)=>RefreshDetection(false);
        modes.SelectedIndexChanged+=(_,_)=>{if(modes.SelectedTab==advanced)UpdateSnippet();};
        SizeChanged+=(_,_)=>UpdateWidths();basicScroll.SizeChanged+=(_,_)=>UpdateWidths();
        ApplyLanguage();
    }
    private static TableLayoutPanel Stack()=>new()
    {
        ColumnCount=1,AutoSize=true,AutoSizeMode=AutoSizeMode.GrowAndShrink,Dock=DockStyle.Top,
        ColumnStyles={new ColumnStyle(SizeType.Percent,100)}
    };
    private static Button ActionButton(string name)=>new()
    {
        Name=name,AutoSize=false,Size=new Size(250,40),
        Font=new Font("Segoe UI",10,FontStyle.Regular),Padding=new Padding(12,0,12,0),
        Margin=new Padding(0,0,8,0),TextAlign=ContentAlignment.MiddleCenter
    };
    internal string CurrentSkinDirectory=>InitialSkinDirectory(gamePath(),userDataPath());
    internal void ShowBasic()
    {
        modes.SelectedTab=basic;
        RefreshDetection(false);
        install.Focus();
    }
    internal int CreateExt()
    {
        var panels=GameLanguageResolver.CreatePanelLocalizer(localizer);
        int count=SkinPanelInstaller.InstallExt(gamePath(),CurrentSkinDirectory,panels.Text("PanelFatigueTitle"),profileOptions(),panels);
        RefreshDetection(true);return count;
    }
    internal void RefreshDetection(bool throwErrors=false)
    {
        folder.Text=localizer.Text("SkinBasicFolder",CurrentSkinDirectory);
        try{detection=ExtSkinCatalog.Detect(gamePath(),CurrentSkinDirectory);RenderDetection();result.Text="";}
        catch(Exception error)when(error is IOException or UnauthorizedAccessException or InvalidDataException or System.Xml.XmlException or ArgumentException)
        {
            detection=[];families.Rows.Clear();result.Text=localizer.Text("SkinBasicScanError",error.Message);
            if(throwErrors)throw new LauncherException("SkinInstallError",error.Message);
        }
        UpdateWidths();
    }
    private void RenderDetection()
    {
        families.Rows.Clear();
        foreach(var (prefix,key) in new[]{("fm2008_ext_","SkinFamilyBase"),("steklo_ext_","SkinFamilySteklo"),("steklo_black_ext_","SkinFamilyStekloBlack")})
        {
            var variants=detection.Where(v=>v.Skin.DirectoryName.StartsWith(prefix,StringComparison.Ordinal)).ToArray();
            int available=variants.Count(v=>v.SourceAvailable);
            string state=available==0?localizer.Text("SkinSourceMissing"):localizer.Text("SkinSourceDetected",available,variants.Length);
            var problems=variants.Where(v=>v.Problem is not null).Select(v=>v.Problem).Distinct().ToArray();
            if(problems.Length>0)state+="\n"+string.Join("\n",problems);
            string outputs=string.Join("\n",variants.Where(v=>v.SourceAvailable||v.ExtPresent).Select(v=>
                (v.Skin.DisplayName??v.Skin.DirectoryName)+" - "+localizer.Text(v.ExtPresent?"SkinVariantPresent":"SkinVariantCreate")));
            families.Rows.Add(localizer.Text(key),state,outputs.Length==0?localizer.Text("SkinSourceInstallFirst"):outputs);
        }
        families.AutoResizeRows(DataGridViewAutoSizeRowsMode.AllCells);FitFamilyTable();families.ClearSelection();families.CurrentCell=null;
    }
    private void FitFamilyTable()
    {
        int height=families.ColumnHeadersHeight+families.Rows.Cast<DataGridViewRow>().Sum(row=>row.Height)+4;
        if(families.Height!=height)families.Height=height;
    }
    internal static string InitialSkinDirectory(string gamePath,string userDataPath)
    {
        if(!string.IsNullOrWhiteSpace(userDataPath))return Path.Combine(userDataPath,"skins");
        var candidate=Path.Combine(Path.GetDirectoryName(gamePath)??"","Dane","skins");
        return Directory.Exists(candidate)?candidate:Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),"Sports Interactive","Football Manager 2008","skins");
    }
    internal void ApplyLanguage()
    {
        changingLanguage=true;
        try
        {
            Text=localizer.Text("SkinTab");basic.Text=localizer.Text("SkinBasicTab");advanced.Text=localizer.Text("SkinAdvancedTab");
            heading.Text=localizer.Text("SkinBasicHeading");notice.Text=localizer.Text("SkinBasicNotice");folder.Text=localizer.Text("SkinBasicFolder",CurrentSkinDirectory);
            install.Text=localizer.Text("SkinBasicCreate");detect.Text=localizer.Text("SkinBasicDetect");copy.Text=localizer.Text("SkinCopy");
            instructions.Text=WindowsLines(localizer.Text("SkinAdvancedInstructions"));
            families.Columns[0].HeaderText=localizer.Text("SkinFamilyColumn");families.Columns[1].HeaderText=localizer.Text("SkinDetectionColumn");families.Columns[2].HeaderText=localizer.Text("SkinVariantsColumn");
            int selected=Math.Max(0,snippets.SelectedIndex);for(int i=0;i<7;i++)snippets.Items[i]=localizer.Text("SkinAdvancedSnippet"+i);snippets.SelectedIndex=selected;
            if(detection.Count>0)RenderDetection();result.Text="";UpdateSnippet();UpdateRuntime(statistics,running);UpdateWidths();
        }
        finally{changingLanguage=false;}
    }
    private void UpdateWidths()
    {
        int width=Math.Max(200,ClientSize.Width-65);
        foreach(var label in new[]{heading,notice,folder,result,runtime,destination})label.MaximumSize=new Size(width,0);
    }
    private void UpdateSnippet()
    {
        try
        {
            var panels=GameLanguageResolver.CreatePanelLocalizer(localizer);
            string[] files=["player training.xml","team squad.xml","tactic person list.xml","person list table.xml","player profile.xml","match team stats short.xml","<skin_ext>/<skin_ext>.xml"];
            int i=Math.Max(0,snippets.SelectedIndex);destination.Text=localizer.Text("SkinSnippetDestination",i<6?"<skin_ext>/panels/"+files[i]:files[i]);
            xml.Text=i switch
            {
                0=>SkinPanelInstaller.TrainingFragment.Replace("Zm\u0119czenie sezonowe",SecurityElement.Escape(panels.Text("PanelFatigueTitle")),StringComparison.Ordinal),
                1=>SkinPanelInstaller.SquadFragment,2=>SkinPanelInstaller.TacticsFragment,
                3=>SkinPanelInstaller.ColumnRegistryFragment(panels.Text("PanelFatigueTitle")),
                4=>ProfileReference(panels),
                5=>"<record id=\"Frtt\" width=\"200\"><flags id=\"sort_disabled\" value=\"true\"/><flags id=\"box_style\" value=\"no_border\"/><record id=\"column_properties\"><flags id=\"alignment\" value=\"left,centre_y\"/><flags id=\"spec\" value=\"control,small\"/></record></record>",
                6=>"<properties version=\"1.0\">\n  <string id=\"name\" value=\"My Skin Ext\"/>\n  <string id=\"author\" value=\"Original author / FM08 Extended\"/>\n  <string id=\"version\" value=\"0.1.3\"/>\n  <string id=\"required_version\" value=\"8.0.2\"/>\n  <flags id=\"parent\" value=\"my_skin\"/>\n</properties>",_=>""
            };
            if(i==5)xml.Text=XElement.Parse(xml.Text).ToString();
            xml.Text=WindowsLines(xml.Text);
        }
        catch(Exception error)when(error is IOException or UnauthorizedAccessException or InvalidDataException or System.Xml.XmlException or ArgumentException)
        {xml.Text=localizer.Text("SkinBasicScanError",error.Message);}
    }
    private string ProfileReference(Localizer panels)
    {
        var resolver=new SkinResourceResolver(gamePath(),CurrentSkinDirectory);
        return XDocument.Parse(Encoding.UTF8.GetString(PlayerProfileXml.Transform(resolver.Get("fm2008","player profile.xml"),new(true,true),panels))).ToString();
    }
    private static string WindowsLines(string text)=>text.Replace("\r\n","\n",StringComparison.Ordinal).Replace("\n",Environment.NewLine,StringComparison.Ordinal);
    internal void UpdateRuntime(PanelStatistics? value,bool isRunning)
    {
        statistics=value;running=isRunning;install.Enabled=!running;
        runtime.Text=value is null?localizer.Text(running?"PanelNotActive":"PanelNotRunning"):localizer.Text("PanelStatistics",value.Reads,value.Hidden,value.Invalid,value.TrainingUpdates);
        runtime.ForeColor=value is{Invalid:>0}?LauncherTheme.Error(isDarkMode()):LauncherTheme.Text(isDarkMode());
    }
}
