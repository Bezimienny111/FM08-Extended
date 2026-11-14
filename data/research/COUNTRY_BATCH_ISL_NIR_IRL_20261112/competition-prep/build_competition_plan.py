from pathlib import Path
import json,re,html,hashlib,datetime,unicodedata
B=Path(__file__).resolve().parent;P=B.parent;R=P.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(name,x):(B/name).write_text(json.dumps(x,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def text(name):
 raw=(B/'sources'/(name+'.html')).read_bytes()
 try:s=raw.decode('utf-8')
 except UnicodeDecodeError:s=raw.decode('windows-1252',errors='replace')
 return html.unescape(re.sub('<[^>]+>','',s))
rx=re.compile(r'^\s*(\d+)\.\s*([^\d\n]+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*-\s*(\d+)\s+(-?\d+)',re.M)
def rows(s):
 a=[]
 for m in rx.finditer(s):
  rank,name,mp,w,d,l,gf,ga,pts=m.groups();a.append(dict(Position=int(rank),Name=name.strip(),Matches=int(mp),Wins=int(w),Draws=int(d),Losses=int(l),GoalsFor=int(gf),GoalsAgainst=int(ga),Points=int(pts)))
 return a
def first_table(s,key):
 start=s.index(key);start=s.index('Final Table',start);tail=s[start:]
 lines=tail.splitlines();a=[]
 for line in lines:
  r=rows(line)
  if r:a.extend(r)
  elif a and not line.strip():break
 return a
def validate(a,n,mp):
 assert len(a)==n and len({r['Position'] for r in a})==n
 assert {r['Position'] for r in a}==set(range(1,n+1))
 assert all(r['Matches'] in mp for r in a)
 assert all(r['Wins']+r['Draws']+r['Losses']==r['Matches'] for r in a)
 return a
isl=text('isl-2025');nir=text('nir-2025-26');irl=text('irl-2025')
# Post-split cumulative final rows replace regular-stage tables; never sum cumulative phases.
a=first_table(isl,'Championship Playoff  \u00a7champ')+first_table(isl,'Relegation Playoff  \u00a7releg')
is1=validate(a,12,{27});is2=validate(first_table(isl,'==== 1. deild ===='),12,{22});is3=validate(first_table(isl,'==== 2. deild ===='),12,{22})
prem_end=nir.index('Cup Tournaments',nir.index('Playoff Stage'))
ni1=validate(sorted({r['Position']:r for r in rows(nir[:prem_end]) if r['Matches']==38}.values(),key=lambda r:r['Position']),12,{38})
start=nir.rindex('\nChampionship\n');end=nir.index('Premier Intermediate League',start)
ni2=validate(rows(nir[start:end]),12,{38});ni3=validate(first_table(nir[nir.rindex('\nPremier Intermediate League\n'):],'Premier Intermediate League'),14,{26})
ir1=validate(first_table(irl,'SSE Airtricity League'),10,{36});ir2=validate(first_table(irl[irl.rindex('\nFirst Division\n'):],'First Division'),10,{35,36})
lein=text('irl-leinster-finals');mun=text('irl-munster-finals')
def season_cut(s,label,nextlabel):
 start=s.rindex('\n'+label+'\n');end=s.find('\n'+nextlabel+'\n',start+1);return s[start:end if end>=0 else len(s)]
ls=validate(rows(season_cut(lein,'2024/25','2025/26')),14,{26})
ms=validate(first_table(season_cut(mun,'2024/25','2025/26'),'Premier Division'),10,{18})
tables={'Iceland_Besta_2025':dict(Source='sources/isl-2025.html',Season='2025',Stage='Cumulative final championship1-6 and relegation7-12',Rows=is1),'Iceland_First_2025':dict(Source='sources/isl-2025.html',Season='2025',Rows=is2),'Iceland_Second_2025':dict(Source='sources/isl-2025.html',Season='2025',Rows=is3),'NorthernIreland_Premier_2025_26':dict(Source='sources/nir-2025-26.html',Season='2025/26',Stage='Final cumulative split table',Rows=ni1),'NorthernIreland_Championship_2025_26':dict(Source='sources/nir-2025-26.html',Season='2025/26',Stage='Final cumulative split table',Rows=ni2),'NorthernIreland_PIL_2025_26':dict(Source='sources/nir-2025-26.html',Season='2025/26',Rows=ni3),'Ireland_Premier_2025':dict(Source='sources/irl-2025.html',Season='2025',Rows=ir1),'Ireland_First_2025':dict(Source='sources/irl-2025.html',Season='2025',Note='Harps/Kerry35matches final: voidmatch, not incomplete season',Rows=ir2),'Ireland_Leinster_2024_25':dict(Source='sources/irl-leinster-finals.html',Season='2024/25',Rows=ls),'Ireland_Munster_2024_25':dict(Source='sources/irl-munster-finals.html',Season='2024/25',Rows=ms)}
dump('closed-tables.json',tables)
world=R/'COUNTRY_BATCH_KOR_COL_ISR_20261112/native-world-identities.json';w=read(world);by={r['ClubUID']:r for r in w}
req=read(P/'native-competition-requirements.json')
for path,h in req['source_pins'].items():assert sha(Path('J:/FM08dev')/path)==h
# CompetitionUIDs refer to existing competitions. No new club UID is allocated here.
comp={899:7840132,900:7840133,904:7841964,161:130023,162:130024,275:147023,125:129372,126:129373}
countryidx={'Iceland':148,'Northern Ireland':159,'Ireland':163}
core=read(P/'source-targets.json');assert len(core)==72
extraids=[(68651,'Dollingstown',52004979),(84162,'Ballymacash Rangers',414171),(38179,'Portstewart',130170),(97229,'Oxford Sunnyside',None),(35843,'Dergview',416241),(9025,'Ballyclare Comrades',1273),(48871,'Knockbreda',414230),(21931,'Coagh United',130167),(4421,'Lisburn Distillery',1280),(21932,'Banbridge Town',130159),(77129,"St James Swifts",None),(109766,'Rosario',414168),(44769,"St. Mochta's",561413),(33029,'Midleton',129426)]
extras=[]
for tm,name,uid in extraids:
 profile=B/'sources/tm-clubs'/f'{tm}-profile.json';x=read(profile);country='Northern Ireland' if len(extras)<12 else 'Ireland';native=by.get(uid)
 if native:assert native['Country']==countryidx[country] and native['NameFamilyIndex']==native['TeamTailFamilyIndex'] and native['TeamTailFamilyUID']==uid and native['NativeTeamKind']==0
 extras.append(dict(Country=country,LeagueCountry=country,TMID=str(tm),Name=x['name'],RealLevel=3,APISeason='2026' if country=='Northern Ireland' else '2025',RealSeason='26/27' if country=='Northern Ireland' else '2026',Competitions=['NIR3' if country=='Northern Ireland' else 'regional_classic_backfill'],ProfileFile=str(profile),ProfileSHA256=sha(profile),NativeClubUID=uid,IdentityDecision='reuse_confirmed_country_name_family' if uid else 'new_confirmed_real_entity',IdentityEvidence=([native] if native else [])+[dict(Source='sources/nir-conference-participants.html' if country=='Northern Ireland' else 'closed-tables.json',Evidence='Current2026/27 conference participant, not a fabricated club' if country=='Northern Ireland' else '2024/25 regional champion selected for classic-format shortage')],PlayersFetched=0,RosterStatus='PARTIAL_SOURCE_NOT_COLLECTED_ENGINE_FILL_PER_USER',SourceDatesShifted=False,SugarDaddy=False,PublicStadium=x.get('stadium') or dict(name=x.get('stadium_name'),capacity=x.get('stadium_seats')),SourceClubURL='https://www.transfermarkt.com'+x['url']))
assert len(extras)==14
dump('extra-clubs.json',extras)
plans=[];moves=[]
# High-priority previous top tier comes before previous lower tier; then final rank.
niup={'3463','63172','41137','24104'};irup={'27774','7039'};isdown={'21864','8037'};islower={'25873','30580'}
for r in core+extras:
 t=str(r['TMID']);c=r['Country'];level=r['RealLevel'];curr=alt=None
 if c=='Iceland':
  curr=899 if level==1 and t not in isdown else (904 if t in islower else 900);alt=899 if level==1 else 900
 elif c=='Northern Ireland':curr=161 if level==1 or t in niup else (162 if level==2 else 275);alt=curr
 else:curr=125 if level==1 or t in irup else 126;alt=curr
 z=dict(r);z.update(LeagueCountry=c,NativeCountryIndex=countryidx[c],CurrentDivision=curr,CurrentDivisionUID=comp[curr],AlternativeDivision=alt,AlternativeDivisionUID=comp[alt],DesiredDivision=curr,DesiredAlternative=alt,RegionalDivision=None,RegionalPolicy='Preserve guarded existing regional value; new team sentinel-1; repair all engine-required regional minima independently',SourceRosterScope='existing72confirmed_squads' if r in core else 'additional14_partial_no_forced_squad',SugarDaddy=False)
 plans.append(z)
 if (c=='Iceland' and (t in isdown or t in islower)) or (c=='Northern Ireland' and t in niup) or (c=='Ireland' and t in irup):moves.append(dict(TMID=t,Name=r['Name'],Country=c,RealLevel=level,CurrentDivision=curr,AlternativeDivision=alt,Rule='Previous completed level then final rank; Iceland alternative restores12+12 native expansion'))
assert len(plans)==86 and len({str(z['TMID']) for z in plans})==86
for c,expected in [('Iceland',{899:10,900:12,904:2}),('Northern Ireland',{161:16,162:12,275:12}),('Ireland',{125:12,126:10})]:
 actual={i:sum(z['Country']==c and z['CurrentDivision']==i for z in plans) for i in expected};assert actual==expected,(c,actual)
assert {i:sum(z['Country']=='Iceland' and z['AlternativeDivision']==i for z in plans) for i in [899,900]}=={899:12,900:12}
# Existing regional baselines are not a claim that their rosters/memberships are modernized.
pools=[]
for q in req['requirements']:
 if q['CompetitionIndex'] in [899,900,161,162,275,125,126]:continue
 idx=q['CompetitionIndex'];members=[r for r in w if r['CurrentDivision']==idx];pools.append(dict(Requirement=q,MemberCount=len(members),Members=members,Interpretation='Entire existing COMP membership; do not apply country filtering by fallback UID. Validate post-loader effective count separately.'))
removals={394:[52004979,414171,1900709],163:[414175],572:[414179,414230,414168]}
regional=[]
for idx,uids in removals.items():
 q=next(x for x in req['requirements'] if x['CompetitionIndex']==idx);before=len([x for x in w if x['CurrentDivision']==idx]);regional.append(dict(CompetitionIndex=idx,CompetitionUID=q['CompetitionUID'],Before=before,Minimum=q['Minimum'],MovedOutUIDs=uids,AfterBeforeRepair=before-len(uids),RequiredBackfill=q['Minimum']-(before-len(uids)),Mode='Existing guarded native same-country cascade, not an assertion of contemporary regional allocation',NoSyntheticPeople=True))
assert sum(x['RequiredBackfill'] for x in regional)==7
dump('native-lower-pool-baseline.json',dict(NativeWorld=str(world),NativeWorldSHA256=sha(world),Pools=pools,RegionalRepairs=regional,UnchangedRequirements=req['requirements'],SpecialCalls=req['special_registration_calls']))
derry=by[591];assert derry['Country']==derry['TeamCountry']==163 and derry['TeamTailFamilyUID']==591 and derry['NameFamilyIndex']==derry['TeamTailFamilyIndex']
exceptions=[dict(ID='Treaty2026',Decision='ELIGIBLE_KEEP_TREATY_NAME_2026',TMID='88224',Country='Ireland',Facts=['OfficialLOI2026licence explicitly listsTreatyUnited.','Club21Sep2026release says approvedLimerickbrandadoptionfrom2027; TM(-2026)doesnotmeanclubceasedduring2026.','Do not merge currentTreaty entity into historicalLimerick native records merely becauseIP/name acquired.'],Sources=['https://www.leagueofireland.ie/news/2026-league-ireland-club-licences-awarded/','https://treatyunitedfc.com/treaty-united-confirms-completion-of-agreement-to-unite-behind-the-limerick-fc-identity/']),dict(ID='Derry',Decision='PRESERVE_NATIVE_COUNTRY',TMID='920',Native=derry,LeagueCountry='Ireland',Facts=['GeographicDerry/NI is distinct from FM08 native competitive national affiliation.','ActualX15nativeCountry163andTeamCountry163; do not guess159 or151.']),dict(ID='NationalConference',Decision='USE_CONFIRMED_CURRENT_NIR3_NOT_OLD_PIL',Facts=['12currentclubsconfirmedbyNAFLannouncementreported11June2026.','OldPIL25/26 used only as previous completed rank evidence.','FourPILclubs promotedto16teamChampionship; remaining10plusStJamesandRosarioform12.'],Sources=['https://www.newsletter.co.uk/sport/football/northern-ireland/nafl-confirm-the-12-clubs-set-to-compete-in-inaugural-conference-league-premier-division-8672554','sources/NIR3-current-26-27-clubs.json']),dict(ID='SourceIncompleteTables',Decision='REPLACE_WITH_FINAL_CUMULATIVE_TABLES',Facts=['IS1TM22regulargames is not final27; NI33is not final38.','Do not sum cumulative splitphase totals.','IR2FinnHarps/Kerry35games is genuinefinal after void fixture; do not invent36th.']),dict(ID='TechnicalLowerPools',Decision='GUARDED_REPAIR_BEFORE_WRITE_PASS',Facts=['NIrequires7existing-native regional replacements: MidUlster3/NAFLPremier1/NAFL1A3.','Countryagent commonstructureprepare resolves exactnativeUIDs with before/afterreceipt, preserving minima; these are technicalclassic allocations, not newlysourcedmodernregionalrankings.','No newMidUlsterclub creation needed; officialregionalfacts archived as fallbackreference.','IrelandMunster26->25afterMidleton >=23; Leinster14>=10; Ulster13>=10 unchanged.','IcelandLower42minusguardedmovedclubs >=28 must be recomputed on selectednativeidentitymapping for bothforms; baseline is not post-loaderproof.'])]
dump('decisions.json',exceptions)
plan=dict(Status='SOURCE_COMPETITION_PLAN_COMPLETE_NATIVE_PROJECTION_PENDING',CreatedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),Countries=['Iceland','Northern Ireland','Ireland'],CoreClubsWithCollectedSquads=72,AdditionalRealPartialClubs=14,TotalModernizedPlayableSourceClubTargets=86,ProfilesExpected=86,Clubs=plans,CascadeMoves=moves,NativeRequirementsFile=str(P/'native-competition-requirements.json'),NativeRequirementsSHA256=sha(P/'native-competition-requirements.json'),ClosedTablesFile='closed-tables.json',LowerPoolFile='native-lower-pool-baseline.json',ExceptionsFile='decisions.json',IcelandForms={'0':{'PremierUID':7840132,'PremierCount':10,'FirstUID':7840133,'FirstCount':12,'ExtraLowerCount':2},'1':{'PremierUID':7840132,'PremierCount':12,'FirstUID':7840133,'FirstCount':12}},TechnicalPending=['Nativeidentityprojectionof72coreclubsglobalresolver','Guarded7NIRregionalbackfillswithUIDreceipts','Postprojectionbothforms/current+effectivealternate+regionalgatevalidation','Native/SI/newcareer/seasonallseparatestatuses; noDBwritehere'],DataGaps=['14extrasquadspartial/notcollected peruserpolicy; enginefillsmissingpeople','Extraindividual stadium fields mayremainunknown; nofictionalstadiums','Native_lower_pools preservedtechnicalcatalogue, notallmodernized','Treaty2027Limerickbrandingnotappliedto2026snapshot'],NoUIDAllocation=True,NativeDBWrites=False,APIfootballCalls=0,SourceDatesShifted=False)
dump('plan.json',plan)
lines=['# ISL / NIR / IRL: source competition plan','','86 real club targets: 72 already collected squads + 14 additional partial clubs. No UID allocation or database write.','', '| Country | Form0 / current | Form1 / alternative |','|---|---|---|','| Iceland | Premier10, First12,2sourceclubsinitiallylower | Premier12, First12 |','| Northern Ireland | Premier16, First12, Second12 | Same explicitmembership |','| Ireland | Premier12, First10 | Same explicitmembership |','','Previous tables: Iceland2025full27/seniorFirst22; NI25/26full38plusPIL26; Ireland2025fullseason, including voidmatch exception. Regional supplement uses tables ending2025, not current2026tables. RSSSF authors KarelStokkermans andHansSchoggl credited; sourceURLs/hashes in source-index files.','','## Explicit classic-format moves','']
for m in moves:lines.append(f"- {m['Country']}: {m['Name']} (TM{m['TMID']}) currentCOMPindex{m['CurrentDivision']}, alternate{m['AlternativeDivision']}.")
lines+=['','## Important decisions','','Treaty is licensed for2026. Announced Limerick branding starts2027; no automatic merge with oldLimerick entity. Derry nativeUID591 already hasCountry163/TeamCountry163; preserve it. NationalConference12current clubs are separately sourceconfirmed; oldPIL onlysuppliespreviousrank.','','## Technical readiness','','All20existingmin/max requirements and8sourceC hashes retained. Nativeprojection remains pending. NI7regional gaps must be filled by common guarded native cascade, retaining country/firstteam and allgates. This does not claim current regionalmemberships. Iceland expansion10to12 and bothforms require effectivepostloader checks. Do not inferplayability fromrawcounts alone.','','No new fictional players or forcedDOBresearch.14extra clubs have sourceprofiles/stadium fields; squads intentionallypartial. No import, acceptedbase edit, EXE or FM interaction.','']
(B/'RAPORT.md').write_text('\n'.join(lines),encoding='utf-8')
outs=['plan.json','closed-tables.json','extra-clubs.json','native-lower-pool-baseline.json','decisions.json','RAPORT.md']
manifest=dict(Status='SOURCE_PLAN_PASS_NATIVE_PENDING',Outputs={n:sha(B/n) for n in outs},NativeWorldSHA256=sha(world),NativeRequirementsSHA256=sha(P/'native-competition-requirements.json'),SourceFiles={str(p.relative_to(B)):sha(p) for p in sorted((B/'sources').rglob('*')) if p.is_file()},ProtectedRosterFactsSHA256=sha(P/'roster-facts.json'),Protected72TargetsSHA256=sha(P/'source-targets.json'),NoDBWrite=True)
dump('manifest.json',manifest)
assert len(read(B/'plan.json')['Clubs'])==86
print(json.dumps(dict(Status='SOURCE_PLAN_PASS',Clubs=86,AdditionalPartial=14,RegionalTechnicalRepairSlots=7,PlanSHA256=sha(B/'plan.json'),ManifestSHA256=sha(B/'manifest.json'))))
