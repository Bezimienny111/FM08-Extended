"""Compile only X10 scope wrapper from checked shared worker; never rebuild main editor."""
from x10_pipeline import *
def main():
 d=ROOT/'FM08-Database-Tools/scratch';out=B/'tools';worker=d/'ApplyPolandRosterBatch.cs';s=worker.read_text(encoding='utf-8')
 replacements=[
 ('scope=="x7108","Unsupported roster scope"','scope=="x7108"||scope=="x10154","Unsupported roster scope"'),
 ('x7=scope=="x7108",countryScoped=italy||hungary||three||x2||x3||x7;int expectedClubs=x7?108:','x7=scope=="x7108",x10=scope=="x10154",countryScoped=italy||hungary||three||x2||x3||x7||x10;int expectedClubs=x10?154:x7?108:'),
 ('int targetCountry=(three||x2||x3||x7)?-1:','int targetCountry=(three||x2||x3||x7||x10)?-1:'),
 ('(x7?"sco-svk-svn-sin-x7":','(x10?"ser-rom-rsa-rus-x10":x7?"sco-svk-svn-sin-x7":'),
 ('   if(x7)Require(B7Ints(manifest,"target_country_indices")','   if(x10)Require(B7Ints(manifest,"target_country_indices").SetEquals(new[]{176,164,40,165}),"Wrong X10 country set");\n   if(x7)Require(B7Ints(manifest,"target_country_indices")'),
 ('(hungary||three||x2||x3||x7)&&manifest.ContainsKey("nationality_repairs")','(hungary||three||x2||x3||x7||x10)&&manifest.ContainsKey("nationality_repairs")'),
 ('(x2||x3||x7)?new DateTime','(x2||x3||x7||x10)?new DateTime'),
 ('new IdPool(x7?1694000000:','new IdPool(x10?1698000000:x7?1694000000:'),
 (',x7?1696000000:',',x10?1700000000:x7?1696000000:'),
 ('new IdPool(x7?1808000000:','new IdPool(x10?1810000000:x7?1808000000:'),
 (',x7?1809000000:',',x10?1811000000:x7?1809000000:')]
 for a,b in replacements:
  assert a in s,a;s=s.replace(a,b)
 old='if(clubsPlan.ContainsKey(ti)){if(x7){'
 new='if(clubsPlan.ContainsKey(ti)){if(x10){var cp=clubsPlan[ti];int ci=N4I(cp,"CountryIndex");Require(N4I(x,"CountryIndex")==ci&&((cp["Country"]=="Serbia"&&ci==176)||(cp["Country"]=="Romania"&&ci==164)||(cp["Country"]=="South Africa"&&ci==40)||(cp["Country"]=="Russia"&&ci==165)),"Foreign country in X10 target");}else if(x7){'
 assert old in s;s=s.replace(old,new)
 old='   Require(identities.Select(x=>N4I(x,"PlayingClubIndex")).Where(wanted.Contains).Distinct().Count()==(B7Text(manifest,"stage")=="pilot"?Convert.ToInt32(manifest["pilot_clubs"]):expectedClubs),"Italy roster coverage differs");'
 new="""   if(x10){
    var empty=B7Ints(manifest,"structural_only_club_uids");Require(empty.IsSubsetOf(declared),"Structural-only UID outside target map");
    var emptyTeams=new HashSet<int>(map.Where(x=>empty.Contains(N4I(x,"ClubUID"))).Select(x=>N4I(x,"TeamIndex")));
    var actorTeams=new HashSet<int>(identities.Select(x=>N4I(x,"PlayingClubIndex")));
    Require(!actorTeams.Overlaps(emptyTeams),"Declared structural-only club has actors");
    if(B7Text(manifest,"stage")=="full")Require(actorTeams.SetEquals(wanted.Except(emptyTeams)),"Unlisted empty club or incomplete X10 actor coverage");
    else Require(actorTeams.Count==Convert.ToInt32(manifest["pilot_clubs"]),"X10 pilot actor coverage differs");
   }else{
"""+old+"""
   }"""
 assert old in s;s=s.replace(old,new)
 # Structural-only existing clubs must have every original member explicitly protected from cleanup.
 old='  var actors=new HashSet<int>(reused.Union(releases).Union(duplicate));'
 new='  if(x10){var es=B7Ints(manifest,"structural_only_club_uids");var et=new HashSet<int>(map.Where(x=>es.Contains(N4I(x,"ClubUID"))).Select(x=>N4I(x,"TeamIndex")));Require(!players.Any(p=>et.Contains(p.ClubId)&&releases.Contains(p.Id)),"Structural-only club roster must be preserved");}\n'+old
 assert old in s;s=s.replace(old,new)
 ws=out/'ApplyPolandRosterBatch-X10.cs';ws.write_text(s,encoding='utf-8')
 wrapper=(d/'ApplyX7RosterBatch.cs').read_text(encoding='utf-8').replace('ApplyX7RosterBatch','ApplyX10RosterBatch').replace('X7RosterBatch','X10RosterBatch').replace('"x7108"','"x10154"');q=out/'ApplyX10RosterBatch.cs';q.write_text(wrapper,encoding='utf-8')
 sources=list(d.glob('*NativeSquads.cs'))+[d/'PolandSquadsN4.cs',d/'RepairNativeContracts.cs',ws,q]
 editor=out/'FM08_Database_Editor.exe';assert hashlib.sha256(editor.read_bytes()).hexdigest()==read(B/'manifest.json')['editor_sha256']
 args=['C:/Windows/Microsoft.NET/Framework/v4.0.30319/csc.exe','/nologo','/optimize+','/platform:x64','/target:exe','/main:ApplyX10RosterBatch','/out:'+str(out/'ApplyX10RosterBatch.exe'),'/r:System.Windows.Forms.dll','/r:System.Drawing.dll','/r:System.Xml.dll','/r:System.Web.Extensions.dll','/r:'+str(editor)]+list(map(str,sources))
 z=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace');(out/'roster-build.log').write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,z.stdout+z.stderr
 dump(out/'roster-build-manifest.json',dict(scope='x10154',scope_id='ser-rom-rsa-rus-x10',target_country_indices=[176,164,40,165],target_clubs=154,editor_rebuilt=False,editor_sha256=hashlib.sha256(editor.read_bytes()).hexdigest(),sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sources},binaries={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in [editor,out/'ApplyX10RosterBatch.exe']},explicit_structural_only_semantics=True,uid_ranges={'new_players':[1698000000,1700000000],'loans':[1810000000,1811000000]},validation_status='compiled_only_pilot_and_negative_tests_pending'))
 print('X10 SCOPE ADAPTER COMPILED; editor unchanged, pilot/negative pending.',flush=True)
if __name__=='__main__':main()
