from pathlib import Path
import json,datetime,sys
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent
assert not (B/'manifest.json').exists()
x=dict(Status='SOURCE_ONLY_COMPETITION_SCOPE_BEFORE_ROSTERS',Countries=['England'],SnapshotDate='2026-11-14',RealSeason='26/27',PreviousCompletedSeason='25/26',NativeNationIndex=139,NativeNationUID=765,ExpectedClassicPlayableGroups=[20,24,24,24,24,22,22],ClassicPlayingClubs=160,NativeWriterAllowed=False,UIDAllocationAllowed=False,NewTESTVersionReserved=False,ReferenceCandidate='X20acceptedto2011; X21notacceptedcrash2007-10-05, do not freeze/use asnewnativeinput',DatabaseWritten=False,APIfootballCalls=0,GraphicsScope=False,FMOrLauncherMutated=False,DateShiftAtSource=False,MissingPlayers='No forced players/GK/DOB. Confirmed profiles only; preserve explicit gaps for engine.',Cache='existing shared rawcache, original URL/body/hash/fetched_at preserved',CollectionOrder='fullclassicmembership+cascade+identities+parents closed first, then rosters/players/loans')
(B/'manifest.json').write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
