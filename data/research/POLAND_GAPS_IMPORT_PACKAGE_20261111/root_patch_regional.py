"""One declared stale regional assignment; keep prior verified staging immutable."""
from pathlib import Path
import sys,struct,shutil,zlib,subprocess,hashlib
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[4];B=Path(__file__).resolve().parent;W=B/'structure-root';V=B/'structure-regional-root'
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
from create_italy_structure_i1_20261108 import read,dump,pins,load

def main():
 assert read(W/'root-independent-verification.json')['status']=='PASS_PRIVATE_NATIVE_STRUCTURE_NOT_SI_OR_RUNTIME'
 assert not V.exists(),'Do not overwrite regional attempt'
 src=W/'structure-db';before=pins(src);report=read(W/'structure-report.json');assert before==report['output_hashes']
 rec=read(W/'native-structure-after.json')['records'];r=next(x for x in rec if x['ClubUID']==55006622)
 a=load(src,'server_db.dat');at=r['Start']+47
 assert struct.unpack_from('<i',a,r['Start']+7)[0]==49 and struct.unpack_from('<i',a,at)[0]==48
 changed=bytearray(a);struct.pack_into('<i',changed,at,-1)
 inverse=bytearray(changed);struct.pack_into('<i',inverse,at,48);assert bytes(inverse)==a
 V.mkdir();dest=V/'structure-db';shutil.copytree(src,dest)
 (dest/'server_db.dat').write_bytes((src/'server_db.dat').read_bytes()[:9]+zlib.compress(changed))
 for p in ['manifest.json','structure-config.json','club-map.csv','foreign-owner-map.csv','new-clubs-sugar-daddy-audit.csv','native-structure.json']:shutil.copyfile(W/p,V/p)
 editor=ROOT/'FmLauncher/data/research/PERSONALITY_CODEC_REPAIR_20261111/root-applied/build/FM08_Database_Editor.exe'
 args=[ROOT/'FmLauncher/data/research/SWEDEN_SELECTION_REPAIR_X4_20261110/tools/ExportWholeNativeStructure.exe',dest,editor,V/'native-structure-after.json']
 result=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300)
 (V/'whole-export.log').write_text(result.stdout+result.stderr,encoding='utf-8');assert result.returncode==0,result.stderr
 rr=read(V/'native-structure-after.json')['records'];nr=next(x for x in rr if x['ClubUID']==55006622)
 reread=load(dest,'server_db.dat');assert bytes(changed)==reread and nr==r
 for rel,hashval in before.items():
  if rel!='server_db.dat':assert pins(dest)[rel]==hashval
 assert pins(src)==before
 patch=dict(ClubUID=55006622,Name='União Atlético Povoense',offset=at,before=48,after=-1,main_preserved=49,previous_roster_and_other_TEAM_bytes_preserved=True,reason='Not among final PT1-4 catalogue/selected56 regional teams; remove old extra GroupC participant',before_payload_sha256=hashlib.sha256(a).hexdigest(),after_payload_sha256=hashlib.sha256(changed).hexdigest(),inverse_exact=True)
 report.update(output=str(dest),output_hashes=pins(dest),root_regional_patch=patch)
 dump(V/'structure-report.json',report)
 code=(B/'root_verify_structure.py').read_text(encoding='utf-8')
 needle=" inverse(old,a,sr['SERVER_edits']);inverse(load(src,'client_db.dat'),c,sr['CLIENT_edits'])"
 replacement=" normalized=bytearray(a);rp=sr['root_regional_patch'];assert struct.unpack_from('<i',normalized,rp['offset'])[0]==rp['after'];struct.pack_into('<i',normalized,rp['offset'],rp['before'])\n inverse(old,bytes(normalized),sr['SERVER_edits']);inverse(load(src,'client_db.dat'),c,sr['CLIENT_edits'])"
 assert code.count(needle)==1;code=code.replace(needle,replacement)
 needle="o[23:]==v[23:]";assert code.count(needle)==1
 code=code.replace(needle,"o[23:]==normalized[n['Start']+23:n['Footer']+8]")
 ns={'__name__':'root_regional_verifier','__file__':str(B/'root_verify_structure.py')};exec(compile(code,str(V/'configured-root-verifier.py'),'exec'),ns);ns['W']=V;ns['main']()
 result=read(V/'root-independent-verification.json')
 result['unrelated_TEAM_bytes_previous_regional_preserved']=False
 result.update(unrelated_TEAM_bytes_preserved=True,previous_fields_preserved=True,regional_fields_preserved_except_declared_one=patch,actual_playable_TEAM_memberships=186)
 dump(V/'root-independent-verification.json',result)
 (V/'configured-root-verifier.py').write_text(code,encoding='utf-8')
 assert pins(src)==before
 dump(V/'regional-patch-proof.json',dict(status='PASS',patch=patch,prior_structure_unchanged=True,all36_actual_forms_rechecked=True,output=str(dest),output_hashes=pins(dest)))
 print('PASS bounded Povoense regional48->-1;GroupC14;186 playable memberships;prior staging immutable',flush=True)
if __name__=='__main__':main()