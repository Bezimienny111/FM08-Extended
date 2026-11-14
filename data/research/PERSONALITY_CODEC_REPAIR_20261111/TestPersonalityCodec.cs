using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Collections.Generic;
using System.Web.Script.Serialization;
using P=FM08_Database_Editor.PlayerRecord;
class TestPersonalityCodec {
 static BindingFlags F=BindingFlags.NonPublic|BindingFlags.Static;static Type E=typeof(FM08_Database_Editor),W=typeof(VerifiedNativeSquadsWorker);static int cases;
 static void Need(bool b,string m){if(!b)throw new Exception(m);cases++;}
 static object Call(string n,params object[] a){return E.GetMethod(n,F).Invoke(null,a);}
 static byte[] Load(string d,string n){return(byte[])Call("DecompressFile",Path.Combine(d,n+"_db.dat"));}
 static readonly string[] Names={"Adaptability","Ambition","Loyalty","Pressure","Professionalism","Sportsmanship","Temperament","Controversy"};
 // INDEPENDENT ORACLE: official SI TEST_X12 UID8074, source pins outside this test.
 static readonly byte[] Oracle={2,4,6,8,10,12,14,16};
 static byte[] Named(P p){return new[]{p.Adaptability,p.Ambition,p.Loyalty,p.Pressure,p.Professionalism,p.Sportsmanship,p.Temperament,p.Controversy};}
 static string Hash(byte[] a){using(var h=System.Security.Cryptography.SHA256.Create())return BitConverter.ToString(h.ComputeHash(a)).Replace("-","");}
 static P Del(){return new P{Id=8074,PersonOffset=41239985,NationIdOffset=41240191,ClubIdOffset=41240212};}
 static P New(string nation){return new P{Id=-1,FirstName="Alessandro",LastName="Del Piero",BirthDate=new DateTime(1985,11,9),Nationality=nation,Club="",CA=100,PA=120,Height=180,Weight=75,WeeklyWage=500,SquadNumber=77,ContractExpires=new DateTime(2010,6,30),Adaptability=2,Ambition=4,Loyalty=6,Pressure=8,Professionalism=10,Sportsmanship=12,Temperament=14,Controversy=16};}
 static void Reject(Action f){try{f();}catch(InvalidDataException){cases++;return;}throw new Exception("Expected InvalidDataException");}
 static List<P> Players(byte[] p,byte[] s,Dictionary<int,string> clubs,Dictionary<int,string> nations){
  object[] f={s,0,0};var first=(Dictionary<int,string>)E.GetMethod("ParseFirstNames",F).Invoke(null,f);
  object[] l={s,(int)f[2],null,0};var last=(Dictionary<int,string>)E.GetMethod("ParseSurnames",F).Invoke(null,l);
  var common=(Dictionary<int,string>)Call("ParseCommonNames",s,(int)l[3]);
  return(List<P>)Call("BuildPlayerList",p,Call("ParsePersonData",p,first,last,common,clubs),Call("ParseEntityTreeAndTags",s),l[2],clubs,nations);
 }
 static int Main(string[] a){try{
  var pins=new Dictionary<string,string>();foreach(string d in a.Take(2))foreach(string n in new[]{"people","server","client"}){string f=Path.Combine(d,n+"_db.dat");pins[f]=Hash(File.ReadAllBytes(f));}
  byte[] u=Load(a[1],"people");var del=Del();Call("ReadNativePersonalityProfiles",u,new List<P>{del});Need(Named(del).SequenceEqual(Oracle),"X12 named read vs official oracle");
  int r=FM08_Database_Editor.ResolveNativePersonalityRecord(u,del);Need(r==96121383,"Variable prefix reference index2652");
  Need(u.Skip(r+1).Take(8).SequenceEqual(Oracle),"Pinned official SI body");
  Need(FM08_Database_Editor.EncodeNativePersonality(del).SequenceEqual(Oracle),"Encoder vs official oracle");
  string uh=Hash(u);FM08_Database_Editor.WriteNativePersonality(u,del,false);Need(Hash(u)==uh,"X12 no-op full PEOPLE");
  FM08_Database_Editor.InitCsvRegistry();
  for(int k=0;k<8;k++){
   var f=FM08_Database_Editor.allCsvFields.Single(x=>x.Key==Names[k]);f.Setter(del,u,"19");Need(u[r+k+1]==19,"Named setter offset "+Names[k]);
   // Independent whole-payload inverse proves no hidden writes.
   u[r+k+1]=Oracle[k];Need(Hash(u)==uh,"Only one expected byte changes "+Names[k]);f.Setter(del,u,Oracle[k].ToString());
  }
  del.Controversy=255;FM08_Database_Editor.WriteNativePersonality(u,del,true);Need(Hash(u)==uh,"PreserveExistingData exact");
  Reject(()=>FM08_Database_Editor.WriteNativePersonality(u,del,false));Reject(()=>FM08_Database_Editor.SetNativePersonalityField(del,u,"Controversy","21"));Reject(()=>FM08_Database_Editor.SetNativePersonalityField(del,u,"bad","1"));
  u[r+8]=21;Reject(()=>FM08_Database_Editor.ResolveNativePersonalityRecord(u,del));u[r+8]=16;
  var missing=new P{Id=1,Controversy=5};Call("ReadNativePersonalityProfiles",u,new List<P>{missing});Need(Named(missing).All(x=>x==0),"Missing never fabricated");
  u=null;GC.Collect();
  byte[] p=Load(a[0],"people"),s=Load(a[0],"server"),c=Load(a[0],"client");string ph=Hash(p);
  int count=BitConverter.ToInt32(p,4),h=(int)Call("Find89ByteTable",p)-89-count*17;var tmp=new P();
  for(int i=0;i<count;i++){int row=h+4+i*17;FM08_Database_Editor.DecodeNativePersonality(p,row,tmp);byte[] vals=FM08_Database_Editor.EncodeNativePersonality(tmp);Buffer.BlockCopy(vals,0,p,row+1,8);}
  Need(Hash(p)==ph,"802 all 17B roundtrip byte exact");
  var clubs=(Dictionary<int,string>)Call("ParseClubs",s);var nations=(Dictionary<int,string>)Call("ParseNations",s);var ps=Players(p,s,clubs,nations);var dp=ps.Single(x=>x.Id==8074);
  Need(Named(dp).SequenceEqual(new byte[]{16,19,20,18,16,16,17,1}),"802 named values without hardcoded fallback");
  FM08_Database_Editor.NationsRev.Clear();foreach(var x in nations)if(!FM08_Database_Editor.NationsRev.ContainsKey(x.Value))FM08_Database_Editor.NationsRev[x.Value]=x.Key;
  FM08_Database_Editor.ClubsRev.Clear();foreach(var x in clubs)if(!string.IsNullOrEmpty(x.Value)&&!FM08_Database_Editor.ClubsRev.ContainsKey(x.Value))FM08_Database_Editor.ClubsRev[x.Value]=x.Key;
  var pp=(byte[])p.Clone();var ss=(byte[])s.Clone();var cc=(byte[])c.Clone();var one=New(dp.Nationality);
  FM08_Database_Editor.AppendNativePlayer(ref pp,ref ss,ref cc,one,new List<P>());
  int rowOne=FM08_Database_Editor.ResolveNativePersonalityRecord(pp,one);Need(rowOne>=0&&pp.Skip(rowOne+1).Take(8).SequenceEqual(Oracle),"Actual single builder oracle order");
  int oh=(int)Call("Find89ByteTable",pp)-89-(count+1)*17;Need(p.Skip(h+4).Take(count*17).SequenceEqual(pp.Skip(oh+4).Take(count*17)),"Single builder preserved old rows");
  pp=null;ss=null;cc=null;GC.Collect();
  var batch=New(dp.Nationality);batch.Club=clubs[995];Type poolType=W.GetNestedType("IdPool",BindingFlags.NonPublic);
  object pool=Activator.CreateInstance(poolType,BindingFlags.Instance|BindingFlags.NonPublic,null,new object[]{1699000000,1699100000,new byte[][]{p,s,c}},null);
  object[] v={p,s,c,new List<P>{batch},ps,new Dictionary<P,int>{{batch,995}},pool};
  W.GetMethod("AppendBatch",F).Invoke(null,v);pp=(byte[])v[0];
  int rowBatch=FM08_Database_Editor.ResolveNativePersonalityRecord(pp,batch);Need(rowBatch>=0&&pp.Skip(rowBatch+1).Take(8).SequenceEqual(Oracle),"Actual guarded batch builder oracle order");
  int bh=(int)Call("Find89ByteTable",pp)-89-(count+1)*17;Need(p.Skip(h+4).Take(count*17).SequenceEqual(pp.Skip(bh+4).Take(count*17)),"Batch preserved old rows");
  Need(Hash(p)==ph,"802 original buffer unchanged");foreach(var pin in pins)Need(Hash(File.ReadAllBytes(pin.Key))==pin.Value,"Disk input pin unchanged");
  File.WriteAllText(a[2],new JavaScriptSerializer().Serialize(new{status="PASS",cases,source_pins=pins,oracle=Oracle,rows_802_roundtrip=count,actual_single_builder=true,actual_batch_builder=true,database_writes=false}));
  Console.WriteLine("PASS "+cases+" checks; "+count+" rows; actual single and batch builders; no DB writes");return 0;
 }catch(Exception e){Console.Error.WriteLine(e);return 1;}}
}
