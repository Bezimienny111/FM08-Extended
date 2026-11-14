from pathlib import Path
from collections import Counter,defaultdict
import json,csv,re,unicodedata,hashlib,sys
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=R/'POLAND_GAPS_IMPORT_PACKAGE_20261111';SRC=R/'PORTUGAL_PERU_NORWAY_POLAND_PREP_20261111'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(n,x):(B/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def save(n,rows):
 with (B/n).open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def norm(s):
 s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()
 s=re.sub(r'\b(sad|clube|club|futebol|fotballklubb|fotballforening|fotball|deportivo|desportivo|associacao|asociacion|futbol|de|da|do|cf|fc|fbc|cd|sc|fk|ik|if|il|sk|ad|gd|ud)\b',' ',s)
 return ''.join(re.findall('[a-z0-9]+',s))
MANUAL={'21101':763464,'6399':1380,'239':1422,'2423':2448,'294':1487,'13025':109106,'3325':1480,'632':1343,'66144':53000237,'35030':1339,'36405':750750,'22820':1389,'2955':754972,
 '17479':308104,'35588':5290626,'76945':5290593,'2734':303815,'19520':5290629,'11622':8832487,
 '8189':2404,'10140':2395,'15268':109037,'13445':1401,'59547':1424,'11085':741496,
 '10331':55000308,'10330':55000306,'10789':55000307,'35024':103279,'3274':2414}
FORCE_NEW={'2434':('Salgueiros08 new2008 entity regained oldbrand2015/2016; preserve oldSportComercio1486','https://www.jpn.up.pt/2015/12/09/desporto-alma-salgueirista-renovada/'),'2431':('Current Estrela2011/2020 distinct from extinct1904 club1473','https://www.record.pt/futebol/futebol-nacional/campeonato-de-portugal/detalhe/socios-do-estrela-aprovam-fusao-com-o-sintra-football-em-assembleia-geral'),
 '110302':('AVS SAD renamed Vilafranquense SAD2013 in2023; distinct from CD Aves and continuingUDVilafranquense club','https://afsfut.pt/dev/wp-content/uploads/2023/12/Relato%CC%81rio-e-Contas-22.23.pdf'),
 '1701':('New CAFelgueiras founded2006 after old1932club extinct2005','https://www.fcpf.pt/wp-content/uploads/2025/05/revista120.pdf'),
 '7788':('New AcadViseu entity2006 Farminhao protocol, oldCAF2388financialinsolvency; preserve older history','https://academicodeviseu.pt/historia.php'),
 '2829':('ADMarco09 current entity, do not reuse oldFCMarco2407 by shared locality','https://www.transfermarkt.com/-/startseite/verein/2829'),
 '47794':('FCMaiaLidador separate current entity, do not take oldFCMaia2402','https://www.transfermarkt.com/-/startseite/verein/47794'),
 '10217':('Sarpsborg08 co-operation formed2008; distinct from continuingSarpsborgFK and Sparta','https://www.transfermarkt.com/-/startseite/verein/10217'),
 '35609':('Fyllingsdalen merger2011 new entity, not one predecessorFyllingen1314','https://www.transfermarkt.com/-/startseite/verein/35609'),
 '91296':('RanaFK current2017cooperation distinct oldMo/Rana club','https://www.transfermarkt.com/-/startseite/verein/91296'),
 '114390':('FCSanMarcos modern professional entity, not UniversidadNacionalMayorSanMarcos5290558','https://www.transfermarkt.com/-/startseite/verein/114390'),
 '124163':('EstudiantilCNI distinct sporting entity from ColegioNacionalIquitos5290573','https://www.transfermarkt.com/-/startseite/verein/124163')}
def clubs():
 world=read(B/'native-world-identities.json');byuid={w['ClubUID']:w for w in world};prior=read(SRC/'club-identity-candidates.json');target={x['TMID']:x for x in read(SRC/'source-targets.json')};index=defaultdict(list)
 for w in world:
  for label in w['Names']:
   n=norm(label)
   if len(n)>=4:index[n].append(w)
 out=[]
 for old in prior:
  c=dict(target[old['TMID']]);p=read(SRC/c['ProfileFile']);country=old['NativeCountryIndex'];parent=old['SourceMainClubTMID']if old['SourceMainClubTMID']!=c['TMID']and old['SourceClubTypeID']==2 else''
  labels=list(dict.fromkeys([p.get('name',''),p.get('official_name',''),p.get('short_name','')]+[a.get('name','')for a in p.get('historical_names',[])]))
  candidates={}
  for name in labels:
   n=norm(name)
   for w in index.get(n,[]):
    if w['Country']!=country:continue
    if parent and not(w['ParentUID']or re.search(r'(?:\bB\b|\bII\b|2\s*$)', ' '.join(w['Names']),re.I)):continue
    if not parent and w['ParentUID']is not None:continue
    candidates[w['ClubUID']]=w
  uid=MANUAL.get(c['TMID']);reason='explicit_full_name_historical_alias_and_country';evidence=['https://www.transfermarkt.com/-/startseite/verein/'+c['TMID']]
  if c['TMID']in FORCE_NEW:uid=None;decision='new_distinct_entity';reason,e=FORCE_NEW[c['TMID']];evidence=[e]
  elif uid:decision='reuse_verified_explicit_alias'
  elif len(candidates)==1:uid=next(iter(candidates));decision='reuse_exact_source_alias_country';reason='Unique normalized current/official/short/historical source name in same country and compatible reserve type'
  elif old['IdentityDecision']=='unique_source_alias_candidate'and not parent:
   v=old['NativeCandidates'][0];w=byuid.get(v['ClubUID'])
   if w and w['Country']==country and w['ParentUID']is None:uid=w['ClubUID'];decision='reuse_previous_alias_revalidated_fresh_X11'
   else:decision='defer_identity_conflict'
  elif len(candidates)>1:decision='defer_ambiguous_identity'
  else:decision='new_missing_native_entity';reason='Real current club; no verified matching same-country entity; do not inherit unrelated history'
  if uid:
   w=byuid[uid];assert w['Country']in[country,-1]
   if parent and w['ParentUID']is None:assert re.search(r'\bB\b|\bII\b|\b2\b',' '.join(w['Names']),re.I),('reserve accidentally mapped parent',c['TMID'],w)
  else:w={}
  c.update(NativeCountryIndex=country,ParentTMID=parent,ReserveTeam=bool(parent),NativeClubUID=uid,NativeTeamIndex=w.get('TeamIndex'),NativeFamilyIndex=w.get('FamilyIndex'),ExistingStadiumIndex=w.get('StadiumIndex',-1),NativeParentUID=w.get('ParentUID'),NativeCountryRepairTo=country if uid and w['Country']==-1 else None,IdentityDecision=decision,IdentityReason=reason,IdentityEvidence=evidence,SourceNames=labels,FreshCandidates=list(candidates),PublicStadium=p.get('stadium')or{},ProfileFile=str((SRC/c['ProfileFile']).resolve()),RosterFile=str((SRC/c['RosterFile']).resolve()),SugarDaddy=False,DesiredDivision=None,SourceCompetition=c['Competitions'][0])
  out.append(c)
 used=[x['NativeClubUID']for x in out if x['NativeClubUID']];assert len(used)==len(set(used)),[(u,[x['Name']for x in out if x['NativeClubUID']==u])for u,n in Counter(used).items()if n>1]
 dump('club-plan-draft.json',out);dump('club-identity-summary.json',dict(clubs=len(out),decisions=dict(Counter(x['IdentityDecision']for x in out)),deferred=[x for x in out if x['IdentityDecision'].startswith('defer')],no_UID_allocated=True))
 print('CLUBS',Counter(x['IdentityDecision']for x in out),flush=True)
def table(comp):
 f=next((SRC/'sources/tm-competitions').glob(comp+'-previous_completed*table.json'))
 return [dict(v,PreviousCompetition=comp,PreviousGroup=t.get('name'),PreviousSource=str(f))for t in read(f)['tables']for v in t['rows']]
def rank(c,prev):return (prev[c['TMID']]['position'],-prev[c['TMID']]['points']/max(1,prev[c['TMID']]['matches']),-prev[c['TMID']]['goal_difference']/max(1,prev[c['TMID']]['matches']),-prev[c['TMID']]['wins']/max(1,prev[c['TMID']]['matches']),c['TMID'])
def allocate():
 plan=read(B/'club-plan-draft.json');decisions=[]
 req=read(SRC/'native-competition-requirements.json')['requirements'];catalog={r['index']:r['uid']for r in read(B/'competition-catalog.json')}
 for r in req:assert catalog[r['CatalogueIndex']]==r['CompetitionUID'],('competition UID/index mismatch',r)
 for country,comp1,comp2,n1,n2,d1,d2,d3,real3,real4 in [('Portugal','PO1','PO2',16,16,44,45,[46,47,48,1070],['PT3A'],['CPSA','CPSB','CPSC','CPSD']),('Norway','NO1','NO2',14,16,501,502,[504,505,506,507],['NO31','NO32'],['NO41','NO42','NO43','NO44','NO45','NO46'])]:
  allc=[c for c in plan if c['Country']==country];top=[c for c in allc if comp1 in c['Competitions']];second=[c for c in allc if comp2 in c['Competitions']];p1={x['club_id']:x for x in table(comp1)};p2={x['club_id']:x for x in table(comp2)}
  down1=sorted([c for c in top if c['TMID']in p1],key=lambda c:rank(c,p1),reverse=True)[:len(top)-n1];ids={c['TMID']for c in down1}
  for c in top:c['DesiredDivision']=d2 if c['TMID']in ids else d1;c['SelectionReason']='worst_eligible_continuing_by_previous_final_to_native_second'if c['TMID']in ids else'current_top_preserved'
  second+=down1;down2=sorted([c for c in second if c['TMID']in p2],key=lambda c:rank(c,p2),reverse=True)[:len(second)-n2];ids={c['TMID']for c in down2}
  for c in second:c['DesiredDivision']=None if c['TMID']in ids else d2;c['SelectionReason']='worst_eligible_continuing_previous_second_to_native_third'if c['TMID']in ids else c.get('SelectionReason','current_second_preserved')
  third=[c for c in allc if any(t in c['Competitions']for t in real3)]+down2;used={c['TMID']for c in top+second+third};p3={x['club_id']:x for t in real3 for x in table(t)};p4={x['club_id']:x for t in real4 for x in table(t)}
  choices=[c for c in allc if c['TMID']not in used and any(t in c['Competitions']for t in real4)]
  parenttier={c['TMID']:c['DesiredDivision']for c in top+second}
  # No reserve enters same native level as its own first team.
  blockedparents={c['TMID']for c in third}
  eligible=[c for c in choices if not(c['ParentTMID']and c['ParentTMID']in blockedparents)]
  relegated=[c for c in eligible if c['TMID']in p3]
  rest=[c for c in eligible if c['TMID']not in p3 and c['TMID']in p4]
  rest.sort(key=lambda c:rank(c,p4));relegated.sort(key=lambda c:rank(c,p3))
  selected=(relegated+rest)[:56-len(third)];assert len(selected)==56-len(third)
  for c in selected:c['SelectionReason']='preserve_eligible_previous_third_relegated'if c in relegated else'best_available_previous_lower_final_rank_normalized_points_GD';c['PreviousRank']=(p3 if c in relegated else p4)[c['TMID']]
  third+=selected
  # Geographic bands preserve exact14; explicit native labels are neutral group1..4.
  def lat(c):
   st=c['PublicStadium'];return float(st['latitude'])if st.get('latitude')is not None else 0
  missing=[c['TMID']for c in third if c['PublicStadium'].get('latitude')is None];assert not missing,('geographic_coordinate_missing',country,missing)
  third.sort(key=lambda c:(-lat(c),c['TMID']))
  for k,c in enumerate(third):c['DesiredDivision']=d3[k//14];c['RegionalRule']='four geographic latitude bands14each; exact native groups; source stadium coordinates';c['RegionalLatitude']=lat(c)
  for c in allc:
   if c['DesiredDivision']is None:c['DesiredDivision']=49 if country=='Portugal'else 539;c['SelectionReason']='retained_current_lower_catalogue_outside_native_playable_capacity'
  decisions.append(dict(country=country,top_down=[{'TMID':c['TMID'],'Name':c['Name'],'previous':p1[c['TMID']]}for c in down1],second_down=[{'TMID':c['TMID'],'Name':c['Name'],'previous':p2[c['TMID']]}for c in down2],third_selected_lower=[{'TMID':c['TMID'],'Name':c['Name'],'reason':c['SelectionReason'],'previous':c.get('PreviousRank')}for c in selected],excluded_same_level_reserves=[c['TMID']for c in choices if c not in eligible]))
 # Peru annual final2025, independently recorded final aggregate with actual sanctions/withdrawal.
 annual=[('6593',1,79),('28999',2,70),('184',3,68),('3377',4,63),('17479',5,57),('2734',6,56),('76945',7,52),('2724',8,50),('54478',9,50),('35588',10,49),('21655',11,48),('21169',12,38),('47107',13,37),('2415',14,36),('99517',15,33),('21170',16,32),('21178',17,29),('35589',18,28)]
 # Names/IDs checked against cached previous Apertura/Clausura catalogues; don't silently trust shorthand ID.
 known={x['club_name']:x['club_id']for comp in ['TDeA','TDeC']for x in table(comp)}
 annualnames=['Universitario de Deportes','Cusco FC','Club Alianza Lima','Club Sporting Cristal','Alianza Atletico Sullana','FBC Melgar','Deportivo Garcilaso','Club Cienciano','CD Los Chankas','Asociacion Deportiva Tarma','Sport Huancayo','Club Atletico Grau','Comerciantes Unidos','Sport Boys Association','Club Juan Pablo II College','Universidad Tecnica de Cajamarca','Ayacucho FC','Alianza Universidad']
 candidates={norm(k):v for k,v in known.items()}
 ann={}
 for (tid,pos,pts),name in zip(annual,annualnames):
  key=norm(name);found=candidates.get(key)
  if not found:
   target=[c for c in plan if c['Country']=='Peru'and norm(c['Name'])==key];found=target[0]['TMID']if len(target)==1 else None
  assert found,('Peru annual name ID',name,known)
  ann[found]=dict(position=pos,points=pts,source='https://www.rsssf.org/tablesp/peru2025.html',secondary='https://larepublica.pe/futbol-peruano/2025/11/21/tabla-acumulada-de-la-liga-1-del-futbol-peruano-asi-va-la-clasificacion-de-los-clubes-1487535',scope='final2025 aggregate; sanctions and Binacional disaffiliation already reflected; not live2026 table')
 top=[c for c in plan if c['Country']=='Peru'and c['RealLevel']==1];cont=[c for c in top if c['TMID']in ann];down=sorted(cont,key=lambda c:(ann[c['TMID']]['position'],c['TMID']),reverse=True)[:len(top)-12];ids={c['TMID']for c in down}
 for c in plan:
  if c['Country']=='Peru':c['DesiredDivision']=597 if c in top and c['TMID']not in ids else 599;c['SelectionReason']='six_worst_continuing_by_final2025_annual_to_lower_pool'if c['TMID']in ids else'current_top_promoted_preserved'if c in top else'current_second_nonplayable_native_pool';c['PreviousRank']=ann.get(c['TMID'])
 decisions.append(dict(country='Peru',top_down=[dict(TMID=c['TMID'],Name=c['Name'],previous=ann[c['TMID']])for c in down],annual=ann,phase_policy='use published final annual table, never current2026 or unconstrained phase sums'))
 dump('club-plan.json',plan);dump('allocation-decisions.json',decisions);print('COUNTS',Counter(c['DesiredDivision']for c in plan),flush=True)


def poland():
 import html
 old=R/'POLAND_DATABASE_2627_R1_20261108';n7=old/'native-V25-N7/prepared-r2'
 previous=read(n7/'full-native.json');provenance={str(x['id90']):x for x in read(n7/'provenance.json')};audit=read(SRC/'poland-existing-data-audit.json')
 native={int(x['ID']):x for x in csv.DictReader((B/'audit/players.csv').open(encoding='utf-8-sig'))};world={x['ClubUID']:x for x in read(B/'native-world-identities.json')}
 priorclubs=list(csv.DictReader((n7/'club_map.csv').open(encoding='utf-8-sig')));clubuids={int(c['ClubUID'])for c in priorclubs}
 missingclubs=clubuids-set(world);assert not missingclubs
 uidrows=[];absent=[]
 for row in previous['subjects']:
  uid=row['uid'];cur=native.get(uid)
  if cur is None:absent.append(dict(UID=uid,ID90=row['id90'],reason='not_in_current_player_export_preserve_pending_identity_audit'));continue
  proof=provenance[str(row['id90'])]
  uidrows.append(dict(UID=uid,ID90=row['id90'],Imie=cur['FirstName'],Nazwisko=cur['LastName'],NativeDOB=cur['BirthDate'],SourceDOB=proof.get('sourceDOB'),CurrentOwnerTEAM=cur['ClubIndex'],CurrentOwnerName=cur['Club'],N7OwnerTEAM=row['owner'],N7PlayingTEAM=row['playing'],OwnershipChangedSinceN7=str(cur['ClubIndex'])!=str(row['owner']),CA=cur['CA'],PA=cur['PA'],N7AbilitySource=proof['ability_source'],RatingsAction='preserve_current_X11_and_any_prior_talent',Source=proof['profile90']))
 bio=[]
 for gap in audit['unresolved_birth_facts']:
  ident=gap['id90'];files=sorted(old.rglob('*'+ident+'*90minut*.html'));f=files[0]if files else None;raw='';value=''
  if f:
   data=f.read_bytes();raw=' '.join(html.unescape(re.sub('<[^>]*>',' ',data.decode('iso-8859-2'))).split());m=re.search(r'Data urodzenia\s*(.*?)\s*Miejsce urodzenia',raw,re.I);value=m.group(1).strip()if m else''
  valid=re.fullmatch(r'\d{1,2}\s+[A-Za-ząćęłńóśźż]+\s+\d{4}|\d{1,2}\.\d{1,2}\.\d{4}|\d{4}-\d{2}-\d{2}|\d{4}',value or'') is not None
  bio.append(dict(gap,CachedPrimaryFile=str(f)if f else None,CachedPrimarySHA256=hashlib.sha256(f.read_bytes()).hexdigest()if f else None,SourceBirthRaw=value,VerifiedDateCandidate=valid,Decision='primary_date_present_parse_required'if valid else'preserve_gap_no_forced_player_search_engine_may_fill',NewPersonCreated=False))
 assert not any(x['VerifiedDateCandidate']for x in bio),('new_primary_DOB_to_reconcile',bio)
 save('poland-current-player-inventory.csv',uidrows)
 dump('poland-gap-review.json',dict(status='cached_primary_review_complete_no_speculative_additions',clubs_verified=len(clubuids),current_imported_UIDs_present=len(uidrows),UIDs_absent=absent,raw_gaps=bio,nationality_differences_preserved=audit['nationality_conflicts_preserved'],ratings_action='All accepted current data and granted talents preserved; any proven legacy estimate proposal is separate review inventory',new_network_calls=0,API_sports_requests=0,no_roster_rescrape=True,source_priority='90minut above API',native_database_changed=False))
 print('POLAND',len(clubuids),'clubs',len(uidrows),'UIDs','absent',len(absent),'unresolvedDOB',len(bio),flush=True)
def owners():
 import types
 source=R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/x10_owners.py'
 code=source.read_text(encoding='utf-8').replace("str(p.relative_to(B))","str(p.resolve())")
 ns={'__name__':'package_owner_reuse','__file__':str(source)}
 sys.path.insert(0,str(source.parent));exec(compile(code,str(source),'exec'),ns)
 ns['B']=B;ns['S']=SRC/'sources'
 dump('source-targets.json',read(B/'club-plan.json'));dump('roster-facts.json',read(SRC/'roster-facts.json'))
 ns['owners']()
def project():
 # Exact append-order projection only; no DAT writes and no claim of native materialization.
 plan=read(B/'club-plan.json');world=read(B/'native-world-identities.json');byuid={x['ClubUID']:x for x in world}
 ti=max(x['TeamIndex']for x in world)+1;fi=max(x['FamilyIndex']for x in world)+1;nextuid=1800140001
 useduids={x['ClubUID']for x in world};maps=[];bytm={};ledger=[]
 for c in sorted(plan,key=lambda c:(bool(c['ParentTMID']),c['Country'],int(c['TMID']))):
  uid=c['NativeClubUID'];isnew=uid is None;parent=bytm[c['ParentTMID']]if c['ParentTMID']else None
  if isnew:
   uid=nextuid;nextuid+=1;assert uid not in useduids;useduids.add(uid);team=ti;ti+=1;family=parent['FamilyIndex']if parent else fi
   if not parent:fi+=1
   parentuid=parent['ClubUID']if parent else''
  else:
   w=byuid[uid];team=w['TeamIndex'];family=w['FamilyIndex'];parentuid=w['ParentUID']or''
  row=dict(ClubName=c['Name'],ClubUID=uid,TeamIndex=team,FamilyIndex=family,CountryIndex=c['NativeCountryIndex'],DivisionIndex=c['DesiredDivision'],Group=c['Country']+' '+str(c['DesiredDivision']),RealLeague=c['RealLevel'],Country=c['Country'],TMID=c['TMID'],Kind='projected_new_linked_reserve'if isnew and parent else'projected_new_first_team'if isnew else'existing_native_entity',ParentUID=parentuid,SourceParentTMID=c['ParentTMID'],IdentityDecision=c['IdentityDecision'],ProjectionOnly=isnew)
  maps.append(row);bytm[c['TMID']]=row;ledger.append(dict(TMID=c['TMID'],ClubUID=uid,TeamIndex=team,FamilyIndex=family,IsNew=isnew,SourceParentTMID=c['ParentTMID'],NativeFamilyParentUID=parentuid,NativeMaterialization='PENDING'if isnew else'X11_verified'))
 assert len({x['ClubUID']for x in maps})==len(maps)==292
 save('club-map.csv',maps);dump('club-UID-projection.json',dict(status='pinned_projection_not_a_native_write',source_pins=read(B/'manifest.json')['source_hashes'],UIDrange=[1800140001,nextuid-1],rows=ledger,no_native_data_changed=True))
 print('PROJECTED',len(maps),'new',sum(x['IsNew']for x in ledger),flush=True)


def finalize_owners():
 world=read(B/'native-world-identities.json');byuid={w['ClubUID']:w for w in world};res=read(B/'foreign-owner-resolution-draft.json');core={c['TMID']:c for c in read(B/'club-plan.json')};prior=defaultdict(set)
 folders=['SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/prepared','FOUR_COUNTRY_X7_20261110/prepared','SWEDEN_SWITZERLAND_X3_20261109/prepared','UKRAINE_TURKEY_X2_20261109/prepared','WALES_USA_URUGUAY_2627_B1_20261109/prepared','HUNGARY_DATABASE_2627_H1_20261109/prepared','ITALY_DATABASE_2627_IMPORT_I1_20261108/prepared-r4']
 for folder in folders:
  f=R/folder/'club_map.csv'
  if not f.exists():continue
  for x in csv.DictReader(f.open(encoding='utf-8-sig')):
   if x.get('TMID')and x.get('ClubUID')and int(x['ClubUID'])in byuid:prior[x['TMID']].add(int(x['ClubUID']))
  f=R/folder/'provenance.json'
 raw={}
 for f in (SRC/'sources/tm-raw').glob('*.json'):
  z=read(f)
  if '/clubs?'not in z.get('url','')or z.get('status')!=200:continue
  body=json.loads(z['body']).get('data')or[]
  if isinstance(body,list):
   for club in body:raw[str(club['id'])]=dict(club,raw_file=str(f.resolve()))
 aliases={'5':1101,'605':969} # applied only if fresh full-name/country/UID proof matches below
 knownmanual={'1030':78,'13':1687,'14312':108531,'679':107206,'1693':900678,'18544':102862,'190':505,'26069':1104149,'9099':106054,'3938':102489,'5026':8157175,'605':969,'79389':8630098,'8793':317,'897':1705,'631':630,'931':654,'999':662735}
 for tid,needle in [('5','milan'),('13','atletico madrid'),('1244','leganes'),('2448','gijon'),('190','kobenhavn'),('1177','silkeborg'),('330','atletico mineiro'),('683','olympiakos'),('897','deportivo la coruna'),('3631','america')]:
  c=next((c for c in res if c['CanonicalMainTMID']==tid),None)
  if not c:continue
  ws=[w for w in world if w['Country']==c['NativeCountryIndex']and w['ParentUID']is None and any(norm(n)==norm(needle)for n in w['Names'])]
  if len(ws)==1:knownmanual[tid]=ws[0]['ClubUID']
 planned={};deferred=[]
 for c in res:
  tid=c['CanonicalMainTMID'];ni=c['NativeCountryIndex'];uid=c['NativeClubUID']
  if tid in core:c.update(Decision='within_core_batch',NativeClubUID=core[tid]['NativeClubUID']);continue
  good=[byuid[u]for u in prior.get(tid,set())if byuid[u]['Country']==ni]
  if len(good)==1:uid=good[0]['ClubUID'];c['Decision']='previous_verified_TM_registry_revalidated_X11'
  elif tid in knownmanual:uid=knownmanual[tid];assert byuid[uid]['Country']==ni,('owner_alias_country_mismatch',tid,uid);c['Decision']='explicit_full_city_historical_mainclub_alias'
  if not uid and ni is not None:
   labels=c.get('SourceNames',[]);r=raw.get(tid,{});bd=r.get('baseDetails')or{}
   labels+=[r.get('name'),bd.get('shortName')]
   keys={norm(n)for n in labels if n and len(norm(n))>=4}
   ws=[w for w in world if w['Country']==ni and w['ParentUID']is None and any(norm(n)in keys for n in w['Names'])]
   if len(ws)==1:uid=ws[0]['ClubUID'];c['Decision']='unique_normalized_full_source_alias_same_country'
  if uid:
   w=byuid[uid];assert w['Country']==ni
   c.update(NativeClubUID=uid,NativeTeamIndex=w['TeamIndex'],NativeFamilyIndex=w['FamilyIndex'])
  else:
   r=raw.get(tid,{});bd=r.get('baseDetails')or{};name=r.get('name')or c['Name']
   if ni is None or not name or name.lower()in['unknown','none']or c['Decision']=='defer_unresolved_owner':
    c.update(Decision='defer_owner_without_unambiguous_identity_or_country');deferred.append(c['SourceTMID']);continue
   # Never turn a proxy youth/II name into an invented independent first team.
   if str(bd.get('mainClubId')or tid)!=tid:
    c.update(Decision='defer_missing_parent_owner_profile');deferred.append(c['SourceTMID']);continue
   if tid not in planned:
    pf=B/'owner-source-profiles';pf.mkdir(exist_ok=True);file=pf/(tid+'.json')
    file.write_text(json.dumps(dict(id=tid,name=name,official_name=name,short_name=(bd.get('shortName')or name),stadium={},stadium_name='',source_raw=r.get('raw_file'),SourceType='normalized_owner_identity_from_cached_raw_not_a_full_stadium_profile'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    planned[tid]=dict(TMID=tid,Name=name,Country=c['Country'],LeagueCountry=c['Country'],NativeCountryIndex=ni,RealLevel=1,DesiredDivision=-1,SourceCompetition='owner_only',NativeClubUID=None,ParentTMID='',IdentityDecision='new_real_owner_missing_native_entity',IdentityReason='Confirmed source mainClubId and country from cached active loan; no unique existing native identity',IdentityEvidence=[c.get('RawFile'),'https://www.transfermarkt.com/-/startseite/verein/'+tid],ProfileFile=str(file.resolve()),SugarDaddy=False,OwnerOnly=True,Role='loan_owner_only',PublicStadium={})
   c.update(Decision='new_missing_owner_identity_profile_confirmed',NativeClubUID=None)
 dump('foreign-owner-aliases.json',res);dump('foreign-owner-plan.json',list(planned.values()));dump('foreign-owner-finalization.json',dict(status='identity_plan_only_not_native_write',new_owner_families=len(planned),decisions=dict(Counter(c['Decision']for c in res)),deferred_source_owners=deferred,no_network=True))
 print('FINAL OWNERS',Counter(c['Decision']for c in res),'new',len(planned),'deferred',len(deferred),flush=True)
def project_owners():
 maps=list(csv.DictReader((B/'club-map.csv').open(encoding='utf-8-sig')));world=read(B/'native-world-identities.json');byuid={w['ClubUID']:w for w in world};proj=read(B/'club-UID-projection.json')
 nextuid=proj['UIDrange'][1]+1;ti=max([int(x['TeamIndex'])for x in maps]+[w['TeamIndex']for w in world])+1;fi=max([int(x['FamilyIndex'])for x in maps]+[w['FamilyIndex']for w in world])+1
 out=[]
 for c in sorted(read(B/'foreign-owner-plan.json'),key=lambda c:int(c['TMID'])):
  out.append(dict(ClubName=c['Name'],ClubUID=nextuid,TeamIndex=ti,FamilyIndex=fi,CountryIndex=c['NativeCountryIndex'],DivisionIndex=-1,Group='loan_owner_only',RealLeague=1,Country=c['Country'],TMID=c['TMID'],Kind='projected_new_owner_family',ParentUID='',SourceParentTMID='',IdentityDecision=c['IdentityDecision'],ProjectionOnly=True));nextuid+=1;ti+=1;fi+=1
 save('foreign-owner-map.csv',out or[dict(ClubName='',ClubUID='',TeamIndex='',FamilyIndex='',CountryIndex='',DivisionIndex='',Group='',RealLeague='',Country='',TMID='',Kind='',ParentUID='',SourceParentTMID='',IdentityDecision='',ProjectionOnly='')])
 dump('foreign-owner-projection.json',dict(status='pinned_projection_not_native_materialization',rows=out))
 print('PROJECT OWNERS',len(out),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
