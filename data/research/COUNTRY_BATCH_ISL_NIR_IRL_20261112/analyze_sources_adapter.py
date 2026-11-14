"""Reuse the completed source-fact analyzer; no database bytes are parsed or changed."""
from pathlib import Path
import hashlib,json,collections,csv,sys
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent
ROOT=B.parents[3]
engine=ROOT/"FmLauncher/data/research/COUNTRY_BATCH_GER_MEX_MAS_20261112/analyze_sources.py"
ENGINE_SHA='a92988ab73f72f4153fa596c5fbcfb127ee1353c2f4dc555238c2d6b054f978d'
assert hashlib.sha256(engine.read_bytes()).hexdigest()==ENGINE_SHA,"Shared analyzer changed; review before reuse"
targets=json.loads((B/"source-targets.json").read_text(encoding="utf-8"))
assert len(targets)==72 and all(c.get("ProfileFile") and c.get("RosterFile") and not c.get("FetchError") for c in targets)
namespace={"__file__":str(Path(__file__)),"__name__":"shared_source_fact_engine"}
exec(compile(engine.read_text(encoding="utf-8"),str(engine),"exec"),namespace)
facts=namespace["facts"];loans=namespace["loans"];coverage=namespace["coverage"]
def dump(name,data):(B/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
counts=[]
for country in ["Iceland","Northern Ireland","Ireland"]:
 rows=[c for c in coverage if c["Country"]==country];ff=[f for f in facts if f["Country"]==country]
 ll=[f for f in ff if f["Loan"] and f["AcceptedFactCandidate"]]
 counts.append(dict(Country=country,Clubs=len(rows),Cards=sum(c["Cards"] for c in rows),UniquePlayerIDs=len({f["TMID"] for f in ff}),ConfirmedCandidateRows=sum(f["AcceptedFactCandidate"] for f in ff),AcceptedLoanRows=len(ll),StadiumProfiles=len(rows)))
dup=collections.defaultdict(list)
for f in facts:
 if f["AcceptedFactCandidate"]:dup[f["TMID"]].append(dict(ClubTMID=f["ClubTMID"],Club=f["ClubName"],MembershipStatus=f["MembershipStatus"]))
dump("multi-club-candidate-queue.json",[dict(TMID=k,Assignments=v,Action="resolve actual playing club before native plan; no duplicate person") for k,v in dup.items() if len(v)>1])
dump("coverage-by-country.json",counts)
with (B/"coverage-by-country.csv").open("w",encoding="utf-8-sig",newline="") as f:
 writer=csv.DictWriter(f,fieldnames=list(counts[0]));writer.writeheader();writer.writerows(counts)
dump("source-facts-engine-pins.json",dict(engine=str(engine.relative_to(ROOT)),engine_sha256=ENGINE_SHA,adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),snapshot_date="2026-11-12",source_dob_shifted=False,CA_PA_generated=False,database_written=False))
print(json.dumps(dict(countries=counts,total_cards=len(facts),unique_players=len({f["TMID"] for f in facts}),accepted_rows=sum(f["AcceptedFactCandidate"] for f in facts),loans_candidate=len(loans),accepted_loan_rows=sum(f["Loan"] and f["AcceptedFactCandidate"] for f in facts),source_gaps=len(namespace["gaps"])),ensure_ascii=True))
