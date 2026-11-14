from pathlib import Path
import json,hashlib,subprocess,shutil,sys
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;T=B/'tools';T.mkdir(exist_ok=True)
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 app=read(R/'PERSONALITY_CODEC_REPAIR_20261111/root-applied/application.json');assert app['status']=='APPLIED_MAIN_REBUILT_TESTS_PASS'
 editor=Path(app['editor']);assert H(editor).upper()==app['binaries']['FM08_Database_Editor.exe']
 dest=T/'FM08_Database_Editor.exe'
 if dest.exists():assert H(dest)==H(editor)
 else:shutil.copyfile(editor,dest)
 for file,pin in app['source_files'].items():assert H(ROOT/file).upper()==pin
 checked=R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/tools/ApplyPolandRosterBatch-X10.cs'
 s=checked.read_text(encoding='utf-8')
 assert 'int expectedClubs=x10?154:'in s
 s=s.replace('scope=="x10154"','scope=="x14292"').replace('expectedClubs=x10?154:','expectedClubs=x10?292:').replace('ser-rom-rsa-rus-x10','por-per-nor-pol-gaps-x14').replace('new[]{176,164,40,165}','new[]{162,160,194}')
 old='((cp["Country"]=="Serbia"&&ci==176)||(cp["Country"]=="Romania"&&ci==164)||(cp["Country"]=="South Africa"&&ci==40)||(cp["Country"]=="Russia"&&ci==165))'
 new='((cp["Country"]=="Portugal"&&ci==162)||(cp["Country"]=="Norway"&&ci==160)||(cp["Country"]=="Peru"&&ci==194))'
 assert old in s;s=s.replace(old,new)
 for old,new in [('x10?1698000000:','x10?1702000000:'),('x10?1700000000:','x10?1704000000:'),('x10?1810000000:','x10?1814000000:'),('x10?1811000000:','x10?1815000000:')]:
  assert old in s,old;s=s.replace(old,new)
 s=s.replace('X10','X14')
 s=s.replace('try{return N4Evidence(people,p);}catch(Exception e){', '''// Free variable-prefix PERSON has no parsed ClubIdOffset. Use the exact proven source boundary, never NationOffset+21.
  if(p.ClubIdOffset==0&&before.Length>0){
   int start=p.PersonOffset-15,end=PersonEnd(people,p),owner=start+(before.Owner-before.Start),pi=BitConverter.ToInt32(before.Bytes,0);
   Require(owner>start&&owner+28<=end-8&&BitConverter.ToInt32(people,start)==pi&&BitConverter.ToInt32(people,end-8)==pi&&BitConverter.ToInt32(people,end-4)==p.Id,"Free PERSON source/footer identity differs");
   Require(p.BirthDateOffset-start==before.Dob-before.Start&&BitConverter.ToInt32(people,owner)==-1,"Free PERSON source owner/DOB boundary differs");
   int length=(int)Call("GetNativeContractLength",people,owner+28,end-8,pi);Require(length==0,"Free PERSON retains/unrecognized contract");
   byte[] b=new byte[end-start];Buffer.BlockCopy(people,start,b,0,b.Length);
   return new N4Actor{Uid=p.Id,Start=start,End=end,Owner=owner,Dob=p.BirthDateOffset,Contract=owner+28,Payload=-1,Length=0,Bytes=b};
  }
  try{return N4Evidence(people,p);}catch(Exception e){''')

 s=s.replace('if(countryScoped){\n   string proofs=', 'N4Save(Path.Combine(prepared,"native-contract-resolution.json"),families.ToDictionary(k=>k.Key.ToString(),k=>k.Value));\n  if(countryScoped){\n   string proofs=')

 s=s.replace('"Contract family differs from witnessed identity"', '"Contract family differs from witnessed identity: TEAM="+ti+" UID="+x["ClubUID"]+" resolved="+families[ti]+" witnessed="+x["FamilyIndex"]')

 worker=T/'ApplyPolandRosterBatch-X14.cs';worker.write_text(s,encoding='utf-8')
 wrapper=(R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/tools/ApplyX10RosterBatch.cs').read_text(encoding='utf-8').replace('X10','X14').replace('x10154','x14292')
 wrap=T/'ApplyX14RosterBatch.cs';wrap.write_text(wrapper,encoding='utf-8')
 d=ROOT/'FM08-Database-Tools/scratch';sources=list(d.glob('*NativeSquads.cs'))+[d/'PolandSquadsN4.cs',d/'RepairNativeContracts.cs',worker,wrap]
 args=['C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe','/nologo','/optimize+','/platform:x64','/target:exe','/main:ApplyX14RosterBatch','/out:'+str(T/'ApplyX14RosterBatch.exe'),'/r:System.Windows.Forms.dll','/r:System.Drawing.dll','/r:System.Xml.dll','/r:System.Web.Extensions.dll','/r:'+str(dest)]+list(map(str,sources))
 z=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace');(T/'roster-build.log').write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,z.stdout+z.stderr
 m=dict(status='compiled_only_native_contract_preflight_pilot_pending',scope='x14292',scope_id='por-per-nor-pol-gaps-x14',target_country_indices=[162,160,194],core_clubs=292,structural_only_semantics='Exact declared empty UID allowlist, no fake actors, safe old roster preserved; reject unlisted empty or declared empty with actors',new_player_UID_range=[1702000000,1704000000],loan_UID_range=[1814000000,1815000000],editor=H(dest),source_editor_application=str(R/'PERSONALITY_CODEC_REPAIR_20261111/root-applied/application.json'),checked_scope_source=str(checked),checked_scope_source_sha256=H(checked),sources={str(p.relative_to(ROOT)):H(p)for p in sources},outputs={p.name:H(p)for p in[dest,T/'ApplyX14RosterBatch.exe']},main_editor_rebuilt=False,existing_EXE_overwritten=False,database_writes=False,legacy_rating_plan='Existing CAs preserved by this roster phase; selective model-repair must run as a separately pinned post-phase on fresh UID/record offsets')
 (T/'roster-build-manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('X14 roster adapter compiled; new reviewed codec; no DAT writes')
if __name__=='__main__':main()
