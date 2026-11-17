using System.Text;
using System.Xml.Linq;

namespace FmLauncher;

internal sealed record ExtSkinDefinition(string DirectoryName, string? Parent = null,
    bool CreateWhenParentPresent = false,string? DisplayName=null,bool? LeftMenu=null)
{
    internal byte[] Descriptor(byte[]? parentMetadata=null)
    {
        if (!CreateWhenParentPresent || Parent is null)
            throw new InvalidOperationException("Only catalogued child variants can create metadata.");
        XElement properties;
        if(parentMetadata is null)properties=new("properties",new XAttribute("version","1.0"));
        else
        {
            using var stream=new MemoryStream(parentMetadata);var parent=XDocument.Load(stream);
            if(parent.Root?.Name!="properties")throw new InvalidDataException("Invalid parent skin descriptor.");
            properties=new(parent.Root); // Preserve font/style settings; artwork remains inherited.
        }
        void Set(string tag,string id,string value)
        {
            var found=properties.Elements().Where(x=>(string?)x.Attribute("id")==id).ToArray();
            if(found.Length>1)throw new InvalidDataException("Duplicate skin metadata: "+id);
            if(found.Length==1){found[0].Name=tag;found[0].SetAttributeValue("value",value);}
            else properties.Add(new XElement(tag,new XAttribute("id",id),new XAttribute("value",value)));
        }
        string author=properties.Elements().SingleOrDefault(x=>(string?)x.Attribute("id")=="author")?.Attribute("value")?.Value??"";
        Set("string","name",DisplayName??DirectoryName);
        Set("string","author",author.Length==0?"FM08 Extended":author+" / FM08 Extended");
        Set("string","description","FM08 Extended panels; original skin resources inherited.");
        Set("string","version","0.1.3");Set("string","required_version","8.0.2");Set("flags","parent",Parent);
        var xml=new XDocument(properties);
        return new UTF8Encoding(false).GetBytes(xml.ToString());
    }
}

// One catalogue drives installation scope, optional variant creation and UI notices.
// R20 adds plain Steklo to base and Steklo Black. Noche/NocheExt stay excluded.
// No implicit arbitrary *_ext discovery or Noche child creation.
internal static class ExtSkinCatalog
{
    internal static IReadOnlyList<ExtSkinDefinition> All { get; } =
    [
        new("fm2008_ext_left","fm2008",true,"Base Ext (Left)",true),
        new("fm2008_ext_right","fm2008",true,"Base Ext (Right)",false),
        new("steklo_ext_left","steklo_left",true,"Steklo Ext (Left)"),
        new("steklo_ext_right","steklo",true,"Steklo Ext (Right)"),
        new("steklo_black_ext_left","steklo_left_black",true,"Steklo Black Ext (Left)"),
        new("steklo_black_ext_right","steklo_black",true,"Steklo Black Ext (Right)")
    ];

    internal static IReadOnlyList<ExtSkinDetection> Detect(string gamePath,string skinsPath)
    {
        var resolver=new SkinResourceResolver(gamePath,skinsPath);var result=new List<ExtSkinDetection>();
        foreach(var skin in All)
        {
            bool existing=File.Exists(Path.Combine(skinsPath,skin.DirectoryName,skin.DirectoryName+".xml"));
            bool source=resolver.HasMetadata(skin.Parent!);string? problem=null;
            try
            {
                if(source)resolver.Chain(skin.Parent!);
                if(existing)
                {
                    var chain=resolver.Chain(skin.DirectoryName);
                    if(chain.Count<2 || !chain[1].Equals(skin.Parent,StringComparison.OrdinalIgnoreCase))
                        throw new InvalidDataException("Unexpected Ext parent: "+skin.DirectoryName);
                }
            }
            catch(Exception error)when(error is IOException or InvalidDataException or System.Xml.XmlException or UnauthorizedAccessException)
            {problem=error.Message;source=false;}
            result.Add(new(skin,source,existing,problem));
        }
        return result;
    }
}

internal sealed record ExtSkinDetection(ExtSkinDefinition Skin,bool SourceAvailable,bool ExtPresent,string? Problem);
