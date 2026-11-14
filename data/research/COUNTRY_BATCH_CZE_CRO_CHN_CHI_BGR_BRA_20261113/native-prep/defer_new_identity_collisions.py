from pathlib import Path
from collections import defaultdict,Counter
import json,csv,hashlib,shutil,statistics,sys
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;OLD=B/'prepared';P=B/'prepared-r3';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));rows=lambda p:list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def save(p,vs,fields):
 with p.open('w',encoding='utf-8-sig',newline='')as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(vs)
ps=rows(OLD/'native_players.csv');ids=rows(OLD/'identities.csv');prov=read(OLD/'provenance.json');native=rows(B/'audit/players.csv');nations={x['Nation']for x in rows(B/'audit/nations.csv')};updated={int(i['ExistingID']):(i['ExpectedFirstName'],i['ExpectedLastName'],i['TargetDOB'])for i in ids if int(i['ExistingID'])>0};source=defaultdict(list);groups=defaultdict(list)
for n in native:source[updated.get(int(n['ID']),(n['FirstName'],n['LastName'],n['BirthDate']))].append(n)
for p,i,v in zip(ps,ids,prov):
 if int(p['ExistingID'])<0:groups[(p['FirstName'],p['LastName'],p['BirthDate'])].append((p,i,v))
records=[];bad=set();preserve=set();nationality=[]
for k,vs in groups.items():
 hit=source[k];reasons=[]
 if hit:reasons.append('exact_N4Id_already_in_source_after_reuse_DOB_projection')
 if len(vs)>1:reasons.append('different_source_TMIDs_same_exact_new_N4Id')
 if any(p['Nationality']not in nations for p,i,v in vs):reasons.append('unknown_native_nationality_dictionary_value')
 if not reasons:continue
 for p,i,v in vs:
  sid=str(i['SubjectID']);bad.add(sid);uids=[int(n['ID'])for n in hit];preserve.update(uids)
  d=dict(SubjectID=sid,TMID=v['TMID'],Name=v['name'],Club=v['playing_club_TMID'],Reason=';'.join(reasons),N4Id=dict(FirstName=k[0],LastName=k[1],BirthDate=k[2]),SourceNativeNationality=p['Nationality'],NativeUIDsProtected=uids,NativeMatches=[{key:n[key]for key in ['ID','FirstName','LastName','BirthDate','Nationality','ClubIndex']}for n in hit],OtherSourceTMIDs=[vv['TMID']for pp,ii,vv in vs if vv['TMID']!=v['TMID']],Action='DEFER_NEW_KEEP_NATIVE_IDENTITY_AND_NATIONALITY_NO_FORCED_REUSE')
  records.append(d)
  if hit:nationality.append(d)
assert len(records)==46 and len(nationality)==44 and not(set(updated)&preserve)
assert not P.exists();shutil.copytree(OLD,P);assert all(sha(P/x.name)==sha(x)for x in OLD.iterdir()if x.is_file())
keep=[j for j,i in enumerate(ids)if str(i['SubjectID'])not in bad];ps2=[ps[j]for j in keep];ids2=[ids[j]for j in keep];pv2=[prov[j]for j in keep];loans=rows(OLD/'loans.csv');ls2=[l for l in loans if str(l['SubjectID'])not in bad]
for n,v in [('native_players.csv',ps2),('identities.csv',ids2),('loans.csv',ls2)]:save(P/n,v,list(rows(OLD/n)[0]))
dump(P/'provenance.json',pv2);deferred=read(OLD/'deferred.json')+records;dump(P/'deferred.json',deferred);gaps=read(OLD/'source-gaps.json')+records;dump(P/'source-gaps.json',gaps)
coverage=read(OLD/'coverage.json')
for c in coverage:
 c['Confirmed']=sum(int(i['PlayingClubIndex'])==c['TEAM']for i in ids2);c['Goalkeepers']=sum(int(i['PlayingClubIndex'])==c['TEAM']and p['PosGK']=='20'for i,p in zip(ids2,ps2))
dump(P/'coverage.json',coverage)
m=read(P/'manifest.json');m['counts'].update(prepared=len(ps2),reuse=len(updated),new=sum(int(p['ExistingID'])<0 for p in ps2),loans=len(ls2),actor_clubs=sum(c['Confirmed']>0 for c in coverage),deferred=len(deferred),source_gaps=len(gaps));m.update(status='prepared_r3_exact_N4Id_conflicts_deferred',output=str(B/'roster-db-r3'),prepared_rows=len(ps2),prepared_loans=len(ls2),source_gaps_count=len(gaps),structural_only_club_uids=[c['ClubUID']for c in coverage if c['Confirmed']==0],partial_roster_club_uids=[c['ClubUID']for c in coverage if c['Confirmed']<17 or not c['Goalkeepers']])
for key in ['preserve_absent_uids','protected_player_uids']:m[key]=sorted(set(map(int,m[key]))|preserve)
for key in ['pilot_verification_path','pilot_verification_sha256']:m.pop(key,None)
# Keep the whole immutable talent draw ledger. A deferred winner is not redrawn.
kept_tm={v['TMID']for v in pv2};classrows=rows(OLD/'rating-source-classification.csv');classrows=[x for x in classrows if x['TMID']in kept_tm];save(P/'rating-source-classification.csv',classrows,list(rows(OLD/'rating-source-classification.csv')[0]));classbytm={x['TMID']:x['Class']for x in classrows};plans={x['TMID']:x for x in read(B/'club-plan.json')};stats=[];parts=[]
for country in sorted({c['Country']for c in plans.values()}):
 for level in range(1,7):
  es=[(p,v)for p,v in zip(ps2,pv2)if plans[v['playing_club_TMID']]['Country']==country and int(v['rating_level'])==level]
  if not es:continue
  ca=[int(p['CA'])for p,v in es];pa=[int(p['PA'])for p,v in es];new=sum(int(p['ExistingID'])<0 for p,v in es);stats.append(dict(Country=country,RealLevel=level,Players=len(es),New=new,Preserved=len(es)-new,CAmin=min(ca),CAmean=round(statistics.mean(ca),2),CAstd=round(statistics.pstdev(ca),2),CAmax=max(ca),PAmin=min(pa),PAmean=round(statistics.mean(pa),2),PAmax=max(pa),PA150plus=sum(x>=150 for x in pa),PA180plus=sum(x>=180 for x in pa),UniqueCA=len(set(ca)),MeanDevelopmentGap=round(statistics.mean(y-x for x,y in zip(ca,pa)),2)))
 for cls in sorted(set(classbytm.values())):
  es=[(p,v)for p,v in zip(ps2,pv2)if plans[v['playing_club_TMID']]['Country']==country and classbytm[v['TMID']]==cls]
  if not es:continue
  ca=[int(p['CA'])for p,v in es];pa=[int(p['PA'])for p,v in es];parts.append(dict(Country=country,RatingClass=cls,Players=len(es),CAmin=min(ca),CAmean=round(statistics.mean(ca),2),CAstd=round(statistics.pstdev(ca),2),CAmax=max(ca),PAmin=min(pa),PAmean=round(statistics.mean(pa),2),PAmax=max(pa),UniqueCA=len(set(ca)),MeanDevelopmentGap=round(statistics.mean(y-x for x,y in zip(ca,pa)),2),PA150plus=sum(x>=150 for x in pa),PA180plus=sum(x>=180 for x in pa)))
for n,v in [('rating-distribution.csv',stats),('rating-distribution-by-provenance.csv',parts)]:save(P/n,v,list(v[0]))
remaining=defaultdict(list)
for p,i,v in zip(ps2,ids2,pv2):
 if int(p['ExistingID'])<0:
  k=(p['FirstName'],p['LastName'],p['BirthDate']);assert p['Nationality']in nations and not source[k];remaining[k].append(v['TMID'])
assert all(len(v)==1 for v in remaining.values())and sum(len(v)for v in remaining.values())==5498
m['prepared_hashes']={str(p.relative_to(P)):sha(p)for p in P.rglob('*')if p.is_file()and p.name not in ['manifest.json','native-contract-resolution.json']};dump(P/'manifest.json',m)
dump(B/'new-N4Id-batch-preflight-r3.json',dict(Status='PASS_ALL_NEW_EXACT_N4Id_KEYS_AFTER_DEFER',OriginalNew5544=5544,ComparedNativeRecords=len(native),SimulatedReuseDOBs=len(updated),SourceKeyCollisions44=44,NewNewSourceKeyRows2=2,UnknownNationality=0,DeferredNew46=46,RemainingNew5498=5498,SourceMatchingUIDsPreserved=sorted(preserve),Records=records,NoNewReuse=True,NoAdditionalN4Read=True,TalentDrawsNotRepeated=True,OriginalPreparedManifestSHA256=sha(OLD/'manifest.json'),PreparedR3ManifestSHA256=sha(P/'manifest.json')))
dump(B/'next-batch-nationality-identity-review44.json',nationality)
dump(B/'pilot-r2/failure.json',dict(Status='FAILED_CLOSED_NO_NATIVE_OUTPUT',Reason='44 new exact source keys with conflicting native nationality plus2 new-new exact identity keys found by one complete batch review',NativeOutputCreated=(B/'pilot-db-r2').exists(),RetryPrepared=str(P),N4NotRepeated=True));assert not(B/'pilot-db-r2').exists()
for name in ['apply_rosters.py','apply_legacy_ratings.py']:
 p=B/name;s=p.read_text(encoding='utf-8');s=s.replace("P=B/'prepared'","P=B/'prepared-r3'")
 if name=='apply_rosters.py':s=s.replace("d=B/'pilot-r2'","d=B/'pilot-r3'").replace("output=str(B/'pilot-db-r2')","output=str(B/'pilot-db-r3')")
 p.write_text(s,encoding='utf-8')
print('FINAL_R3',m['counts']);print('MANIFEST',sha(P/'manifest.json'));print('PREFLIGHT',sha(B/'new-N4Id-batch-preflight-r3.json'));print('LOANS_REMOVED',len(loans)-len(ls2))
