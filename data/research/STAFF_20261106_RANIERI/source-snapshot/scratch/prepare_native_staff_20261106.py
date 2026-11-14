from pathlib import Path
r=Path('FM08-Database-Tools')
p=r/'FM08_Database_Editor.cs';t=p.read_text(encoding='utf-8-sig')
assert 'public class FM08_Database_Editor : Form' in t
t=t.replace('public class FM08_Database_Editor : Form','public partial class FM08_Database_Editor : Form',1)
marker='\t\tpanel2.Controls.Add(this.lblStatus);'
assert marker in t
t=t.replace(marker,marker+'\n\t\tvar staffButton = new Button { Text = "Sztab...", Location = new Point(895, 73), Width = 130, Height = 27 };\n\t\tstaffButton.Click += (s, e) => OpenNativeStaffEditor();\n\t\tpanel2.Controls.Add(staffButton);',1)
p.write_bytes(t.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
p=r/'build.ps1';t=p.read_text(encoding='utf-8-sig');old=r'@("$Root\FM08_Database_Editor.cs") $Ui';assert old in t
t=t.replace(old,r'@("$Root\FM08_Database_Editor.cs", "$Root\NativeStaff.cs") $Ui',1)
p.write_text(t,encoding='utf-8')
print('Added staff model, guarded wage batch/CSV API and GUI entry; databases untouched.')

