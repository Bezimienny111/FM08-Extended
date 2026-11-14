from pathlib import Path
import sys,json,csv,hashlib,importlib.util,concurrent.futures,xml.etree.ElementTree as ET,collections,os
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;O=B/'foreign-owners'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,a):(O/n).write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 O.mkdir(exist_ok=True);scope={x['club_uid']for x in csv.DictReader((B/'scope-clubs.csv').open(encoding='utf-8-sig'))};p=R/'COUNTRY_BATCH_BLR_BEL_AUT_AUS_ARG_20261114/native-prep/native-world-identities.json';world={x['ClubUID']:x for x in read(p)};pins={str(p):sha(p)};extras=[]
 for rel in['COUNTRY_BATCH_GER_MEX_MAS_20261112/structure-root/structure-report.json','COUNTRY_BATCH_KOR_COL_ISR_20261112/six-country-stage/structure-root/structure-report.json']:
  p=R/rel;pins[str(p)]=sha(p)
  for c in read(p).get('foreign_owner_map',[]):
   if c['Kind']=='new_first_team'and str(c['ClubUID'])not in scope:
    w=world[c['ClubUID']];assert w['NativeTeamKind']==0 and w['TeamTailFamilyUID']==c['ClubUID']and w['TeamCountry']==c['CountryIndex'];extras.append(dict(c,NativeWitness=w,SourceStructure=str(p),Role='new_foreign_loan_owner_outside_updated_roster_leagues'))
 assert {x['ClubUID']for x in extras}=={1800160044,1800180030,1800180031,1800180032,1800180033}
 targets={f'graphics/pictures/club/{x["ClubUID"]}/{k}'for x in extras for k in['logo','icon']};existing=[]
 for conf in(ROOT/'Dane/graphics').rglob('config.xml'):
  for node in ET.parse(conf).getroot().iter('record'):
   if node.get('to')in targets:existing.append(dict(config=str(conf),attributes=dict(node.attrib)))
 assert not existing,'Existing foreign-owner mappings require separate preservation review'
 libpath=R/'GRAPHICS_MODERN_2627_20261111/build_graphics.py';sp=importlib.util.spec_from_file_location('existing_graphics_owner_delta',libpath);lib=importlib.util.module_from_spec(sp);sp.loader.exec_module(lib);lib.OUT=O;lib.CACHE=B/'cache';lib.LOGON=O/'staging/logos/normal';lib.LOGOS=O/'staging/logos/small'
 for folder in[lib.CACHE,lib.LOGON,lib.LOGOS,O/'backups']:folder.mkdir(parents=True,exist_ok=True)
 items=[dict(kind='logo',uid=str(c['ClubUID']),name=c['ClubName'],urls=[f'https://tmssl.akamaized.net/images/wappen/normal/{c["TMID"]}.png'],proof=[dict(kind='final_structure_foreign_owner_TMID_UID_country_typed_TEAM',TMID=c['TMID'],UID=c['ClubUID'],source=c['SourceStructure'])])for c in extras]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:results=list(pool.map(lib.work,items))
 for folder,kind in[(lib.LOGON,'logo_normal'),(lib.LOGOS,'logo_small')]:lib.update_config(folder,kind)
 assets=[]
 for folder,suffix in[(lib.LOGON,'logo'),(lib.LOGOS,'icon')]:
  for p in folder.glob('*.png'):assets.append(dict(path=str(p.relative_to(ROOT)),target=f'graphics/pictures/club/{p.stem}/{suffix}',sha256=sha(p)))
 dump('scope.json',dict(clubs=extras,source_pins=pins,NoKoldingRoleConversionOrGraphics=True,PublicModified=False,CoreScope=2920,TotalScopeWithOwners=2925));dump('download-ledger.json',results);dump('staging-result.json',dict(assets=assets,rights='LOCAL_ONLY_NOT_PUBLICATION_APPROVED',public_graphics_modified=False));print(json.dumps(dict(extra_clubs=len(extras),status=dict(collections.Counter(x['status']for x in results)),new_png=len(assets))),flush=True)
if __name__=='__main__':main()
