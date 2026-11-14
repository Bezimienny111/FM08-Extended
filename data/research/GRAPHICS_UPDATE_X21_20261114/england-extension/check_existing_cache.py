from pathlib import Path
import json,csv,sys,hashlib,collections
from PIL import Image
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';O=Path(__file__).resolve().parent;B=O.parent;E=R/'COUNTRY_BATCH_ENGLAND_20261114';N=E/'native-prep'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,a):(O/n).write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 paths=[N/'prepared/manifest.json',N/'prepared/provenance.json',N/'prepared/native_players.csv',B/'source-asset-plan.json',B/'staging-result.json'];pins={str(p):sha(p)for p in paths};manifest=read(paths[0]);prov=read(paths[1]);assert manifest['prepared_hashes']['provenance.json']==sha(paths[1]);assert manifest['counts']['prepared']==len(prov)==4016
 new=[p for p in prov if not p.get('existing_id')or int(p['existing_id'])<=0];assert len(new)==manifest['counts']['new']==368
 staged={a['target'].split('/')[3]:a for a in read(B/'staging-result.json')['assets']if '/person/'in a['target']};bytm=collections.defaultdict(list)
 for a in read(B/'source-asset-plan.json')['items']:
  if a['kind']!='face':continue
  for pr in a.get('proof',[]):
   if pr.get('TMID')and pr.get('DOB'):bytm[(str(pr['TMID']),pr['DOB'])].append(a)
 rawcache={};results=[];errors=[];cacheroots=[B/'cache',R/'GRAPHICS_MODERN_2627_20261111/cache',R/'GRAPHICS_COVERAGE_X14_20261112/cache']
 for p in new:
  tm=str(p['TMID']);dob=p['source_dob'];r=dict(TMID=tm,Name=p['name'],SourceDOB=dob,PreparedSubjectID=p['subject_id'],FinalNativeUID='',Status='',SourcePortraitURL='',ReusableFile='',ImageSHA256='',ExistingImageUID='')
  for a in bytm.get((tm,dob),[]):
   img=staged.get(a['uid'])
   if not img:continue
   image=ROOT/img['path']
   if image.is_file()and sha(image)==img['sha256']:
    with Image.open(image)as im:assert im.format=='PNG'and im.size==(180,180);im.verify()
    r.update(Status='READY_VALIDATED_STAGING_EXACT_TMID_DOB',ReusableFile=str(image),ImageSHA256=img['sha256'],ExistingImageUID=a['uid']);break
  raw=p.get('PlayerRaw')or{};rel=raw.get('raw_file','');rp=E/rel if rel else None;item=None
  if rp and rp.is_file():
   if rp not in rawcache:
    assert sha(rp)==raw['file_sha256'];wrap=read(rp);body=wrap['body'];assert hashlib.sha256(body.encode()).hexdigest()==raw['body_sha256'];data=json.loads(body).get('data')or[];data=data.get('players',[])if isinstance(data,dict)else data;rawcache[rp]={str(x['id']):x for x in data};pins[str(rp)]=sha(rp)
   item=rawcache[rp].get(tm)
  if item and item.get('lifeDates',{}).get('dateOfBirth')==dob:
   url=item.get('portraitUrl');url=url if isinstance(url,str)and url.startswith('https://')and'default'not in url.lower()else'';r['SourcePortraitURL']=url
  else:errors.append(dict(TMID=tm,Issue='source_raw_missing_or_exact_DOB_not_verified'))
  if not r['Status']and r['SourcePortraitURL']:
   key=hashlib.sha256(r['SourcePortraitURL'].encode()).hexdigest()+'.bin'
   for base in cacheroots:
    image=base/key
    if not image.is_file():continue
    try:
     with Image.open(image)as im:assert im.width>=20 and im.height>=20;im.verify()
     with Image.open(image)as im:im.load();assert im.convert('RGBA').getbbox()is not None
     r.update(Status='READY_SHARED_CACHE_EXACT_SOURCE_URL',ReusableFile=str(image),ImageSHA256=sha(image));break
    except Exception as ex:errors.append(dict(TMID=tm,Issue='invalid_cached_image',Path=str(image),Error=type(ex).__name__))
  if not r['Status']:r['Status']='CONFIRMED_SOURCE_URL_NOT_CACHED'if r['SourcePortraitURL']else'NO_CONFIRMED_PORTRAIT_URL'
  results.append(r)
 statuses=dict(collections.Counter(r['Status']for r in results));finalpath=N/'final-native-player-UID-ledger.csv';finalpins=N/'final-artifact-pins.json';finalready=False
 if finalpath.is_file()and finalpins.is_file():finalready=read(finalpins).get('final-native-player-UID-ledger.csv')==sha(finalpath)
 summary=dict(Status='PROVISIONAL_ENGLAND_CACHE_AUDIT_NO_FINAL_UID_ASSUMPTIONS',PreparedProfiles=len(prov),PreparedReuse=manifest['counts']['reuse'],PotentialNewProfiles=len(new),Availability=statuses,ReadyImages=sum(r['Status'].startswith('READY_')for r in results),NewDownloadCandidates=sum(r['Status']=='CONFIRMED_SOURCE_URL_NOT_CACHED'for r in results),ExplicitPortraitGaps=sum(r['Status']=='NO_CONFIRMED_PORTRAIT_URL'for r in results),FinalLedgerPinAvailable=finalready,FinalLedger=str(finalpath),SourceRawFilesChecked=len(rawcache),NetworkRequests=0,NewImagesCreated=0,PublicWrites=0,DatabaseWrites=0,GameAccess=False,Errors=errors)
 with(O/'potential-new368-image-cache.csv').open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(results[0]),delimiter=';');w.writeheader();w.writerows(results)
 dump('cache-readiness.json',summary)
 lines=['# Anglia - przyrost grafik po finalnym ledgerze','',f'Prepared4016:3648reuse+368potentialnew. Sprawdzono tylko lokalny staging/cache dla368osob po dokladnymTMID i sourceDOB; nie nadano przyszlychUID.',f'Gotowe obrazy:{summary["ReadyImages"]}; potwierdzoneURL wymagajace pobrania:{summary["NewDownloadCandidates"]}; brakpotwierdzonegoURL:{summary["ExplicitPortraitGaps"]}. Finalnyledgerhashgotowy:{finalready}. To wyniki przygotowania, nie liczby finalnie utworzonych zawodnikow.','', '1. Poczekac na native-prep/final-native-player-UID-ledger.csv oraz final-artifact-pins.json; sprawdzic hash ledgeru i odpowiadajacego mu prepared/provenance. Nie uzywac liczb source4256 ani starszych draftow zamiast finalnego4016/ewentualnych dalszych jawnychodlozen.','2. Polaczyc finalnyUID zTMID+RealDOB i sourceDOB, sprawdzic unikalnosc. RozdzielicNew/reuse, zachowac istniejace poprawnePNG i mapowania. Bez zgadywaniaUID zSubjectID/seed/range.','3. Reuse dokladny TMID+DOB z potential-new368-image-cache.csv oraz potwierdzonyURL->SHAcache. Nie przenosic starychmap; dla nowego finalUID utworzyc przyrostowa kopie grafiki/stage. Najpierw odfiltrowacUID z poprawnym publicznym portretem, aby nie dublowaczasobow.','4. Z finalnegoclub-map orazforeign_owner_map przygotowac tylko faktyczniebrakujace herby/koszulki; Fisherforeignowner uwzglednic jesli finalnieutworzony. Korzystac zcache/profile/pack, bezpowtornegopobieraniakraju/kadr. Niepewnaidentyfikacja/portraitURL pozostajejawna luka; zadnychfikcyjnych obrazow.','5. Oddzielny england-extension/staging i osobny manifest; NIEzmieniac zatwierdzonych23881PNG ani trzech obecnychplanow. Uzyc istniejacego build_graphics.py i transakcyjnegoinstalatora; nie tworzyc nowegoimportera.','6. PolaczoneUID/nazwa/klub/ligamusza pochodzi zfinalnychmap; format180face/logo,20icon,130kit. Instalacja dopiero po rootreview iFM==0/HOLDrelease. Po poprzednichtransakcjach odswiezycpublicconfigsnapshot, zachowacwszystkiestarewpisy/PNG,blokowackolizje,backup+readback.','7. Futwiz403 bezretry/proxy/zmianURL. FC12localpersonalonly, grafiki pozaGitHub/publicznymZIP. Brak oslabianiawalidacji w celuosiagniecia100%pokrycia.','', 'Sprawdzanie bylo bezsieci, beznowychPNG, bezRPM/WPM/FM/editor i bezDBwrite. Finalnegoledgeru nie trzeba traktowacjakozaleznosciimportu: tenwatek nieblokujezapisuAnglii.']
 (O/'INSTRUKCJA.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');assert all(sha(Path(p))==h for p,h in pins.items()),'Source inputs changed during cache audit';dump('manifest.json',dict(Status=summary['Status'],Inputs=pins,ScriptSHA256=sha(Path(__file__)),Outputs={n:sha(O/n)for n in['potential-new368-image-cache.csv','cache-readiness.json','INSTRUKCJA.md']},NetworkRequests=0,PublicWrites=0,DBWrites=0));print(json.dumps(summary,ensure_ascii=True),flush=True);print('MANIFEST_SHA256',sha(O/'manifest.json'),flush=True)
if __name__=='__main__':main()
