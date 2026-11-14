from pathlib import Path
import sys,json,csv,re,hashlib,collections,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');O=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p,sep=';'):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline=''),delimiter=sep))
def dump(n,a):(O/n).write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(n,a):
 with(O/n).open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(a[0]),delimiter=';');w.writeheader();w.writerows(a)
def classify(target):
 for k,pat in [('face',r'graphics/pictures/person/(\d+)/portrait'),('logo',r'graphics/pictures/club/(\d+)/logo'),('icon',r'graphics/pictures/club/(\d+)/icon'),('kit',r'graphics/pictures/team/(\d+)/kits/(home|away|third)')]:
  m=re.fullmatch(pat,target)
  if m:return k,m[1],m[2]if k=='kit'else''
 raise ValueError(target)
def main():
 installed='--installed'in sys.argv
 players=rows(O/'baseline/gracze.csv');clubs=rows(O/'baseline/kluby.csv');sp={x['uid']:x for x in rows(O/'scope-players.csv',',')};assets=read(O/'staging-result.json')['assets']+read(O/'kits/staging-result.json')['assets'];assert len({a['target']for a in assets})==len(assets)
 bykind=collections.Counter();prepared=set();proof=[]
 dest={'face':ROOT/'Dane/graphics/pictures/faces/normal/modern_2627','logo':ROOT/'Dane/graphics/pictures/logos/clubs/normal/modern_2627','icon':ROOT/'Dane/graphics/pictures/logos/clubs/small/modern_2627','kit':ROOT/'Dane/graphics/pictures/kits/2d/modern_2627'}
 maps={k:{n.get('to'):n.get('from')for n in ET.parse(v/'config.xml').getroot().iter('record')if n.get('to')}for k,v in dest.items()}
 for a in assets:
  k,u,slot=classify(a['target']);p=ROOT/a['path'];assert sha(p)==a['sha256'];prepared.add((k,u,slot));bykind[k]+=1
  if installed:
   actual=dest[k]/((u+'_'+slot if k=='kit'else u)+'.png');assert sha(actual)==a['sha256'];assert maps[k].get(a['target'])==actual.stem
   from PIL import Image
   with Image.open(actual)as im:assert im.format=='PNG'and im.size==({'face':180,'logo':180,'icon':20,'kit':130}[k],)*2;im.verify()
  proof.append(dict(a,kind=k,uid=u,slot=slot,installed=installed))
 old=read(O/'baseline/inventory-images.json');preserved=0
 for x in old:
  if x.get('valid')and x.get('sha256'):assert sha(ROOT/x['path'])==x['sha256'];preserved+=1
 changed=[rel for rel,h in read(O/'baseline/manifest.json')['inputs'].items()if rel.endswith('config.xml')and sha(ROOT/rel)!=h]
 if installed:assert set(changed)=={str((d/'config.xml').relative_to(ROOT))for d in dest.values()}|{c['path']for c in read(O/'installation-plan-all-reviewed-dangling.json')['neutralizations']}
 else:assert not changed,'Public configs changed during staging'
 for p in players:
  u=p['uid'];add=int(('face',u,'')in prepared);p.update(zdjecie_przygotowane=add,ma_zdjecie_po_instalacji=int(bool(int(p['ma_zdjecie'])or add)),nowy_w_X15_X21=sp[u]['new'],TMID=sp[u]['tmid'],source_DOB=sp[u]['dob'])
  if installed and add:p['ma_zdjecie']=1;p['ma_zdjecie_lokalnie']=1
 for c in clubs:
  u=c['uid']
  for k,col in [('logo','herb_normal'),('icon','herb_small')]:
   add=int((k,u,'')in prepared);c[col+'_przygotowany']=add;c[col+'_po_instalacji']=int(bool(int(c[col])or add))
   if installed and add:c[col]=1;c[col+'_lokalnie']=1
  for slot in['home','away','third']:
   key='koszulka_'+slot;add=int(('kit',u,slot)in prepared);c[key+'_przygotowana']=add;c[key+'_po_instalacji']=int(bool(int(c[key])or add))
   if installed and add:c[key]=1
  if installed:c['koszulki_sloty_modern']=sum(int(c['koszulka_'+slot])for slot in['home','away','third'])
 write('gracze.csv',players);write('kluby.csv',clubs);write('brakujace_zdjecia_po_delcie.csv',[p for p in players if not p['ma_zdjecie_po_instalacji']]);write('brakujace_herby_po_delcie.csv',[c for c in clubs if not(int(c['herb_normal_lokalnie'])or c['herb_normal_przygotowany'])or not(int(c['herb_small_lokalnie'])or c['herb_small_przygotowany'])])
 latest={}
 for line in(O/'staging-ledger.jsonl').read_text(encoding='utf-8').splitlines():
  x=json.loads(line);latest[(x['kind'],x['uid'])]=x
 dump('download-gaps.json',[x for x in latest.values()if x['status']!='added'])
 base=read(O/'baseline/summary.json');kits=read(O/'kits/verification.json')
 summary=dict(status='LOCAL_INSTALL_INDEPENDENT_READBACK_PASS'if installed else'STAGING_COMPLETE_INSTALLATION_PENDING',scope_players=len(players),scope_clubs=len(clubs),baseline=base,new_staged=dict(bykind),new_total_png=len(assets),installed_png=len(assets)if installed else 0,valid_existing_images_hash_preserved=preserved,public_changed_configs=changed,modern_faces_after_delta=sum(int(p['ma_zdjecie_po_instalacji'])for p in players),missing_faces_after_delta=sum(not int(p['ma_zdjecie_po_instalacji'])for p in players),modern_logos_after_delta=sum(int(c['herb_normal_po_instalacji'])for c in clubs),modern_icons_after_delta=sum(int(c['herb_small_po_instalacji'])for c in clubs),all_local_logos_after_delta=sum(bool(int(c['herb_normal_lokalnie'])or c['herb_normal_przygotowany'])for c in clubs),all_local_icons_after_delta=sum(bool(int(c['herb_small_lokalnie'])or c['herb_small_przygotowany'])for c in clubs),kits=kits,download_final_status=dict(collections.Counter(x['status']for x in latest.values())),rights='LOCAL_PERSONAL_ONLY; no public ZIP or redistribution approval',game_test='PENDING',database_files_changed=False,game_memory_accessed=False)
 dump('summary.json',summary);dump('delta-readback.json',dict(status=summary['status'],assets=proof,old_valid_png_preserved=preserved,public_config_changes=changed,game_test='PENDING'))
 lines=['# Grafiki modern_2627 - TEST_X21','',summary['status'],'',f'Scope: {len(players)} final playerUID / {len(clubs)} clubUID. X14 baseline + final X15/X16/X17/X18/X20/X21 ledgers. X20 final8272/prepared-r3. England excluded; futureUID not guessed.',f'New stagedPNG: {dict(bykind)}. Total{len(assets)}. Sizes: face/logo180,icon20,kit130.',f'After successful installation only: modernfaces{summary["modern_faces_after_delta"]}, missing{summary["missing_faces_after_delta"]}; modernlogos{summary["modern_logos_after_delta"]},icons{summary["modern_icons_after_delta"]}; anylocalvalidlogos/icons{summary["all_local_logos_after_delta"]}/{summary["all_local_icons_after_delta"]}. Valid older assets outside modern are deliberately preserved.',f'Kits2082->{kits["final_png_if_installed"]} for{kits["clubs_with_any_if_installed"]}clubs; home+away{kits["home_away_if_installed"]}.864 newkits2026/27,843 from2025/26.155archives(85reuse+70new),3archives>64MiB+6PNGtextcompressionrejected; guards unchanged.',f'Existing validimageSHA preserved:{preserved}. Configchanges:{len(changed)}. ExactUID configtarget+PNGdimensions/hash; a filename alone is not coverage.259inheritedissues retained inbaseline. Existing SerieA/B fixes protected. Not every image was manually visually compared.', '','Provider cdn.futwiz.com returned403: no retries/proxies/URL substitution. Phase1 preserved. Then only8462 previously unattempted independent confirmedTransfermarkt URLs resumed byhostallowlist. Raw404/403 retained inhttp-errors; gaps explicit inCSV/JSON; no forced person research.','Rights:FC12 localpersonalonly/noredistribution; imageavailability fromTM/EA does not grant publicdistributionrights. No publicZIP.','Plan resolves exactly5old dangling iconmaps in2legacyconfigs; referencedPNGs do not exist. Allothermaps andallPNGs preserved. No broader cleanup.', 'TEST_X21 NativePASS is separate from SI/career/season. No graphicsreport claims career/seasonPASS. FMcache/reload/visual test PENDING. No memoryread/closeFM, no DB/EXE/launcher/skinchange.','','gracze.csv: UID,first,last,club,ma_zdjecie plus staged/after-install flags,TMID/sourceDOB. kluby.csv:UID,name,league,normal/small/home/away/third. Baselineactual columns stay actual until --installed readback. Otherfiles:summary.json,delta-readback.json,download-gaps.json,baseline/*,kits/*,manifest.json.']
 (O/'RAPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 (O/'WZNOWIENIE.md').write_text('# Graphics X21 checkpoint\n\n'+summary['status']+'\n\nRead RAPORT.md and manifest.json. No fullfetch/re-render. Sources staged in staging/ and kits/staging/. Install needs rootreview, FM==0 and release of activeHOLD. NevercloseFM. Applytwo transactions sequentially: regenerate secondplan because firstchanges pinnedglobalconfighash. Afterboth apply use close_report.py --installed for exactnewPNG+alloldSHA+4configscope readback.\n\nFutwiz403 retained; no EAretries thissession. EnglandUID only afterfinalledger. Databases/launcher/skins protected.\n',encoding='utf-8')
 names=['prepare_scope.py','audit_scope.py','stage_missing.py','resume_tm_only.py','close_report.py','source-scope.json','source-asset-plan.json','league-metadata-proof.json','staging-result.json','staging-ledger.jsonl','baseline/manifest.json','summary.json','delta-readback.json','RAPORT.md','WZNOWIENIE.md','gracze.csv','kluby.csv','download-gaps.json','install_delta.py','installation-plan-all.json','installation-plan-all-reviewed-dangling.json','resolve_dangling_icons.py','kits/manifest.json','kits/staging-result.json','kits/verification.json','kits/install_kits_delta.py','kits/installation-plan-all.json']
 dump('manifest.json',dict(status=summary['status'],files={n:sha(O/n)for n in names if(O/n).is_file()},public_modified=installed,rights=summary['rights'],DBModified=False,GameTest='PENDING'))
 print(json.dumps({k:v for k,v in summary.items()if k not in['baseline','kits']},ensure_ascii=True),flush=True)
if __name__=='__main__':main()
