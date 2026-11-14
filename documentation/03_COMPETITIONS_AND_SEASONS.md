# Competitions, country selection and season transitions

## Data does not define every rule

Assigning clubs to an existing COMP is a data change. Increasing a top division's size, adding a national rules module or replacing a stage factory can require different code. The database description XML is not an executable competition host.

The classic database preserves supported FM08 structures; the extended variant can share people/clubs but requires the corresponding launcher runtime and separately tested rules. Starting an extended data folder without its runtime does not reproduce the extended format. Updating DAT files does not transform a world already serialized inside a career.

Classic cascade decisions use completed previous-season standings, not a current live table. Resolve all teams, lower-pool backfills and reserve parents before fetching squads. Missing people do not justify fake profiles or relaxing technical validation. [POLICY](SOURCES.md#policy)

## TEAM assignment fields and loader effects

In the verified serialized TEAM prefix: Current is +7, Previous +11, Alternate +15; Regional is +47. These offsets belong to that format, not arbitrary runtime objects. Previous is not the alternate season assignment.

Country selection has Current and effective Alternate banks. Alternate generally falls back to Current if unset. Native regional membership can be additive; a selected and regional match can contribute twice under a native counter. Country-specific generic pools also have distinct semantics. Preserve each bank's actual minimum/maximum: max=-2 means exactly the minimum, max=-1 means unbounded.

The loaded world can differ from raw DAT. FM08 overwrites historical next-division assignments for some teams. A difference list is not a complete loader write set: an overwrite matching source is invisible in such a list. COMP indices can also change at runtime. Compare by UID and reproduce observed loader transformations.

Selection, eligible scheduler candidates, group draw, fixtures, save/load and the next season are independent checks. Numeric eligibility alone did not prevent the CFA or Belgian Cup failures.

## Country findings

### Poland: third tier and a four-group feeder

The R9.2 pilot demonstrated native group construction and season initialization for UID129560. It uses a UID/type/empty-state guard at D7C9C9, native GROUP_STAGE construction E3A560 and XML-stage binding E29270. An additional guard at D644B2 preserves native initialization through virtual +0x32C rather than hardcoding a year.

Attempt 1 retained a destroyed object's address and crashed at DC412E. Attempt 2 created the four groups but skipped season setup: owner+0xD8=0 and 50 dates in year zero. The final trial produced four groups of 25, valid year-2007 dates, and actual fixtures after the draw on 27 July.

The user confirmed career creation, tables/fixtures, save/reload, the 2008/09 transition and both promotion/relegation playoff results. The recorded balance was 18/18/100, with 3/3 between upper levels and 5/5 with the feeder. Exact tie hosts and mid-playoff save/reload remain separately unproved. This pilot is not the same as the later stock-size 16/18 classic modernization. [POLAND](SOURCES.md#poland)

### Wales and United States: lower pools matter

The first combined update hid these countries after higher divisions depleted required lower pools. The recorded repair requires Welsh Football League Division 1 >=17, USL First >=11 and USL Second >=9. Preserving only playable top-tier counts was insufficient. [POLICY](SOURCES.md#policy)

### Sweden: historical alternate assignments

X3/X4/X5 failed country selection. Fourteen historical loader writes were eventually established; an Orebro1842 overwrite had been invisible when it matched source. X6 changed only GIF Sundsvall1791's serialized Alternate from unset to the compatible lower assignment, preserving its Current squad. Runtime selection, a new career and the 1 April 2008 transition with 16 top-flight clubs and fixtures were user-confirmed. This is a compatibility allocation, not a claim about a real relegation. [SWEDEN](SOURCES.md#sweden)

### Singapore: Current and Alternate must agree with limits

X7 had Current12 versus effective Alternate13 when the maximum was12. X8 repaired six assignment fields and runtime showed12/12; Singapore became selectable. The country uses a calendar-season schedule, so a July career start may enter mid-season. Jurong's data-only presence outside the playable league does not prove automatic future promotion. Small database selection can omit some imported people. [SINGAPORE](SOURCES.md#singapore), [ARCH](SOURCES.md#arch)

### France CFA: candidate pruning is stricter than the selector

The X18 warning was `ARRAY::remove_range() - arguments out of range`, not a proven fatal exception. FRE_CFA UID145438 needed72 slots (4x18), but its pruning candidate list contained67: 53 direct-Current records plus14 generated reserve candidates. Nineteen regional-only physical records did not become scheduler candidates. Two native kind3 teams were already accepted, so blaming all reserve kinds was unsupported.

The identified prune path requires `N > need`: even N=72 gives an invalid endpoint. A later data repair in X19 restored a sufficient eligible direct pool without suppressing the bounds check. X19 career creation passed; it later encountered a separate Dutch playoff defect. [CFA](SOURCES.md#cfa), [CFA-REPAIR](SOURCES.md#cfa-repair)

### Netherlands: period/playoff qualification

X19's playoff stage had7 entrants while a10-team template accessed index9; a replay later exposed8/10 and an out-of-range index8. The original run reached an AV at E293AE. Correct total second-division size did not imply eight eligible second-tier qualifiers.

The accepted classic data correction moves four Jong teams to nonplayable pool550, replaces their places with ranked eligible first teams, and backfills four lower-pool vacancies:12 Current edits. Native kinds, parents, contracts and squads stay intact. The precise refill/invalidation mechanism was not fully reconstructed; the repair limits an incompatible reserve qualification scenario. X20 subsequently passed the user's simulation through2011. This is not proof that every reserve is globally forbidden in every FM08 league. [NETHERLANDS](SOURCES.md#netherlands)

### Belgium: a first-season exception

X21 crashed on5 October2007: Belgian Cup CUP_STAGE contained110 valid teams, but a fixture referenced participant110, beyond0..109, causing C0000005 at DA729E.

The first-season template needs111:74 lower teams +19 second-tier +18 top-tier. The naive second-tier modernization to18 was incompatible with that 2007/08 path. X22 moves RFC Meux UID3200589 from third-tier B to the second tier using the completed25/26 ranking: one Current field; second tier19 and third groups16+15. Other native data is preserved. The user now confirms X22 through2011 without errors. Updating DAT does not repair the already-created X21 save. [BELGIUM](SOURCES.md#belgium), [X22-STATUS](SOURCES.md#x22-status)

### England: all six levels and required lower pools

X23 uses20/24/24/24/24/22/22 across seven groups. Four excess sixth-level clubs retain modernized squads in lower pools: Hereford, King's Lynn and Farnborough to Southern Premier; Dover to Isthmian Premier. Historical successor identities stay distinct. Four legacy ALT conflicts are explicitly repaired. All16 English declarations /32 bank conditions and the global621-condition check passed, but X23 season acceptance remains pending. [X23](SOURCES.md#x23)

### Other scoped checks

China's bank-specific requirements, Brazil's16x8 first-phase scheduled slots, and Czech native reserve-kind witnesses are explicitly reviewed in the later country batches. Treat each as a country contract, not a generic rule transferable by changing a country index. Their source pointers are included in the inventory.

### Thailand: standalone activation without engine changes is blocked

The isolated X9 attempt reported `Cannot find setup_discipline_rules function for rule group`. Generic XML-driven fixture setup did not provide a complete national module: D64730 unconditionally requests `_setup_discipline_rules`. D69A90 also needs it on load; D66B00 does not parse an XML replacement. The observed `rule_group` string is a save block, not an alias selecting a different country's module.

The user rejected engine changes and postponed Thailand. A donor-country replacement is a different compromise affecting identity, national rules and continental access; it was not approved. Do not label X9 successful or silence the warning by clearing discipline metadata. [THAILAND](SOURCES.md#thailand)
