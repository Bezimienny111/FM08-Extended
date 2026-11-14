from pathlib import Path
from collections import Counter
import json,hashlib
B=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
r={x['TMID']:x for x in read(B/'club-plan-draft.json')};world={x['ClubUID']:x for x in read(B/'native-world-identities.json')};persons=read(B/'person-identity-candidates.json')
choices=[('384',1022,'MVV current club-code/name plus Maastricht qualifier; unique native MVV in Holland, preserve ownfirst-team identity'),('150',1733,'RealBetisBalompie versus native RealBetisB.,SAD; B. is abbreviated Balompie in first-team full name, typed kind0 and ownfamily distinguish reserve'),('367',1729,'Same full RayoVallecano deMadridSAD with source spaced S.A.D.; purely legalpunctuation spelling'),('8733',2092,'Current CeltaFortuna profile explicitly retains CeltaVigoB; native CeltaB typedparent1724 equals sourceparent940'),('2672',979,'APO Levadiakos versus APO Levadeiakos: standard romanization, country and unique qualified Levadiakos name'),('6418',129665,'PanetolikosAgrinio versus GFS Panaitolikos: romanization of same specific club name, preserve nativefounded1926'),('5572',129704,'Source official NikiVolouFootballClub versus native GS NikiVolou; Volos is city spelling, not NikiPolygyrou'),('4585',129658,'AnagennisiKarditsa versus AnagennisiKarditsas: Greek grammatical ending; distinctive same club name, not AO Karditsa'),('4603',978,'AE Larisa versus AE Larisa1964; founding-year suffix in native fullname, not other Larisas clubs'),('3392',129659,'Profile current ApollonKalamaria and historical ApollonPontou/1926 versus native MGS ApollonKalamarias; grammatical ending plus same explicit source history'),('11273',2048,'Source official SASP RodezAveyronFootball versus native RodezAveyronFootball; SASP legalprefix only'),('9202',2072,'Source UnionSportiveduLittoraldeDunkerque versus native US LittoralDunkerque; same full expanded name'),('1080',2062,'Source StadeLavalloisMayenneFootballClub versus native StadeLavalloisMayenneFC53; FC abbreviation and department53 suffix'),('7042',2002,'Source official UnionSportiveBoulogneCoteOpale versus native US BoulogneCoteOpale; expanded US and spacing/apostrophe'),('11131',8503181,'Source Klubi04/HJKparent1008 versus native Klubi04 typedparent816; punctuation and Helsinki qualifier')]
out=[]
for tid,u,why in choices:
 x=r[tid];w=world[u];assert w['TeamCountry']==x['NativeCountryIndex']
 if x['ParentTMID']:assert r[x['ParentTMID']]['NativeClubUID']==w['ParentUID']
 else:assert w['ParentUID']is None and w['NativeTeamKind']==0
 supports=[]
 for p in persons:
  if p['PlayingClubTMID']!=tid or not p['ExistingUID']or p['Loan']:continue
  n=next((n for n in p['NativeCandidates']if int(n['ID'])==p['ExistingUID']),None)
  if n and int(n['ClubIndex'])==w['TeamIndex']:supports.append(dict(TMID=p['TMID'],UID=p['ExistingUID'],DOB=n['BirthDate'],OwnerTEAM=int(n['ClubIndex'])))
 out.append(dict(TMID=tid,NativeClubUID=u,Reason=why,SourceNames=x['SourceNames'],SourceProfile=x['ProfileFile'],SourceProfileSHA256=hashlib.sha256(Path(x['ProfileFile']).read_bytes()).hexdigest(),NativeWitness=w,SupportingNativeRosterPeople=supports,NewSources=0,CountryRepair=False,NativeKindOrParentRepair=False))
(B/'local-identity-decisions.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('LOCAL_CACHE_ALIAS_DECISIONS',len(out))