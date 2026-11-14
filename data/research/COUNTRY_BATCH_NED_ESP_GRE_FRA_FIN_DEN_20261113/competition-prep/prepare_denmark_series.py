from pathlib import Path
from html.parser import HTMLParser
import sys,json,re,hashlib,importlib.util,unicodedata
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8');O=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('existing_tables',Path('J:/FM08dev/FmLauncher/data/research/COUNTRY_BATCH_IDN_IND_HKG_20261112/competition-prep/extract_final_tables.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKD',s.casefold())if c.isalnum())
class LinkedTables(m.Tables):
 def __init__(self):super().__init__();self.alllinks=[];self.links=[]
 def handle_starttag(self,t,a):
  if t=='tr' and self.depth==1:self.links=[]
  super().handle_starttag(t,a)
  if self.depth == 1:
   self.links.extend(v for k,v in a if k in ['href','data-navigate-url'])
   self.links.extend('/hold/'+v for k,v in a if k=='data-teamid')
 def handle_endtag(self,t):
  if t=='tr' and self.depth==1 and self.row is not None:self.alllinks.append((list(self.row),list(self.links)))
  super().handle_endtag(t)
def parse(stem,category,group,previous=False):
 p=O/'sources'/(stem+'.html');z=LinkedTables();z.feed(p.read_text(encoding='utf-8'));tables=[t for t in z.tables if any('K'in r and'V'in r and'P'in r for r in t['Rows'][:2])];assert len(tables)==1,(stem,len(tables));table=tables[0];out=[]
 for r in table['Rows']:
  links=[href for saved,lnks in z.alllinks if saved==r for href in lnks]
  if not r or not r[0].isdigit():continue
  assert len(r)>=8;pos=int(r[0]);name=re.sub(r'\s+i$','',r[1]).strip();games,w,d,l=map(int,r[2:6]);gf,ga=map(int,r[6].split('-'));points=int(r[7]);assert games==w+d+l
  ids=[re.search(r'/hold/(\d+)_(\d+)',href)for href in links];ids=[x for x in ids if x];assert ids,(stem,name,links)
  team,pool=ids[0].groups();assert all(x.groups()==(team,pool)for x in ids)
  out.append(dict(Name=name,OriginalDisplayName=r[1],DBUTeamID=team,DBUPoolID=pool,SourceEntityKey='DBUteam:'+team,Country='Denmark',LeagueCountry='Denmark',SourceSeason='2025/26'if previous else'2026/27',RealLevel=5,Category=category,Group=group,Position=pos,FinalOrderingPosition=pos+(10 if category=='qualification' else 0),Matches=games,Wins=w,Draws=d,Losses=l,GoalsFor=gf,GoalsAgainst=ga,GoalDifference=gf-ga,Points=points,SourceFile='competition-prep/'+str(p.relative_to(O)).replace('\\','/'),SourceSHA256=hashlib.sha256(p.read_bytes()).hexdigest(),CurrentTableOnlyForMembership=not previous))
 assert len(out)==10,(stem,len(out));return out
current=sum([parse('denmark-series-current-pool'+str(i),'regular',i)for i in range(1,5)],[]);prev=sum([parse('denmark-series-previous-'+category+'-pool'+str(i),category,i,True)for category in ['promotion','relegation']for i in [1,2]],[])
for r in prev:r['Category']='qualification'if r['Category']=='relegation'else r['Category'];r['FinalOrderingPosition']=r['Position']+(10 if r['Category']=='qualification' else 0)
assert len(current)==40 and len({r['DBUTeamID']for r in current})==40 and len(prev)==40 and all(r['Matches']== 28 for r in prev)
pmap={norm(r['Name']):r for r in prev};assert len(pmap)==40
# These four same-club names appear also among current professional first teams.
# Mark parent proof required and forbid inheriting the earlier FIRST team's ranking.
parent_alias={'aarhusfremad':'Aarhus Fremad','esbjergfb':'Esbjerg fB','hobroik':'Hobro IK','holstebrob':'Holstebro Boldklub'}
higher={'vejgaardb':('45057',10),'odderfodbold':('13290',11),'iflyseng':('29391',12)}
for r in current:
 k=norm(r['Name']);r['ParentIdentityRequired']=k in parent_alias;r['ParentCandidateName']=parent_alias.get(k);r['PromotionEligibleForClassicFill']=k not in parent_alias;r['TMID']=None;r['PreviousFinal']=pmap.get(k)if k not in parent_alias else None
 if k in higher:r['TMID'],r['PreviousHigherFinalPosition']=higher[k];r['PreviousRealLevel']=4
 if k in parent_alias:r['IdentityWarning']='DBUunqualifiedclubname overlaps currenttop4 firstteam: this is a separate reserveTEAM candidate; must prove parent via DBUTeamID before mapping. Never merge currentroster or inherit olderfirstteamrank.'
 else:r['IdentityWarning']='Danish B often means Boldklub, not Bteam. Do not classify KoldingB/VejgaardB/SkovsgaardB as reserves from suffix alone.'
first=[r for r in current if r.get('PreviousHigherFinalPosition')];assert len(first)==3
eligible=[r for r in current if r['PromotionEligibleForClassicFill']and not r.get('PreviousHigherFinalPosition')and r['PreviousFinal']]
eligible.sort(key=lambda r:(r['PreviousFinal']['FinalOrderingPosition'],-r['PreviousFinal']['Points']/r['PreviousFinal']['Matches'],-r['PreviousFinal']['GoalDifference']/r['PreviousFinal']['Matches'],-r['PreviousFinal']['Wins']/r['PreviousFinal']['Matches'],int(r['DBUTeamID'])))
selected=sorted(first,key=lambda r:r['PreviousHigherFinalPosition'])+eligible[:9];assert len(selected)==12
for rank,r in enumerate(selected,1):r['ClassicFillRank']=rank;r['DesiredNativeLevel']=3;r['DesiredDivisionUID']='REGIONAL_EAST_OR_WEST_1701138_1701139_PENDING_GEOGRAPHIC_BALANCE';r['SelectionRule']='Preserve3previousfourthtier_relegated_currentSeriesfirstteams; then9besteligiblecurrentSeriesclubs from previouscomplete28gamefinalplayofftables; reservesexcluded'
result=dict(Status='CURRENT40_PREVIOUS_FINAL40_COMPLETE_12FEEDER_PLAN_IDENTITY_PENDING',Current=current,PreviousFinal=prev,Selected12=selected,NativePlan=dict(Top=12,First=16,SecondEast=16,SecondWest=16,Composition='currentDK3remaining8 +currentDK4L12 +selectedSeries12 =>32; currentSeriesremaining28 meetsmin28; oldnativeLower min39preserved separately'),RulesSource='sources/denmark-series-rules-official.html',RulesQualification='OfficialDBU§7.3 bars reserve sides inDS from promotion to professional nationaldivisions; finalpoints/GF/GA carriedonce under§5.3, neveradd regular again.',TMIDPolicy='Known3higherIDs from provider previousDK4L; nine newsearchIDsnotinvented. All40officialDBUTeamIDpreserved; missingprofiles canremainstructuralonly.',NumericChecks='40unique currentTEAMids;40previousfinal rows, each28matches andW+D+L=matches')
(O/'denmark-series-catalogue.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(O/'denmark-extra12-club-candidates.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('PASS40current/40final;12selected;parent hints4')
for r in selected:print(r['Name'],r['TMID'],r['DBUTeamID'],r.get('PreviousHigherFinalPosition'),r['PreviousFinal']['FinalOrderingPosition']if r['PreviousFinal']else None)
if __name__=='__main__':pass
