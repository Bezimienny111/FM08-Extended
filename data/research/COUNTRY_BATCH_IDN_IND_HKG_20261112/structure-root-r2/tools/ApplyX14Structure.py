"""B1 structural stage. SI-witnessed layouts; bounded identities; exact inverse proof."""
from pathlib import Path
from collections import Counter
import sys,struct,shutil,zlib,re,unicodedata,subprocess,csv
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
from create_italy_structure_i1_20261108 import read,rows,dump,save,load,pins,languages,lang_sections,find_table,club,city,unique,identity,slot,language_spans,repack_languages,apply_verified
from audit_poland_v25_common_r1_20261108 import stadium,Cursor
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'FmLauncher/data/research';B=R/'COUNTRY_BATCH_IDN_IND_HKG_20261112/structure-root-r2';H=R/'HUNGARY_DATABASE_2627_H1_20261109';IT=R/'ITALY_DATABASE_2627_IMPORT_I1_20261108'
_save_nonempty=save
def save(p,x):
 if x:return _save_nonempty(p,x)
 with p.open('w',encoding='utf-8-sig',newline='')as f:csv.DictWriter(f,fieldnames=['ClubName','ClubUID','TeamIndex','FamilyIndex','CountryIndex','DivisionIndex','Group','RealLeague','Country','TMID','Kind','ParentUID','IdentityDecision']).writeheader()

def norm(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',str(s).replace('\u0142','l').replace('\u0141','L')).encode('ascii','ignore').decode().lower())
def words(s):return set(re.findall('[a-z0-9]+',unicodedata.normalize('NFKD',str(s).replace('\u0142','l')).encode('ascii','ignore').decode().lower()))
def name_edits(data,plan,lang):
 if lang not in [8,18]:return []
 names={x['NativeClubUID']:x for x in plan if x['NativeClubUID']and not x.get('ParentTMID')};sec=language_spans(data)['club'];cur=Cursor(data,sec['count_offset']+4);ed=[]
 for _ in range(sec['count']):
  uid=cur.integer()
  for j in range(5):
   start=cur.p;old=cur.string();end=cur.p
   if uid in names and j<2:
    spec=names[uid];pf=read(B/spec['ProfileFile']);target=spec['Name']if j==0 else pf.get('short_name')or spec['Name']
    if old!=target:ed.append((start,end-start,slot(target)[:-1]))
   if j<4:cur.byte()
 assert cur.p==sec['end'];return ed

def main():
 m=read(B/'manifest.json');src=Path(m['source']);expected={k:v.upper() for k,v in m['source_hashes'].items()};assert pins(src)==expected;dest=B/'structure-db';assert not dest.exists()
 a,c=load(src,'server_db.dat'),load(src,'client_db.dat');lb=languages((src/'lang_db.dat').read_bytes());en,_=lang_sections(dict(lb)[8]);cl,cco,cend=find_table(c,[x['uid']for x in en['club']],club);cities,_,_=find_table(c,[x['uid']for x in en['city']],city);_,_,nameco=find_table(a,[x['uid']for x in en['city']],city)
 st,stco,stend=find_table(a,[x['uid']for x in en['stadium']],lambda q:stadium(q,62));cs,cstco,cstend=find_table(c,[x['uid']for x in en['stadium']],lambda q:stadium(q,19));assert all(x['raw'][:1]+x['raw'][44:]==y['raw']for x,y in zip(st,cs))
 records=read(B/'native-structure.json')['records'];byuid={x['ClubUID']:x for x in records};byteam={x['TeamIndex']:x for x in records};oldName=len(cl);oldTeam=max(byteam)+1;first=min(x['Start']for x in records);base=nameco+4;familyspan=a[base:first]
 def footer(fi,uid):return base+unique(familyspan,struct.pack('<iI',fi,uid))+8
 nameend=footer(oldName-1,cl[-1]['uid']);cand=[off for off in range(max(nameend-32,first-100000),first-3)if a[off:off+4]==struct.pack('<i',oldTeam)];assert len(cand)==1;coteam=cand[0];teamend=byteam[oldTeam-1]['Footer']+8
 cf={x['uid']:x for x in cl};tplproof=read(R/'CLUB_STADIUM_CREATION_R1_20261108/si-fixtures.json')['native_N1'];tpl=Path(tplproof['frozen_after_SI']);assert pins(tpl)==tplproof['after_SI_hashes'];ta,tc=load(tpl,'server_db.dat'),load(tpl,'client_db.dat')
 te=unique(ta,struct.pack('<iI',23394,1800001004))+8;ce=unique(tc,struct.pack('<iI',23394,1800001004))+8;tt=unique(ta,struct.pack('<iI',23624,1800001004))+8;se=unique(ta,struct.pack('<iI',15121,1800001001))+8;tree,ctree,team,stad=ta[te-216:te],tc[ce-43:ce],ta[tt-113:tt],ta[se-62:se];assert tree[47]==tree[52]==0 and team[0]==10 and team[62:65]==bytes(3)
 labels={k:{x['uid']:x['names']for x in en[k]}for k in ['city','stadium']};citykeys={x['index']:{norm(x['embedded_name'])}|{norm(n)for n in labels['city'][x['uid']]if n}for x in cities};stadkeys={x['index']:{norm(n)for n in labels['stadium'][x['uid']]if n}for x in st};venueadd=[];venuechanges=[];gaps=[];newvenuekeys={}
 country={'Wales':175,'England':765,'Poland':161,'Italy':150,'Hungary':147,'Germany':145,'Uruguay':195,'United States':120,'USA':120,'Canada':97,'Ukraine':174,'Turkey':173,'Türkiye':173,'Costa Rica':99,'Sweden':171,'Switzerland':172,'Liechtenstein':152,'Scotland':167,'Slovakia':168,'Slovenia':169,'Singapore':79,'Japan':61,'Croatia':135,'Czech Republic':137,'The Gambia':15,'Gambia':15}
 # Resolve England from the fresh nationality audit, never from a remembered index.
 nations=rows(B/'audit/nations.csv');eng=[int(n['NationIndex'])for n in nations if n['Nation']in ['England','Anglia']];assert len(eng)==1;country['England']=eng[0]
 for ni,nation in enumerate(en['nation']):
  for alias in nation['names']:
   if alias:country.setdefault(alias,ni)
 primary={}
 country.update({'Korea, South':80,'Korea, North':74,'United States of America':120,'Hongkong':56})
 def venue(spec):
  pf=read(B/spec['ProfileFile'])if spec.get('ProfileFile')else{};v=pf.get('stadium')or{};uid=int(spec['ClubUID']);p=primary.get(uid,{});name=p.get('Name90')or spec.get('StadiumName')or v.get('name')or pf.get('stadium_name');capacity=p.get('Capacity90')or spec.get('Capacity')or v.get('capacity')or pf.get('stadium_seats');cn=spec.get('CityCountryOverride')or v.get('country_name')or spec['Country'];ni=country.get(cn);assert ni is not None,('stadium country',cn)
  if not name:
   keep=spec.get('ExistingStadiumIndex',-1);gaps.append(dict(ClubUID=uid,field='stadium',reason='no_verified_current_name_existing_retained'if keep>=0 else'no_verified_name_unset'));return keep
  address=spec.get('CityOverride')or v.get('address_line_2')or pf.get('address_line_2')or'';aw=words(address);hits=[x for x in cities if x['nation_index']==ni and any(k and k in {norm(address),norm(re.sub(r'^[0-9 -]+','',address))}for k in citykeys[x['index']])]
  if not hits:hits=[x for x in cities if x['nation_index']==ni and any(k and len(k)>=4 and any(norm(' '.join(sorted(aw)))==k for _ in [0])for k in citykeys[x['index']])]
  # Native localized city names are matched as complete words inside the public stadium address.
  if not hits:
   hits=[x for x in cities if x['nation_index']==ni and any(k and len(k)>=4 and k in norm(address)for k in citykeys[x['index']])];longest=max([max(len(k)for k in citykeys[x['index']])for x in hits],default=0);hits=[x for x in hits if max(len(k)for k in citykeys[x['index']])==longest]
  cityidx=hits[0]['index']if len(hits)==1 else -1
  namekey=norm(name);aliases={norm('Red Bull Arena'):norm('Zentralstadion')}if uid==1800007101 else{}
  matches=[x for x in st if namekey in stadkeys[x['index']]or aliases.get(namekey)in stadkeys[x['index']]];matches=[x for x in matches if 0<=struct.unpack_from('<i',x['raw'],46)[0]<len(cities)and cities[struct.unpack_from('<i',x['raw'],46)[0]]['nation_index']==ni and(cityidx<0 or struct.unpack_from('<i',x['raw'],46)[0]==cityidx)]
  if len(matches)==1:idx=matches[0]['index'];cityidx=struct.unpack_from('<i',matches[0]['raw'],46)[0];action='reuse_verified_name_and_physical_country_city'
  else:
   key=(namekey,ni,cityidx,uid if cityidx<0 else 0)
   if key in newvenuekeys:idx=newvenuekeys[key];action='reuse_new_shared_ground'
   else:
    idx=len(st)+len(venueadd);su=1800210001+len(venueadd);raw=identity(stad,idx,su);cap=int(capacity or 0);assert 0<=cap<300000
    for off,val in [(1,cap),(5,0),(46,cityidx)]:struct.pack_into('<i',raw,off,val)
    assert struct.unpack_from('<i',raw,13)[0]==struct.unpack_from('<i',raw,50)[0]==-1
    venueadd.append(dict(index=idx,uid=su,name=name,city_index=cityidx,physical_country_index=ni,capacity=cap,seating=0,seating_precision='unknown_unset',raw=bytes(raw).hex(),source=p.get('Source90')if p.get('Name90')else spec.get('VenueEvidenceURL')or 'https://www.transfermarkt.com/-/stadion/verein/'+str(spec.get('TMID','')),address=address));newvenuekeys[key]=idx;action='create_verified_ground'
  if cityidx<0:gaps.append(dict(ClubUID=uid,field='stadium_city',reason='no_unique_existing_native_city_address_'+address))
  if not capacity:gaps.append(dict(ClubUID=uid,field='stadium_capacity',reason='unconfirmed_left_unset'))
  venuechanges.append(dict(ClubUID=uid,StadiumIndex=idx,Name=name,CityIndex=cityidx,Action=action));return idx
 plan=read(B/'club-plan.json')+read(B/'foreign-owner-plan.json');country.update({x['Country']:x['NativeCountryIndex']for x in plan});oldvenues=[];assignments={int(x['ClubUID']):venue(x)for x in oldvenues};names=[];clients=[];teams=[];edits=[];cedits=[];mapping=[];additions=[];leaguechanges=[];ownermap=[];bytm={};parent_edits={};retirement_repairs=[]
 for x in plan:
  u=x['NativeClubUID'];div=x['DesiredDivision'];cn=x['NativeCountryIndex'];name=x['Name'];parent=None
  if x.get('ParentTMID'):
   assert x['ParentTMID']in bytm;parent=bytm[x['ParentTMID']]
   if u:assert x['ExistingParentUID']==parent['ClubUID']
  if u:
   r=byuid[u];f=cf[parent['ClubUID']if parent else u];ti=r['TeamIndex'];fi=f['index'];assert f['country_index']==x['SourceCountryIndex'];kind='existing_linked_reserve'if parent else'existing_first_team'
   if cn!=f['country_index']:
    assert (f['country_index']==-1 or (u==5626771 and f['country_index']==70 and cn==54)) and x.get('NativeCountryRepairTo')==cn;start=footer(fi-1,cl[fi-1]['uid']);assert struct.unpack_from('<i',a,start+1)[0]==f['country_index'];edits.append((start+1,4,struct.pack('<i',cn)));cedits.append((f['start']+1,4,struct.pack('<i',cn)))
   if r['CurrentDivisionIndex']!=div:edits.append((r['Start']+7,4,struct.pack('<i',div)));leaguechanges.append(dict(TeamIndex=ti,ClubUID=u,old=r['CurrentDivisionIndex'],target=div))
  else:
   u=x['ProjectedClubUID'];ti=oldTeam+len(teams);fi=parent['FamilyIndex']if parent else oldName+len(names);assert ti==x['ProjectedTeamIndex']and fi==x['ProjectedFamilyIndex'],('projection_changed',x['TMID'],ti,fi,x['ProjectedTeamIndex'],x['ProjectedFamilyIndex']);kind='new_linked_reserve'if parent else'new_first_team'
  spec=dict(x,ClubUID=u,Country=x['Country']);pf=read(B/x['ProfileFile']);spec['StadiumName']=(pf.get('stadium')or{}).get('name')or pf.get('stadium_name');si=venue(spec);assignments[u]=si
  if kind=='new_first_team':
   bb,bc,tm=identity(tree,fi,u),identity(ctree,fi,u),identity(team,ti,u)
   for q in [bb,bc]:struct.pack_into('<i',q,1,cn);struct.pack_into('<H',q,17,int(x.get('YearFounded')or 0))
   bb[52]=0;assert bb[47]==bb[52]==0;struct.pack_into('<i',bb,183,ti);struct.pack_into('<i',tm,91,fi)
   for off,val in [(7,div),(11,div),(15,int(x.get('DesiredAlternative')if x.get('DesiredAlternative')is not None else -1)),(19,si)]:struct.pack_into('<i',tm,off,val)
   names.append(bytes(bb));clients.append(bytes(bc));teams.append(bytes(tm));additions.append(dict(uid=u,team_index=ti,family_index=fi,name=name,country=cn,stadium_index=si,sugar_daddy=False,kind=kind,parent_uid=None))
  elif kind=='new_linked_reserve':
   pi=parent['TeamIndex'];pu=parent['ClubUID'];assert parent['CountryIndex']==cn
   if fi>=oldName:
    ni=fi-oldName;bb=bytearray(names[ni]);assert bb[182]==1 and struct.unpack_from('<i',bb,183)[0]==pi;bb[182]=2;bb[187:187]=struct.pack('<i',ti);names[ni]=bytes(bb)
   else:
    low=footer(fi-1,cl[fi-1]['uid']);end=footer(fi,pu);members=[]
    for r0 in records:
     rend=r0['RosterOffset']+2+4*struct.unpack_from('<H',a,r0['RosterOffset'])[0];ref=struct.unpack_from('<i',a,r0['Footer']-14)[0]
     if not(0<=ref<=100000):
      for pos in range(rend,r0['Footer']-6):
       if a[pos:pos+3]==bytes([0,0,255]):
        value=struct.unpack_from('<i',a,pos+3)[0]
        if 0<value<100000:ref=value;break
     if ref==fi:members.append(r0['TeamIndex'])
    assert pi in members and 0<len(members)<255;count=len(members);hits=[]
    for at in range(low,end-8-4*count):
     if a[at]!=count:continue
     found=list(struct.unpack_from('<'+'i'*count,a,at+1))
     if len(set(found))==count and set(found)==set(members):hits.append((at,found))
    assert len(hits)==1,('parent_member_vector_not_unique',pu,members,hits);at,found=hits[0];edits.append((at,1+4*count,bytes([count+1])+struct.pack('<'+'i'*(count+1),*(found+[ti]))));parent_edits[pu]=dict(source_members=found,new_member=ti,source_offset=at)
   tm=bytearray(team[:87])+bytes([10,0,0,255])+struct.pack('<i',fi)+slot(name)+slot(name)+struct.pack('<iI',ti,u)
   for off,val in [(7,div),(11,div),(15,int(x.get('DesiredAlternative')if x.get('DesiredAlternative')is not None else -1)),(19,si)]:struct.pack_into('<i',tm,off,val)
   teams.append(bytes(tm));additions.append(dict(uid=u,team_index=ti,family_index=fi,name=name,country=cn,stadium_index=si,sugar_daddy=None,kind=kind,parent_uid=pu))
  item=dict(ClubName=name,ClubUID=u,TeamIndex=ti,FamilyIndex=fi,CountryIndex=cn,DivisionIndex=div,Group=x['Country']+' '+str(div),RealLeague=str(x['RealLevel']),Country=x['Country'],TMID=x['TMID'],Kind=kind,ParentUID=parent['ClubUID']if parent else'',IdentityDecision=x['IdentityDecision']);bytm[x['TMID']]=item
  if x.get('Role')=='loan_owner_only':ownermap.append(item)
  else:mapping.append(item)
 wanted={v['TeamIndex']for v in mapping}
 target_by_uid={v['ClubUID']:v for v in mapping}
 def setdiv(r,target,reason):
  at=r['Start']+7;index=next((i for i,v in enumerate(edits)if v[0]==at),None)
  if index is None:edits.append((at,4,struct.pack('<i',target)))
  else:edits[index]=(at,4,struct.pack('<i',target))
  change=next((v for v in leaguechanges if v['ClubUID']==r['ClubUID']),None)
  if change:change.update(target=target,reason=reason)
  else:leaguechanges.append(dict(TeamIndex=r['TeamIndex'],ClubUID=r['ClubUID'],old=r['CurrentDivisionIndex'],target=target,reason=reason))
 cfg=read(B/'structure-config.json')
 for q in cfg['requirements']:
  if q['max']==-1:q['max']=None
 cfg['expected_count_deltas']={d:v for d,v in cfg['expected_count_deltas'].items()if v}
 planned=cfg['moves']
 for move in cfg.get('alternate_moves',[]):
  r=byuid[move['ClubUID']];at=r['Start']+15;before=struct.unpack_from('<i',a,at)[0];assert before==move['Before']
  if before!=move['After']:edits.append((at,4,struct.pack('<i',move['After'])))

 for move in planned:
  r=byuid[move['ClubUID']];assert r['CurrentDivisionIndex']==move['Before'],('stale_move',move)
  if r['ClubUID']in target_by_uid:assert target_by_uid[r['ClubUID']]['DivisionIndex']==move['After']
  if move['Before']!=move['After']:setdiv(r,move['After'],move['Reason'])
 def proposed(r):
  if r['ClubUID']in target_by_uid:return target_by_uid[r['ClubUID']]['DivisionIndex']
  z=next((x for x in leaguechanges if x['ClubUID']==r['ClubUID']),None);return z['target']if z else r['CurrentDivisionIndex']
 expected_counts=Counter(proposed(r)for r in records)
 for x in additions:expected_counts[bytm[next(v['TMID']for v in plan if bytm[v['TMID']]['ClubUID']==x['uid'])]['DivisionIndex']]+=1
 for q in cfg['requirements']:
  count=expected_counts[q['index']];assert count>=q['min'] and(q['max']is None or count<=q['max']),('native_requirement_failed',q,count)
 actual_deltas={str(d):expected_counts[d]-sum(r['CurrentDivisionIndex']==d for r in records)for d in expected_counts if expected_counts[d]!=sum(r['CurrentDivisionIndex']==d for r in records)}
 assert actual_deltas==cfg['expected_count_deltas'],('allocation_differs',actual_deltas,cfg['expected_count_deltas'])
 for u,si in assignments.items():
  if u in byuid and si>=0:
   at=byuid[u]['Start']+19;before=struct.unpack_from('<i',a,at)[0]
   if before!=si:edits.append((at,4,struct.pack('<i',si)))
 sugar=[]
 for x in rows(B/'new-clubs-sugar-daddy-audit.csv'):
  at=int(x['SugarDaddyOffset']);before=int(x['SugarDaddyBefore']);assert a[at]==before
  edits.append((at,1,b'\0'))
  sugar.append(dict(ClubUID=int(x['ClubUID']),before=before,after=0))
 allbuffers=[a,c,load(src,'people_db.dat')]+[v for _,v in lb]
 for uid in [x['uid']for x in additions]+[x['uid']for x in venueadd]:
  for buf in allbuffers:assert struct.pack('<i',uid)not in buf,('UID_collision',uid)
 n=len(names);ns=len(venueadd);edits += [(nameco,4,struct.pack('<i',oldName+n)),(nameend,0,b''.join(names)),(coteam,4,struct.pack('<i',oldTeam+len(teams))),(teamend,0,b''.join(teams)),(stco,4,struct.pack('<i',len(st)+ns)),(stend,0,b''.join(bytes.fromhex(x['raw'])for x in venueadd))];cedits += [(cco,4,struct.pack('<i',oldName+n)),(cend,0,b''.join(clients)),(cstco,4,struct.pack('<i',len(st)+ns)),(cstend,0,b''.join(bytes.fromhex(x['raw'])[:1]+bytes.fromhex(x['raw'])[44:]for x in venueadd))]
 s,proofs=apply_verified(a,edits);cc,cproofs=apply_verified(c,cedits);generated=[];langproof=[];renames={int(v['NativeClubUID']):v for v in plan if v['NativeClubUID']and not v.get('ParentTMID')}
 for lang,data in lb:
  spans=language_spans(data);clsp,stsp=spans['club'],spans['stadium'];ce=b''.join(struct.pack('<i',x['uid'])+slot(x['name']if lang in [8,18]else'')+slot(x['name']if lang in [8,18]else'')+bytes(14)for x in additions if x['kind']=='new_first_team');ve=b''.join(struct.pack('<i',x['uid'])+slot(x['name']if lang in [8,18]else'')for x in venueadd);v,p=apply_verified(data,name_edits(data,plan,lang)+[(clsp['count_offset'],4,struct.pack('<i',oldName+n)),(clsp['end'],0,ce),(stsp['count_offset'],4,struct.pack('<i',len(st)+ns)),(stsp['end'],0,ve)]);generated.append((lang,v));langproof.append(dict(language=lang,inverse_verified=True,edits=p))
 for _,value in generated:lang_sections(value)
 # All inverse and identity checks finish before any database directory is created.
 shutil.copytree(src,dest)
 for f,data in [('server_db.dat',s),('client_db.dat',cc)]:(dest/f).write_bytes((src/f).read_bytes()[:9]+zlib.compress(data))
 (dest/'lang_db.dat').write_bytes(repack_languages((src/'lang_db.dat').read_bytes(),generated));assert load(dest,'people_db.dat')==load(src,'people_db.dat')and pins(src)==expected
 save(B/'club-map.csv',mapping);save(B/'foreign-owner-map.csv',ownermap);dump(B/'structure-report.json',dict(status='structure_written_rosters_pending',source=str(src),source_hashes=expected,output=str(dest),output_hashes=pins(dest),new_clubs=len(teams),new_families=n,new_stadiums=ns,foreign_owner_map=ownermap,retirement_repairs=retirement_repairs,parent_member_edits=parent_edits,additions=additions,venues=venueadd,venue_assignments=venuechanges,venue_gaps=gaps,sugar_daddy_repairs=sugar,league_changes=leaguechanges,SERVER_edits=proofs,CLIENT_edits=cproofs,language_proofs=langproof,inverse_verified=True,people_identical=True))
 editor=B/'tools/FM08_Database_Editor.exe';args=[str(R/'SWEDEN_SELECTION_REPAIR_X4_20261110/tools/ExportWholeNativeStructure.exe'),str(dest),str(editor),str(B/'native-structure-after.json')];r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300);(B/'structure-export.log').write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0,r.stderr;rr=read(B/'native-structure-after.json')['records'];rb={r['TeamIndex']:r for r in rr}
 for x in mapping:assert rb[x['TeamIndex']]['ClubUID']==x['ClubUID']and rb[x['TeamIndex']]['CurrentDivisionIndex']==x['DivisionIndex']
 counts=Counter(r['CurrentDivisionIndex']for r in rr);assert counts==expected_counts,('actual_reload_counts_differ',counts-expected_counts,expected_counts-counts)
 for x in mapping+ownermap:
  r=rb[x['TeamIndex']];assert r['ClubUID']==x['ClubUID']and r['CurrentDivisionIndex']==x['DivisionIndex']
 for old in records:
  new=rb[old['TeamIndex']];expected_alt=next((q['After']for q in cfg.get('alternate_moves',[])if q['ClubUID']==old['ClubUID']),struct.unpack_from('<i',a,old['Start']+15)[0]);assert struct.unpack_from('<i',s,new['Start']+15)[0]==expected_alt,('undeclared_alternate_league_changed',old['ClubUID'])
 for q in cfg['requirements']:assert counts[q['index']]>=q['min']and(q['max']is None or counts[q['index']]<=q['max'])
 # Fresh family walk verifies every project-created flag, independently of original offset positions.
 en2,_=lang_sections(dict(languages((dest/'lang_db.dat').read_bytes()))[8]);families,_,_=find_table(cc,[x['uid']for x in en2['club']],club);_,_,co=find_table(s,[x['uid']for x in en2['city']],city);fb=co+4;span=s[fb:min(r['Start']for r in rr)];addeduids={x['ClubUID']for x in sugar}|{x['uid']for x in additions if x['kind']=='new_first_team'};verified=[]
 for f in families:
  if f['uid']not in addeduids:continue
  off=fb+unique(span,struct.pack('<iI',f['index']-1,families[f['index']-1]['uid']))+8;cur=Cursor(s,off);assert cur.byte()==0;cur.integer();cur.byte();cur.string();cur.byte();cur.string();cur.take(2);cur.num('<H');cur.integer();cur.take(1+12+1+2+4+1+1)
  for _ in range(2):cur.take(cur.byte()*4)
  assert cur.byte()==0;raw=cur.take(45);assert raw[4]==0;verified.append(f['uid'])
 assert len(verified)==len(addeduids);dump(B/'structure-independent.json',dict(status='pass',source_unchanged=True,project_clubs_sugar_daddy_off=len(verified),disabled_flags=sum(x['before']for x in sugar),native_counts={str(q['index']):counts[q['index']]for q in cfg['requirements']},inverse_all_buffers=True,people_identical=True,new_stadiums=ns,assigned_venue_clubs=len(venuechanges),venue_gaps=gaps));print('PASS X7 structure teams',len(teams),'families',n,'stadiums',ns,'SugarOFF',len(verified),'venue_gaps',len(gaps))
if __name__=='__main__':main()
