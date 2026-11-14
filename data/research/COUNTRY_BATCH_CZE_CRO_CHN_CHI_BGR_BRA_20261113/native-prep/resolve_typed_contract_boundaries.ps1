param([string]$Editor,[string]$Source,[string]$Candidates,[string]$Output)
$ErrorActionPreference='Stop'
$asm=[Reflection.Assembly]::LoadFrom([IO.Path]::GetFullPath($Editor))
$type=$asm.GetType('FM08_Database_Editor')
$flags=[Reflection.BindingFlags]'NonPublic,Static'
$decompress=$type.GetMethod('DecompressFile',$flags).CreateDelegate([System.Func[System.String,System.Byte[]]])
$server=[byte[]]$decompress.Invoke((Join-Path $Source 'server_db.dat'))
$people=[byte[]]$decompress.Invoke((Join-Path $Source 'people_db.dat'))
$data=Get-Content -LiteralPath $Candidates -Raw -Encoding UTF8 | ConvertFrom-Json
$teams=[int[]]$data.Teams
$method=$type.GetMethod('ResolveNativeClubContractReferences',[Reflection.BindingFlags]'Public,Static')
$callArgs=New-Object object[] 3
$callArgs[0]=$server
$callArgs[1]=[BitConverter]::ToInt32($people,0)
$callArgs[2]=$teams
$resolution=$method.Invoke($null,$callArgs)
$refs=@{}
foreach($entry in $resolution.GetEnumerator()){$refs[[string]$entry.Key]=[int]$entry.Value}
$inside=$type.GetMethod('IsInsideNativeString',$flags)
$insideArgs=New-Object object[] 2
$insideArgs[0]=$server
$boundary=$type.GetMethod('IsNativeClubFamilyBoundary',$flags)
$boundaryArgs=New-Object object[] 3
$boundaryArgs[0]=$server
$boundaryArgs[2]=[int]$data.TeamStart
$offsets=@{}
$witnesses=New-Object 'System.Collections.Generic.List[object]'
foreach($family in $data.Families){
 $good=New-Object 'System.Collections.Generic.List[int]'
 foreach($position in $family.Positions){
  $at=[int]$position
  $insideArgs[1]=$at
  $boundaryArgs[1]=$at+8
  $isString=[bool]$inside.Invoke($null,$insideArgs)
  $isBoundary=[bool]$boundary.Invoke($null,$boundaryArgs)
  if((-not $isString) -and $isBoundary){$good.Add($at)}
 }
 if($good.Count -ne 1){throw "No unique typed FAMILY boundary for index $($family.FamilyIndex), UID $($family.FamilyUID): $($good.Count)"}
 $offsets[[string]$family.FamilyIndex]=$good[0]
 $witnesses.Add(@{FamilyIndex=[int]$family.FamilyIndex;FamilyUID=[int]$family.FamilyUID;RawCandidates=@($family.Positions);TypedOffset=$good[0]})
}
@{Resolution=$refs;TypedOffsets=$offsets;Witnesses=@($witnesses.ToArray());Predicate='Existing compiled IsNativeClubFamilyBoundary and not IsInsideNativeString; exactly one per requested FAMILY';NativeWrite=$false} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Output -Encoding UTF8
Write-Output ('Typed FAMILY boundaries: '+$offsets.Count+'; actual TEAM contract references: '+$refs.Count)
