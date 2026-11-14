using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Web.Script.Serialization;
class ExportNativeStructure {
 static int Main(string[] a){try{if(a.Length!=3)throw new ArgumentException("source-db editor-exe output-json");string ed=Path.GetFullPath(a[1]);var d=AppDomain.CreateDomain("NativeStructure",null,new AppDomainSetup{ApplicationBase=Path.GetDirectoryName(ed)});try{var w=(NativeStructureWorker)d.CreateInstanceFromAndUnwrap(Assembly.GetExecutingAssembly().Location,typeof(NativeStructureWorker).FullName);w.Run(Path.GetFullPath(a[0]),Path.GetFullPath(a[2]));}finally{AppDomain.Unload(d);}return 0;}catch(Exception e){Console.Error.WriteLine(e);return 1;}}
}
public sealed class NativeStructureWorker:MarshalByRefObject {
 static System.Collections.Generic.Dictionary<int,FM08_Database_Editor.NativeClubDivisionRecord> ReadAll(byte[] a,int n) {
 var result=new System.Collections.Generic.Dictionary<int,FM08_Database_Editor.NativeClubDivisionRecord>();
 var method=typeof(FM08_Database_Editor).GetMethod("TryReadNativeClubRecord",BindingFlags.NonPublic|BindingFlags.Static);
 for(int p=8;p<a.Length-65;p++) {
  if(a[p]!=10)continue;int prev=BitConverter.ToInt32(a,p-8);if(prev<0||prev>=a.Length/71)continue;
  int div=BitConverter.ToInt32(a,p+7),last=BitConverter.ToInt32(a,p+11);if(div < -1||div>=a.Length/4||last < -1||last>=a.Length/4)continue;
  object[] v=new object[]{a,p,n,null};if(!(bool)method.Invoke(null,v))continue;
  var r=(FM08_Database_Editor.NativeClubDivisionRecord)v[3];if(result.ContainsKey(r.ClubIndex))throw new System.IO.InvalidDataException("Duplicate club index");
  result.Add(r.ClubIndex,r);p=r.Footer+7;
 } return result;
}
public void Run(string source,string output){if(File.Exists(output))throw new IOException("Output already exists");var method=typeof(FM08_Database_Editor).GetMethod("DecompressFile",BindingFlags.NonPublic|BindingFlags.Static);byte[] server=(byte[])method.Invoke(null,new object[]{Path.Combine(source,"server_db.dat")}),people=(byte[])method.Invoke(null,new object[]{Path.Combine(source,"people_db.dat")});int count=BitConverter.ToInt32(people,0);var records=ReadAll(server,count);var rows=records.Values.OrderBy(x=>x.ClubIndex).Select(x=>new{TeamIndex=x.ClubIndex,ClubUID=BitConverter.ToInt32(server,x.Footer+4),Start=x.Start,Footer=x.Footer,RosterOffset=x.RosterOffset,RosterSize=BitConverter.ToUInt16(server,x.RosterOffset),FamilyIndex=-1,CurrentDivisionIndex=x.CurrentDivisionIndex,PreviousDivisionIndex=x.PreviousDivisionIndex,EuropeanCompetitionIndex=x.EuropeanCompetitionIndex}).ToArray();var j=new JavaScriptSerializer{MaxJsonLength=int.MaxValue};File.WriteAllText(output,j.Serialize(new{person_count=count,records=rows}),new System.Text.UTF8Encoding(false));Console.WriteLine("Exported pinned native structure rows: "+rows.Length);}
}
