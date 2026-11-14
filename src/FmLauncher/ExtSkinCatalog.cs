using System.Text;
using System.Xml.Linq;

namespace FmLauncher;

internal sealed record ExtSkinDefinition(string DirectoryName, string? Parent = null,
    bool CreateWhenParentPresent = false)
{
    internal byte[] Descriptor()
    {
        if (!CreateWhenParentPresent || Parent is null)
            throw new InvalidOperationException("Only catalogued child variants can create metadata.");
        var xml = new XDocument(new XElement("properties", new XAttribute("version", "1.0"),
            new XElement("string", new XAttribute("id", "name"), new XAttribute("value", DirectoryName)),
            new XElement("string", new XAttribute("id", "author"), new XAttribute("value", "Emircan Uysaler / FM08 Extended")),
            new XElement("string", new XAttribute("id", "description"), new XAttribute("value", "Noche with FM08 Extended player panels.")),
            new XElement("string", new XAttribute("id", "version"), new XAttribute("value", "0.1.3")),
            new XElement("string", new XAttribute("id", "required_version"), new XAttribute("value", "8.0.2")),
            new XElement("flags", new XAttribute("id", "parent"), new XAttribute("value", Parent))));
        return new UTF8Encoding(false).GetBytes(xml.ToString());
    }
}

// One catalogue drives installation scope, optional variant creation and UI notices.
// Noche assets stay in the original parent. No implicit arbitrary *_ext discovery.
internal static class ExtSkinCatalog
{
    internal static IReadOnlyList<ExtSkinDefinition> All { get; } =
    [
        new("fm2008_ext_left"), new("fm2008_ext_right"),
        new("steklo_black_ext_left"), new("steklo_black_ext_right"),
        new("NocheExt", "noche", CreateWhenParentPresent: true)
    ];
}
