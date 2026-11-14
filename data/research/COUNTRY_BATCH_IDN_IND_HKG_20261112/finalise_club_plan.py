from pathlib import Path
from collections import Counter
import json,hashlib,re
B=Path(__file__).resolve().parent;R=B.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(n,x):(B/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
root=R/'WORK_20261112/X17_IDENTITY_REVIEW/decisions.json';assert hashlib.sha256(root.read_bytes()).hexdigest()=='645c0fbeea90ec8f7ed6fab718f5a80117b52d42af39e0f6a1ecbe2f6401b7e1'
rm={str(x['tmid']):x for x in read(root)['decisions']};local=read(B/'local-alias-decisions.json');lm={x['TMID']:x for x in local};world={x['ClubUID']:x for x in read(B/'native-world-identities.json')};plans=read(B/'club-plan-draft.json');raw={};rawref={}
for p in(B/'sources/tm-raw').glob('*.json'):
 x=read(p)
 if '/clubs?'not in x['url']:continue
 body=json.loads(x['body']).get('data')
 if isinstance(body,list):
  for row in body:raw[str(row['id'])]=row;rawref[str(row['id'])]=str(p.resolve())
for c in plans:
 tid=c['TMID'];x=None
 if tid in rm:x=rm[tid];uid=x['uid'];reason=x['reason'];proof=str(root);decision='reuse_root_documented_identity'
 elif tid in lm:x=lm[tid];uid=x['NativeClubUID'];reason=x['Reason'];proof=str(B/'local-alias-decisions.json');decision='reuse_local_documented_identity'
 if x and uid is None:
  c.update(NativeClubUID=None,NativeTeamIndex=None,NativeFamilyIndex=None,ExistingStadiumIndex=-1,NativeParentUID=None,IdentityDecision='new_entity_candidate',IdentityReason=reason,IdentityEvidence=c['IdentityEvidence']+[proof])
 elif x:
  w=world[uid];assert w['Country']==w['TeamCountry']==c['NativeCountryIndex']and w['NativeTeamKind']==0 and w['TeamTailFamilyUID']==uid
  c.update(NativeClubUID=uid,NativeTeamIndex=w['TeamIndex'],NativeFamilyIndex=w['FamilyIndex'],ExistingStadiumIndex=w['StadiumIndex'],NativeParentUID=w['ParentUID'],IdentityDecision=decision,IdentityReason=reason,IdentityEvidence=c['IdentityEvidence']+[proof])
 if c['NativeClubUID']is None:
  assert c['IdentityDecision']=='new_entity_candidate',c;c['IdentityDecision']='new_real_entity_no_verified_native_predecessor';c['IdentityReason']='Current confirmed source club/country; no safe exactnativeidentity, preserve other existinghistories. Newrecord does not assert absenceofallhistorical links.'
 else:
  w=world[c['NativeClubUID']];c['NativeCountryRepairTo']=c['NativeCountryIndex']if w['Country']==-1 else None
 c['ProfileFile']=str((B/c['ProfileFile']).resolve());c['RosterFile']=str((B/c['RosterFile']).resolve());c['YearFounded']=(lm.get(tid,{}).get('YearFoundedUpdate') or 0) if not c['NativeClubUID']else world[c['NativeClubUID']]['YearFounded'];c['LeagueCountry']=c['Country'];c['SugarDaddy']=False
 if tid=='112843':
  p=read(Path(c['ProfileFile']));assert 'Makassar City FC'in c['SourceNames']and p['name']=='Bintang Galaxy FC';c['SelectedPreviousName']='Makassar City';c['Name']=p['name'];c['IdentityReason']+=' Currentprofile explicitly retains MakassarCity historicalalias.'
 if c.get('PreviousRankEvidencePending'):
  e=next(x for x in read(B/'competition-prep/extra15-club-targets.json')if x['TMID']==tid);c['PreviousRankEvidencePending']=False;c['PreviousRankEvidence']=e;c['MembershipQualification']=e['MembershipQualification']
used=[c['NativeClubUID']for c in plans if c['NativeClubUID']];assert len(used)==len(set(used))and len(plans)==133
# Broad city/island bands, never fabricated point coordinates. Current registered address takes precedence over temporary stadium.
bands={10:['Banda Aceh','Medan','Pekanbaru','Padang','Palembang','Batam','Muara Enim','Lampung'],20:['Jakarta','Tangerang','Bekasi','Bandung','Depok','Tasikmalaya','Ciamis','Kuningan','Garut'],30:['Yogyakarta','Sleman','Semarang','Kendal','Jepara','Surakarta (Solo)','Kudus','Karanganyar','Pati','Tegal','Purbalingga','Bantul','Kebumen'],40:['Surabaya','Sidoarjo','Kediri','Malang','Pamekasan','Lamongan','Blitar','Pasuruan','Ngawi','Gresik','Bojonegoro','Jember','Nganjuk'],50:['Legian-Kuta','Denpasar'],60:['Samarinda','Banjarmasin','Balikpapan Selatan','Sangatta','Martapura','Kalteng'],70:['Makassar','Donggala','Konawe','Palu','Manado'],80:['Ngada'],90:['Jayapura','Kota Biak','Paniai','Wamena']}
lookup={n:k for k,ns in bands.items()for n in ns};region=[]
ip=read(B/'competition-prep/indonesia-plan.json');idn={x['TMID']:x for x in ip['Clubs']}
for c in plans:
 if c['Country']!='Indonesia':continue
 cp=idn[c['TMID']];p=read(Path(c['ProfileFile']));base=raw.get(c['TMID'],{}).get('baseDetails') or {}; superior=base.get('superiorClub') or {}; loc=superior.get('location') or {};city=loc.get('city')or p.get('address_line_2')or'';city=re.sub(r'^\d+\s+','',city).strip();reason='current_registered_source_club_city'
 if c['TMID']=='53944':city='Lampung';reason='explicit_current_club_name_Lampung_over_stale_Jakarta_registered_address'
 if c['TMID']=='100752':city='Kalteng';reason='explicit_current_club_name_Kalteng_over_stale_Tangerang_registered_address'
 assert city in lookup,('unresolved_city_broad_region',c['TMID'],c['Name'],city)
 band=lookup[city];lon=loc.get('longitude');lat=loc.get('latitude');valid=lon is not None and 90<float(lon)<145 and lat is not None and -12<float(lat)<8 and city==loc.get('city')and c['TMID']!='92053'
 sortlon=float(lon)if valid else None
 region.append(dict(TMID=c['TMID'],Name=c['Name'],NativeTier=cp['NativeTier'],City=city,BroadGeographyBand=band,SourceLongitude=sortlon,SourceLatitude=float(lat)if valid else None,CoordinateUsed=valid,RawSourceFile=rawref.get(c['TMID']),ProfileFile=c['ProfileFile'],EvidenceReason=reason,CoordinateCaveat='No fabricated point; broadcity/island band when rawcoordinate missing/contradicts city. Sangatta rawcoordinate points toTimor and is ignored.'))
for tier,size,divs in[(1,18,[618,617]),(2,10,[885,884,886,895])]:
 selected=sorted([r for r in region if r['NativeTier']==tier],key=lambda r:(r['BroadGeographyBand'],r['SourceLongitude']if r['SourceLongitude']is not None else 999,r['City'],int(r['TMID'])))
 assert len(selected)==size*len(divs)
 for i,r in enumerate(selected):r['DesiredDivision']=divs[i//size];r['DesiredAlternative']=615 if tier==1 else 616;r['SelectionOrder']=i+1;r['GeographicCompromise']='Exactnativecounts takepriority; equal-sizedwest/east broadcitybands may splitan island atgroupboundary; detailedtraveloptimisationnotclaimed.'
geo={r['TMID']:r for r in region};other={x['TMID']:x for n in['india-plan.json','hong-kong-plan.json']for x in read(B/'competition-prep'/n)['Clubs']}
for c in plans:
 if c['Country']=='Indonesia':
  cp=idn[c['TMID']];g=geo[c['TMID']];c.update(DesiredDivision=g['DesiredDivision'],DesiredAlternative=g['DesiredAlternative'],NativeTier=cp['NativeTier'],SelectionReason=cp['Reason'],RegionAssignment=g)
 else:
  cp=other[c['TMID']];c.update(DesiredDivision=cp['DesiredDivision'],DesiredAlternative=cp['DesiredAlternative'],SelectionReason='current_source_or_classic_previous_completed_season_cascade')
 c['RegionalDivision']=None
assert Counter(c['DesiredDivision']for c in plans)==Counter({618:18,617:18,885:10,884:10,886:10,895:10,643:10,880:22,636:10,637:15})
dump('club-identities-reviewed.json',plans);dump('club-plan.json',plans);dump('indonesia-region-projection.json',dict(Status='GEOGRAPHIC_CLASSIC_PROJECTION_PINNED_NOT_RUNTIME',Records=region,CurrentGroupCounts=dict(Counter(r['DesiredDivision']for r in region)),AlternativeParentCounts=dict(Counter(r['DesiredAlternative']for r in region)),Caveat='No exactnewcoordinatesortraveloptimisation; family savedregions must be cleared/updated by guardedwriter before loaderreplay.'))
dump('club-plan-proof-pins.json',{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in[root,B/'local-alias-decisions.json',B/'competition-prep/indonesia-plan.json',B/'competition-prep/india-plan.json',B/'competition-prep/hong-kong-plan.json',B/'competition-prep/extra15-club-targets.json',B/'club-plan-draft.json']})
print('PLAN133',len(used),'reuse',133-len(used),'new','counts',dict(Counter(c['DesiredDivision']for c in plans)),flush=True)
