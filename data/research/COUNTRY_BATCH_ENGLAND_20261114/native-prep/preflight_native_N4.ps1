param([Parameter(Mandatory=$true)][string]$Batch,[string]$N4WorkerPath='J:/FM08dev/FmLauncher/data/research/COUNTRY_BATCH_BLR_BEL_AUT_AUS_ARG_20261114/native-prep/tools/ApplyBatchRoster-Current.exe',[string]$ExpectedWorkerSHA256='5ef53f49f578129c078c6cee5d22690d5c8a85c09c9b6501aadea5565eaf2b38')
$ErrorActionPreference='Stop'
$base=[IO.Path]::GetFullPath($Batch)
$source=Join-Path $base 'input/X22-after-SI'
$tool=[IO.Path]::GetFullPath($N4WorkerPath)
$editor=Join-Path $base 'tools/FM08_Database_Editor.exe'
$freeze=Get-Content -LiteralPath (Join-Path $base 'source-freeze.json') -Raw -Encoding UTF8|ConvertFrom-Json
if([IO.Path]::GetFullPath($freeze.frozen)-ne[IO.Path]::GetFullPath($source)){throw 'N4 source must be the pinned X22 freeze'}
function Assert-N4PinnedSource {
 foreach($name in @('people_db.dat','server_db.dat')){
  $actual=(Get-FileHash -LiteralPath (Join-Path $source $name) -Algorithm SHA256).Hash.ToLowerInvariant()
  if($actual-ne([string]$freeze.hashes.$name).ToLowerInvariant()){throw ('N4 immutable source hash changed: '+$name)}
 }
}
Assert-N4PinnedSource
if((Get-FileHash -LiteralPath $tool -Algorithm SHA256).Hash.ToLowerInvariant()-ne$ExpectedWorkerSHA256.ToLowerInvariant()){throw 'N4 read-only worker hash differs from pinned verified build'}
if((Get-FileHash -LiteralPath $editor -Algorithm SHA256).Hash.ToLowerInvariant()-ne'6af063b5cee8d6f47326c3a62cc56c25138b01d07d43eb4745a850d2233bc17b'){throw 'N4 editor hash mismatch'}
$editorasm=[Reflection.Assembly]::LoadFrom($editor)
$asm=[Reflection.Assembly]::LoadFrom($tool)
$worker=$asm.GetType('VerifiedNativeSquadsWorker')
$ed=$editorasm.GetType('FM08_Database_Editor')
if($null-eq$worker-or$null-eq$ed){throw 'N4 expected verified worker/editor type missing'}
$flags=[Reflection.BindingFlags]'NonPublic,Static'
$dec=$ed.GetMethod('DecompressFile',$flags).CreateDelegate([Func[string,byte[]]])
$people=[byte[]]$dec.Invoke((Join-Path $source 'people_db.dat'));$server=[byte[]]$dec.Invoke((Join-Path $source 'server_db.dat'))
$args1=New-Object object[] 1;$args1[0]=$server
$clubs=$ed.GetMethod('ParseClubs',$flags).Invoke($null,$args1)
$nations=$ed.GetMethod('ParseNations',$flags).Invoke($null,$args1)
$args4=New-Object object[] 4;$args4[0]=$people;$args4[1]=$server;$args4[2]=$clubs;$args4[3]=$nations
$all=$worker.GetMethod('ReadPlayers',$flags).Invoke($null,$args4)
$actorRequest=Get-Content -LiteralPath (Join-Path $base 'N4-requested-UIDs.json') -Raw -Encoding UTF8|ConvertFrom-Json
$wanted=New-Object 'System.Collections.Generic.HashSet[int]';foreach($u in $actorRequest.UIDs){$null=$wanted.Add([int]$u)}
$participants=New-Object 'System.Collections.Generic.HashSet[int]';foreach($u in $actorRequest.ParticipantUIDs){$null=$participants.Add([int]$u)}
$method=$worker.GetMethod('N4Evidence',$flags);$call=New-Object object[] 2;$call[0]=$people
$pass=New-Object 'System.Collections.Generic.List[object]';$fail=New-Object 'System.Collections.Generic.List[object]';$seen=New-Object 'System.Collections.Generic.HashSet[int]'
$sha=[System.Security.Cryptography.SHA256]::Create()
foreach($p in $all){
 $uid=[int]$p.Id
 if(-not $wanted.Contains($uid)){continue}
 if(-not $seen.Add($uid)){throw "Repeated native UID $uid"}
 $call[1]=$p
 try{
  $e=$method.Invoke($null,$call)
  $hex=[BitConverter]::ToString($sha.ComputeHash([byte[]]$e.Bytes)).Replace('-','').ToLowerInvariant()
  $pass.Add(@{UID=$uid;Participant=$participants.Contains($uid);Start=[int]$e.Start;End=[int]$e.End;OwnerOffset=[int]$e.Owner;DOBOffset=[int]$e.Dob;ContractOffset=[int]$e.Contract;PayloadOffset=[int]$e.Payload;ContractLength=[int]$e.Length;WholePERSONSHA256=$hex;PersonIndex=[BitConverter]::ToInt32($people,[int]$e.Start);OwnerTEAM=[int]$p.ClubId})
 }catch{
  $reason=$_.Exception.Message;if($_.Exception.InnerException){$reason=$_.Exception.InnerException.Message}
  $fail.Add(@{UID=$uid;Participant=$participants.Contains($uid);SourceFirstNameReaderLabel=[string]$p.FirstName;SourceLastNameReaderLabel=[string]$p.LastName;CommonName=[string]$p.CommonName;Club=[int]$p.ClubId;Reason=$reason;OwnerOffset=[int]$p.ClubIdOffset;DOBOffset=[int]$p.BirthDateOffset;NationOffset=[int]$p.NationIdOffset;Action='FAIL_CLOSED; defer participant or preserve legacy record before any writer, never skip N4'})
 }
}
if($seen.Count-ne$wanted.Count){throw "Missing source actor UIDs $($wanted.Count-$seen.Count)"}
Assert-N4PinnedSource
@{Status='GLOBAL_SOURCE_N4_FORMAT_PREFLIGHT_READ_COMPLETE';Requested=$wanted.Count;Passed=$pass.Count;Failures=@($fail.ToArray());Participants=$participants.Count;ParticipantFailures=@($fail|Where-Object Participant).Count;Predicate='Unchanged N4Evidence from verified X17 worker; source bytes untouched';NativeWrite=$false;Rows=@($pass.ToArray())}|ConvertTo-Json -Depth 7|Set-Content -LiteralPath (Join-Path $base 'N4-source-contract-preflight.json') -Encoding UTF8
Write-Output ('N4 SOURCE checked='+$seen.Count+' passed='+$pass.Count+' failures='+$fail.Count+' participantFailures='+@($fail|Where-Object Participant).Count)
