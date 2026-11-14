from pathlib import Path
import json,hashlib,sys
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;S=B.parent
rd=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,x):(B/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
w={x['ClubUID']:x for x in rd(B/'native-world-identities.json')};draft=rd(B/'club-plan-draft.json')
reuse={'3057':250,'1096':262,'475':278,'1199':292,'3789':234,'44394':8152873,'7672':239,'11939':3200589,'14':152,'4383':137953,'4443':5602973,'7001':5605434,'2364':101154,'1829':102485,'14602':3101435,'10233':102472,'5551':426430,'7831':130220,'8445':15004168,'3901':527945,'28643':539089,'28107':18008817,'2715':216,'2974':3200591}
reasons={
'3901':'Matricule94: cached RACS Couillet historical name and official RAAL history; preserve unrelated old La Louvieroise169. https://www.raal.be/histoire/',
'28643':'Matricule4068: cached Red Star Waasland history and official2022 agreement; preserve KSK Beveren266. https://www.skbeveren.be/2022/06/historisch-akkoord/',
'28107':'Current Lierse Kempenzonen history identifies KFC Oosterzonen: unique native Oosterzonen Oosterwijk18008817; preserve old Lierse268.',
'2715':'Seraing matricule167 is former Boussu-Dour/Francs-Borains216, not Seresien3200935. Official former club confirms2014 move. https://www.francsborains.be/histoire-le-matricule-167/',
'2974':'Current Francs Borains matricule5192 is Heppignies Lambusart Fleurus3200591;167 is now Seraing. https://www.francsborains.be/wp-content/uploads/2023/04/5192-Royal-Francs-Borains.pdf ; https://www.walfoot.be/news/2014-05-15/boussu-dour-en-promotion-charleroi-fleurus-en-p1',
'8445':'Exact existing Wellington Phoenix15004168. Preserve native sporting country Australia177; source physical New Zealand180 recorded. No new club or country overwrite.',
'7831':'Same Brisbane/Queensland Roar entity and Suncorp ground; retain native130220.',
'2364':'Exact First Vienna101154 retains kind9/contract family16009253. Preserve existing shared-family representation; no role conversion, parent edit or duplicate family.',
'4383':'Young Violets is Austria Wien Amateure137953 kind14 parent152; historical source Austria Vienna Reserves plus Generali ground.',
'4443':'SturmII5602973 kind14 parent156; source historical Sturm Amateure alias.',
'7001':'RapidII5605434 kind14 parent155; exact source parent and amateur/II role.'}
new_overrides={'54291':[171],'11853':[158],'130767':[1300125],'54189':[257,212],'37024':[16001238,137976],'23158':[137965]}
plans=[];dec=[]
for src in draft:
 x=dict(src);t=x['TMID'];u=reuse.get(t,x['NativeClubUID']);reason=reasons.get(t,'Explicit full-name/local alias with correct country and team role; cached current/profile/history evidence.') if t in reuse else x['IdentityReason']
 if t in new_overrides:u=None;reason='Current confirmed entity retained separately; predecessor continuity or representation not proven within bounded evidence. Preserve historical candidates.'
 if u:
  z=w[u]
  if t=='8445':x['NativeCountryIndex']=z['TeamCountry'];x['SportingCountryException']='Native A-League country Australia retained; source physical New Zealand recorded'
  assert z['TeamCountry']==x['NativeCountryIndex'],(t,u,'country')
  if x['ParentTMID']:assert z['ParentUID'],(t,u,'source reserve mismatch')
  elif z['ParentUID']:assert t=='2364' and z['NativeTeamKind']==9,(t,u,'unsupported representation')
  x.update(NativeClubUID=u,NativeTeamIndex=z['TeamIndex'],NativeFamilyIndex=z['TeamTailFamilyIndex'],NativeContractFamilyIndex=z['TeamTailFamilyIndex'],NativeContractFamilyUID=z['TeamTailFamilyUID'],NativeParentUID=z['ParentUID'],NativeTeamKind=z['NativeTeamKind'],ExistingStadiumIndex=z['StadiumIndex'],SourceCountryIndex=z['TeamCountry'],NativeCountryRepairTo=None,YearFounded=z['YearFounded'],IdentityDecision='reuse_explicit_closed_identity',IdentityReason=reason)
 else:
  x.update(NativeClubUID=None,NativeTeamIndex=None,NativeFamilyIndex=None,NativeContractFamilyIndex=None,NativeContractFamilyUID=None,NativeParentUID=None,NativeTeamKind=None,ExistingStadiumIndex=-1,SourceCountryIndex=x['NativeCountryIndex'],NativeCountryRepairTo=None,YearFounded=0,IdentityDecision='new_distinct_confirmed_current_entity',IdentityReason=reason)
  x['PreserveNativeUIDs']=sorted(set(new_overrides.get(t,[])+[v['UID']for v in x['FreshCandidates']]))
 x.update(NativeImportEligible=True,SugarDaddy=False,DesiredDivision=x['TargetNativeDivisionIndex'],DesiredAlternative=x.get('TargetNativeAlternativeDivisionIndex',-1),RegionalDivision=-1)
 if x['ParentTMID'] and not u:
  x['RequiredNativeReserveKind']=14 if x['Country']=='Austria' else 3
  x['ReserveKindEvidence']='Frozen Austria second-level native137953/137976 kind14; linked role retained' if x['Country']=='Austria' else 'Existing common linked B-team role3 schema. Belgium newB generic nonplaying550 only; parent preserved.'
 plans.append(x);dec.append(dict(TMID=t,Name=x['Name'],UID=u,Decision=x['IdentityDecision'],Reason=reason,SourceSHA256=sha(Path(x['ProfileFile'])),PreserveNativeUIDs=x.get('PreserveNativeUIDs',[])))
bytm={x['TMID']:x for x in plans}
for x in plans:
 if x['ParentTMID']:
  par=bytm[x['ParentTMID']];assert par['NativeCountryIndex']==x['NativeCountryIndex']
  if x['NativeClubUID']:assert x['NativeParentUID']==par['NativeClubUID'],(x['TMID'],'parent')
assert len({x['NativeClubUID']for x in plans if x['NativeClubUID']})==sum(bool(x['NativeClubUID'])for x in plans)
bel=[189,204,214,260,276,281,283,3200568,3200583,3200584,6600093,6600097,8154745,178,215,206]
blr=[485661,485664,485683,5410551,7484293,7484294,17000071,17001659,485673,485676]
used={x['NativeClubUID']for x in plans if x['NativeClubUID']};fallback=[]
for country,us in [('Belgium',bel),('Belarus',blr)]:
 for u in us:
  z=w[u];assert u not in used and z['NativeTeamKind']==0 and not z['ParentUID'] and z['TeamCountry']==(131 if country=='Belgium' else 132)
  fallback.append(dict(LogicalKey='retained-existing-'+str(u),TMID=None,NativeClubUID=u,Name=z['Names'][0],Country=country,NativeCountryIndex=z['TeamCountry'],DesiredDivision=801 if country=='Belarus' else None,DesiredAlternative=-1,DesiredRegional=-1,NoPersonImport=True,PreserveRosterAndFamily=True,PreserveNames=True,Modernized=False,Reason='Existing senior physical TEAM retained for classic format; no asserted2026 rank/current modernization',NativeWitness=z))
dump('club-plan.json',plans);dump('identity-decisions.json',dec);dump('deferred-clubs.json',[]);dump('structural-fallbacks.json',fallback)
assign=[dict(TMID=x['TMID'],Name=x['Name'],Country=x['Country'],NativeClubUID=x['NativeClubUID'],DesiredDivision=x['DesiredDivision'],DesiredAlternative=x['DesiredAlternative'],DesiredRegional=-1,DesiredCompetitionUID=x['TargetNativeCompetitionUID'],SourceParentTMID=x['ParentTMID'],RequiredNativeReserveKind=x.get('RequiredNativeReserveKind'),PreserveNativeKind=x['NativeTeamKind'],Reason=x['ClassicPlacementReason'])for x in plans]
dump('core-assignments.json',assign)
report=dict(Status='IDENTITIES_RESOLVED_REGIONAL_PROJECTION_PENDING',Clubs=201,Reuse=sum(bool(x['NativeClubUID'])for x in plans),New=sum(not x['NativeClubUID']for x in plans),StructuralPreserved=26,ReconciledMemberships=39,SharedFamilyPreserved=['2364'],NativeWrite=False,PlanSHA256=sha(B/'club-plan.json'))
dump('identity-plan-summary.json',report);print(json.dumps(report))
