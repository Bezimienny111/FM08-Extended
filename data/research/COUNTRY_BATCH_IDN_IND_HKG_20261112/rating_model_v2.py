"""Deterministic project estimates; real scouting ratings are preserved."""
from datetime import date
import hashlib,random
VERSION="squad-spread-2026-27-v2"
REFERENCE_DATE=date(2026,7,1)
ADULT_CA={1:(123,163),2:(98,143),3:(73,119),4:(55,103),5:(40,88)}
COUNTRY_ADJUSTMENT={"Indonesia":-40,"India":-45,"Hong Kong":-45,"Portugal":-5,"Norway":-15,"Peru":-30,"Poland":-15,"Germany":0,"Mexico":-10,"Malaysia":-40,"South Korea":-15,"Colombia":-15,"Israel":-20,"Iceland":-25,"Northern Ireland":-35,"Ireland":-25}
PA_GAINS=((16,28,55),(18,22,45),(21,14,34),(24,8,20),(28,1,10),(99,0,4))
def rng(uid,purpose):
 return random.Random(int.from_bytes(hashlib.sha256((VERSION+"|"+str(uid)+"|"+purpose).encode()).digest(),"big"))
def estimate(uid,country,real_level,dob,role,existing=None,fc_ca=None,fc_pa=None,old_award=None):
 age=REFERENCE_DATE.year-dob.year-((REFERENCE_DATE.month,REFERENCE_DATE.day)<(dob.month,dob.day))
 if not 14<=age<=50:raise ValueError("unverified_age_or_outside_preparation_range")
 if existing:
  # All credible/native and already accepted estimates stay fixed unless a separately pinned repair allows them.
  ca,pa=existing
  return dict(CA=ca,PA=pa,AbilitySource="preserved_native_profile",Age=age,SeedUID=str(uid),ModelVersion=VERSION,Reestimated=False)
 r=rng(uid,"CA");p=rng(uid,"PA")
 if fc_ca is not None:
  ca=int(fc_ca);source="verified_FC27_CA_estimated_PA_v2"
 else:
  low,high=ADULT_CA[real_level]
  penalty=-30 if age<18 else -17 if age<=20 else -5 if age<=23 else 0
  penalty-=5 if role=="GK"and age>=36 else 8 if role!="GK"and age>=33 else 3 if role!="GK"and age>=30 else 0
  # Player-specific independent triangular spread. No club-wide shared fallback.
  ca=round(r.triangular(low,high,(low+high)/2))+COUNTRY_ADJUSTMENT[country]+penalty
  ca=max(20,min(180,ca));source="estimated_real_level_age_individual_spread_v2"
 if fc_pa is not None:pa=max(ca,int(fc_pa));source="verified_FC27_CA_PA"
 else:
  _,lo,hi=next(row for row in PA_GAINS if age<=row[0]);pa=min(200,ca+p.randint(lo,hi))
 if old_award is not None:pa=max(pa,int(old_award))
 assert 1<=ca<=pa<=200
 return dict(CA=ca,PA=pa,AbilitySource=source,Age=age,SeedUID=str(uid),ModelVersion=VERSION,Reestimated=True)
def test():
 assert estimate("tm:1","Portugal",1,date(2008,1,1),"ST")==estimate("tm:1","Portugal",1,date(2008,1,1),"ST")
 values=[estimate("tm:"+str(i),"Poland",2,date(2008,1,1),"ST")for i in range(1000)]
 assert len({x["CA"]for x in values})>=30
 assert all(x["PA"]>=x["CA"]and 22<=x["PA"]-x["CA"]<=45 for x in values)
 saved=estimate(123,"Peru",1,date(2006,1,1),"MC",existing=(97,178))
 assert(saved["CA"],saved["PA"])==(97,178)and not saved["Reestimated"]
 assert estimate("tm:2","Norway",3,date(2007,1,1),"DC",old_award=195)["PA"]>=195
 assert estimate("tm:3","Portugal",1,date(2000,1,1),"MC",fc_ca=151,fc_pa=165)["CA"]==151
 assert estimate("tm:3","Portugal",1,date(2000,1,1),"MC",fc_ca=151,fc_pa=165)["PA"]==165
 for country in COUNTRY_ADJUSTMENT:
  for level in ADULT_CA:
   for age in [14,16,18,21,24,28,33,40,50]:
    x=estimate("case:"+country+str(level)+str(age),country,level,date(2026-age,1,1),"GK")
    assert 1<=x["CA"]<=x["PA"]<=200
 print("PASS deterministic spread, young gains, preserved profiles/awards, all4countries5levels9ages")
if __name__=="__main__":test()
