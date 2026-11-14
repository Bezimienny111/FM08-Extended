param([string]$Tag='build-r6-1')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$repo=Split-Path -Parent $root
$batch=Join-Path $repo 'FmLauncher\data\imports\ASSIGNMENT_REPAIR_20261106\execution-r6'
$out=Join-Path $batch $Tag
& "$root\build.ps1" -OutputDirectory $out
if($LASTEXITCODE -and $LASTEXITCODE -ne 0){throw 'Base build failed'}
$csc=Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe'
$native=@(Get-ChildItem -LiteralPath "$root\scratch" -File -Filter '*NativeSquads.cs' | Sort-Object Name | ForEach-Object {$_.FullName})
$sources=$native+@("$root\scratch\RepairNativeContracts.cs","$root\scratch\AssignmentRepairR6.cs")
& $csc /nologo /optimize+ /platform:x64 /target:exe /main:AssignmentRepairR6 "/out:$out\AssignmentRepairR6.exe" /r:System.Windows.Forms.dll /r:System.Drawing.dll /r:System.Xml.dll /r:System.Web.Extensions.dll "/r:$out\FM08_Database_Editor.exe" @sources
if($LASTEXITCODE -ne 0){throw 'R6 build failed'}
$all=@("$root\FM08_Database_Editor.cs","$root\NativeStaff.cs","$root\build.ps1","$root\scratch\build_assignment_r6.ps1","$root\scratch\prepare_assignment_r6.py","$root\scratch\verify_assignment_r6.py")+$sources
$snapshot=Join-Path $out 'source-snapshot'
New-Item -ItemType Directory -Path $snapshot | Out-Null
$srcpins=@($all | Sort-Object -Unique | ForEach-Object {
 $relative=$_.Substring($root.Length+1)
 $dest=Join-Path $snapshot $relative
 New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
 Copy-Item -LiteralPath $_ -Destination $dest
 [pscustomobject]@{Path=$relative;SHA256=(Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash}
})
$binpins=@(Get-ChildItem -LiteralPath $out -File -Filter '*.exe' | ForEach-Object {[pscustomobject]@{Path=$_.Name;SHA256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}})
[pscustomobject]@{Platform='x64';Sources=$srcpins;Outputs=$binpins} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$out\r6-build-manifest.json" -Encoding UTF8
Write-Output "R6 build ready: $out"

