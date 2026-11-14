param([switch]$VerifyOnly)

$ErrorActionPreference = 'Stop'

try {

    $pilotRoot = $PSScriptRoot

    $manifest = Get-Content -LiteralPath (Join-Path $pilotRoot 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json

    if (!$VerifyOnly -and $manifest.status -notin @('prepared_for_r9_game_test', 'r9_game_pilot_passed_user_confirmed')) { throw 'R9 package has not passed final preflight.' }
    $dbRoot = Join-Path $pilotRoot 'user-data\db\TEST_POL_3_LEVEL_R9'

    foreach ($entry in $manifest.database_output_hashes.PSObject.Properties) {

        $path = Join-Path $dbRoot $entry.Name

        if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing database file: $path" }

        if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $entry.Value) { throw "Database file changed: $path" }

    }

    $archive = Join-Path $pilotRoot 'runtime\data\updates\update-802\data\comps.efa'

    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $manifest.runtime_comp_archive_sha256) { throw 'Unexpected competition resource archive.' }

    $tool = Join-Path $pilotRoot 'tools\PolandThirdTierFatesR9.exe'

    if ((Get-FileHash -LiteralPath $tool -Algorithm SHA256).Hash -ne $manifest.pilot_tool_sha256) { throw 'Pilot tool hash differs.' }

    $runtime = Join-Path $pilotRoot 'runtime'

    & $tool --verify (Join-Path $runtime 'fm.exe')

    if ($LASTEXITCODE -ne 0) { throw 'Native ABI / executable check failed.' }

    & $tool --verify-runtime $runtime

    if ($LASTEXITCODE -ne 0) { throw 'Runtime layout check failed.' }

    Write-Host 'PASS: database hashes, resources, x86 ABI and isolated runtime.'

    if ($VerifyOnly) { exit 0 }

    & $tool --launch $runtime

    exit $LASTEXITCODE

} catch {

    Write-Error $_ -ErrorAction Continue

    exit 1

}

