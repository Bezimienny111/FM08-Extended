"""Freeze club identities and geographic allocation; no native DB writes."""
from x10_pipeline import *
from collections import Counter
def main():
 targets=read(B/'source-targets.json');draft={x['TMID']:x for x in read(B/'club-plan-draft.json')};world={x['ClubUID']:x for x in read(B/'native-world-identities.json')};rr={x['TMID']:x for x in read(R/'RUSSIA_RSA_PREP_X10_20261111/club-native-resolution.json')};rootro={str(x['tmid']):x for x in read(B/'root-romania-identity-decisions.json')['decisions']}
 aliases={'6622':1301374,'32113':5742611,'33328':5748006,'4645':120779,'8819':5742987,'3544':120783,'4646':136465}
 forcednew={
 '2209':('Borac1926 follows2019 Provo relocation/rename; no safe Provo native; do not take historicalBorac1301381','https://www.prvaliga.rs/en/tim/borac-1926/'),
 '31146':('OriginalBor ceased2017_18; currentBor1919 created2018_19','https://fkbor1919.rs/istorija/'),
 '42813':('OriginalDubocica withdrew2014; currentGFK project separate, preserve136468','https://www.juznevesti.com/sport/dubocica-i-zvanicno-odustala-od-takmicenja/'),
 '36923':('CurrentOFKVrsac derivesOFKVrsacUnited founded2007, not olderFKVrsac native5746397; no safe continuous reuse proved','https://en.wikipedia.org/wiki/OFK_Vr%C5%A1ac'),
 '2674':('CurrentProleter023 isNaftagasElemir relocation2026, nativeNaftagas missing; do not use oldBanat/Proleter records','https://fkproleter023.com/istorija/'),
 '8687':('CurrentCSMCeahlaul2016 separate from dissolved oldFC club1498','https://www.acsmceahlaul.ro/'),
 '111687':('CurrentACSMinerulLupeni reformed2021 separate nativehistoricalMinerul7546336','https://www.transfermarkt.com/-/startseite/verein/111687')}
 plan=[]
 for c in targets:
  x=dict(c);d=draft.get(c['TMID'],{});uid=d.get('NativeClubUID');decision=d.get('IdentityDecision');why='Fresh native full-name/country match and current source profile; no known identity split';evidence=['https://www.transfermarkt.com/-/startseite/verein/'+c['TMID']]
  if c['Country']in['Russia','South Africa']:
   z=rr[c['TMID']];uid=z['NativeClubUID'];decision=z['decision'];why=z['reason'];evidence=z['evidence'];x['NativeCountryRepairTo']=z.get('NativeCountryRepairTo')
  elif c['TMID']in aliases:uid=aliases[c['TMID']];decision='reuse_verified_native_historical_name_alias';why='Same club and town, sponsor/transliteration/name variant; explicit canonical native UID'
  elif c['TMID']in rootro:
   z=rootro[c['TMID']];uid=None;decision='new_distinct_entity';why=z['evidence_paraphrase'];evidence=z['sources'];x['YearFounded']=z.get('entity_foundation_year_supported')or 0
  elif c['TMID']in forcednew:uid=None;decision='new_distinct_entity';why,e=forcednew[c['TMID']];evidence=[e]
  elif c['TMID']=='frf-kse-targu-secuiesc':uid=57002781;decision='reuse_native_current_official_identity_structural_only';why='Same native ACSKSETarguSecuiesc; preserve roster, no forced player search';evidence=['https://ksetargusecuiesc.com/',c['RankingEvidence']]
  elif decision=='ambiguous_native_identity':raise AssertionError(('unresolved_core_identity',c['TMID'],c['Name']))
  elif uid is None:decision='new_missing_native_entity';why='Current real source participant; no verified safe native country/full-historical name match; preserve old histories'
  w=world.get(uid,{})
  if uid:
   assert w and (w['Country']==c['NativeCountryIndex']or w['Country']==-1),(c['TMID'],uid,w)
   if w['Country']==-1:x['NativeCountryRepairTo']=c['NativeCountryIndex']
  x.update(NativeClubUID=uid,NativeTeamIndex=w.get('TeamIndex'),NativeFamilyIndex=w.get('FamilyIndex'),SourceCountryIndex=w.get('Country'),ExistingStadiumIndex=w.get('StadiumIndex',-1),IdentityDecision=decision,IdentityReason=why,IdentityEvidence=evidence,ParentTMID=c.get('ParentTMID',''),PublicStadium=read(B/c['ProfileFile']).get('stadium')or{},SugarDaddy=False,NativeMappingFinal=True)
  plan.append(x)
 roman=[x for x in plan if x['Country']=='Romania'and x['DesiredDivision']is None];assert len(roman)==36
 locked_east={'122344','frf-kse-targu-secuiesc'};locked_west={'111687'}
 geographic=[x for x in roman if x['TMID']not in locked_east|locked_west]
 assert all(x['PublicStadium'].get('longitude')is not None for x in geographic)
 ordered=sorted(geographic,key=lambda x:(-float(x['PublicStadium']['longitude']),x['TMID']))
 east=locked_east|{x['TMID']for x in ordered[:18-len(locked_east)]}
 for x in roman:
  x['DesiredDivision']=863 if x['TMID']in east else 864
  x['RegionalRule']='East/West geographic split18each; published stadium longitude with county fallback KSE/Cov asnaEast,StefanestiIlfovEast,MinerulHunedoaraWest'
  x['RegionalLocationEvidence']='confirmed county fallback without invented coordinates'if x['TMID']in locked_east|locked_west else dict(stadium_name=x['PublicStadium'].get('name'),address=x['PublicStadium'].get('address_line_2'),longitude=x['PublicStadium'].get('longitude'))
 assert len(plan)==154 and len({x['TMID']for x in plan})==154
 reused=[x['NativeClubUID']for x in plan if x['NativeClubUID']];assert len(reused)==len(set(reused))
 expected={210:12,767:18,862:18,863:18,864:18,177:16,178:22,202:16,203:16}
 assert Counter(x['DesiredDivision']for x in plan)==Counter(expected)
 dump(B/'club-plan.json',sorted(plan,key=lambda x:bool(x['ParentTMID'])))
 dump(B/'core-identity-finalization.json',dict(status='identities_and_source_allocation_final_no_database_write',clubs=len(plan),reused=len(reused),new_teams=154-len(reused),new_reserves=[x['TMID']for x in plan if x['ParentTMID']],country_repairs=[dict(TMID=x['TMID'],ClubUID=x['NativeClubUID'],before=x['SourceCountryIndex'],after=x['NativeCountryRepairTo'])for x in plan if x.get('NativeCountryRepairTo')is not None],native_playable_counts=expected,source_club_counts=dict(Counter(x['Country']for x in plan))))
 print('CORE154',Counter(x['Country']for x in plan),'reuse',len(reused),'new',154-len(reused),'counts',expected,flush=True)
if __name__=='__main__':main()
