param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot ('out\build-' + (Get-Date -Format 'yyyyMMdd-HHmmss')))
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
$Csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $Csc -PathType Leaf)) { throw 'Missing .NET Framework C# compiler.' }
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Build output already exists; choose a new directory.' }
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
$Editor = Join-Path $OutputDirectory 'FM08_Database_Editor.exe'
$InputFiles = New-Object 'System.Collections.Generic.HashSet[string]'
function Build-Tool([string]$Name, [string]$Main, [string[]]$Sources, [string[]]$References) {
    $Arguments = @('/nologo', '/optimize+', '/platform:x64', "/out:$OutputDirectory\$Name.exe")
    if ($Name -eq 'FM08_Database_Editor') { $Arguments += '/target:winexe' }
    else { $Arguments += '/target:exe' }
    if ($Main) { $Arguments += "/main:$Main" }
    foreach ($Reference in $References) { $Arguments += "/r:$Reference" }
    foreach ($Source in $Sources) {
        if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) { throw "Missing source: $Source" }
        [void]$InputFiles.Add($Source)
    }
    & $Csc @Arguments @Sources
    if ($LASTEXITCODE -ne 0) { throw "Build failed: $Name" }
}
$Ui = @('System.Windows.Forms.dll', 'System.Drawing.dll', 'System.Xml.dll')
Build-Tool 'FM08_Database_Editor' '' @("$Root\FM08_Database_Editor.cs") $Ui
$Native = @(Get-ChildItem -LiteralPath "$Root\scratch" -File -Filter '*NativeSquads.cs' |
    Sort-Object Name | ForEach-Object { $_.FullName })
$Native += "$Root\scratch\RepairNativeContracts.cs"
if ($Native.Count -ne 22) { throw "Expected 22 native importer sources, found $($Native.Count)." }
$References = $Ui + @($Editor, 'System.Web.Extensions.dll')
Build-Tool 'ApplyVerifiedNativeSquads' 'ApplyVerifiedNativeSquads' $Native $References
Build-Tool 'ApplyGuardedSquadGaps' 'ApplyGuardedSquadGaps' ($Native + "$Root\scratch\ApplyGuardedSquadGaps.cs") $References
Build-Tool 'RepairPolandU17Assignments' 'RepairPolandU17Assignments' ($Native + "$Root\scratch\RepairPolandU17Assignments.cs") $References
foreach ($Name in @('ExportNativeClubSnapshot', 'TestNativeDatabaseWrites', 'AuditNativeFutureTransfers')) {
    Build-Tool $Name $Name @("$Root\scratch\$Name.cs") ($References + "$OutputDirectory\ApplyVerifiedNativeSquads.exe")
}
Build-Tool 'TestRecoveredImporter' 'TestRecoveredImporter' @("$Root\tests\TestRecoveredImporter.cs") (
    $References + "$OutputDirectory\ApplyVerifiedNativeSquads.exe")
Build-Tool 'TestNativeLoans' 'TestNativeLoans' @("$Root\tests\TestNativeLoans.cs") $References
$SourceHashes = @($InputFiles | Sort-Object | ForEach-Object {
    [pscustomobject]@{
        Path = $_.Substring($Root.Length + 1)
        SHA256 = (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash
    }
})
$OutputHashes = @(Get-ChildItem -LiteralPath $OutputDirectory -File | Sort-Object Name | ForEach-Object {
    [pscustomobject]@{ Path = $_.Name; SHA256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
})
[pscustomobject]@{
    Platform = 'x64'
    Sources = $SourceHashes
    Outputs = $OutputHashes
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$OutputDirectory\build-manifest.json" -Encoding UTF8
Write-Output "Built source-only tools without database writes: $OutputDirectory"
