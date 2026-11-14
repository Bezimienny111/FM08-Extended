from pathlib import Path
import sys,csv,json,re,hashlib,collections,xml.etree.ElementTree as ET
from PIL import Image
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;O=B/'combined-review'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p,sep=';'):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline=''),delimiter=sep))
def dump(n,a):(O/n).write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(n,a):
 with(O/n).open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(a[0]),delimiter=';');w.writeheader();w.writerows(a)
def main():
 O.mkdir(exist_ok=True)
 stop=read(B/'SESSION_STOP_PINS.json');assert all(sha(B/n)==h for n,h in stop.items()),'Frozen core artifact changed'
 plans={'core':B/'installation-plan-all-reviewed-dangling.json','kits':B/'kits/installation-plan-all.json','owners':B/'foreign-owners/installation-plan-all.json'}
 data={k:read(p)for k,p in plans.items()};assert all(d['status']=='READY_FOR_ROOT_REVIEW'and not d['collisions']for d in data.values());assert data['owners']['counts']=={'icon':4,'logo':4};assert not data['owners']['neutralizations']
 cfg=data['owners']['all_public_config_pins'];now={str(p.relative_to(ROOT)):p for p in(ROOT/'Dane/graphics').rglob('config.xml')};assert set(now)==set(cfg);assert all(sha(p)==cfg[n]for n,p in now.items())
 owners=read(B/'foreign-owners/scope.json')['clubs'];assert len(owners)==5;ownerids={str(x['ClubUID'])for x in owners};assets=read(B/'foreign-owners/staging-result.json')['assets'];prepared=set();owner_png_proof=[]
 for a in assets:
  m=re.fullmatch(r'graphics/pictures/club/(\d+)/(logo|icon)',a['target']);assert m and m[1]in ownerids;u,k=m.groups();p=ROOT/a['path'];assert sha(p)==a['sha256'];size=180 if k=='logo'else 20
  with Image.open(p)as im:assert im.format=='PNG'and im.size==(size,size);im.verify()
  with Image.open(p)as im:im.load();assert im.convert('RGBA').getbbox()is not None
  prepared.add((u,k));owner_png_proof.append(dict(a,uid=u,kind=k,size=size))
 assert len(prepared)==8 and len({u for u,k in prepared})==4
 wanted={f'graphics/pictures/team/{u}/kits/{slot}'for u in ownerids for slot in['home','away','third']};kitmaps=collections.defaultdict(list)
 for n,p in now.items():
  for node in ET.parse(p).getroot().iter('record'):
   target=node.get('to')
   if target not in wanted:continue
   src=p.parent/node.get('from','');src=src if src.suffix.lower()=='.png'else Path(str(src)+'.png');valid=False
   if src.is_file():
    try:
     with Image.open(src)as im:valid=im.format=='PNG';dims=list(im.size);im.verify()
    except Exception:valid=False
   kitmaps[target].append(dict(config=n,source=str(src),valid=valid))
 kitassets=read(B/'kits/staging-result.json')['assets'];assert not any(a['target']in wanted for a in kitassets),'Owner kit delta scope changed'
 players=rows(B/'gracze.csv');clubs=rows(B/'kluby.csv');original={c['uid']:dict(c)for c in clubs};assert len(clubs)==2920 and not ownerids&set(original)
 sourceclubs={c['club_uid']:c for c in rows(B/'scope-clubs.csv',',')}
 for c in clubs:c.update(scope_role='final_roster_club_map',source_TMID=sourceclubs[c['uid']]['tmid'])
 for x in owners:
  uid=str(x['ClubUID']);row={k:'0'for k in clubs[0]};row.update(uid=uid,nazwa_klubu=x['ClubName'],kraj=x['Country'],liga='No assigned native league - foreign loan owner',division_index=str(x['NativeWitness']['CurrentDivision']),scope_role='new_foreign_loan_owner_without_roster_modernization',source_TMID=x['TMID'])
  assert x['NativeWitness']['NativeTeamKind']==0 and x['NativeWitness']['TeamTailFamilyUID']==x['ClubUID']
  for k,col in [('logo','herb_normal'),('icon','herb_small')]:row[col+'_przygotowany']=str(int((uid,k)in prepared));row[col+'_po_instalacji']=row[col+'_przygotowany']
  for slot in['home','away','third']:
   valid=any(m['valid']for m in kitmaps.get(f'graphics/pictures/team/{uid}/kits/{slot}',[]));row['koszulka_'+slot]=str(int(valid));row['koszulka_'+slot+'_po_instalacji']=str(int(valid))
  row['koszulki_sloty_lokalnie']=str(sum(int(row['koszulka_'+s])for s in['home','away','third']));clubs.append(row)
 assert len(clubs)==2925 and len({c['uid']for c in clubs})==2925
 patch=R/'BELGIUM_CUP_REPAIR_X22_20261114/native-patch-proof.json';proof=read(patch);assert proof['UID']==3200589 and proof['Name']=='TEST_X22'and proof['WholeBufferInverse']is True
 assert proof['Edit']['BeforeHex']=='03000000'and proof['Edit']['AfterHex']=='01000000'
 cat={str(x['index']):x for x in read(B/'competition-catalog.json')};assert cat['1']['uid']==2 and cat['3']['uid']==4
 meux=next(c for c in clubs if c['uid']=='3200589');assert meux['division_index']=='3';oldleague=meux['liga'];meux['division_index']='1';meux['liga']=cat['1']['names'][0];changedplayers=0
 for p in players:
  if p['klub_uid']=='3200589':assert p['liga']==oldleague;p['liga']=meux['liga'];changedplayers+=1
 for c in clubs:
  if c['uid']not in original:continue
  diffs={k:(v,c[k])for k,v in original[c['uid']].items()if c[k]!=v};assert not diffs or(c['uid']=='3200589'and set(diffs)=={'liga','division_index'})
 write('gracze.csv',players);write('kluby.csv',clubs);write('foreign-owner-clubs.csv',[c for c in clubs if c['uid']in ownerids])
 gaps=[c for c in clubs if not(int(c['herb_normal_lokalnie'])or int(c['herb_normal_przygotowany']))or not(int(c['herb_small_lokalnie'])or int(c['herb_small_przygotowany']))];write('brakujace_herby_po_instalacji.csv',gaps)
 kitsmissing=sum(not int(c['koszulka_'+s+'_po_instalacji'])for c in clubs for s in['home','away','third']);base=read(B/'summary.json')
 summary=dict(Status='COMBINED_STAGING_REVIEW_READY_PUBLIC_INSTALL_HOLD',SourcePlayersThrough='TEST_X21 final UID ledgers',LeagueMetadataAmendment='TEST_X22 RFCMeux only; no database writes',ScopePlayers=len(players),CoreClubs=2920,ForeignOwners=5,ScopeClubs=len(clubs),StagedPNG=23881,NewFaces=20586,NewNormalLogos=864,NewIcons=724,NewKits=1707,InstalledPNG=0,ModernFacesIfInstalled=base['modern_faces_after_delta'],MissingModernFacesIfInstalled=base['missing_faces_after_delta'],ModernLogosIfInstalled=sum(int(c['herb_normal_po_instalacji'])for c in clubs),ModernIconsIfInstalled=sum(int(c['herb_small_po_instalacji'])for c in clubs),AnyLocalLogosIfInstalled=sum(bool(int(c['herb_normal_lokalnie'])or int(c['herb_normal_przygotowany']))for c in clubs),AnyLocalIconsIfInstalled=sum(bool(int(c['herb_small_lokalnie'])or int(c['herb_small_przygotowany']))for c in clubs),MissingLogoClubs=len(gaps),KitMissingSlotsIfInstalled=kitsmissing,OwnerExistingKitMappings=sum(len(v)for v in kitmaps.values()),OwnerExistingKitValidSlots=sum(any(m['valid']for m in kitmaps.get(t,[]))for t in wanted),OwnerNewPNGReadback=len(owner_png_proof),PublicConfigSnapshotCount=len(cfg),CoreOldPNGHashPASSInherited=42299,CoreOldPNGNotRedecoded=True,ReviewPlans={k:dict(Path=str(p),SHA256=sha(p))for k,p in plans.items()},Rights='Local use only; FC12 no redistribution; TM/EA availability is not publication license',PublicWrites=0,GameMemoryAccessed=False,GameVisualTest='PENDING',ActiveOwnedDownloadProcesses=[])
 dump('summary.json',summary);dump('owner-readback.json',dict(Status='READBACK_PASS_STAGING_ONLY',Assets=owner_png_proof,KitMappingEvidence=dict(kitmaps),ExpectedKitTargets=sorted(wanted),PublicConfigSnapshotSHA256=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),FrozenCorePinsPreserved=stop,MeuxAmendment=dict(Source=str(patch),SHA256=sha(patch),UID=3200589,BeforeDivisionIndex=3,AfterDivisionIndex=1,BeforeLeague=oldleague,AfterLeague=meux['liga'],ChangedClubRows=1,ChangedPlayerLeagueRows=changedplayers)))
 commands=[dict(Step=1,Operation='apply core only AFTER root review + HOLD release + FM==0',Args=['python',str(B/'resolve_dangling_icons.py'),'--apply',str(plans['core'])],PinnedPlanSHA256=sha(plans['core'])),dict(Step=2,Operation='archive currently pinned kit plan; regenerate after core; review only expected prior config changes before apply',PlanToArchive=str(plans['kits']),SHA256ToArchive=sha(plans['kits']),GenerateArgs=['python',str(B/'kits/install_kits_delta.py')],ApplyArgs=['python',str(B/'kits/install_kits_delta.py'),'--apply',str(plans['kits'])]),dict(Step=3,Operation='archive currently pinned owner plan; regenerate after both prior transactions; review delta before apply',PlanToArchive=str(plans['owners']),SHA256ToArchive=sha(plans['owners']),GenerateArgs=['python',str(B/'foreign-owners/install_delta.py'),'--scope','all'],ApplyArgs=['python',str(B/'foreign-owners/install_delta.py'),'--apply',str(plans['owners'])]),dict(Step=4,Operation='independent core+kit readback; owners additionally require all8 destination PNG/config readback before combined installed status',Args=['python',str(B/'close_report.py'),'--installed'])]
 dump('installation-commands.json',dict(Status='NOT_EXECUTED_INSTALL_HOLD',GlobalConfigHashGuard='Plans2/3 intentionally become stale after earlier transactions; never apply stale plans or weaken checks',NeverCloseFMOrEditor=True,Steps=commands))
 lines=['# Zbiorczy przeglad grafik - X21 UID i etykiety lig X22','',summary['Status'],'',f'Zakres:72319 graczy;2920 core klubow +5 klubow-wlascicieli wypozyczen =2925. Nowy raport; coreCSV/manifesty/plany pozostaja niezmienione.',f'Przygotowane23881 PNG:20586 twarzy180px,864 herby180px,724 ikony20px,1707 koszulek130px. Zainstalowano0. Liczby po instalacji sa warunkowe:38674 twarze modern,33645 brakow;{summary["AnyLocalLogosIfInstalled"]}/2925 klubow z poprawnym lokalnym herbem i ikona,4 kluby bez herbu.',f'Koszulki:3789 plikow po instalacji;{kitsmissing} brakujacych slotow(home/away/third) w2925 klubach. Dla5 owners odczytano jedynie istniejace mapowania, bez pobierania lub badan zewnetrznych. Nowych8 ownerPNG przeszlo hash/format/wymiary/alpha/readback; ich plan ma0 kolizji.','Tzeirei Kfar Kana UID1800180033/TM89132: zachowany404; niczego nie ponawiano. Kolding2121 DEFER poza zakresem owners.',f'RFC Meux3200589: tylko w NOWYM raporcie liga zmieniona z{oldleague} na{meux["liga"]}, indeks3->1, zgodnie z zamknietym native-patch-proof X22. Poprawiono1wierszklubu i{changedplayers}etykiet ligi graczy. Brak zmian bazy/UID/kadry.','Wszystkie16 pinow SESSION_STOP zachowane. Nie dekodowano ponownie core42299 poprawnych obrazow; aktualny snapshot1416 publicznychconfigow zgodny z gotowym planem. Apply ponownie sprawdzi wszystkie przypiete stare i nowe obrazy.','', 'Instalacja nadal HOLD. Konkretne argumenty winstallation-commands.json. Transakcje sekwencyjne:core,kits,owners. Plan kolejnej transakcji trzeba zarchiwizowac i odswiezyc po poprzedniej, bo hashguard celowo wykryje zmiany. Root musi zatwierdzic plan i zwolnicHOLD; guard FM==0 nie jest omijany. Nie zamykanoFM/edytora ani nie czytano ich pamieci.','', 'Prawa: FC12 tylko lokalnyuzytek, bez redystrybucji. TM/EA nie udziela licencji przez sama dostepnosc. Zadnego publicznegoZIP. EAFutwiz403 zachowane, bez ponowien/proxy/zmianURL. Brak nowych pobran wtym etapie. Anglia nie ma zgadywanych przyszlychUID.','', 'Pliki: gracze.csv(uid/imie/nazwisko/klub/zdjecie),kluby.csv(uid/nazwa/liga/herby/koszulki),foreign-owner-clubs.csv,brakujace_herby_po_instalacji.csv,summary.json,owner-readback.json,installation-commands.json. Kontrola wgrze/cache PENDING; ten raport nie potwierdza sezonuX22.']
 (O/'RAPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 (O/'WZNOWIENIE.md').write_text('# Grafiki - final review przygotowany\n\n'+summary['Status']+'\n\nCzytaj RAPORT.md, manifest.json i installation-commands.json. NIE instalowac bez rootHOLDrelease i review. Nie pobierac ponownie23881PNG. Brak aktywnych wlasnych pobran. Core piny chronione; nowe CSV obejmuja5 owners i metadataRFCMeuxX22. Po apply wymagany niezalezny odczyt8ownerPNG i laczne installedstatus dopiero po wszystkich transakcjach.\n',encoding='utf-8')
 assert len(rows(O/'gracze.csv'))==72319 and len(rows(O/'kluby.csv'))==2925
 reload={c['uid']:c for c in rows(O/'kluby.csv')};assert set(reload)==set(original)|ownerids and reload['3200589']['division_index']=='1'
 assert all(sha(B/n)==h for n,h in stop.items())and all(sha(p)==cfg[n]for n,p in now.items())
 inputs={str(p):sha(p)for p in[B/'SESSION_STOP_PINS.json',B/'manifest.json',B/'kluby.csv',B/'gracze.csv',B/'foreign-owners/scope.json',B/'foreign-owners/staging-result.json',patch,*plans.values(),Path(__file__)]}
 outputs={p.name:sha(p)for p in O.iterdir()if p.is_file()and p.name!='manifest.json'};dump('manifest.json',dict(Status=summary['Status'],Inputs=inputs,Outputs=outputs,NetworkRequests=0,PublicWrites=0,DBWrites=0,GameAccess=False));print(json.dumps(summary,ensure_ascii=True),flush=True);print('MANIFEST_SHA256',sha(O/'manifest.json'),flush=True)
if __name__=='__main__':main()
