# Substitutions, benches and consistent Rules display

## Verified native domain

FM08 has29 native substitution codes0..28. Getters AFE0D0 and AFE150 provide substitution and bench limits. The native enum names distinguish goalkeeper exceptions, extra-time variants and side-dependent cases. Two codes with equal base numbers are not necessarily equivalent rules.

The complete raw flag0/flag1 results are in [substitution-codes.csv](substitution-codes.csv), derived from the original PE-switch audit. Examples:

| Code | Substitutions flag0/1 | Bench flag0/1 | Qualification |
|---:|---|---|---|
|0|3/3|7/7|three_from_seven|
|1|3/3|5/5|three_from_five|
|11,13|3/3|5/5|Different native extra-time meanings|
|19|0/0|0/0|Vanilla formatter emits no description|
|22|3/3|7/5|Asymmetric; retain native context|
|28|10/12|10/12|Asymmetric all-from variant|

The extra-pool getter AFE080 is an additional flag, not a universal fourth substitution, concussion rule or complete extra-time model. The caller's flag cannot be replaced by a guessed home/away value on neutral grounds. [MATCH-RULES](SOURCES.md#match-rules)

## Assignment coverage

The static survey found373 distinct competition classes and375 binding rows,302 proven literal COMP UIDs,73 unresolved UID parameters,24 explicit XML assignments and478 final map rows. These are not375 playable leagues or a complete live mapping of every fixture.

Four earlier UI labels were corrected: code4=DAN_PREM UID6; code6=BEL_THIRD_REGION with unresolved child UID; code26=KOR_LEAGUE_2 UID5707678; code21=BLR_FIRST UID7483366. RTTI, constructor arguments and the correct stage method establish these bindings; a nearby function filename does not.

## What our launcher changes

Independent bench and substitution overrides operate globally per native code, with supported values0..12. Single and grouped editing resolve into the same29 records. Groups are UI convenience; they do not create competition-specific rules. Two competitions sharing one code cannot receive different enforced limits through this interface.

The installed process uses an immutable applied snapshot. Desired configuration is not evidence of installed behaviour. Installation/readback, process creation identity, EXE hash and payload checks determine readiness; losing them invalidates the applied state. Do not claim hot updating of cached fixtures or in-progress matches.

## Why the league Rules screen initially stayed unchanged

AFDBF0 formats the localized description using its own switch. It does not call the two patched getters. Therefore an engine getter change did not automatically update the displayed numbers.

The rule row pipeline is RULES_PANEL -> DD5AD0/DD4730 -> DD5C70. Rowtype8 carries match payload at `row+0x28`, not+0x20. 7637E0 reads its code at payload+0x1B9 and delegates to AFDBF0.

R12 adds a formatter integration using the same effective resolver and verified applied snapshot as enforcement, preserving the original rule payload. The user confirmed Serie A, nativecode0, showing9 substitutes and5 changes. That is a scoped visual acceptance, not a universal proof of every stage or in-match cache. [RULES-UI](SOURCES.md#rules-ui), [RULES-R12](SOURCES.md#rules-r12)

## Remaining Rules-screen families

The complete [38-discriminator display catalogue](native-rules-display-catalogue.json) preserves native input fields, formatter paths and enforcement limitations. The display audit catalogs38 row discriminators: dates/draw dates; win/draw/loss and bonus points; games/legs/splits; foreign/domestic/age/homegrown/wage restrictions; extra time, away goals, penalties/replays; ranking/tiebreakers; promotion/relegation/playoffs; continental qualification; cards/suspensions; transfer and loan windows; registration; financial prizes/deductions.

These fields have native display paths. Apart from the supported bench/substitution changes, their actual enforcement is not thereby patched. A future change needs the scheduler/eligibility/financial consumer and display to agree. No generic text replacement should pretend to implement a new access list or suspension rule.

## Substitution windows: reference implementation, not current FM08 feature

OpenFM2007 tracks used windows separately from substitutions. It handles player and AI paths, interval exemptions, extra-time additions and parking remaining substitutions after the last window. `windows=0` means unlimited windows. Our two getter overrides do not implement any of this.

A static counterexample in the reference's last-window handling can reject a second player substitution in the same batch after the first consumes the final window. Its16 pointer-indexed TEAM_STATE slots are not serialized. These are porting concerns, not observed FM08 gameplay failures. A future port needs a match/side lifecycle, both execution paths, a proper batch identity, interval/ET proof and persistence tests. [FM07-WINDOWS](SOURCES.md#fm07-windows)

## Useful acceptance cases

Check native fallback; each independently enabled limit; mixed single/group edits; codes19/22/28; side context; localized native string construction/destruction; lost applied state; OFF; existing versus newly built match caches. Window tests, if implemented later, must additionally cover several changes in the last window, AI, halftime and reload.
