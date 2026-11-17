# Launcher backup — 17 November2026

Branch: `backup/launcher-0.1.3-r23-20261117`.
Working baseline: `0.1.3 R23`.

This backup preserves the current launcher source, test sources, local English
engine documentation and compact research/checkpoint notes. A copy of the
built R23 app is in `dev-snapshots/launcher-0.1.3-r23/` without personal settings.
No release or main merge is part of this operation.

Included launcher changes since the last main commit:

- Header/sidebar/features/details UI, Graphics and Community Links pages,
  clearer Basic/Advanced skin tools and collapsible startup logs.
- Compatible INI/JSON settings, autosave and preservation of unknown keys.
- Ext player panels, hidden attributes and role highlighting, FM-language
  localization, and team-talk reactions retained after substitutions.
- Applied substitutions/bench settings displayed on the native league rules page.
- Six Ext variants; installation only from Skins > Basic, with backups and
  read-only PLAY readiness checks. NocheExt support is withdrawn.
- Direct PLAY without an unconditional warning/summary; actual guards and
  error messages remain enabled.

The compiled-source hashes are checked against the R23 receipt. Historical
tests are backed up as they stand; the full suite is not claimed passing.
See the snapshot README for obsolete API tests and outstanding game checks.

Large raw research exports, full game memory dumps, player datasets, databases,
the user's career saves, installed skins and local configuration stay outside
this Git backup. Compact reports describe their locations and current status.
