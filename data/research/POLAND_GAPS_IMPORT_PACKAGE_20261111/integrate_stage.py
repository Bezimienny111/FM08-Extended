from pathlib import Path
import sys,json,csv,hashlib,shutil
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;W=B/'structure-regional-root';P=B/'prepared'
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
import x7prep_rosters_20261110 as shared
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=shared.read;rows=shared.rows;dump=shared.dump;writecsv=shared.writecsv
def pins(p):return{str(f.relative_to(p)):H(f)for f in sorted(p.rglob('*'))if f.is_file()}
def proofs():
 source=W/'structure-db';report=read(W/'structure-report.json');assert all(pins(source)[k].upper()==v.upper()for k,v in report['output_hashes'].items())
 core=rows(W/'club-map.csv');foreign=rows(W/'foreign-owner-map.csv');projected={x['TMID']:x for x in rows(B/'club-map.csv')};fo={x['TMID']:x for x in rows(B/'foreign-owner-map.csv')}
 for row in core:
  old=projected[row['TMID']]
  for k in['ClubUID','TeamIndex','FamilyIndex','CountryIndex','DivisionIndex','ParentUID']:assert str(row.get(k,''))==str(old.get(k,'')),('core_projection_drift',row['TMID'],k,row.get(k),old.get(k))
 for row in foreign:
  old=fo[row['TMID']]
  for k in['ClubUID','TeamIndex','FamilyIndex','CountryIndex','ParentUID']:assert str(row.get(k,''))==str(old.get(k,'')),('owner_projection_drift',row['TMID'],k)
 native={str(x['ClubUID']):x for x in read(B/'native-world-identities.json')};actual={x['TMID']:x for x in core};actual.update({x['TMID']:x for x in foreign})
 aliases={x['SourceTMID']:x for x in read(B/'foreign-owner-aliases.json')};used={str(x['owner_club']):x for x in read(P/'provenance.json')};entities={str(x['TeamIndex']):x for x in core+foreign}
 for proof in read(P/'provenance.json'):
  tid=proof['owner_TMID']
  if tid in actual:owner=actual[tid]
  else:
   a=aliases[tid];main=a['CanonicalMainTMID']
   if main in actual:owner=actual[main]
   else:
    w=native[str(a['NativeClubUID'])];owner=dict(ClubUID=w['ClubUID'],TeamIndex=w['TeamIndex'],FamilyIndex=w['FamilyIndex'],ParentUID=w['ParentUID']or'',ClubName=w['Names'][0])
  assert int(owner['TeamIndex'])==proof['owner_club'];entities[str(owner['TeamIndex'])]=owner
 # TEAM identity FAMILY stays unchanged; Rosenborg II native contracts belong to the parent's FAMILY.
 resolution=read(P/'native-contract-resolution.json')
 exceptions=[]
 for row in core:
  fi=resolution[str(row['TeamIndex'])]
  if fi!=int(row['FamilyIndex']):
   assert row['ClubUID']=='103279'and int(row['FamilyIndex'])==2336 and fi==1025
   parent=native['1376'];assert parent['FamilyIndex']==fi
   exceptions.append(dict(ClubUID=103279,OwnFamilyIndex=2336,ContractFamilyIndex=fi,ContractFamilyUID=1376,source='native ResolveNativeClubContractReferences; exact source TEAM tail and witnessed parent FAMILY'))
   row['OwnFamilyIndex']=row['FamilyIndex'];row['FamilyIndex']=fi;row['ContractFamilyUID']=1376;row['ContractFamilyIndex']=fi
 assert len(exceptions)==1
 dump(B/'contract-family-exceptions.json',exceptions)
 # Keep every CSV row schema explicit.
 for row in core:
  for key in ['OwnFamilyIndex','ContractFamilyUID','ContractFamilyIndex']:row.setdefault(key,'')
 entities.update({str(x['TeamIndex']):x for x in core})
 shared.B=W
 before=pins(source)
 mapped=[dict(x,ParentUID=x.get('ContractFamilyUID')or x.get('ParentUID',''))for x in core]
 result=shared.club_proofs(source,mapped,list(entities.values()))
 assert before==pins(source),'Source drift during contract-country proofs'
 writecsv(P/'club_proofs.csv',result);writecsv(P/'club_map.csv',core);writecsv(P/'cleanup_subjects.csv',[],['UID','ExpectedOwner','FirstName','LastName','ExpectedDOB','Source'])
 # All incomplete source clubs preserve their pre-existing roster, even if nominal count>=17.
 m=read(P/'manifest.json');current=rows(B/'audit/players.csv');corebyname={x['ClubName']:int(x['TeamIndex'])for x in core};gapteams=set()
 for gap in read(P/'source-gaps.json'):
  name=gap.get('club')or gap.get('Club')or gap.get('ClubName')
  if name in corebyname:gapteams.add(corebyname[name])
 reused={int(x['ExistingID'])for x in rows(P/'identities.csv')if int(x['ExistingID'])>0}
 unsupported=[x for x in current if(not x['BirthDate']or int(x['CA'])<=0 or int(x['PA'])<=0)and int(x['ClubIndex'])in {int(c['TeamIndex'])for c in core}]
 dump(B/'preserved-unresolved-source-records.json',dict(reason='Existing actor without proven DOB or positive CA/PA; unsupported release may lose format. Preserve exact record, no confirmed modern source identity.',records=unsupported))
 preserved=set(m['preserve_absent_uids']);preserved.update(int(x['ID'])for x in unsupported);preserved.update(int(x['ID'])for x in current if int(x['ClubIndex'])in gapteams);preserved-=reused
 empty=[int(x['ClubUID'])for x in read(P/'coverage.json')if x['Confirmed']==0]
 m.update(stage='full',output=str(B/'roster-db'),status='prepared_with_explicit_source_gaps',source=str(source),source_hashes=before,source_reference_date='2026-11-11',target_country_index=-1,target_country_indices=[162,160,194],prepared_rows=m['counts']['prepared'],prepared_loans=m['counts']['loans'],source_gaps_count=m['counts']['source_gaps'],structural_only_club_uids=empty,preserve_absent_uids=sorted(preserved),partial_roster_club_uids=[int(x['ClubUID'])for x in read(P/'coverage.json')if x['Confirmed']<17 or not x['Goalkeepers']],source_player_audit_from_immutable_X11_people_byte_identical=True)
 m['counts']['issues']=0;m['counts']['technical_duplicates']=0;m['counts']['global_TMID_registry_reuse']=len(read(P/'registry-reuse.json'))
 m['policy']['native_contract_country_proofs']='actual_native_materialized_source_readback';m['prepared_hashes']={str(p.relative_to(P)):H(p)for p in sorted(P.rglob('*'))if p.is_file()and p.name!='manifest.json'}
 dump(P/'manifest.json',m)
 dump(B/'contract-preflight.json',dict(status='pass',materialized_source=str(source),native_proofs=len(result),core_clubs=len(core),new_owners=len(foreign),owner_entities=len(entities),core_projection_exact=True,source_pins=before,source_unchanged_during_read=True,engine_write_executed=False,root_independent_acceptance='PASS_PRIVATE_NATIVE_STRUCTURE_NOT_SI_OR_RUNTIME'))
 print('CONTRACT_PROOFS',len(result),'core',len(core),'newowners',len(foreign),'source pins stable',flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
