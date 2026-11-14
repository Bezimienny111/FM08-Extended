# Finances, sponsorship and reputation

## Separate quantities, separate evidence

Club cash, transfer allowance, wage allowance, actual payroll, debt, future income, commercial contracts, club value and player-market value are different quantities. A figure needs currency, unit, period and reference date. A technical raw zero is not automatically a confirmed real-world zero. The displayed currency is not proof of the stored unit.

The later finance/reputation review is still a proposal for broader calibration; it did not implement modern financial amounts for every club. Our priority remains squads, team identities and league membership. Same-tier native financial templates are explicit estimates, not researched commercial deals. [FINANCE](SOURCES.md#finance), [FINANCE-PLAN](SOURCES.md#finance-plan)

## What the formats prove

C6C940 selects a finance object through CLUB+0x11C in FM08, compared with+0x118 in the FM07 reference. The FM08 kind0 base reader CC35C0 consumes45 bytes, versus31 in the older schema. Kind1 and other variants require separate support.

The common kind0 payload contains several signed raw integers, a date blob and floating fields. Their historical technical names are not confirmation of balance, transfer budget, wage budget or annual income semantics. Do not copy FM07 offsets or relabel every scalar as euros.

The editor exposes Future Income and Future Income End Date. Visibility of those fields does not establish whether they represent annual sponsoring, one-off receipts, defaults, generated income or exact expiry behaviour. The requested practical policy is analogous same-tier amounts where the field is proven, not invented sponsor names or contracts.

FM07's SPONSOR table contains identities/names/flags; preserving it in a converter is not modernization of club contract amounts and dates. FM08 has additional sponsorship-related code paths recorded in the older research, but a complete safe commercial-contract writer and all cashflow semantics remain open.

### Runtime sponsorship records already located

The finance-summary path94E8E3..94EC62 reads32-byte records from an observed object's+0x430 with count+0x570. The owning class was not conclusively established. Recorded fields include season amount+0, date data+4, end-year word+0xA, signed length byte+0xC, type+0xD and sponsor identifier+0x10. Unnamed type0 selects kit, type3 stadium and the remaining observed fallback general. This is a display-reader finding, not a complete type enumeration or a generator/accounting implementation. [LEGACY-STATUS](SOURCES.md#legacy-status)

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
