# OpenFM2007 reference: capabilities, gaps and FM08 porting

## Reference identity and interpretation

Local repository: `reference/OpenFM2007`. Reviewed commit: `8395779d64019385153ce2cf451a6621db6db393`. The working copy was verified without fetching newer upstream changes. Findings below describe that snapshot, not today's remote HEAD.

Separate code present, offline tests, developer-reported gameplay and our repeated tests. FM07 addresses, layouts and constructors are not FM08 addresses. A generic host or a parsed option is not automatically a complete working feature. [FM07-COMPARE](SOURCES.md#fm07-compare), [FM07-README](SOURCES.md#fm07-readme)

## Capability map

| Area | Reference implementation | FM08 implication |
|---|---|---|
|Database schemas|Single read/write schema definitions, broad FM07 table coverage and history tools|Reuse architecture and tests; adapt FM08 version gates and differing records|
|Modern conversion|FM24/FM27 source conversion, updates, people/club relationships and UID remapping|A useful mapping reference; not a ready FM08 converter or completeness guarantee|
|Calendar/start year|Data-wide date/year shift and guarded engine year-site patches|A full calendar port is much larger than our DOB mapping|
|Display|Window/fullscreen/zoom/input scaling, proxy/launcher startup and hi-res text/image replay|Potential independent work; widget/rendering ABIs need FM08 evidence|
|Performance|Measured fast file I/O and rendering paths, external profiling tools|Ideas to profile on FM08, not promised speed gains|
|Match squads|26-person match squad /15-player bench path and extra tactical-ID save data|Beyond current FM08 override range; requires structure/UI/save changes|
|Substitution windows|Human and AI paths, interval exceptions, ET additions and state|Useful design, with last-window and persistence gaps|
|Competition host|Native stage settings, children, cups, league/split structures and lifecycle methods|Requires FM08 host/ABI/ownership mappings|
|Modern UEFA|League phases, access lists, draws, knockouts, coefficients, prizes and UI|Substantial port; long-lived state still incomplete in reference|
|Commentary|Token-aware merging of newer English event lines into older structure|Preserve event identities/tokens/cache; no automatic FM08 adoption|

## What actually matched our FM08 data

Controlled read/round-trip comparisons found:
- CLIENT STADIUM:15,122 records byte-exact under the unchanged reference schema.
- CLIENT CLUB:23,395 records byte-exact after preserving four extra bytes per kit.
- CITY:20,273 records in each examined stream after adding an FM08 int32 before the footer.
- LOAN:6,211 records match the32-byte schema.
- LANG: the first12 tables in all20 languages match; additional FM08 trailing bytes must be retained.

SERVER CLUB/TEAM/STADIUM did not pass unchanged FM07 schemas. FM07 uses version0x0430; FM08 uses0x0477. The GROUP_STAGE constructor has ret12 in FM07 and ret16 in our FM08 profile. Virtual slot78 decimal is not offset+0x78. These differences rule out numerical address or whole-record copying.

## Modern UEFA architecture

The reference separates:
- `complg`: definitions and native settings;
- `comphost/comphost_generic`: objects, stages, transitions and lifecycle;
- `compseed`: access lists, countries, titleholders and entrants;
- `compdraw`: league-phase solver and checker;
- `compcoef`: points and coefficient histories;
- `compdump/fm07compare`: logs and independent season/rule checking.

CL UID1301394 and EL1301396 retain their identities; Conference31051584 is added. The data supplies36 clubs with8 distinct opponents for CL/EL (144 matches each), and36 with6 for Conference (108). The project implements the1..8 direct/9..24 playoff/25..36 eliminated structure.

League-phase draws use pots, home/away constraints, country restrictions and bounded backtracking, with a20,000-attempt limit. Qualification draws can refer to a future tie winner/loser; they must resolve those placeholders before building the next fixtures. Rounds also receive losers from other competitions.

Access lists, cup winners, titleholders, vacancies, EPS, inactive associations, final hosts, penalties/away goals, prize timing, records and Super Cup consumers are separate pieces. Replacing Intertoto requires updating its seeding consumers; deleting a database record alone is unsafe. [FM07-UEFA](SOURCES.md#fm07-uefa), [UEFA-GAPS](SOURCES.md#uefa-gaps)

## Confirmed checks and current gaps

We independently checked the144/144/108 fixture-plan shapes, opponents, pot/home-away constraints and97 comparator tests. Those tests did not run the mod inside FM07.

At the pinned latest phase plan, T47 is superseded and T47.1 remains next. The developer fixed second-world crashes and bracket/UI defects, but qualifying still stalls in a second world's second season. Qualification bindings, per-season sizes and global caches need reset/rebuild.

Current-season coefficient points and awarded bonuses are held in memory and are not fully serialized by savearc. That module's extended tactical IDs are not a UEFA-state save implementation. The club coefficient container still retains five seasons despite a parsed club_ring10 option; ranking lag and some bonus lines remain incomplete.

A later README success paragraph does not erase a later phase-plan failure. Some inactive-association selection and vacancy order rules are explicit project approximations. Record that policy instead of presenting it as independently verified current UEFA regulations.

## Other useful mechanisms and limitations

Substitution windows are independent of squad26. They require both the human and AI change paths and a match/side series identity. The source-level final-window counterexample and unpersisted16-slot TEAM_STATE table need attention before a port. [FM07-WINDOWS](SOURCES.md#fm07-windows)

Hi-res rendering keeps a logical surface and replays understood operations on a physical shadow surface, with input scaling. An image cache was removed because verification cost/staleness outweighed it; an off-screen-text replay experiment crashed and was removed. Those removed experiments are not advertised active capabilities.

The fast-I/O/rendering profile estimated about1.2x processing improvement in its own setup. Dynamic-cast caching was rejected after measurement showed only about0.12% of the main thread. A redraw throttle had no measured gain and hurt match smoothness; morale multithreading was rejected as risky. These are valuable negative results, not FM08 performance measurements.

The year-shift tool updates real date/year fields and preserves the1900 sentinel. Engine patches adjust relevant hardcoded years while excluding historical/UI cache constants and special real-world phase-in logic. FM07's20-year shift to2026 is not our FM08's19-year age mapping.

## What would need porting

FM08 already has some mapped native stage constructors, explicit fixture/bracket routes, UEFA seeding, dates, reputation and save callbacks. Poland R9.2 proves a small scoped group/season integration. It does not provide the full UEFA host.

A bounded port needs a declared format and balanced entrants; verified FM08 factories/ABI/ownership; stage lifecycle and calendar; access list and cross-cup routing; solver/checker; table/bracket/history/UI; one-time financial/coefficient accounting; and persistence/reset from the beginning. Add a new COMP and names where necessary, but never confuse data registration with behaviour.

The most independently reusable pieces are the neutral definitions, solver/checker, log format and lifecycle test matrix. A smaller alternate-draw/rundown feature may avoid a full generic host, but still needs native round progression and save/load proof.

No UEFA port, squad26 port, window limiter, hi-res renderer or full start-year shift has been implemented for FM08 merely by writing this documentation.
