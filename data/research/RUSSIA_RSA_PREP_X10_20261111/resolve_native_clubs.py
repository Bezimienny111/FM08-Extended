from pathlib import Path
import json,collections,hashlib
R=Path.cwd()/'FmLauncher/data/research';B=R/'RUSSIA_RSA_PREP_X10_20261111'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
world=read(R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/native-world-identities.json');byuid={x['ClubUID']:x for x in world}
draft={x['TMID']:x for x in read(R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/club-plan-draft.json')if x['Country']in['Russia','South Africa']}
targets=read(B/'source-targets.json')
aliases={'964':1301108,'232':1529,'2410':1518,'121':1520,'932':1525,'2698':130509,'2741':1301106,'1083':1301104,'3725':477632,'2696':1523,'14589':477352,'1124':130496,'11127':1533,'1186':130498,'23110':130553,'14590':477455,'3729':130501,'3690':130561,'12439':130548,'3714':130506,'2374':130510,'3243':1522,'11125':477540,'3733':130550,'3834':130511,'11123':476286,'6432':8066924,'6356':1644,'2557':1645,'568':1643,'9370':130772,'14187':5682979,'7011':131270,'2303':5680082,'23285':5688086}
notes={
'16704':('Krasnodar2008 is distinct from nativeKrasnodar2000 UID484768',[]),
'41231':('Sochi2018 is distinct from Sochi04 native8081702',[]),
'75231':('Current Makhachkala2019/Dinamo2021 differs from old Dinamo1946 native476932',[]),
'49702':('Current Olimpiyets2015 differs from old FC NizhniyNovgorod2007 native58022748',[]),
'75068':('New ANO FCNovosibirsk createdJuly2019, renamedSibirJune2024; not native58001661',['https://www.fcsib.ru/club/history/']),
'3609':('Old SC Rotor went bankrupt2015; current reformed project kept separate',['https://www.themoscowtimes.com/2015/04/09/russian-football-club-rotor-volgograd-goes-bust-a45620']),
'12668':('RichardsBay2017 is not Hellenic130764 or Thanda5680099; licence acquisition does not prove identity',[]),
'14187':('Same Maritzburg club relocates2024 and renamesDurbanCity; not historical DurbanCity5682155',['https://maritzburgunited.co.za/240814-club-statement.htm','https://durbancityfc.com/about/']),
'2303':('Owner statement confirms purchase of whole MpumalangaBlackAces club and relocation2016',['https://www.news24.com/sport/soccer/psl/comitis-confirms-black-aces-will-relocate-20160606','https://www.sportsclub.co.za/local/cape-town-city-unveiled/']),
'6432':('First team itself namedVolgarGazprom2 in2007-2009; standalone nativefinancialfamily/ParentUIDNone, not automatic Bteam takeover',['https://volgar-fc.ru/history','https://fakelfc.ru/news/view/8719-predstavlyaem-sopernika-volgar']),
'133914':('LeicesterfordCity133914 differs from JDRStars54668; no licence-only identity merge',[]),
'102349':('Official RealNative is current CasricStars; no safe oldentity to hijack',['https://www.psl.co.za/'])}
out=[]
for c in targets:
 tid=c['TMID'];uid=aliases.get(tid);v=byuid.get(uid);p=read(B/c['ProfileFile'])
 if v:
  assert v['ParentUID']is None
  assert v['Country']==c['NativeCountryIndex']or(tid=='3729'and uid==130501 and v['Country']==-1 and 'Arsenal Tula'in v['Names'])
 why,urls=notes.get(tid,('Canonical firstteam current/fullhistorical identity and country; alias checked; no linkedreserve taken'if v else'Current real club confirmed; no safe native continuity, create separately preserving unrelated historical entities',[]))
 candidates=draft.get(tid,{}).get('NativeCandidates',[])
 if v and not any(x['ClubUID']==uid for x in candidates):candidates=candidates+[v]
 out.append(dict(TMID=tid,Name=c['Name'],Country=c['Country'],NativeClubUID=uid,NativeTeamIndex=v['TeamIndex']if v else None,NativeFamilyIndex=v['FamilyIndex']if v else None,ParentClubUID=None,NativeCountryRepairTo=165 if tid=='3729'else None,decision='reuse_verified_identity'if v else'new_distinct_or_missing_native_entity',reason=why,evidence=[dict(kind='profile',path=c['ProfileFile'],url='https://www.transfermarkt.com'+p.get('url','')),dict(kind='native_catalogue',path='../SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/native-world-identities.json')]+[dict(kind='continuity_evidence',url=u)for u in urls],candidates=candidates))
used=[x['NativeClubUID']for x in out if x['NativeClubUID']]
assert len(out)==70 and len(used)==len(set(used))==35
(B/'club-native-resolution.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
summary=dict(total=70,reuse=35,new=35,no_UID_allocation=True,no_DB_write=True,all_reused_parent_None=True,explicit_missing_country_repair={'130501':165})
(B/'club-native-resolution-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
m=read(B/'manifest.json');m['native_identity_resolution']=summary;m['files']['club-native-resolution.json']=hashlib.sha256((B/'club-native-resolution.json').read_bytes()).hexdigest()
(B/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary))
