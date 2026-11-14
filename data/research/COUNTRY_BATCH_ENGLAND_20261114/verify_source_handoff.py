from pathlib import Path
import json,hashlib,datetime,collections,sys
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ready=read(B/'source-ready-for-root-review.json');manifest=read(B/'source-manifest.json');qa=read(B/'source-qa.json');gate=read(B/'scope-closures/England.json');closed=read(B/'scope-closures/England-targets.json');progress=read(B/'roster-progress/England-targets.json');facts=read(B/'roster-facts.json');summary=read(B/'source-progress.json')
assert ready['Status']=='READY_SOURCE_DATA_ONLY_NOT_IMPORTED'and not ready['NativeWriteAllowed']and not ready['DatabaseWritten']and not ready['UIDAllocation']
assert ready['SourceManifestSHA256']==sha(B/'source-manifest.json')and ready['SourceQASHA256']==sha(B/'source-qa.json')and ready['ReportSHA256']==sha(B/'SOURCE_RAPORT.md')
for f,h in manifest['Files'].items():assert sha(B/f)==h,('manifesthash',f)
for f,h in gate['Inputs'].items():assert sha(Path(f))==h,('scopeinputhash',f)
assert gate['TargetsSHA256']==sha(B/'scope-closures/England-targets.json')and len(closed)==len(progress)==164
sig=lambda rows:sorted((r['TMID'],r['Country'],r['APISeason'])for r in rows)
assert sig(closed)==sig(progress)and len({r['TMID']for r in closed})==164
assert all('PlayersFetched'in r and not r.get('FetchError')for r in progress)
assert len(facts)==4312 and sum(r['AcceptedFactCandidate']for r in facts)==4256 and len({r['TMID']for r in facts if r['AcceptedFactCandidate']})==4256
assert sum(r['Loan']and r['AcceptedFactCandidate']for r in facts)==495 and len(read(B/'roster-source-gaps.json'))==56
assert all(r['NativeDOBNotCalculated']and r['CA_PA_NotGenerated']and not r['ReadyForNativeImport']for r in facts)
assert sum(r['TargetNativeLevel']<=6 for r in closed)==160 and sum(r['TargetNativeLevel']==7 for r in closed)==4
rawindex=read(B/'raw-source-index.json');assert len({r['raw_file']for r in rawindex})==len(rawindex)
for r in rawindex:
 f=B/r['raw_file'];raw=read(f);assert sha(f)==r['file_sha256']and raw['url']==r['url']and raw['fetched_at']==r['fetched_at'];bodyhash=hashlib.sha256(raw['body'].encode()).hexdigest();assert bodyhash==raw['sha256']==r['body_sha256']
result=dict(Status='PASS_INDEPENDENT_SOURCE_READBACK_NOT_NATIVE_IMPORT',CheckedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),SourceReadySHA256=sha(B/'source-ready-for-root-review.json'),ManifestFilesVerified=len(manifest['Files']),RawResponsesVerified=len(rawindex),ClosedScopeInputsVerified=len(gate['Inputs']),ClosedClubCount=164,PlayingCount=160,RegionalDownCount=4,Cards=4312,AcceptedUniquePeople=4256,AcceptedLoans=495,SourceGaps=56,MissingPlayersNotForced=True,OriginalRawURLBodyTimestampHashesPreserved=True,SourceDatesUnshifted=True,CA_PA_Generated=False,NativeUIDAllocated=False,NativeDBWrite=False,SourceCollectionComplete=True,NativeWriterAllowed=False,ImportStillBlockedByAcceptedSourceAndNativeProjection=True,OwnedActiveProcesses=[],ReadyFile='source-ready-for-root-review.json',SourceReport='SOURCE_RAPORT.md')
(B/'source-independent-readback.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result));print('READBACK_SHA256',sha(B/'source-independent-readback.json'))
