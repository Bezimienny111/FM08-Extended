# Player panels, skins and asset identity

## What is accepted

The user accepted R6's first-click role switching and compact Full-HD layout, R8's single legend frame, and R10's uniform name-plus-value highlight and game-language selection. R12 adds the separately accepted Rules description. Acceptance was scoped to the reported views; it is not proof of every skin/monitor/state.

The supported Ext catalogue is:
- fm2008_ext_left and fm2008_ext_right;
- steklo_black_ext_left and steklo_black_ext_right;
- NocheExt, inheriting the original noche parent when available.

Shared panel changes must include NocheExt. Parent resources remain protected; do not duplicate an entire skin's graphics into the child. The installer uses receipts, backups, hash/readback and an active-game guard. [SKINS](SOURCES.md#skins), [PANEL-R10](SOURCES.md#panel-r10), [NOCHE](SOURCES.md#noche)

## Runtime data and access scope

XML property names alone do not supply every raw value. Native scout-star properties are not raw CA/PA; debug XML declarations do not prove release-build number rendering. CLIENT_BASE_PERSON references can be proxies requiring a typed bridge to the actual server person.

The implemented scope retains own-club/local-game gates and missing-data output. Removing the old explanatory sentence from the panel did not remove those gates. Missing values must display unavailable rather than fabricated neutral attributes.

Twelve hidden values are grouped into Personality, Character and Hidden Attributes: eight personality traits plus Consistency, Important Matches, Injury Proneness and Dirtiness. The distinct SI personality sample defines trait meaning; runtime getters and DAT layout are separate proofs.

R3 showed why a global SERVER scratch property list was the wrong viewer source: it contained no Hhum while the actual PERSON_SCREEN property bag did. R2 additionally encountered a legitimate constructor sentinel-1 mistaken for a live reference. The repaired integration uses the real frontend lifecycle and typed context. [R2-FAIL](SOURCES.md#r2-fail), [R3-FAIL](SOURCES.md#r3-fail)

## Role highlighting

Eleven Genie-derived role profiles choose importance, not a native CA budget. Agreed thresholds: weight>=60 key;20..59 important; otherwise no highlight. Key names are bold with stronger background, important rows use a softer background. Number colour and number font retain the game's original meaning.

Real table cells are STANDARD_COLUMN_LABEL, not LABEL. Names and values each paint a native BOX. Extending a name rectangle alone is insufficient because a later value BOX can cover it. The R9/R10 solution registers both columns, draws after each own BOX and uses disjoint row bands rather than an extra numeric badge. It does not edit attribute values.

The role popup commits the new symbol inside FB4980 before its event. Earlier routing read the previous role and required two selections. R6 synchronizes after the native commit and re-resolves the current popup, with profile/generation/lifecycle guards. A destroyed popup must never be dereferenced after a callback. [FIRST-CLICK](SOURCES.md#first-click), [VALUE-BG](SOURCES.md#value-bg)

The Full-HD layout places three compact four-row hidden tables directly below the main attributes and a single styled legend beneath the photo. The selected role remains visible; No highlighting clears backgrounds. A small-resolution guarantee is not implied by the user's Full-HD test.

## Language

Our additions use FM's saved current_language.xml: Polish -> PL; any other language -> EN. Launcher language remains independent. INSTALL and PLAY resolve the locale for both XML and runtime strings. A language change during a running game takes effect after restarting/reloading Ext.

Literal text/name/title/hint handling prevents mixed native translations from partially translating our English labels. Existing manual edits or unknown receipts are not overwritten indiscriminately.

## Skins, caches and rendering boundaries

FMF resources, cascade inheritance, native factories, widget classes, property binding and renderer lifetimes form separate layers. Adding XML cannot by itself invent a new backend value or provide a draw callback.

Cache and currency display can mislead. The reported repeated300,000/325,000 wages in X16 were withdrawn after currency/skin refresh restored normal values. No wage rewrite was justified. The R2/R3 functional failures were different: pinned runtime evidence proved actual resolver/widget defects.

## Faces, logos and kits

Mappings use final in-game person/club UID, not Transfermarkt ID, a temporary subject number or table index. Reuse proven TMID+real DOB -> final UID; generated future players and same-name people are not interchangeable.

The current prepared delta has20,586 faces180px,864 normal logos180px,724 icons20px,1,707 kits130px, plus214 England faces180px:24,095 target PNGs. These are staged additions, not installed totals. Existing good assets are preserved; missing pictures are not manufactured.

Each PNG requires format/dimensions/alpha/hash checks and XML mapping readback. Install sequentially: base, kits, foreign owners, England. Later plans must be archived and regenerated after earlier config changes; do not bypass a changed-hash guard. At this documentation snapshot FM is still running, so installation is HOLD. [GRAPHICS](SOURCES.md#graphics), [ENGLAND-FACES](SOURCES.md#england-faces)

Downloaded availability is not a redistribution licence. The recorded FC12 kit terms permit local use only; these third-party images were excluded from the GitHub code/database backup. That restriction concerns those assets, not our own research summaries.
