using System.Text;
using System.Xml;
using System.Xml.Linq;

namespace FmLauncher;

internal sealed record ProfileHiddenField(uint Property, string Id, string Polish, string English, int PersonSlot = 0, int PlayerSelector = -1);

internal static class PlayerProfileFields
{
    // Each slot is a verified PERSON virtual getter; no fixed ACTUAL_PLAYER/PERSON offset.
    // R5 + raw PE evidence: SKIN_PLAYER_PANELS_IMPLEMENTATION_20261111/root-native-evidence/evidence.json.
    internal static IReadOnlyList<ProfileHiddenField> Hidden { get; } =
    [
        new(0x46684164, "FhAd", "Adaptacja", "Adaptability", 0x218),
        new(0x4668416D, "FhAm", "Ambicja", "Ambition", 0x21C),
        new(0x46684C6F, "FhLo", "Lojalność", "Loyalty", 0x224),
        new(0x46685072, "FhPr", "Presja", "Pressure", 0x228),
        new(0x46685066, "FhPf", "Profesjonalizm", "Professionalism", 0x22C),
        new(0x46685370, "FhSp", "Sportowa postawa", "Sportsmanship", 0x230),
        new(0x46685465, "FhTe", "Temperament", "Temperament", 0x234),
        new(0x4668436F, "FhCo", "Regularność", "Consistency", PlayerSelector: 0x46),
        new(0x4668496D, "FhIm", "Ważne mecze", "Important matches", PlayerSelector: 0x49),
        new(0x4668496E, "FhIn", "Podatność na kontuzje", "Injury proneness", PlayerSelector: 0x4A),
        new(0x46684469, "FhDi", "Nieczysta gra", "Dirtiness", PlayerSelector: 0x43),
        // Original802 / controlled SI8-vector / live UID8074 proof: PERSON238 -> C81A90.
        new(0x46684374, "FhCt", "Kontrowersyjność", "Controversy", 0x238)
    ];
}

internal static class PlayerProfileXml
{
    internal const string RoleWidgetId = "Fpos";
    internal const string NoRoleId = "Fpn0";
    internal static string RoleItemId(int index) => "Fp" + (index + 1).ToString("00",
        System.Globalization.CultureInfo.InvariantCulture);

    internal static byte[] Transform(byte[] source, PlayerProfilePanelOptions options, Localizer localizer)
    {
        options.Validate();
        if (!options.PositionHighlightsEnabled && !options.HiddenAttributesEnabled) return source;
        using var input = new MemoryStream(source);
        var xml = XDocument.Load(input, LoadOptions.PreserveWhitespace);
        XElement One(string tag, string id) => xml.Descendants(tag).SingleOrDefault(
            value => (string?)value.Attribute("id") == id)
            ?? throw new InvalidDataException("Missing unique profile element " + id + ".");
        var attributes = One("container", "attr");
        var buttons = One("container", "btna");
        var menu = One("widget", "attv");
        if ((string?)menu.Attribute("class") != "embedded_popup_button"
            || (string?)attributes.Attribute("class") != "group_box")
            throw new InvalidDataException("Unsupported player profile layout.");
        if (xml.Descendants().Any(value => ((string?)value.Attribute("id")) is "Fpos" or "Fhid" or "Faur"))
            throw new InvalidDataException("Profile already contains an unmanaged FMExt block; use its installation manifest.");
        var technical = xml.Descendants("container").SingleOrDefault(
            value => (string?)value.Attribute("file") == "player profile technical attributes");
        var mental = xml.Descendants("container").SingleOrDefault(
            value => (string?)value.Attribute("file") == "player profile mental attributes");
        var physical = xml.Descendants("container").SingleOrDefault(
            value => (string?)value.Attribute("file") == "player profile physical attributes");
        if (technical is null || mental is null || physical is null
            || !attributes.Descendants().Contains(technical) || !attributes.Descendants().Contains(mental)
            || !attributes.Descendants().Contains(physical))
            throw new InvalidDataException("Missing native attribute containers; no replacement tables will be created.");
        // The original three child containers and their unique native tables remain single instances.
        var originalContents = attributes.Nodes().ToArray();
        foreach (var item in originalContents) item.Remove();
        var native = new XElement("container", new XAttribute("id", "Faur"));
        // The longest native table is fourteen20px rows plus its header. Keep the
        // hidden row immediately below it instead of stretching the upper area.
        if (options.HiddenAttributesEnabled) native.SetAttributeValue("height", "304");
        native.Add(originalContents);
        attributes.Add(new XElement("layout", new XAttribute("class", "arrange_vertical_attachment"),
            new XAttribute("alignment", options.HiddenAttributesEnabled ? "top" : "bottom, extend"),
            new XAttribute("gap", "3")),
            new XElement("layout", new XAttribute("class", "stick_to_sides_attachment"),
                new XAttribute("alignment", "horizontal"), new XAttribute("layout_children", "true"),
                new XAttribute("inset", "0")), native);
        if (options.PositionHighlightsEnabled)
        {
            var popup = new XElement("widget", new XAttribute("class", "embedded_popup_button"),
                new XAttribute("id", RoleWidgetId), new XAttribute("text", localizer.Text("ProfilePanelPosition")),
                new XAttribute("selection", NoRoleId), new XAttribute("auto_size", "horizontal"),
                new XAttribute("fixed", "false"), new XAttribute("auto_tick_exclusive", "true"),
                new XAttribute("embed_in_frame", "true"), new XAttribute("appearance", "menu/embedded/view"),
                new XAttribute("save_current_state", "true"), new XAttribute("save_default_state", "true"));
            var items = new XElement("list", new XAttribute("id", "items"),
                new XElement("record", new XAttribute("id", NoRoleId),
                    new XAttribute("name", localizer.Text("ProfilePanelNone"))));
            for (var index = 0; index < PositionHighlightModel.Roles.Count; index++)
                items.Add(new XElement("record", new XAttribute("id", RoleItemId(index)),
                    new XAttribute("name", PositionHighlightModel.Roles[index].Name(localizer.Code))));
            popup.Add(items);
            // mbch is the native profile menu-change route; the custom payload must read this
            // separate popup without changing attv/pamb or duplicating pltt/plmt/plpt.
            popup.Add(new XElement("record", new XAttribute("id", "select_event"),
                new XElement("flags", new XAttribute("id", "event_id"), new XAttribute("value", "mbch"))));
            buttons.Add(popup);
            // Keep explanatory text out of the three attribute columns. The photo/card
            // uses at most fifteen native20px rows; the legend occupies the free left area.
            var personal = xml.Descendants("container").SingleOrDefault(value =>
                (string?)value.Attribute("file") == "player profile personal details")
                ?? throw new InvalidDataException("Missing unique personal-details panel.");
            var photoColumn = new XElement("container", new XAttribute("id", "Fpsi"),
                new XElement("layout", new XAttribute("class", "arrange_vertical_attachment"),
                    new XAttribute("alignment", "top"), new XAttribute("offset", "0"), new XAttribute("gap", "6")),
                new XElement("layout", new XAttribute("class", "stick_to_sides_attachment"),
                    new XAttribute("alignment", "horizontal"), new XAttribute("layout_children", "true"),
                    new XAttribute("inset", "0")));
            personal.ReplaceWith(photoColumn);
            personal.SetAttributeValue("height", "304");
            // A single native TABLE provides the skin's heading/body. Its wrapper
            // has no appearance, avoiding the second frame and inherited title insets.
            var legendTable = new XElement("widget", new XAttribute("class", "table"),
                new XAttribute("id", "Fltb"), new XAttribute("mode", "fill_rows, stripe_rows, printable"),
                new XAttribute("layout", "-1"), new XAttribute("row_height", "20"),
                new XAttribute("fixed_size_rows", "true"), new XAttribute("stretch_to_fit_rows", "true"),
                new XAttribute("row_spacing", "0"),
                new XElement("list", new XAttribute("id", "headings"),
                    new XElement("record", new XAttribute("text", localizer.Text("ProfilePanelLegendTitle")),
                        new XAttribute("alignment", "left,centre_y"))),
                new XElement("list", new XAttribute("id", "column_properties"),
                    new XElement("record", new XAttribute("indx", "0"), new XAttribute("alignment", "left,centre_y"))),
                new XElement("list", new XAttribute("id", "column_display_properties"),
                    new XElement("record", new XAttribute("indx", "0"), new XAttribute("left", "4"),
                        new XAttribute("right", "4"), new XAttribute("sort_disabled", "true"))));
            var legendLines = localizer.Text("ProfilePanelLegend").Split(". ", StringSplitOptions.RemoveEmptyEntries);
            for (var row = 0; row < legendLines.Length; row++)
            {
                var text = legendLines[row];
                if (!text.EndsWith('.')) text += ".";
                legendTable.Add(new XElement("widget", new XAttribute("class", "text"),
                    new XAttribute("id", row == 0 ? "Fleg" : "Flg" + (row + 1)),
                    new XAttribute("col", "0"), new XAttribute("row", row), new XAttribute("text", text),
                    new XAttribute("multiline", "false"), new XAttribute("alignment", "left,centre_y"),
                    new XAttribute("colour", "attribute label"), new XAttribute("size", "8")));
            }
            var legend = new XElement("container", new XAttribute("id", "Flgb"),
                new XAttribute("height", 20 * (legendLines.Length + 1) + 8),
                new XElement("layout", new XAttribute("class", "stick_to_sides_attachment"),
                    new XAttribute("alignment", "all"), new XAttribute("layout_children", "true"),
                    new XAttribute("inset", "0")), legendTable);
            photoColumn.Add(personal, legend);
        }
        if (options.HiddenAttributesEnabled)
        {
            // Use all three native-width columns: four20px rows in each leave the upper
            // technical/mental tables enough height for all fourteen attributes at FullHD.
            var personality = PlayerProfileFields.Hidden.Where(field => field.PersonSlot != 0).ToArray();
            var other = PlayerProfileFields.Hidden.Where(field => field.PersonSlot == 0).ToArray();
            var hidden = new XElement("container", new XAttribute("id", "Fhid"),
                new XAttribute("height", "112"),
                new XElement("layout", new XAttribute("class", "arrange_horizontal_attachment"),
                    new XAttribute("alignment", "fill"), new XAttribute("layout", "-1,-1,-1"),
                    new XAttribute("offset", "0"), new XAttribute("gap", "4")),
                new XElement("layout", new XAttribute("class", "stick_to_sides_attachment"),
                    new XAttribute("alignment", "vertical"), new XAttribute("layout_children", "true"),
                    new XAttribute("inset", "0")));
            XElement HiddenTable(string id, string title, IReadOnlyList<ProfileHiddenField> fields)
            {
                var table = new XElement("widget", new XAttribute("class", "table"),
                    new XAttribute("id", id), new XAttribute("mode", "fill_rows, stripe_rows, printable"),
                    new XAttribute("layout", "-1,25,25"), new XAttribute("row_height", "20"),
                    new XAttribute("fixed_size_rows", "true"), new XAttribute("stretch_to_fit_rows", "true"),
                    new XAttribute("row_spacing", "0"),
                    new XElement("list", new XAttribute("id", "headings"),
                        new XElement("record", new XAttribute("text", title),
                            new XAttribute("alignment", "left,centre_y"), new XAttribute("column_span", "3"))),
                    new XElement("list", new XAttribute("id", "column_display_properties"),
                        new XElement("record", new XAttribute("indx", "0"), new XAttribute("left", "4"),
                            new XAttribute("sort_disabled", "true")),
                        new XElement("record", new XAttribute("indx", "1"), new XAttribute("top", "0"),
                            new XAttribute("bottom", "0"), new XAttribute("right", "4"),
                            new XAttribute("sort_disabled", "true")),
                        new XElement("record", new XAttribute("indx", "2"), new XAttribute("left", "0"),
                            new XAttribute("right", "0"), new XAttribute("sort_disabled", "true"))),
                    new XElement("list", new XAttribute("id", "column_properties"),
                        new XElement("record", new XAttribute("indx", "0"),
                            new XAttribute("alignment", "left,centre_y")),
                        new XElement("record", new XAttribute("indx", "1"),
                            new XAttribute("alignment", "right,centre_y"), new XAttribute("style", "semi_bold"))));
                for (var row = 0; row < fields.Count; row++)
                {
                    var field = fields[row];
                    table.Add(new XElement("widget", new XAttribute("class", "label"),
                        new XAttribute("col", "0"), new XAttribute("row", row),
                        new XAttribute("colour", "attribute label"),
                        new XAttribute("text", localizer.Code == "pl" ? field.Polish : field.English)),
                        new XElement("widget", new XAttribute("class", "label"), new XAttribute("id", field.Id),
                            new XAttribute("col", "1"), new XAttribute("row", row),
                            new XAttribute("alignment", "right,centre_y"), new XAttribute("style", "semi_bold"),
                            new XAttribute("text", "----"), new XAttribute("hint", localizer.Text("ProfileFieldRange"))));
                }
                return table;
            }
            hidden.Add(HiddenTable("Fhp1", localizer.Text("ProfilePanelPersonality"), personality.Take(4).ToArray()),
                HiddenTable("Fhp2", localizer.Text("ProfilePanelCharacter"), personality.Skip(4).ToArray()),
                HiddenTable("Fhp3", localizer.Text("ProfilePanelHidden"), other));
            attributes.Add(hidden);
        }
        // Own labels must remain in the chosen panel locale even when FM's UI
        // language is different. These native aliases and translate=false are used
        // by the shipped skin XML; do not apply them to the game's original panels.
        foreach (var id in new[] { RoleWidgetId, "Flgb", "Fhid" })
        {
            var block = xml.Descendants().SingleOrDefault(value => (string?)value.Attribute("id") == id);
            if (block is null) continue;
            foreach (var element in block.DescendantsAndSelf().ToArray())
            foreach (var attribute in element.Attributes().Where(value =>
                value.Name.LocalName is "text" or "name" or "title" or "subtitle" or "hint").ToArray())
            {
                element.AddFirst(new XElement("string",
                    new XAttribute("id", attribute.Name.LocalName + "_not_translated"),
                    new XAttribute("value", attribute.Value), new XAttribute("translate", "false")));
                attribute.Remove();
            }
        }
        using var output = new MemoryStream();
        using (var writer = XmlWriter.Create(output, new XmlWriterSettings
        {
            Encoding = new UTF8Encoding(false), Indent = false, OmitXmlDeclaration = xml.Declaration is null
        })) xml.Save(writer);
        return output.ToArray();
    }
}
