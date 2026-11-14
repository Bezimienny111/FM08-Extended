from pathlib import Path
import sys,json
sys.dont_write_bytecode=True
root=Path('J:/FM08dev');b=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'FM08-Database-Tools/scratch'));sys.path.insert(0,str(b))
source=root/'FmLauncher/data/research/POLAND_GAPS_IMPORT_PACKAGE_20261111/integrate_stage.py'
s=source.read_text(encoding='utf-8').replace("W=B/'structure-regional-root'","W=B/'structure-root'")
old="""   assert row['ClubUID']=='103279'and int(row['FamilyIndex'])==2336 and fi==1025
   parent=native['1376'];assert parent['FamilyIndex']==fi
   exceptions.append(dict(ClubUID=103279,OwnFamilyIndex=2336,ContractFamilyIndex=fi,ContractFamilyUID=1376,source='native ResolveNativeClubContractReferences; exact source TEAM tail and witnessed parent FAMILY'))
   row['OwnFamilyIndex']=row['FamilyIndex'];row['FamilyIndex']=fi;row['ContractFamilyUID']=1376;row['ContractFamilyIndex']=fi
 assert len(exceptions)==1"""
new="""   plans={x['TMID']:x for x in read(B/'club-plan.json')}
   plan=plans[row['TMID']];parent_tid=plan.get('ParentTMID')
   assert parent_tid and parent_tid in actual,('contract_parent_source_missing',row)
   parent=actual[parent_tid];assert int(parent['FamilyIndex'])==fi,('native_contract_parent_mismatch',row,parent,fi)
   exceptions.append(dict(ClubUID=int(row['ClubUID']),OwnFamilyIndex=int(row['FamilyIndex']),ContractFamilyIndex=fi,ContractFamilyUID=int(parent['ClubUID']),source='existing editor native contract resolver + current source mainClubId + exact materialized parent FAMILY witness'))
   row['OwnFamilyIndex']=row['FamilyIndex'];row['FamilyIndex']=str(fi);row['ContractFamilyUID']=parent['ClubUID'];row['ContractFamilyIndex']=str(fi)
 assert len(exceptions)==22,('unexpected_native_reserve_contract_family_count',len(exceptions))"""
assert old in s;s=s.replace(old,new).replace("target_country_indices=[162,160,194]","target_country_indices=[145,109,70,54]").replace("source_reference_date='2026-11-11'","source_reference_date='2026-11-12'").replace("source_player_audit_from_immutable_X11_people_byte_identical","source_player_audit_from_immutable_X14_people_byte_identical")
out=b/'integrate_stage.py';assert not out.exists();out.write_text(s,encoding='utf-8')
ns={'__name__':'configured_integration','__file__':str(out)};exec(compile(s,str(out),'exec'),ns);ns['proofs']()
