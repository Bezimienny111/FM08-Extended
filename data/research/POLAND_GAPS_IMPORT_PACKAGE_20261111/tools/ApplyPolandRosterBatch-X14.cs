using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Reflection;
using System.Globalization;
using System.Collections;
using System.Collections.Generic;
using P=FM08_Database_Editor.PlayerRecord;

// Compile with the existing VerifiedNativeSquadsWorker partial sources and PolandSquadsN4.cs.
class ApplyPolandRosterBatch {
 static int Main(string[] a) { try {
  if(a.Length!=4&&(a.Length!=5||a[4]!="--validate"))throw new ArgumentException("editor source output preparedDir [--validate]");
  string editor=Path.GetFullPath(a[0]);
  var domain=AppDomain.CreateDomain("PolandRosterBatch",null,new AppDomainSetup{ApplicationBase=Path.GetDirectoryName(editor)});
  try {var w=(VerifiedNativeSquadsWorker)domain.CreateInstanceFromAndUnwrap(Assembly.GetExecutingAssembly().Location,typeof(VerifiedNativeSquadsWorker).FullName);w.PolandRosterBatch(a[1],a[2],a[3],a.Length==5);}
  finally {AppDomain.Unload(domain);} return 0;
 } catch(Exception e){Console.Error.WriteLine(e);return 1;} }
}
public sealed partial class VerifiedNativeSquadsWorker {
 static string B7File(string dir,params string[] names){foreach(string n in names){string p=Path.Combine(dir,n);if(File.Exists(p))return p;}throw new FileNotFoundException("Missing prepared file: "+string.Join(" / ",names));}
 static string B7Text(Dictionary<string,object> m,params string[] keys){foreach(string k in keys)if(m.ContainsKey(k))return Convert.ToString(m[k],CultureInfo.InvariantCulture);throw new InvalidDataException("Missing manifest field: "+string.Join(" / ",keys));}
 static string B7BufferHash(byte[] b){using(var h=System.Security.Cryptography.SHA256.Create())return BitConverter.ToString(h.ComputeHash(b)).Replace("-","");}
 static DateTime B7Date(string s){return DateTime.ParseExact(s,"yyyy-MM-dd",CultureInfo.InvariantCulture);}
 static List<Dictionary<string,string>> B7Rows(string path){return File.ReadAllLines(path,Encoding.UTF8).Skip(1).Any(x=>!string.IsNullOrWhiteSpace(x))?AbRows(path):new List<Dictionary<string,string>>();}
 static HashSet<int> B7Ints(Dictionary<string,object> m,string key){var r=new HashSet<int>();if(m.ContainsKey(key))foreach(object x in (IEnumerable)m[key])Require(r.Add(Convert.ToInt32(x,CultureInfo.InvariantCulture)),"Duplicate manifest UID");return r;}
 static void B7Pins(string source,Dictionary<string,object> m){
  Require(Path.GetFullPath(source).Equals(Path.GetFullPath(B7Text(m,"source","source_db")),StringComparison.OrdinalIgnoreCase),"Source path pin differs");
  var pins=(Dictionary<string,object>)m["source_hashes"];Require(pins.Count==Directory.GetFiles(source,"*",SearchOption.AllDirectories).Length,"Source inventory differs");
  foreach(var p in pins)Require(N4Hash(Path.Combine(source,p.Key)).Equals(Convert.ToString(p.Value),StringComparison.OrdinalIgnoreCase),"Source hash differs: "+p.Key);
 }
 static void B7PinFile(string file,string key,Dictionary<string,object> m){
  string hash=null;object v;if(m.TryGetValue(key,out v))hash=Convert.ToString(v);
  if(m.ContainsKey("prepared_hashes")){var pins=(Dictionary<string,object>)m["prepared_hashes"];if(pins.TryGetValue(Path.GetFileName(file),out v))hash=Convert.ToString(v);}
  Require(!string.IsNullOrEmpty(hash)&&N4Hash(file).Equals(hash,StringComparison.OrdinalIgnoreCase),"Prepared pin missing/differs: "+Path.GetFileName(file));
 }
 static void B7ActorProof(byte[] oldPeople,byte[] people,N4Actor x,N4Actor y,bool released,bool legacy,bool nationalityRepair){
  Require(x.Owner-x.Start==y.Owner-y.Start&&x.Dob-x.Start==y.Dob-y.Start,"Subject prefix shape changed");
  var allowed=new HashSet<int>();foreach(int off in new[]{x.Owner-x.Start,x.Owner-x.Start+5})for(int k=0;k<4;k++)allowed.Add(off+k);allowed.Add(x.Owner-x.Start+27);
  if(legacy)for(int k=-2;k<2;k++)allowed.Add(x.Dob-x.Start+k);
  if(nationalityRepair)for(int k=0;k<4;k++)allowed.Add(x.Dob+5-x.Start+k);
  for(int i=0;i<x.Contract-x.Start;i++)Require(allowed.Contains(i)||oldPeople[x.Start+i]==people[y.Start+i],"Unexpected subject prefix UID "+x.Uid+" byte "+i);
  if(released)Require(y.Length==0,"Released subject retains contract");
  else if(x.Length>0){Require(x.Length==y.Length&&x.Payload>=0&&y.Payload-y.Contract==x.Payload-x.Contract,"Existing contract shape changed");var ca=new HashSet<int>();foreach(int off in new[]{31,35,39,54})for(int k=0;k<4;k++)ca.Add(x.Payload-x.Contract+off+k);ca.Add(x.Payload-x.Contract+60);for(int i=0;i<x.Length;i++)Require(ca.Contains(i)||oldPeople[x.Contract+i]==people[y.Contract+i],"Unexpected contract byte UID "+x.Uid+" byte "+i);}
  else Require(y.Length==65,"Missing generated main contract");
  int tail=x.Contract+x.Length,next=y.Contract+y.Length;Require(x.End-tail==y.End-next,"Subject tail shape changed");EqualRange(oldPeople,tail,people,next,x.End-tail,"subject protected tail");
 }
 static N4Actor B7AfterEvidence(byte[] people,P p,N4Actor before,string prepared){
  // Free variable-prefix PERSON has no parsed ClubIdOffset. Use the exact proven source boundary, never NationOffset+21.
  if(p.ClubIdOffset==0&&before.Length>0){
   int start=p.PersonOffset-15,end=PersonEnd(people,p),owner=start+(before.Owner-before.Start),pi=BitConverter.ToInt32(before.Bytes,0);
   Require(owner>start&&owner+28<=end-8&&BitConverter.ToInt32(people,start)==pi&&BitConverter.ToInt32(people,end-8)==pi&&BitConverter.ToInt32(people,end-4)==p.Id,"Free PERSON source/footer identity differs");
   Require(p.BirthDateOffset-start==before.Dob-before.Start&&BitConverter.ToInt32(people,owner)==-1,"Free PERSON source owner/DOB boundary differs");
   int length=(int)Call("GetNativeContractLength",people,owner+28,end-8,pi);Require(length==0,"Free PERSON retains/unrecognized contract");
   byte[] b=new byte[end-start];Buffer.BlockCopy(people,start,b,0,b.Length);
   return new N4Actor{Uid=p.Id,Start=start,End=end,Owner=owner,Dob=p.BirthDateOffset,Contract=owner+28,Payload=-1,Length=0,Bytes=b};
  }
  try{return N4Evidence(people,p);}catch(Exception e){
   int start=p.PersonOffset-15,end=PersonEnd(people,p);string path=Path.Combine(prepared,"postwrite-format-failure-"+p.Id+".json");Require(!File.Exists(path),"Preserve prior format diagnostic");var b=new byte[end-start];Buffer.BlockCopy(people,start,b,0,b.Length);N4Save(path,new{uid=p.Id,first=p.FirstName,last=p.LastName,start,end,owner_offset=p.ClubIdOffset,nation_offset=p.NationIdOffset,dob_offset=p.BirthDateOffset,club=p.ClubId,expected_prefix_owner=before.Owner-before.Start,expected_prefix_dob=before.Dob-before.Start,source_record=Convert.ToBase64String(before.Bytes),after_record=Convert.ToBase64String(b),reason=e.Message});throw new InvalidDataException("Postwrite actor format UID "+p.Id+": "+e.Message,e);
  }
 }
 public void PolandRosterBatch(string source,string output,string prepared,bool validateOnly){ScopedRosterBatch(source,output,prepared,validateOnly,"poland126");}
 public void ScopedRosterBatch(string source,string output,string prepared,bool validateOnly,string scope){
  Require(scope=="poland126"||scope=="italy132"||scope=="hungary48"||scope=="three80"||scope=="x2123"||scope=="x3189"||scope=="x7108"||scope=="x14292","Unsupported roster scope");
  bool italy=scope=="italy132",hungary=scope=="hungary48",three=scope=="three80",x2=scope=="x2123",x3=scope=="x3189",x7=scope=="x7108",x10=scope=="x14292",countryScoped=italy||hungary||three||x2||x3||x7||x10;int expectedClubs=x10?292:x7?108:x3?189:x2?123:three?80:hungary?48:italy?132:126;int targetCountry=(three||x2||x3||x7||x10)?-1:hungary?147:italy?150:126;
  source=Path.GetFullPath(source);output=Path.GetFullPath(output);prepared=Path.GetFullPath(prepared);
  string manifestPath=B7File(prepared,"manifest.json");var manifest=N4Read(manifestPath);B7Pins(source,manifest);
  Require(Path.GetFullPath(B7Text(manifest,"output","output_db")).Equals(output,StringComparison.OrdinalIgnoreCase),"Output path pin differs");
  Require(!Directory.Exists(output)&&!File.Exists(output)&&!output.StartsWith(source+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase),"Output exists or is inside source");
  string csv=B7File(prepared,"native_players.csv","native-players.csv"),mapfile=B7File(prepared,"club_map.csv","club-map.csv"),idfile=B7File(prepared,"identities.csv"),loanfile=B7File(prepared,"loans.csv");
  B7PinFile(csv,"csv_sha256",manifest);B7PinFile(mapfile,"club_map_sha256",manifest);B7PinFile(idfile,"identities_sha256",manifest);B7PinFile(loanfile,"loans_sha256",manifest);
  var rows=B7Rows(csv);var identities=B7Rows(idfile);var map=B7Rows(mapfile);var loanRows=B7Rows(loanfile);
  Require(rows.Count>0&&rows.Count==identities.Count&&map.Count==expectedClubs,"Incomplete scoped prepared batch");
  if(countryScoped){
   Require(new[]{"prepared","prepared_with_explicit_source_gaps","pilot_prepared"}.Contains(B7Text(manifest,"status")),"Italy input still has unresolved import rows");
   Require(Convert.ToInt32(((Dictionary<string,object>)manifest["counts"])["issues"])==0,"Unresolved Italy import rows");
   if(B7Text(manifest,"stage")=="full"&&!validateOnly){
    string pilot=B7Text(manifest,"pilot_verification_path");Require(File.Exists(pilot)&&N4Hash(pilot).Equals(B7Text(manifest,"pilot_verification_sha256"),StringComparison.OrdinalIgnoreCase),"Missing/changed independent Italy pilot");
    var pr=N4Read(pilot);Require(B7Text(pr,"status")=="pass"&&B7Text(pr,"source_db")==source,"Pilot belongs to another source");
   }
   Require(B7Text(manifest,"scope_id")==(x10?"por-per-nor-pol-gaps-x14":x7?"sco-svk-svn-sin-x7":x3?"swe-swi-nazaryna-x3":x2?"ukr-tur-miami123-x2":three?"three80-b1":hungary?"hungary48-h1":"italy132-i1")&&Convert.ToInt32(manifest["target_country_index"])==targetCountry,"Wrong Italy scope/country");
   if(x10)Require(B7Ints(manifest,"target_country_indices").SetEquals(new[]{162,160,194}),"Wrong X14 country set");
   if(x7)Require(B7Ints(manifest,"target_country_indices").SetEquals(new[]{167,168,169,79}),"Wrong X7 country set");
   if(x3)Require(B7Ints(manifest,"target_country_indices").SetEquals(new[]{171,172,152,174}),"Wrong X3 country set");
   if(x2)Require(B7Ints(manifest,"target_country_indices").SetEquals(new[]{173,174,120}),"Wrong X2 country set");
   if(three)Require(B7Ints(manifest,"target_country_indices").SetEquals(new[]{175,120,97,195}),"Wrong B1 country set");
   Require(Convert.ToInt32(manifest["prepared_rows"])==rows.Count&&Convert.ToInt32(manifest["prepared_loans"])==loanRows.Count,"Italy counts differ");
   foreach(var x in identities){Require(x.ContainsKey("SubjectID"),"Missing Italy subject key");x["ID90"]=x["SubjectID"];}
   foreach(var x in loanRows){Require(x.ContainsKey("SubjectID"),"Missing Italy loan subject key");x["ID90"]=x["SubjectID"];}
  }
  var clubsPlan=map.ToDictionary(x=>N4I(x,"TeamIndex"));var wanted=new HashSet<int>(clubsPlan.Keys);Require(map.Select(x=>N4I(x,"ClubUID")).Distinct().Count()==map.Count,"Repeated target club UID");
  if(countryScoped){
   var declared=B7Ints(manifest,"target_club_uids");Require(declared.SetEquals(map.Select(x=>N4I(x,"ClubUID"))),"Italy declared club UID set differs");
   if(x10){
    var empty=B7Ints(manifest,"structural_only_club_uids");Require(empty.IsSubsetOf(declared),"Structural-only UID outside target map");
    var emptyTeams=new HashSet<int>(map.Where(x=>empty.Contains(N4I(x,"ClubUID"))).Select(x=>N4I(x,"TeamIndex")));
    var actorTeams=new HashSet<int>(identities.Select(x=>N4I(x,"PlayingClubIndex")));
    Require(!actorTeams.Overlaps(emptyTeams),"Declared structural-only club has actors");
    if(B7Text(manifest,"stage")=="full")Require(actorTeams.SetEquals(wanted.Except(emptyTeams)),"Unlisted empty club or incomplete X14 actor coverage");
    else Require(actorTeams.Count==Convert.ToInt32(manifest["pilot_clubs"]),"X14 pilot actor coverage differs");
   }else{
   Require(identities.Select(x=>N4I(x,"PlayingClubIndex")).Where(wanted.Contains).Distinct().Count()==(B7Text(manifest,"stage")=="pilot"?Convert.ToInt32(manifest["pilot_clubs"]):expectedClubs),"Italy roster coverage differs");
   }
   if(B7Text(manifest,"stage")=="pilot")wanted.IntersectWith(identities.Select(x=>N4I(x,"PlayingClubIndex")));
  }
  var id90=identities.ToDictionary(x=>N4I(x,"ID90"));var loans=loanRows.ToDictionary(x=>N4I(x,"ID90"));
  var pair=new Dictionary<int,Dictionary<string,string>>();
  // Identity rows are positional partners of the native CSV; every UID and destination is verified independently.
  for(int i=0;i<rows.Count;i++){var r=rows[i];var ident=identities[i];int id=N4I(ident,"ID90");Require(N4I(r,"ExistingID")==N4I(ident,"ExistingID")&&N4I(r,"ClubIndex")==N4I(ident,"OwnerClubIndex")&&r["BirthDate"]==ident["TargetDOB"]&&clubsPlan.ContainsKey(N4I(ident,"PlayingClubIndex")),"CSV/identity pairing differs at "+i);pair.Add(id,r);}
  foreach(var r in rows.Where(x=>N4I(x,"ExistingID")<0))Require(!string.IsNullOrWhiteSpace(r["FirstName"])&&!string.IsNullOrWhiteSpace(r["LastName"])&&r["FirstName"].Length<=120&&r["LastName"].Length<=120,"New native names require supported nonempty first/surname: "+r["FirstName"]+" "+r["LastName"]);
  Console.WriteLine("PASS: pinned manifest/CSV pairing, scope="+scope+"; rows="+rows.Count);
  foreach(var l in loans){Require(id90.ContainsKey(l.Key),"Loan has no roster subject");var x=l.Value;string buy=x["BuyType"].Trim().ToLowerInvariant();Require(new[]{"optional","none","unknown"}.Contains(buy),"Mandatory/unsupported buy type rejected");Require(N4I(x,"OwnerClubIndex")==N4I(id90[l.Key],"OwnerClubIndex")&&N4I(x,"LoanClubIndex")==N4I(id90[l.Key],"PlayingClubIndex")&&N4I(x,"OwnerClubIndex")!=N4I(x,"LoanClubIndex"),"Loan ownership/destination mismatch");Require(B7Date(x["NativeStartDate"])<=B7Date(x["NativeEndDate"])&&!string.IsNullOrWhiteSpace(x["SourceURL"]),"Invalid loan dates/evidence");string fee=x["FeeToBuyNative"];if(!string.IsNullOrWhiteSpace(fee)&&fee!="-1"){Require(buy=="optional"&&int.Parse(fee,CultureInfo.InvariantCulture)>0&&x["FeeConversionStatus"]=="verified_native_currency","Unverified or inapplicable optional fee");}}
  byte[] people=Load(source,"people_db.dat"),server=Load(source,"server_db.dat"),client=Load(source,"client_db.dat");byte[] oldPeople=(byte[])people.Clone(),oldServer=(byte[])server.Clone(),oldClient=(byte[])client.Clone();
  int oldCount=BitConverter.ToInt32(people,0),oldPers=BitConverter.ToInt32(people,4),oldAttrs=BitConverter.ToInt32(people,8);
  var clubs=(Dictionary<int,string>)Call("ParseClubs",server);var nations=(Dictionary<int,string>)Call("ParseNations",server);var players=ReadPlayers(people,server,clubs,nations);var byUid=players.ToDictionary(x=>x.Id);
  var records=FM08_Database_Editor.ParseNativeClubDivisions(server,oldCount);var owners=new HashSet<int>(identities.Select(x=>N4I(x,"OwnerClubIndex")));Require(owners.All(x=>x>=0&&records.ContainsKey(x)),"Unknown owner TEAM");
  var families=FM08_Database_Editor.ResolveNativeClubContractReferences(server,oldCount,map.Select(x=>N4I(x,"TeamIndex")).Union(owners));
  N4Save(Path.Combine(prepared,"native-contract-resolution.json"),families.ToDictionary(k=>k.Key.ToString(),k=>k.Value));
  if(countryScoped){
   string proofs=B7File(prepared,"club_proofs.csv");B7PinFile(proofs,"club_proofs_sha256",manifest);
   var clubProofs=B7Rows(proofs).ToDictionary(x=>N4I(x,"TeamIndex"));
   Require(map.Select(x=>N4I(x,"TeamIndex")).Union(owners).All(clubProofs.ContainsKey),"Missing Italy/foreign owner proof");
   foreach(var c in clubProofs){
    var x=c.Value;int ti=c.Key,off=N4I(x,"CountryOffset"),foot=N4I(x,"FamilyFooter");
    Require(records.ContainsKey(ti)&&BitConverter.ToInt32(server,records[ti].Footer+4)==N4I(x,"ClubUID"),"Foreign/target TEAM UID differs");
    Require(off>0&&off+4<=server.Length&&server[off-1]==0&&BitConverter.ToInt32(server,off)==N4I(x,"CountryIndex")&&BitConverter.ToInt32(server,foot)==N4I(x,"FamilyIndex")&&BitConverter.ToInt32(server,foot+4)==N4I(x,"FamilyUID"),"Country/family witness differs");
    if(families.ContainsKey(ti))Require(families[ti]==N4I(x,"FamilyIndex"),"Contract family differs from witnessed identity: TEAM="+ti+" UID="+x["ClubUID"]+" resolved="+families[ti]+" witnessed="+x["FamilyIndex"]);
    if(clubsPlan.ContainsKey(ti)){if(x10){var cp=clubsPlan[ti];int ci=N4I(cp,"CountryIndex");Require(N4I(x,"CountryIndex")==ci&&((cp["Country"]=="Portugal"&&ci==162)||(cp["Country"]=="Norway"&&ci==160)||(cp["Country"]=="Peru"&&ci==194)),"Foreign country in X14 target");}else if(x7){var cp=clubsPlan[ti];int ci=N4I(cp,"CountryIndex");Require(N4I(x,"CountryIndex")==ci&&((cp["Country"]=="Scotland"&&ci==167)||(cp["Country"]=="Slovakia"&&ci==168)||(cp["Country"]=="Slovenia"&&ci==169)||(cp["Country"]=="Singapore"&&ci==79)),"Foreign country in X7 target");}else if(x3){var cp=clubsPlan[ti];int ci=N4I(cp,"CountryIndex");Require(N4I(x,"CountryIndex")==ci&&((cp["Country"]=="Sweden"&&ci==171)||(cp["Country"]=="Switzerland"&&ci==172)||(cp["Country"]=="Liechtenstein"&&ci==152)||(cp["Country"]=="Ukraine"&&ci==174&&N4I(cp,"ClubUID")==1895)),"Foreign country in X3 target");}else if(x2){var cp=clubsPlan[ti];int ci=N4I(cp,"CountryIndex");Require(N4I(x,"CountryIndex")==ci&&((cp["Country"]=="Ukraine"&&ci==174)||(cp["Country"]=="Turkey"&&ci==173)||(cp["Country"]=="USA"&&ci==120)),"Foreign country in X2 target");}else if(three){var cp=clubsPlan[ti];int ci=N4I(cp,"CountryIndex");Require(N4I(x,"CountryIndex")==ci&&((cp["Country"]=="Wales"&&ci==175)||(cp["Country"]=="Uruguay"&&ci==195)||(cp["Country"]=="USA"&&(ci==120||ci==97))),"Foreign country in B1 target");}else Require(N4I(x,"CountryIndex")==targetCountry,"Foreign country in Italy target");}
   }
  }
  FM08_Database_Editor.ClubsRev.Clear();foreach(var c in clubs)if(!string.IsNullOrWhiteSpace(c.Value)&&!FM08_Database_Editor.ClubsRev.ContainsKey(c.Value))FM08_Database_Editor.ClubsRev[c.Value]=c.Key;
  foreach(var c in map){int ti=N4I(c,"TeamIndex");Require(records.ContainsKey(ti)&&BitConverter.ToInt32(server,records[ti].Footer+4)==N4I(c,"ClubUID")&&records[ti].CurrentDivisionIndex==N4I(c,"DivisionIndex")&&families[ti]==N4I(c,"FamilyIndex"),"Club UID/division/family differs: "+ti);clubs[ti]=c["ClubName"];FM08_Database_Editor.ClubsRev[c["ClubName"]]=ti;}
  foreach(int o in owners){string label="__VERIFIED_OWNER_"+o.ToString(CultureInfo.InvariantCulture);FM08_Database_Editor.ClubsRev[label]=o;}
  FM08_Database_Editor.NationsRev.Clear();foreach(var n in nations)if(!FM08_Database_Editor.NationsRev.ContainsKey(n.Value))FM08_Database_Editor.NationsRev[n.Value]=n.Key;FM08_Database_Editor.InitCsvRegistry();
  var nationalityRepairs=new HashSet<int>();var reused=new HashSet<int>();var legacy=new HashSet<int>();var uidBy90=new Dictionary<int,int>();
  foreach(var x in identities){int u=N4I(x,"ExistingID"),id=N4I(x,"ID90");Require(loans.ContainsKey(id)||N4I(x,"OwnerClubIndex")==N4I(x,"PlayingClubIndex"),"Non-loan owner differs");if(u<0)continue;Require(reused.Add(u)&&byUid.ContainsKey(u),"Duplicate/missing reused UID");var p=byUid[u];Require(p.FirstName==x["ExpectedFirstName"]&&p.LastName==x["ExpectedLastName"]&&p.BirthDate.HasValue&&p.BirthDate.Value.ToString("yyyy-MM-dd")==x["ExpectedDOB"]&&(p.ClubIdOffset>0?p.ClubId:-1)==N4I(x,"ExpectedClubIndex")&&p.CA==N4I(x,"ExistingCA")&&p.PA==N4I(x,"ExistingPA"),"Stale reused identity: "+u);
   Require(rows[identities.IndexOf(x)]["FirstName"]==p.FirstName&&rows[identities.IndexOf(x)]["LastName"]==p.LastName,"Reused name change is not authorized");
   string targetNation=rows[identities.IndexOf(x)]["Nationality"];
   if(p.Nationality!=targetNation){
    Require((hungary||three||x2||x3||x7||x10)&&manifest.ContainsKey("nationality_repairs"),"Nationality correction requires an explicit scoped witness");
    var repairs=(Dictionary<string,object>)manifest["nationality_repairs"];Require(repairs.ContainsKey(u.ToString()),"Unwitnessed nationality correction");
    var repair=(Dictionary<string,object>)repairs[u.ToString()];Require(Convert.ToString(repair["expected_native_nation"])==p.Nationality&&Convert.ToString(repair["target_native_nation"])==targetNation&&!string.IsNullOrWhiteSpace(Convert.ToString(repair["source_url"]))&&nations.Values.Contains(targetNation)&&p.NationIdOffset==p.BirthDateOffset+5,"Nationality correction witness or raw layout differs");nationalityRepairs.Add(u);
   }

   DateTime target=B7Date(x["TargetDOB"]);if(target!=p.BirthDate.Value){if(p.BirthDate.Value.AddYears(-19)!=target){
    Require(countryScoped&&manifest.ContainsKey("dob_repairs"),"DOB repair must be explicit");
    var repairs=(Dictionary<string,object>)manifest["dob_repairs"];Require(repairs.ContainsKey(u.ToString()),"Unapproved DOB correction");
    var repair=(Dictionary<string,object>)repairs[u.ToString()];Require(Convert.ToString(repair["expected_native_dob"])==x["ExpectedDOB"]&&Convert.ToString(repair["target_native_dob"])==x["TargetDOB"]&&!string.IsNullOrWhiteSpace(Convert.ToString(repair["source_url"])),"DOB correction witness differs");
   }legacy.Add(u);}uidBy90[id]=u;}
  var duplicate=B7Ints(manifest,"duplicate_retire_uids");Require(duplicate.All(u=>byUid.ContainsKey(u)&&!reused.Contains(u)),"Retirement list missing/overlaps confirmed subject");
  var oldLoans=FM08_Database_Editor.ParseNativeLoans(server,oldCount);var sourceOwner=players.ToDictionary(x=>BitConverter.ToInt32(people,x.PersonOffset-15),x=>x.ClubIdOffset>0?x.ClubId:-1);
  var outbound=new HashSet<int>(oldLoans.Where(x=>sourceOwner.ContainsKey(x.PersonIndex)&&wanted.Contains(sourceOwner[x.PersonIndex])&&sourceOwner[x.PersonIndex]!=x.ClubId).Select(x=>x.PersonIndex));
  var releases=new HashSet<int>(players.Where(x=>wanted.Contains(x.ClubId)&&!reused.Contains(x.Id)&&!duplicate.Contains(x.Id)&&!outbound.Contains(BitConverter.ToInt32(people,x.PersonOffset-15))).Select(x=>x.Id));
  if(countryScoped){
   var cleanup=B7Rows(B7File(prepared,"cleanup_subjects.csv"));
   B7PinFile(B7File(prepared,"cleanup_subjects.csv"),"cleanup_subjects_sha256",manifest);
   if(B7Text(manifest,"stage")!="pilot")foreach(var x in cleanup){
    int u=N4I(x,"UID");Require(byUid.ContainsKey(u)&&byUid[u].ClubId==N4I(x,"ExpectedOwner")&&byUid[u].FirstName==x["FirstName"]&&byUid[u].LastName==x["LastName"]&&byUid[u].BirthDate.Value.ToString("yyyy-MM-dd")==x["ExpectedDOB"]&&N4I(x,"ExpectedOwner")==10097,"Entella cleanup provenance differs");
    if(!reused.Contains(u))releases.Add(u);
   }
   var earlyPreserve=B7Ints(manifest,"preserve_absent_uids");Require(earlyPreserve.All(byUid.ContainsKey),"Preserved UID missing");releases.ExceptWith(earlyPreserve);
   var protectedUids=B7Ints(manifest,"protected_player_uids");Require(!protectedUids.Overlaps(reused.Union(releases).Union(duplicate)),"Italy conflicts with protected prior import");
   var duplicateProofs=(Dictionary<string,object>)manifest["duplicate_proofs"];Require(duplicateProofs.Count==duplicate.Count,"Unwitnessed technical duplicate list");
   foreach(int u in duplicate){
    Require(duplicateProofs.ContainsKey(u.ToString()),"Missing duplicate proof");var z=(Dictionary<string,object>)duplicateProofs[u.ToString()];int canonical=Convert.ToInt32(z["canonical_uid"]);var d=byUid[u];
    Require(reused.Contains(canonical)&&canonical!=u&&d.FirstName==Convert.ToString(z["expected_first"])&&d.LastName==Convert.ToString(z["expected_last"])&&d.BirthDate.Value.ToString("yyyy-MM-dd")==Convert.ToString(z["expected_dob"])&&!string.IsNullOrWhiteSpace(Convert.ToString(z["source_url"])),"Technical duplicate identity proof differs");
    DateTime target=B7Date(Convert.ToString(z["target_dob"]));Require(d.BirthDate.Value==target||d.BirthDate.Value.AddYears(-19)==target,"Technical duplicate is not the same DOB phase");
    Require(identities.Any(v=>N4I(v,"ExistingID")==canonical&&B7Date(v["TargetDOB"])==target),"Duplicate canonical target DOB differs");
   }
   var preserve=B7Ints(manifest,"preserve_absent_uids");Require(preserve.All(byUid.ContainsKey),"Preserved source-gap UID missing");releases.ExceptWith(preserve);
  }
  if(x10){var es=B7Ints(manifest,"structural_only_club_uids");var et=new HashSet<int>(map.Where(x=>es.Contains(N4I(x,"ClubUID"))).Select(x=>N4I(x,"TeamIndex")));Require(!players.Any(p=>et.Contains(p.ClubId)&&releases.Contains(p.Id)),"Structural-only club roster must be preserved");}
  var actors=new HashSet<int>(reused.Union(releases).Union(duplicate));var before=actors.ToDictionary(u=>u,u=>N4Evidence(people,byUid[u]));
  var updatePersons=new HashSet<int>(actors.Select(u=>BitConverter.ToInt32(people,byUid[u].PersonOffset-15)));var replacedLoans=oldLoans.Where(x=>updatePersons.Contains(x.PersonIndex)).ToList();
  if(replacedLoans.Count>0){Require(manifest.ContainsKey("allow_replace_subject_loans")&&Convert.ToBoolean(manifest["allow_replace_subject_loans"]),"Existing subject loans require explicit replacement policy");server=FM08_Database_Editor.RemoveNativeLoans(server,oldCount,updatePersons);}
  var retirementBefore=FM08_Database_Editor.ParseRetirements(server);
  if(duplicate.Count>0){
   var contractedDuplicate=new HashSet<int>(duplicate.Where(u=>byUid[u].ClubIdOffset>0));
   if(contractedDuplicate.Count>0)FM08_Database_Editor.RetireNativePlayersBulk(ref people,ref server,players,contractedDuplicate,(x2||x3||x7||x10)?new DateTime(2006,1,1):new DateTime(2007,7,1));
   var freeDuplicate=players.Where(p=>duplicate.Contains(p.Id)&&!contractedDuplicate.Contains(p.Id)).ToList();
   foreach(var p in freeDuplicate){Require(before[p.Id].Length==0,"Unowned duplicate has a contract");DateTime d;p.RetirementDate=(x2||x3||x7||x10)?new DateTime(2006,1,1):(retirementBefore.TryGetValue(p.Id,out d)?d:new DateTime(2007,7,1));}
   if(freeDuplicate.Count>0)server=FM08_Database_Editor.SyncRetirements(server,freeDuplicate);
  }
  var revive=players.Where(x=>reused.Contains(x.Id)&&retirementBefore.ContainsKey(x.Id)).ToList();foreach(var p in revive)p.RetirementDate=null;if(revive.Count>0)server=FM08_Database_Editor.SyncRetirements(server,revive);
  var estimates=new List<object>();
  foreach(var x in identities.Where(x=>N4I(x,"ExistingID")>0)){int u=N4I(x,"ExistingID"),id=N4I(x,"ID90");var p=byUid[u];var r=pair[id];p.Club="__VERIFIED_OWNER_"+x["OwnerClubIndex"];p.ClubAssignmentPending=true;
   if(!loans.ContainsKey(id))p.SquadNumber=byte.Parse(r["SquadNumber"],CultureInfo.InvariantCulture);p.ContractDetailsPending=true;
   if(legacy.Contains(u))FM08_Database_Editor.UpdatePlayerBirthDate(p,people,B7Date(x["TargetDOB"]));
   if(nationalityRepairs.Contains(u))FM08_Database_Editor.UpdatePlayerNation(p,people,r["Nationality"]);
   if(before[u].Length==0||!p.ContractExpires.HasValue||p.ContractExpires.Value<new DateTime(2007,7,1)){p.ContractExpires=new DateTime(2010,6,30);p.ContractExpiresPending=true;if(before[u].Length==0)p.WeeklyWage=N4I(r,"WeeklyWage");estimates.Add(new{uid=u,field="ContractExpires",value="2010-06-30",precision="technical_estimate"});}
  }
  foreach(int u in releases){var p=byUid[u];p.Club="";p.ClubAssignmentPending=true;}
  Console.WriteLine("Validated source identities; applying native owners/contracts; reused="+reused.Count+", released="+releases.Count);
  FM08_Database_Editor.SyncClubAssignmentsBulk(ref people,ref server,players);
  Console.WriteLine("PASS: native owner/contract updates");
  var newPlayers=new List<P>();var targets=new Dictionary<P,int>();var newIds90=new List<int>();var uniqueIdentity=new HashSet<string>(players.Where(p=>!duplicate.Contains(p.Id)).Select(N4Id));
  foreach(var x in identities.Where(x=>N4I(x,"ExistingID")<0)){int id=N4I(x,"ID90");var p=new P{Id=-1};SetProfile(p,pair[id]);Require(nations.Values.Contains(p.Nationality)&&uniqueIdentity.Add(N4Id(p)),"New duplicate/unknown nationality: "+id);p.Club="__VERIFIED_OWNER_"+x["OwnerClubIndex"];newPlayers.Add(p);newIds90.Add(id);targets[p]=N4I(x,"OwnerClubIndex");}
  var pool=new IdPool(x10?1702000000:x7?1694000000:x3?1692000000:x2?1689000000:three?1687000000:hungary?1685000000:italy?1683000000:1681000000,x10?1704000000:x7?1696000000:x3?1694000000:x2?1691000000:three?1689000000:hungary?1687000000:italy?1685000000:1683000000,people,server,client);AppendBatch(ref people,ref server,ref client,newPlayers,players,targets,pool);
  Console.WriteLine("PASS: new native PERSON/name/attribute/personality batch; added="+newPlayers.Count);
  for(int i=0;i<newPlayers.Count;i++)uidBy90[newIds90[i]]=newPlayers[i].Id;
  int newCount=BitConverter.ToInt32(people,0);records=FM08_Database_Editor.ParseNativeClubDivisions(server,newCount);var rosters=owners.ToDictionary(o=>o,o=>Roster(server,records[o]));
  foreach(var p in newPlayers)Require(rosters[targets[p]].Add(BitConverter.ToInt32(people,p.PersonOffset-15)),"Repeated new roster person");RewriteRosters(ref server,newCount,rosters);
  var afterPlayers=ReadPlayers(people,server,clubs,nations);var afterUid=afterPlayers.ToDictionary(p=>p.Id);var loanPool=new IdPool(x10?1814000000:x7?1808000000:x3?1807000000:x2?1805000000:three?1804000000:hungary?1803000000:italy?1802000000:1801000000,x10?1815000000:x7?1809000000:x3?1808000000:x2?1806000000:three?1805000000:hungary?1804000000:italy?1803000000:1802000000,people,server,client);var loanRequests=new List<FM08_Database_Editor.NativeLoanWriteRequest>();
  foreach(var l in loans){var x=l.Value;var p=afterUid[uidBy90[l.Key]];string fee=x["FeeToBuyNative"];int? raw=string.IsNullOrWhiteSpace(fee)?(int?)null:int.Parse(fee,CultureInfo.InvariantCulture);loanRequests.Add(new FM08_Database_Editor.NativeLoanWriteRequest{PersonIndex=BitConverter.ToInt32(people,p.PersonOffset-15),ClubId=N4I(x,"LoanClubIndex"),UniqueId=loanPool.Allocate(1),StartDate=B7Date(x["NativeStartDate"]),EndDate=B7Date(x["NativeEndDate"]),FeeToBuyRaw=raw,SquadNumber=byte.Parse(pair[l.Key]["SquadNumber"],CultureInfo.InvariantCulture),
   WageContribution=x.ContainsKey("WagePercent")&&!string.IsNullOrWhiteSpace(x["WagePercent"])?(byte?)byte.Parse(x["WagePercent"],CultureInfo.InvariantCulture):null,
   CanBeRecalled=x.ContainsKey("Recall")&&!string.IsNullOrWhiteSpace(x["Recall"])?(bool?)bool.Parse(x["Recall"]):null});}
  server=FM08_Database_Editor.ApplyNativeLoans(server,newCount,loanRequests);pool.Verify(people,server,client);loanPool.Verify(people,server,client);
  var after=actors.ToDictionary(u=>u,u=>B7AfterEvidence(people,afterUid[u],before[u],prepared));foreach(int u in actors)B7ActorProof(oldPeople,people,before[u],after[u],releases.Contains(u)||duplicate.Contains(u),legacy.Contains(u),nationalityRepairs.Contains(u));
  int oa=AttributesStart(oldPeople),na=AttributesStart(people),oh=oa-8-oldPers*17,nh=na-8-(oldPers+newPlayers.Count)*17;EqualRange(oldPeople,oa,people,na,oldAttrs*89,"all old 89B attributes");EqualRange(oldPeople,oh+4,people,nh+4,oldPers*17,"all old 17B personalities");
  int pc=16,nc=16;foreach(var x in before.Values.OrderBy(x=>x.Start)){var y=after[x.Uid];Require(x.Start-pc==y.Start-nc,"Non-subject PERSON gap length differs");EqualRange(oldPeople,pc,people,nc,x.Start-pc,"all non-subject PERSON gaps");pc=x.End;nc=y.End;}Require(oh-pc==nh-newPlayers.Count*299-nc,"Last PERSON gap length differs");EqualRange(oldPeople,pc,people,nc,oh-pc,"last protected PERSON gap");
  var rosterProof=N4RosterProof(oldServer,server,oldCount,newCount);var retired=FM08_Database_Editor.ParseRetirements(server);Require(duplicate.All(retired.ContainsKey)&&reused.All(u=>!retired.ContainsKey(u)),"Retirement result differs");foreach(var r in retirementBefore)if(!duplicate.Contains(r.Key)&&!reused.Contains(r.Key))Require(retired.ContainsKey(r.Key)&&retired[r.Key]==r.Value,"Unrelated retirement changed");Require(retired.Keys.All(u=>retirementBefore.ContainsKey(u)||duplicate.Contains(u)),"Unexpected new retirement");
  B7Pins(source,manifest);B7PinFile(csv,"csv_sha256",manifest);B7PinFile(mapfile,"club_map_sha256",manifest);B7PinFile(idfile,"identities_sha256",manifest);B7PinFile(loanfile,"loans_sha256",manifest);
  if(validateOnly){Console.WriteLine("BUFFER_SHA256 people="+B7BufferHash(people)+" server="+B7BufferHash(server)+" client="+B7BufferHash(client));Console.WriteLine("PASS: validate-only full in-memory scoped batch; no output created; rows="+rows.Count+", new="+newPlayers.Count+", reused="+reused.Count+", releases="+releases.Count+", loans="+loans.Count);return;}
  Directory.CreateDirectory(output);foreach(string f in Directory.GetFiles(source,"*",SearchOption.AllDirectories)){string rel=f.Substring(source.Length+1);if(Path.GetExtension(rel).Equals(".xml",StringComparison.OrdinalIgnoreCase)&&string.IsNullOrEmpty(Path.GetDirectoryName(rel)))continue;string dest=Path.Combine(output,rel);Directory.CreateDirectory(Path.GetDirectoryName(dest));File.Copy(f,dest);}
  foreach(var b in new Dictionary<string,byte[]>{{"people_db.dat",people},{"server_db.dat",server},{"client_db.dat",client}})File.WriteAllBytes(Path.Combine(output,b.Key),(byte[])Call("CompressFile",b.Value,(byte[])Call("GetFileHeader",Path.Combine(source,b.Key))));FM08_Database_Editor.WriteDatabaseMetadata(source,output);
  // Actual disk reload independently re-parses every current identity, owner, main contract and loan destination.
  byte[] dp=Load(output,"people_db.dat"),ds=Load(output,"server_db.dat");var diskPlayers=ReadPlayers(dp,ds,clubs,nations).ToDictionary(p=>p.Id);var diskClubs=FM08_Database_Editor.ParseNativeClubDivisions(ds,newCount);var diskLoans=FM08_Database_Editor.ParseNativeLoans(ds,newCount);var diskRefs=FM08_Database_Editor.ResolveNativeClubContractReferences(ds,newCount,owners);var evidence=new List<object>();
  foreach(var x in identities){int id=N4I(x,"ID90"),owner=N4I(x,"OwnerClubIndex"),playing=N4I(x,"PlayingClubIndex"),uid=uidBy90[id];var p=diskPlayers[uid];var row=pair[id];var e=N4Evidence(dp,p);int pi=BitConverter.ToInt32(dp,p.PersonOffset-15);int ca=N4I(x,"ExistingID")>0?N4I(x,"ExistingCA"):N4I(row,"CA"),pa=N4I(x,"ExistingID")>0?N4I(x,"ExistingPA"):N4I(row,"PA");Require(p.FirstName==row["FirstName"]&&p.LastName==row["LastName"]&&p.BirthDate.HasValue&&p.BirthDate.Value==B7Date(x["TargetDOB"])&&p.ClubId==owner&&p.CA==ca&&p.PA==pa&&p.Nationality==row["Nationality"],"Disk identity/owner/profile differs: "+id);Require(e.Payload>=0&&BitConverter.ToInt32(dp,e.Payload+31)==diskRefs[owner]&&BitConverter.ToInt32(dp,e.Payload+26)==pi&&Roster(ds,diskClubs[owner]).Contains(pi),"Disk main contract/owner roster differs: "+id);
   if(loans.ContainsKey(id)){var lr=loanRequests.Single(z=>z.PersonIndex==pi);var actual=diskLoans.Where(z=>z.PersonIndex==pi&&z.ClubId==playing).ToList();Require(actual.Count==1&&actual[0].StartDate==lr.StartDate&&actual[0].EndDate==lr.EndDate&&actual[0].FeeToBuyRaw==(lr.FeeToBuyRaw??-1)&&!Roster(ds,diskClubs[playing]).Contains(pi),"Disk loan dates/fee/borrower ownership differs: "+id);}else Require(p.SquadNumber==N4I(row,"SquadNumber"),"Disk permanent shirt differs");
   evidence.Add(new{id90=id,uid,person=pi,owner,playing,first=p.FirstName,last=p.LastName,dob=x["TargetDOB"],CA=p.CA,PA=p.PA,start=e.Start,end=e.End,owner_offset=e.Owner,contract=e.Contract,payload=e.Payload,length=e.Length});
  }
  var diskRetired=FM08_Database_Editor.ParseRetirements(ds);foreach(int u in releases)Require(diskPlayers[u].ClubIdOffset==0&&diskRetired.ContainsKey(u)==retirementBefore.ContainsKey(u),"Released player owner/retirement differs");
  N4Save(Path.Combine(prepared,"full-native.json"),new{status="pass",source,output,rows=rows.Count,clubs=map.Count,added=newPlayers.Count,reused=reused.Count,released=releases.Count,loans=loans.Count,original_count=oldCount,new_count=newCount,original_personalities=oldPers,original_attributes=oldAttrs,old_personality_header=oh,new_personality_header=nh,old_attributes_start=oa,new_attributes_start=na,subjects=evidence,actor_before=before.Values,actor_after=after.Values,released_uids=releases,duplicate_retire_uids=duplicate,revived_uids=revive.Select(p=>p.Id).ToArray(),technical_estimates=estimates,nationality_repair_uids=nationalityRepairs,contracting_family=families.ToDictionary(x=>x.Key.ToString(),x=>x.Value),name_before=N4Names(oldServer,oldClient),name_after=N4Names(server,client),retire_before=N4RetireLayout(oldServer),retire_after=N4RetireLayout(server),loan_table_before=Call("FindNativeLoanTable",oldServer,oldCount),loan_table_after=Call("FindNativeLoanTable",server,newCount),loan_count_before=oldLoans.Count,loan_count_after=diskLoans.Count,replaced_loan_records=replacedLoans.Select(x=>x.RecordIndex).ToArray(),loan_requests=loanRequests,roster_changes=rosterProof,all_old_personalities_attributes_preserved=true,all_non_subject_PERSON_bytes_preserved=true,source_hashes=manifest["source_hashes"]});
  B7Pins(source,manifest);Console.WriteLine("PASS: full batch, actual reload, all old attributes/personalities, non-subject PERSON gaps, TEAM prefix/suffix; rows="+rows.Count+", new="+newPlayers.Count+", reused="+reused.Count+", loans="+loans.Count);
 }
}
