using System.Security.Cryptography;
using System.Text;
using System.Xml;
using System.Xml.Linq;
using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    private static string? PanelXmlText(XElement element,string property) =>
        (string?)element.Elements("string").SingleOrDefault(e=>(string?)e.Attribute("id")==property+"_not_translated")?.Attribute("value")
        ?? (string?)element.Attribute(property)
        ?? (string?)element.Elements("string").SingleOrDefault(e=>(string?)e.Attribute("id")==property)?.Attribute("value");

    private static void TestGameLanguageResolver(string output)
    {
        Directory.CreateDirectory(output);
        var pref=Path.Combine(output,"current_language.xml");
        var ui=PanelLocalizer();ui.Select("en");
        void Save(string name,Encoding encoding)
        {
            using var writer=XmlWriter.Create(pref,new XmlWriterSettings{Encoding=encoding});
            new XDocument(new XElement("record",new XElement("string",new XAttribute("id","valu"),
                new XAttribute("value",name)))).Save(writer);
        }
        foreach(var (native,panel) in new[]{("polish","pl"),(" POLISH ","pl"),("english","en"),
            ("german","en"),("spanish","en"),("unknown-custom-language","en")})
        {
            Save(native,Encoding.Unicode);
            var before=SHA256.HashData(File.ReadAllBytes(pref));
            var selected=GameLanguageResolver.Resolve(pref);
            Assert(!selected.Fallback && selected.PanelLanguage==panel);
            var localizer=GameLanguageResolver.CreatePanelLocalizer(ui,pref);
            Assert(localizer.Code==panel && ui.Code=="en" && !ReferenceEquals(ui,localizer));
            var payload=GamePanelPatch.Build(0x10000000,0x11000000,new byte[0x70],localizer,new(true,true));
            Assert(payload.Data.AsSpan().IndexOf(Encoding.Unicode.GetBytes(localizer.Text("PanelFatigueTitle")+"\0"))>=0);
            foreach(var field in PlayerProfileFields.Hidden)
                Assert(payload.Data.AsSpan().IndexOf(Encoding.Unicode.GetBytes((panel=="pl"?field.Polish:field.English)+"\0"))>=0);
            Assert(SHA256.HashData(File.ReadAllBytes(pref)).SequenceEqual(before));
        }
        Save("polish",new UTF8Encoding(false));
        Assert(GameLanguageResolver.Resolve(pref).PanelLanguage=="pl");
        ui.Select("pl");Save("french",Encoding.Unicode);
        Assert(GameLanguageResolver.CreatePanelLocalizer(ui,pref).Code=="en" && ui.Code=="pl");
        foreach(var invalid in new[]{
            "<record><string id='valu' value='polish'/><string id='valu' value='english'/></record>",
            "<record><string id='valu' value=' '/></record>","<record>","<wrong/>",
            "<!DOCTYPE record [<!ENTITY ext SYSTEM 'file:///not-read'>]><record><string id='valu' value='&ext;'/></record>",
            new string(' ',65537)+"<record/>"})
        {
            File.WriteAllText(pref,invalid,Encoding.UTF8);
            var result=GameLanguageResolver.Resolve(pref);
            Assert(result.Fallback && result.PanelLanguage=="en");
        }
        var missing=Path.Combine(output,"does-not-exist.xml");
        Assert(GameLanguageResolver.Resolve(missing) is {Fallback:true,PanelLanguage:"en"});
        Assert(!File.Exists(missing));
        Assert(GameLanguageResolver.PreferencePath.EndsWith(Path.Combine("Sports Interactive","Football Manager 2008",
            "settings","Version 800","current_language.xml"),StringComparison.OrdinalIgnoreCase));
        Console.WriteLine("PASS: saved FM language UTF16/UTF8, Polish->PL/all others->EN, independent UI locale, runtime field/title strings, missing/ambiguous/malformed/DTD/oversized fallback; preferences read-only.");
    }
}
