# Bug register and corrections

This register separates native preconditions, incorrect data, our implementation defects, reference-project gaps and corrected research claims. Fixed means only the stated scope was accepted. A later successful database holiday does not test every optional hook. Machine-readable counterpart: [bug-register.json](bug-register.json).

## ENG-CFA-01

**Category:** Competition precondition. **Status:** Mitigated in X19; inherited later tests.

CFA selector counts passed, but scheduler pruning had67 candidates for72 places and needs N>need.

Restore eligible direct candidates; preserve bounds checks and accepted reserve kinds.

Evidence: [CFA](SOURCES.md#cfa), [CFA-REPAIR](SOURCES.md#cfa-repair). [Topic](03_COMPETITIONS_AND_SEASONS.md).

## ENG-NLD-01

**Category:** Competition qualification/data. **Status:** Mitigated in X20; user season test through2011.

Dutch playoff template expected10; observed7, later8 entrants caused out-of-range TEAM access.

Twelve Current edits remove incompatible Jong exposure and backfill first/lower teams; full refill mechanism remains partial.

Evidence: [NETHERLANDS](SOURCES.md#netherlands). [Topic](03_COMPETITIONS_AND_SEASONS.md).

## ENG-BEL-01

**Category:** First-season data exception. **Status:** Resolved in X22; user through2011.

X21 Belgian Cup had110 entrants but referenced slot110; AV atDA729E.

Restore first-season second tier19 through RFC Meux; cup111. New career required.

Evidence: [BELGIUM](SOURCES.md#belgium), [X22-STATUS](SOURCES.md#x22-status). [Topic](03_COMPETITIONS_AND_SEASONS.md).

## ENG-THA-01

**Category:** Missing national module. **Status:** Deferred by user.

X9 cannot find setup_discipline_rules; generic fixture XML is not a complete Thai module.

Keep X9 failed; no discipline suppression, country impersonation or engine change without new scope.

Evidence: [THAILAND](SOURCES.md#thailand). [Topic](03_COMPETITIONS_AND_SEASONS.md).

## DATA-SEL-01

**Category:** Country lower-pool allocation. **Status:** Resolved in recorded X1 repair.

Wales/USA became unavailable after required feeder pools were depleted.

Validate top and lower minima, both banks and cascade backfills.

Evidence: [POLICY](SOURCES.md#policy). [Topic](03_COMPETITIONS_AND_SEASONS.md).

## DATA-SEL-02

**Category:** Loader model. **Status:** Resolved in X6; runtime/career/season accepted.

Swedish difference-only overlay missed a14th write when source already matched it.

Use full observed loader write set; preserve Current and change scoped Alternate only.

Evidence: [SWEDEN](SOURCES.md#sweden). [Topic](03_COMPETITIONS_AND_SEASONS.md).

## DATA-SEL-03

**Category:** Alternate assignment. **Status:** Resolved in X8 selector.

Singapore Current12/Alternate13 exceeded maximum12.

Scoped six-field repair; check both loaded forms.

Evidence: [SINGAPORE](SOURCES.md#singapore). [Topic](03_COMPETITIONS_AND_SEASONS.md).

## OUR-POL-01

**Category:** Object identity. **Status:** Resolved in R9.2 pilot.

A guard retained an allocation that XML-version replacement destroyed; crashDC412E.

Resolve current UID/type instead of remembering the first address.

Evidence: [POLAND](SOURCES.md#poland). [Topic](03_COMPETITIONS_AND_SEASONS.md).

## OUR-POL-02

**Category:** Initialization order. **Status:** Resolved in R9.2; season accepted.

Four groups existed but skipped native season-year initialization; dates in year0.

Permit the earlier native season-init path; do not hardcode calendar year.

Evidence: [POLAND](SOURCES.md#poland). [Topic](03_COMPETITIONS_AND_SEASONS.md).

## OUR-CONTRACT-01

**Category:** Native reference interpretation. **Status:** Corrected by SI controls.

Contract payload+31 had been treated as status instead of the contract FAMILY reference.

Resolve proper owner family and consistent person/roster/contract links.

Evidence: [ARCH](SOURCES.md#arch), [STAFF](SOURCES.md#staff). [Topic](02_NATIVE_DATABASE_FORMAT.md).

## OUR-LOAN-01

**Category:** Reader assumption. **Status:** Corrected; SI samples verified.

Loan parser required every entry UID footer to be-1 and rejected a real SI-created loan.

Support unique positive entry UIDs while preserving all structural guards.

Evidence: [LOANS](SOURCES.md#loans). [Topic](02_NATIVE_DATABASE_FORMAT.md).

## OUR-PERSONALITY-01

**Category:** Shared reader/writer bug. **Status:** Codec corrected; historical data audit separate.

Controversy at+3 shifted five traits; matching reader/writer could conceal the error.

SI eight-distinct-values oracle; canonical order+1..8. Do not rotate all old data blindly.

Evidence: [PERSONALITY](SOURCES.md#personality). [Topic](02_NATIVE_DATABASE_FORMAT.md).

## OUR-NAMES-01

**Category:** Historical native-creation failure. **Status:** Historical unresolved R6025 path.

Correcting a shared surname reference count did not make every old raw native-creation trial load.

Preserve failed samples; name-country segmentation and independent SI acceptance matter.

Evidence: [ARCH](SOURCES.md#arch). [Topic](02_NATIVE_DATABASE_FORMAT.md).

## OUR-NAMES-02

**Category:** Missing embedded club names. **Status:** Corrected by later shared writer; general lookup cause partial.

Three clubs had valid EN/PL names but empty embedded full/short names and blank UI rows.

Fill six logical fields in SERVER/CLIENT; preserve UID/order; no universal fallback or global sort claim.

Evidence: [BLANK-NAMES](SOURCES.md#blank-names). [Topic](02_NATIVE_DATABASE_FORMAT.md).

## OUR-EXPORT-01

**Category:** Exporter search threshold. **Status:** Corrected by full typed export.

Old22MiB scan start could omit early TEAM records in differently sized databases.

Use whole-structure scan from8 with the same structural validation.

Evidence: [POLICY](SOURCES.md#policy). [Topic](02_NATIVE_DATABASE_FORMAT.md).

## OUR-FAMILY-01

**Category:** Identity/boundary assumption. **Status:** Corrected in typed proof workflow.

Name FAMILY, contract FAMILY and an8-byte coincidence were not sufficient to identify every native family.

Fresh typed TEAM tail, parent and materialized contract boundary; reject ambiguity.

Evidence: [X23](SOURCES.md#x23), [FINANCE-PLAN](SOURCES.md#finance-plan). [Topic](02_NATIVE_DATABASE_FORMAT.md).

## OUR-DPA-01

**Category:** Virtual inheritance/hook. **Status:** Corrected source and x86 cases; long run separately scoped.

Normal PLAYER name offsets dereferenced0x10 for a combined player/non-player; AV at01E00135.

Native virtual-base conversion to PERSON; keep type-specific identity proof.

Evidence: [ARCH](SOURCES.md#arch), [PA-PATCH](SOURCES.md#pa-patch). [Topic](01_EVIDENCE_AND_ENGINE_ARCHITECTURE.md).

## OUR-AGING-01

**Category:** Incoming branch/hook layout. **Status:** Corrected and native-execution tested.

Original branches landed inside overwritten aging-hook bytes; AV atA359C1.

Preserve A359C1/A3563E shared entries and test both incoming paths.

Evidence: [ARCH](SOURCES.md#arch), [AGING-CODE](SOURCES.md#aging-code). [Topic](06_TRAINING_AGING_AND_STAFF.md).

## OUR-PANEL-01

**Category:** UI lifecycle/reference. **Status:** R2 failure corrected in successors.

A constructor reference sentinel-1 was treated as a live object.

Validate typed reference and lifecycle; do not hide all faults with a generic pointer cutoff.

Evidence: [R2-FAIL](SOURCES.md#r2-fail). [Topic](08_PLAYER_PANELS_SKINS_AND_GRAPHICS.md).

## OUR-PANEL-02

**Category:** Viewer context. **Status:** Resolved in later working panels.

R3 used an empty global SERVER scratch Hhum rather than actual frontend viewer context.

Typed PERSON_SCREEN/current connection route with own-club gates.

Evidence: [R3-FAIL](SOURCES.md#r3-fail), [PANEL-R10](SOURCES.md#panel-r10). [Topic](08_PLAYER_PANELS_SKINS_AND_GRAPHICS.md).

## OUR-BG-01

**Category:** Wrong widget class. **Status:** Resolved in later working panels.

R3 registered LABEL, but all actual attribute cells were STANDARD_COLUMN_LABEL.

Correct factory, draw path, destructor and scoped native fixtures.

Evidence: [R3-BG](SOURCES.md#r3-bg). [Topic](08_PLAYER_PANELS_SKINS_AND_GRAPHICS.md).

## OUR-BG-02

**Category:** Event ordering. **Status:** Resolved R6; user first-click acceptance.

R5 role symbol committed but background retained previous role until a second choice.

Synchronize after native popup commit, then resolve current live popup.

Evidence: [FIRST-CLICK](SOURCES.md#first-click). [Topic](08_PLAYER_PANELS_SKINS_AND_GRAPHICS.md).

## OUR-BG-03

**Category:** Cell geometry/paint order. **Status:** Resolved R10; user acceptance.

Highlighting numeric text produced a separate badge; later cell BOX could cover a wider name band.

Draw disjoint row bands after both native BOX paints; preserve numeric colour/font.

Evidence: [VALUE-BG](SOURCES.md#value-bg), [PANEL-R10](SOURCES.md#panel-r10). [Topic](08_PLAYER_PANELS_SKINS_AND_GRAPHICS.md).

## OUR-UI-01

**Category:** Layout. **Status:** Resolved R8; user acceptance.

Legend had duplicate framing/scrollbar and cramped hidden tables.

Single skin-style legend; compact three-by-four hidden tables under attributes.

Evidence: [PANEL-R8](SOURCES.md#panel-r8), [PANEL-R10](SOURCES.md#panel-r10). [Topic](08_PLAYER_PANELS_SKINS_AND_GRAPHICS.md).

## OUR-RULES-01

**Category:** Display/enforcement mismatch. **Status:** Resolved R12; scoped Serie A user acceptance.

Native Rules formatter had its own switch and still showed7/3 despite9/5 getters.

Use installed effective-rule resolver and native localized string machinery.

Evidence: [RULES-UI](SOURCES.md#rules-ui), [RULES-R12](SOURCES.md#rules-r12). [Topic](04_MATCH_RULES_AND_RULES_SCREEN.md).

## OUR-FIN-01

**Category:** Inherited test flag. **Status:** Corrected; X23 verifies756 project familiesOFF.

Wieczysta and Termalica inherited Sugar Daddy flags during tests.

Explicit OFF/readback for every project-created family; not a global wipe of authentic clubs.

Evidence: [FINANCE](SOURCES.md#finance), [POLICY](SOURCES.md#policy), [X23](SOURCES.md#x23). [Topic](09_FINANCES_REPUTATION_SPONSORS.md).

## POLICY-ABILITY-01

**Category:** Estimate quality. **Status:** Corrected selectively in X11 and later v2 batches.

Earlier imported estimates were too uniform and often left little development room.

Stable individual spread and age-sensitive PA margins only for proven estimates; preserve credible ratings.

Evidence: [RATINGS](SOURCES.md#ratings), [X23](SOURCES.md#x23). [Topic](05_PLAYER_GENERATION_AND_ABILITY.md).

## DISPLAY-WAGE-01

**Category:** Display/cache report. **Status:** Withdrawn after user refresh.

Repeated extreme X16 wage displays returned to normal after currency/skin refresh.

Do not rewrite contracts on this withdrawn report; audit stopped by user.

Evidence: [USER-DECISIONS](SOURCES.md#user-decisions). [Topic](08_PLAYER_PANELS_SKINS_AND_GRAPHICS.md).

## IDENTITY-MESSI-01

**Category:** Reported game/editor discrepancy. **Status:** Deferred by user.

Modern Messi appeared free at career start while editor assignment looked correct.

No proven contract/MLS cause; user asked to skip. Do not label repaired.

Evidence: [NAZARYNA](SOURCES.md#nazaryna). [Topic](13_RESEARCH_BACKLOG.md).

## IDENTITY-NAZ-01

**Category:** Duplicate person. **Status:** Corrected in X3; native evidence.

Yehor/Yegor Nazaryna duplicates in Shakhtar.

Keep canonical1612002632; remove/retire technical1689002224; preserve canonical CA/PA and attributes.

Evidence: [NAZARYNA](SOURCES.md#nazaryna). [Topic](02_NATIVE_DATABASE_FORMAT.md).

## IDENTITY-KOLDING-01

**Category:** Club-family/role hazard. **Status:** Bounded mapping corrected/protected.

Similar Kolding identities and a kind3/parent relationship could be conflated.

Preserve typed roles/families; no broad name-only role conversion.

Evidence: [FINANCE-PLAN](SOURCES.md#finance-plan), [X23](SOURCES.md#x23). [Topic](02_NATIVE_DATABASE_FORMAT.md).

## DOC-CA-01

**Category:** Research erratum. **Status:** Corrected by later assembly audit.

AD2630 was called a CA normalizer; it only multiplies25..79 by5.

Actual later normalizer A7A860; retain original report with explicit erratum.

Evidence: [ABILITY](SOURCES.md#ability). [Topic](05_PLAYER_GENERATION_AND_ABILITY.md).

## DOC-UID-01

**Category:** Research erratum. **Status:** Superseded.

Old attribute-pid+1 shortcut was described as universal person UID.

Use PERSON and typed table footer identities; indices/UIDs are independent.

Evidence: [ARCH](SOURCES.md#arch). [Topic](02_NATIVE_DATABASE_FORMAT.md).

## DOC-SAVE-01

**Category:** Overstated lifecycle event. **Status:** Open proof gap.

A hook named SaveCompleted can fire through intermediate/refusal epilogues.

Do not commit companion state without proved durable save completion.

Evidence: [COMPANION](SOURCES.md#companion). [Topic](10_SAVE_LOAD_AND_COMPATIBILITY.md).

## DOC-RULEMAP-01

**Category:** Mislabelled classes. **Status:** Four bindings corrected.

Nearest-function labels misattributed Denmark, Belgium, Korea and Belarus rule examples.

RTTI/vtable/constructor UID evidence; leave unresolved parameters unknown.

Evidence: [MATCH-RULES](SOURCES.md#match-rules). [Topic](04_MATCH_RULES_AND_RULES_SCREEN.md).

## TOOLS-DECOMP-01

**Category:** Analysis coverage limitation. **Status:** Known limitation.

REA/Ghidra returned no function for three actual stage methods.

Validate bytes, RTTI and true entry; failure to decompile is not absence of code.

Evidence: [MATCH-RULES](SOURCES.md#match-rules), [R5](SOURCES.md#r5). [Topic](01_EVIDENCE_AND_ENGINE_ARCHITECTURE.md).

## UP-UEFA-01

**Category:** OpenFM2007 lifecycle. **Status:** Upstream snapshot open T47.1.

Qualification stalls in the second season of a second world despite prior fixes.

Reset/rebuild bindings, sizes and caches; two-world/two-season matrix before port.

Evidence: [FM07-UEFA](SOURCES.md#fm07-uefa), [UEFA-GAPS](SOURCES.md#uefa-gaps). [Topic](11_OPENFM2007_CAPABILITIES_AND_PORTING.md).

## UP-SAVE-01

**Category:** OpenFM2007 persistence. **Status:** Upstream snapshot open.

Current coefficient points/awarded bonuses are not fully serialized.

Do not confuse tactical savearc blocks with UEFA persistence.

Evidence: [FM07-UEFA](SOURCES.md#fm07-uefa), [COMPANION](SOURCES.md#companion). [Topic](10_SAVE_LOAD_AND_COMPATIBILITY.md).

## UP-WINDOW-01

**Category:** OpenFM2007 static counterexample. **Status:** Unverified runtime; must test before port.

After first change consumes final window, used_up can reject another change in the same batch.

Permit completion of current series but block a new stoppage; test real record ordering.

Evidence: [FM07-WINDOWS](SOURCES.md#fm07-windows). [Topic](04_MATCH_RULES_AND_RULES_SCREEN.md).

## UP-WINDOW-02

**Category:** OpenFM2007 state model. **Status:** Reference limitation.

Window TEAM_STATE uses16 pointer-keyed entries and no demonstrated serialization.

Stable match/side lifecycle and reload policy; do not copy pointer cache as persistence.

Evidence: [FM07-WINDOWS](SOURCES.md#fm07-windows). [Topic](10_SAVE_LOAD_AND_COMPATIBILITY.md).

## UP-COEF-01

**Category:** OpenFM2007 model coverage. **Status:** Reference limitation.

club_ring10 parsed, native club history five; access-ranking lag and some bonus lines incomplete.

Review data/execution separately and declare deliberate approximations.

Evidence: [FM07-UEFA](SOURCES.md#fm07-uefa). [Topic](11_OPENFM2007_CAPABILITIES_AND_PORTING.md).

## UP-RENDER-01

**Category:** OpenFM2007 experiment. **Status:** Withdrawn upstream experiment.

Off-screen text replay crashed; image caching/redraw throttling had adverse or unhelpful results.

Keep removed experiments as lessons, not active capabilities or promised speedups.

Evidence: [FM07-README](SOURCES.md#fm07-readme). [Topic](11_OPENFM2007_CAPABILITIES_AND_PORTING.md).

## EXT-SAVE-01

**Category:** Persistence experiment. **Status:** Not adopted.

An extra arbitrary FM archive member was lost on native resave.

Design a verified companion transaction; native archive readability alone is insufficient.

Evidence: [ARCH](SOURCES.md#arch), [COMPANION](SOURCES.md#companion). [Topic](10_SAVE_LOAD_AND_COMPATIBILITY.md).

## TOOL-MINISE-01

**Category:** External compatibility report. **Status:** Deferred; no stable reproduction.

User reported mini-SE stopped reading players, then asked to skip the issue.

Do not conclude launcher corrupts player data without a repeatable target/build trace.

Evidence: [USER-DECISIONS](SOURCES.md#user-decisions). [Topic](13_RESEARCH_BACKLOG.md).

## DATA-RET-01

**Category:** User-requested cleanup. **Status:** X24 inventory in progress.

Project-scheduled dates must become1January2007; every target must be checked for surviving contracts/loans.

Proven project UID scope only; preserve stock retirements, revived modern people and X23-after-SI source.

Evidence: [USER-DECISIONS](SOURCES.md#user-decisions). [Topic](13_RESEARCH_BACKLOG.md).


## DOC-ATTR-01

**Category:** Historical offset-base ambiguity. **Status:** Superseded by typed record proof.

Old compendium section3.2 labels an identity-prefixed89-byte reader window; it is not the typed attribute-record base used by current native creation.

Use structural byte0, GK1, Crossing26, Concentration80 and footer index81/UID85; keep runtime and DAT indices separate.

Evidence: [ARCH](SOURCES.md#arch), [NATIVE-BUILDER](SOURCES.md#native-builder). [Topic](02_NATIVE_DATABASE_FORMAT.md).

## ENGINE-CURRENCY-01

**Category:** Reported currency-preference drift. **Status:** Shared runtime
transitions observed; spontaneous preference change/root cause not reproduced.

The user reports BRL/USD becoming selected in Preferences during play. A120s
read-only recording in their no-launcher session observed GBP/EUR shared-state
switches lasting seconds, while the on-disk selected currency stayed GBP.
The user confirmed holiday throughout, no manual currency change or opening
Preferences. A five-second paused follow-up sampled only GBP; the intervening
restoration was not traced. Temporary native conversions share global
currency state with display/preferences and restore it on ordinary return.
A Preferences constructor branch snapshots that shared state; applying the
panel persists it. Overlapping transactions are a plausible failure mechanism,
not a captured failing schedule. Do not periodically force the global currency:
real financial calculations use its rate too.

The local C++ unwind map of converter F599C0 contains only a temporary-object
destructor, without currency restoration. This is an additional static exception
safety gap; no actual throw or failure to recover in an outer scope was observed.

Evidence and exact limits: [currency investigation](../FmLauncher/data/research/CURRENCY_PREFERENCE_DRIFT_20261116/REPORT.md).
