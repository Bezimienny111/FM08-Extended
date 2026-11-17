# Launcher 0.1.3 R23 development backup

This directory preserves the last built R23 application. It is a branch snapshot,
not a GitHub Release, a public release announcement or a merge into main.

The EXE requires the .NET8 Windows Desktop runtime and the user's own compatible
FM08 executable. No game executable, game data, skin artwork, career saves or
personal INI/JSON settings are included. Configure the paths after opening it.
Skin creation/update remains available only from Skins > Basic.

`SHA256SUMS.txt` covers the copied payload. `R23_BUILD_RECEIPT.json` preserves
the original source/binary hashes and focused check results. The source code is
under `src/FmLauncher` in this branch.

The original build receipt hashes Windows working-copy source bytes. Git
normalizes source text line endings according to `.gitattributes`; the backup
manifest separately records the actual staged bytes. Snapshot payload files
are marked `-text` to retain their original checksums after a clone/download.

The last focused checks passed: R22 navigation/read-only readiness16 checks,
and R23 direct start/configuration/error propagation3 checks. These do not claim
that the historical combined test suite is current: it still contains calls to
removed `EnsurePanelLanguage` and confirmation-based `LaunchGame` APIs. Those
tests require updates before treating the entire suite as a release gate.

The current catalog contains Base Ext, Steklo Ext and Steklo Black Ext, each in
Left/Right variants. NocheExt remains unsupported; older Noche documents/tests
are historical. New plain Steklo rendering still has its separately recorded
in-game check pending.
