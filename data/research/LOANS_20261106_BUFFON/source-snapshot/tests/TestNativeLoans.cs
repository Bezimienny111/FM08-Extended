using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;

class TestNativeLoans {
 static int passed;
 static readonly BindingFlags Hidden=BindingFlags.NonPublic|BindingFlags.Static;
 static void Require(bool ok,string label){if(!ok)throw new InvalidDataException(label);}
 static void Check(string label,Action test){test();passed++;Console.WriteLine("PASS: "+label);}
 static void Reject(string label,byte[] data){Check(label,()=>{try{FM08_Database_Editor.ParseNativeLoans(data,40);}catch(InvalidDataException){return;}throw new Exception("Malformed loan table accepted: "+label);});}
 static byte[] Load(string directory,string name){return (byte[])typeof(FM08_Database_Editor).GetMethod("DecompressFile",Hidden).Invoke(null,new object[]{Path.Combine(directory,name)});}
 static int Table(byte[] server,int count){return (int)typeof(FM08_Database_Editor).GetMethod("FindNativeLoanTable",Hidden).Invoke(null,new object[]{server,count});}
 static string Hash(string path){using(var s=File.OpenRead(path))using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(s)).Replace("-","");}
 static Dictionary<string,string> Hashes(string root){return Directory.GetFiles(root,"*",SearchOption.AllDirectories).ToDictionary(p=>p.Substring(root.Length+1),Hash);}
 static byte[] Synthetic(params int[] ids){
  byte[] b=Enumerable.Repeat((byte)167,12+4+ids.Length*32+12).ToArray();BitConverter.GetBytes(ids.Length).CopyTo(b,12);
  for(int j=0;j<ids.Length;j++){int p=16+j*32;Array.Clear(b,p,32);BitConverter.GetBytes(10+j).CopyTo(b,p+1);BitConverter.GetBytes(992).CopyTo(b,p+5);
   BitConverter.GetBytes((ushort)181).CopyTo(b,p+9);BitConverter.GetBytes((ushort)2007).CopyTo(b,p+11);BitConverter.GetBytes((ushort)181).CopyTo(b,p+13);BitConverter.GetBytes((ushort)2008).CopyTo(b,p+15);
   b[p+17]=4;b[p+18]=255;BitConverter.GetBytes(5000000+j).CopyTo(b,p+19);b[p+23]=50;BitConverter.GetBytes(j).CopyTo(b,p+24);BitConverter.GetBytes(ids[j]).CopyTo(b,p+28);
  }return b;
 }
 static void SyntheticTests(){
  Check("legacy repeated -1 loan UIDs accepted",()=>Require(FM08_Database_Editor.ParseNativeLoans(Synthetic(-1,-1),40).Count==2,"legacy rows"));
  Check("mixed legacy and distinct positive UIDs accepted",()=>{var r=FM08_Database_Editor.ParseNativeLoans(Synthetic(-1,1800000090,1800000091),40);Require(r.Count==3&&r[1].UniqueId==1800000090&&r[2].RecordIndex==2,"mixed UIDs");});
  Check("raw option, unset shirt, fee and percentage preserved",()=>{var r=FM08_Database_Editor.ParseNativeLoans(Synthetic(1800000090),40)[0];Require(r.OptionsRaw==4&&r.SquadNumberRaw==255&&r.FeeToBuyRaw==5000000&&r.WageContributionRaw==50,"raw fields");});
  Check("zero-based native dates include leap-year end",()=>{var r=FM08_Database_Editor.ParseNativeLoans(Synthetic(-1),40)[0];Require(r.StartDate==new DateTime(2007,7,1)&&r.EndDate==new DateTime(2008,6,30),"dates");});
  Reject("zero loan UID rejected",Synthetic(0));Reject("negative UID other than -1 rejected",Synthetic(-2));Reject("duplicate positive loan UID rejected",Synthetic(1800000090,1800000090));
  byte[] b=Synthetic(-1);b[16]=1;Reject("unknown record flag rejected",b);
  b=Synthetic(-1);BitConverter.GetBytes(40).CopyTo(b,17);Reject("out-of-range PERSON rejected",b);
  b=Synthetic(-1);BitConverter.GetBytes(-2).CopyTo(b,21);Reject("invalid loan club rejected",b);
  b=Synthetic(-1);BitConverter.GetBytes((ushort)2101).CopyTo(b,27);Reject("invalid start year rejected",b);
  b=Synthetic(-1);BitConverter.GetBytes((ushort)366).CopyTo(b,29);Reject("out-of-year end date rejected",b);
  b=Synthetic(-1);BitConverter.GetBytes(7).CopyTo(b,40);Reject("incorrect record index rejected",b);
  Check("removal renumbers only indices and preserves positive UIDs",()=>{
   byte[] old=Synthetic(1800000090,-1,1800000091),snapshot=(byte[])old.Clone();byte[] result=FM08_Database_Editor.RemoveNativeLoans(old,40,new HashSet<int>{11});
   var r=FM08_Database_Editor.ParseNativeLoans(result,40);Require(r.Count==2&&r[0].UniqueId==1800000090&&r[1].UniqueId==1800000091&&r[1].RecordIndex==1,"retained identity");
   Require(old.SequenceEqual(snapshot)&&old.Take(12).SequenceEqual(result.Take(12))&&old.Skip(old.Length-12).SequenceEqual(result.Skip(result.Length-12)),"protected synthetic bytes");
   byte[] expected=old.Skip(80).Take(32).ToArray();BitConverter.GetBytes(1).CopyTo(expected,24);Require(expected.SequenceEqual(result.Skip(48).Take(32)),"only footer index may change");
  });
  Check("empty removal selection is byte-identical no-op",()=>{byte[] s=Synthetic(-1,1800000090);Require(object.ReferenceEquals(s,FM08_Database_Editor.RemoveNativeLoans(s,40,new HashSet<int>())) ,"no-op copied buffer");});
 }
 static int Main(string[] a){try{
  Require(a.Length==3,"Expected official-802 TEST_LOAN report-json");string baseline=Path.GetFullPath(a[0]),fixture=Path.GetFullPath(a[1]);
  var pins=Hashes(baseline);var fixturePins=Hashes(fixture);
  SyntheticTests();
  byte[] p=Load(baseline,"people_db.dat"),q=Load(fixture,"people_db.dat"),server=Load(baseline,"server_db.dat"),edited=Load(fixture,"server_db.dat");
  int count=BitConverter.ToInt32(p,0);Require(count==BitConverter.ToInt32(q,0),"PERSON count differs");
  var old=FM08_Database_Editor.ParseNativeLoans(server,count);var current=FM08_Database_Editor.ParseNativeLoans(edited,count);
  Check("official 8.0.2 retains all 6210 legacy loan rows",()=>Require(old.Count==6210&&old.All(r=>r.UniqueId==-1)&&old.All(r=>r.PersonIndex!=3474),"official baseline"));
  Check("TEST_LOAN contains 6210 legacy rows plus one positive-UID row",()=>Require(current.Count==6211&&current.Count(r=>r.UniqueId==-1)==6210&&current.Count(r=>r.UniqueId==1800000090)==1,"new fixture rows"));
  var buffon=current.Single(r=>r.PersonIndex==3474);
  Check("Buffon loan destination and native identity match SI",()=>Require(buffon.ClubId==992&&buffon.RecordIndex==6210&&buffon.UniqueId==1800000090,"Buffon identifiers"));
  Check("Buffon dates and raw terms match user screenshot",()=>Require(buffon.StartDate==new DateTime(2007,7,1)&&buffon.EndDate==new DateTime(2008,6,30)&&buffon.OptionsRaw==0&&buffon.SquadNumberRaw==255&&buffon.FeeToBuyRaw==5000000&&buffon.WageContributionRaw==50,"Buffon terms"));
  int before=Table(server,count),after=Table(edited,count);
  Check("all pre-existing loan bytes match SI",()=>Require(server.Skip(before+4).Take(6210*32).SequenceEqual(edited.Skip(after+4).Take(6210*32)),"old loan rows changed"));
  byte[] removed=FM08_Database_Editor.RemoveNativeLoans(edited,count,new HashSet<int>{3474});
  Check("removing positive-UID loan restores complete original loan table",()=>Require(server.Skip(before).Take(4+6210*32).SequenceEqual(removed.Skip(after).Take(4+6210*32)),"original table not restored"));
  Check("removal preserves every byte outside the edited SI loan table",()=>Require(edited.Take(after).SequenceEqual(removed.Take(after))&&edited.Skip(after+4+6211*32).SequenceEqual(removed.Skip(after+4+6210*32)),"outside-table bytes changed"));
  Check("both fixture directories remain byte-identical",()=>Require(pins.OrderBy(x=>x.Key).SequenceEqual(Hashes(baseline).OrderBy(x=>x.Key))&&fixturePins.OrderBy(x=>x.Key).SequenceEqual(Hashes(fixture).OrderBy(x=>x.Key)),"input hashes changed"));
  File.WriteAllText(a[2],new JavaScriptSerializer{MaxJsonLength=int.MaxValue}.Serialize(new{status="pass",checks=passed,baseline,fixture,source_hashes=pins,fixture_hashes=fixturePins,editor_sha256=Hash(typeof(FM08_Database_Editor).Assembly.Location),test_source="TestNativeLoans.cs"}),new UTF8Encoding(false));
  Console.WriteLine("PASS: "+passed+" native loan checks; no database writes.");return 0;
 }catch(Exception e){Console.Error.WriteLine(e);return 1;}}
}
