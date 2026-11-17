# Finances, sponsorship and reputation

## Separate quantities, separate evidence

Club cash, transfer allowance, wage allowance, actual payroll, debt, future income, commercial contracts, club value and player-market value are different quantities. A figure needs currency, unit, period and reference date. A technical raw zero is not automatically a confirmed real-world zero. The displayed currency is not proof of the stored unit.

The later finance/reputation review is still a proposal for broader calibration; it did not implement modern financial amounts for every club. Our priority remains squads, team identities and league membership. Same-tier native financial templates are explicit estimates, not researched commercial deals. [FINANCE](SOURCES.md#finance), [FINANCE-PLAN](SOURCES.md#finance-plan)

## What the formats prove

C6C940 selects a finance object through CLUB+0x11C in FM08, compared with+0x118 in the FM07 reference. The FM08 kind0 base reader CC35C0 consumes45 bytes, versus31 in the older schema. Kind1 and other variants require separate support.

The common kind0 payload contains several signed raw integers, a date blob and floating fields. Their historical technical names are not confirmation of balance, transfer budget, wage budget or annual income semantics. Do not copy FM07 offsets or relabel every scalar as euros.

The editor exposes Future Income and Future Income End Date. Their precise binding to native sponsorship agreements remains unproven. Actual native agreement generation, renewal and accounting were subsequently traced on15November2026; see the continuation below. The requested practical database policy remains analogous same-tier amounts where the field is proven, not invented real sponsor names or contracts.

FM07's SPONSOR table contains identities/names/flags; preserving it in a converter is not modernization of club contract amounts and dates. FM08 source club agreements and payment paths are now identified, but a safe database contract writer and runtime cashflow/reload validation remain open.

### Runtime sponsorship records already located

The finance-summary path94E8E3..94EC62 reads32-byte records at+0x430/count+0x570. Later RTTI/dynamic-cast evidence establishes the owner as **FINANCES_PANEL_INFO**, a panel snapshot. These offsets must not be used as the actual source-contract layout. Recorded snapshot fields include season amount+0, date data+4, end-year word+0xA, signed length byte+0xC, type+0xD and display identifier+0x10. Unnamed type0 selects kit, type3 stadium and the remaining observed fallback general; this is not a complete source type enumeration. Source records and generation are described below. [LEGACY-STATUS](SOURCES.md#legacy-status)

## Sugar Daddy: proven field and current policy

D390C0 recognizes SUGAR_DADDY opcode0x36; D3DDF0 reaches finance virtual+0x198, ultimately C5E220, which sets runtime finance+0x0C. CC35C0 maps it to byte+4 of a correctly located kind0 payload. A controlled SI checkbox change and later removal samples establish the boolean.

Do not interpret that as an unlimited-money formula: contribution amounts, timing and owner changes were not fully traced. It also affects the recorded staff-quota path.

The user superseded the old owner-wealth recommendation on9 November: every project-created club has Sugar Daddy OFF, including wealthy-owner clubs and external loan owners. Each import explicitly writes/checks it for all earlier project families. X23 independently verifies756 families OFF. Do not zero unrelated authentic clubs globally or infer the flag solely from a billionaire owner. [POLICY](SOURCES.md#policy), [PERSONALITY](SOURCES.md#personality), [X23](SOURCES.md#x23)

The user-reported extreme wages in X16 were a display/currency-cache issue and the audit was stopped. That report is not evidence for scaling every contract or financial field.

## Club versus competition reputation

The typed TEAM reputation candidate is a signed16 read from DAT TEAM+3 into runtime TEAM+0x70; first-team getters can supply shared club context. An inventory observed values0..9700, not an independently proven universal editor maximum. A new global club calibration still needs the planned SI semantics/control sample.

Competition reputation is a different word at COMP+0x84, typically on the1..20 scale. The studied68-byte COMP record stores the corresponding word at+0x0E. UID and table index are distinct: Serie A is UID32, not22;22 is the German top division UID.

Two historical career observations found the same values for39 selected competitions, but this does not prove league reputation can never change. Identified writes include initialization, loading/copying, a zero-valued parent inheriting its first child's reputation, and Network Competition100000023 being set to20. The parent rule is not a sporting-growth formula. [ARCH](SOURCES.md#arch)

## UEFA coefficients are not reputation

EUR_SEEDING's annual callbackE25F30 reaches the June15 rollover throughE20E20. Its initialization call has a different mode; not every invocation is a season completion.

Native club history contains five scaled year values. The traced annual club addition uses current club points plus0.33 of the selected country's latest annual result. Country history can have six entries while the ranking sum uses only0..4. This is FM08 evidence, not the modern OpenFM2007 coefficient model. Exact all-round bonus rules were not closed by that audit.

## Our optional reputation extension

The initial observer kept an immutable baseline, simulated targets and recorded reports. A real two-year user observation changed ten simulated values while native reputations stayed unchanged. That was observer-mode acceptance.

Later source implements a separate optional actual-change path in GameLeagueChangesPatch and LeagueChanges. It uses career identity/generation guards, baseline targets, a two-year cadence, bounded one-point steps and a journal. Do not repeat the old observer-only description as the present state of all source; equally, do not treat an unrelated database holiday test as acceptance of every enabled optional reputation feature.

The baseline model is `R_target=clamp(round(R_start+1.7*(sqrt(C_now)-sqrt(C_start))),1,20)`, with a bounded adjustment rather than adding a fresh increment to the already changed baseline every year. The coefficient1.7 and calibration are our policy, not recovered stock behaviour. Existing-save baselines, branch/reload identity and journals require their own compatibility contract. [REPUTATION-CODE](SOURCES.md#reputation-code)

## Proposed modernization order

Inventory current values and family sharing; verify units and SI labels; calibrate reputation separately; compare day-zero explicit and engine-generated finance; then validate one season's cashflow without counting the same funding twice. Assign a financial change once per FAMILY. Do not confuse real sporting tier with a technical compatibility placement in another classic division.

## Recurring domestic TV: allocation traced on15 November2026

The identified full-finance route credits a club on Sundays using its competition's
annual entitlement divided by52. This is a per-club getter, not a conserved pool
divided automatically by league size. National overrides differ: England/Germany
have fixed shares, France/Portugal/Brazil use reputation bands, Spain/Italy add
another club-field input, and Poland/Denmark use previous league/finishing data.
England also overrides the effective getter for relegation support. Reputation
updates can therefore alter native income without any extra financial patch.

The generic competition-reputation fallback applies only when its level/type
gates allow it and no individual `itvm` array exists. Do not extrapolate it to
all leagues, or infer zero total TV income from one getter returning zero.
The actual credit and forecast paths must share any future allocation change;
adding a new weekly receipt alongside native payments would double-count income.

Full formulas, original currencies, function addresses, evidence hashes and
runtime limitations: [TV allocation report](../FmLauncher/data/research/COMPETITION_PRIZE_TV_ENGINE_20261114/tv_20261115/TV_ALLOCATION_REPORT.md).
Static analysis confirmed; runtime payment/reload/year-total test pending. This
investigation did not change the database, game or launcher.

## Native sponsorship continuation:15 November2026

The source financial-agreement container is CLUB+0x140 (getterC5ED60), not the
panel snapshot. Source objects are0x2C bytes; amount+0x24 is the **total deal
value**, divided by native duration to display/pay the annual amount. Source
types1/3/4 credit the sponsorship ledger throughA42420 ->finance+B0 ->CC7B00.
The same container also has non-sponsorship categories, including type5 TV.

New agreement generatorD2E330 already combines club reputation, **domestic
league reputationCOMP+0x84**, adjusted nation inputs, bounded randomness and
country-specific money rules. C5F720 stores annual amount times duration and
the club-reputation baseline. Ordinary renewalA42420 instead uses the ratio of
current to saved **club** reputation, raised to the fourth power for sponsor
types1/3/4, with75–250% annual bounds and additional baseline/ceiling cases.
These are stock engine findings, not our new policy.

Explicit agreement payments use seasonal processing throughA44B30/CC8C60, with
a300-day last-processed-date gate and season/calendar conditions. Initialization
mode1 subtracts positive cash before categorised credit, producing no net new
cash. A separate monthly pathA42990/CC6A00 generates commercial income for
particular nation branches; one offsets annual explicit sponsorship by1/12.
Changing all sponsor-labelled receipts globally would therefore be unsafe.

Separate optional modifiers are feasible for domesticTV, prize categories,
European distributions, new sponsor contracts and renewal. They must use the
right reputation field, preserve forecasts/contract display, and avoid repeatedly
scaling already modified amounts. Multiplier strengths and runtime implementation
are not approved/completed by this analysis.

[Full sponsor formulas, accounting paths and modifier design](../FmLauncher/data/research/COMPETITION_PRIZE_TV_ENGINE_20261114/sponsors_20261115/REPORT.md)
include original instruction hashes and explicit remaining runtime tests. Editor
Future Income binding and a safe native contract writer remain unproven.

## Currency context and preference drift —16 November2026

Native conversion helpers temporarily change process-global currency ID/rate
and restore them on ordinary return. Display selection and a Preferences
constructor branch also read that state. These are not independently isolated
contexts. A read-only no-launcher session recorded shared GBP/EUR changes lasting
seconds with unchanged on-disk GBP selection; the actual spontaneous BRL/USD
preference failure and writer remain untraced. Do not call the concurrency model
a confirmed root cause or assume launcher responsibility. A periodic preference
enforcer could interfere with financial conversions and is not an approved fix.

[Currency report and original instruction/runtime evidence](../FmLauncher/data/research/CURRENCY_PREFERENCE_DRIFT_20261116/REPORT.md).
