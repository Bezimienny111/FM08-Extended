# New-player attributes and PA population controls — 16 November 2026

The native paths inspected here support a distinction between **probability**, **total population maintenance**, and **per-player validity limits**. No hard quota such as “only 50 players may have PA180+” was found in the inspected permanent-generation/PA-selection paths. This is a scoped negative finding, not a proof about every indirect call or every world-maintenance routine in FM08.

No launcher, game process, database, skin, or saved career was changed. The current launcher remains R23. The balancing prototype is an offline arithmetic experiment, not an installed newgen feature.

## Evidence

- Original `fm.exe` SHA256: `157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d`, image base400000.
- Existing R5 Ghidra export, copied selected C in `evidence/`. Source prototypes are sometimes inaccurate; native instructions settle register/stack arithmetic.
- Fresh Capstone disassembly and byte ranges from the same original EXE, recorded in `engine-proof.json`. Linear ranges are not reconstructed control-flow graphs; initial broad club-pa range includes a small following-function tail. The corrected exact-span supplement is authoritative for that boundary.
- Captured native B[15][80] and recovered Q equations from `../PLAYER_ABILITY_POSITION_AUDIT_20261115/`, not Genie weights for CA accounting.
- REA `list_documents` did not return during this turn. Its waiting caller was stopped; no target was opened or engine setup changed by this investigation. Static continuation used preserved R5 and original file bytes. This does not assert that an unreturned server request completed.

## 1. What determines the number of high-PA players?

### Permanent intake and population

`882570` handles initial youth completion and `883770` seasonal generation. They control how many people are created using squad/position shortages and nation population context. `NATION+12C` is incremented when the permanent factory creates a person; `+130` holds a baseline used by the seasonal controller. The reviewed five seasonal factory callsites are not followed by a visible “count high-PA players and reject this new player” branch in that controller. Registration and indirect call coverage remains a boundary.

These are not histogram bins for PA bands. A squad-size gate, an annual batch size, and the virtual-player pool of200 must not be described as a PA quota.

### Club-generated PA

`CB1350` selects/resolves PA, calling `C64270` for club context and `C80440` to expand a negative category. `C64270` uses club quality (`C63E90`: reputation plus CLUB fieldsE0/E1), country context, a mode argument, detail byte1B1EE79 and random branches. Some special UID branches apply. No world-wide high-PA histogram/count comparison was identified in the inspected helper. E0/E1 and mode/detail labels still need exact editor/runtime mapping; they must not be silently named after modern FM fields.

The global1B212B8 passed into the random helpers is RNG context. `F56800` delegates to the stateful random generator at context+8; the inspected callsites do not establish it as a high-PA counter.

### Country path: population can affect probabilities

The no-club/empty-PA branch of `CB1350` is different. With country+11B==0, instructionsCB1431–CB14C2 recover:

```text
n = country.current_player_count (+12C)
k = trunc(n / 450)
f = signed country byte +F7
s = clamp(k * 10/f, 1, 10) if f > 0
    clamp(k * 5,    1, 10) otherwise
first high-result gate: R(trunc(float32(s) * 300)) == 0
later gates use factors100,30,5
```

The division-by450 compiler sequence was independently checked over0..199999. The first gate opens a range starting at180 with a separately randomized upper bound. This is **not** the overall PA190+ chance; later reconciliation, existing CA and other branches matter. The observed range wrapper has an exclusive upper bound.

Examples with f=10: n=1000 gives first-gate denominator600; n=4500 gives3000. The denominator is bounded by the scale clamp. See `country-population-gates.json`. This is a concrete population-dependent probability mechanism, not “after X stars, stop generating stars.” The editor label of +F7 is not proven here. Do not apply this formula to ordinary club intake or the separate country+11B!=0 branch.

For country+11B!=0, native FPU instructions instead read +F7 and the signed16 country field+10C in a different expression. Recovered constants include0.1,0.0002,5 and200. That branch is deliberately not conflated with the population formula above.

## 2. Individual PA limits and rare extreme PA

`F566E0` returns the high32 bits of a product of a nonnegative31-bit random word and2N. For normal positive small N, `R(N)` is in0..N-1. `5C7740(a,b)` swaps unordered endpoints and returns min+R(max-min). This establishes **exclusive upper bounds**; there is no implicit +1.

With no higher existing valid CA floor, the resolved negative categories are:

| Category | PA range from this converter |
|---|---|
| -10 |170–199, with the reroll below |
| -9 |150–179 |
| -8 |130–159 |
| -7 |110–139 |
| -6 |90–119 |
| -5 |70–99 |
| -4 |50–79 |
| -3 |30–59 |
| -2 |10–39 |
| -1 |1–19 |

In `C80440`, a first -10 draw>=190 triggers **one** fresh draw over the same range. It does not loop until the result is below190. Under an ideal independent uniform-call model, PA190–199 therefore has probability about1/9 instead of1/3, conditional on selecting -10 and using the170 floor. This is not a percentage of all newgens. PRNG discretization/correlations and context are not simulated. `negative-pa-distributions.json` records the illustrative model.

A higher existing valid CA changes the lower endpoint. For CA>=190 the preceding1/9 example does not apply; CA200 can produce PA200. Other PA-setting paths can also supply200. This converter alone must not be called a world-wide PA200 ban.

`CB1350` clears invalid PA>200 or below-10 before resolution. `CB3000` reconciles PA>=CA and clamps final PA to1..200. There are also **conditional repair limits** of2*CA or3*CA in CB344D–CB347F. They are reached only during PA repair, under an additional date-comparison/flag condition, with the original PA not<-1; an already valid PA>=CA bypasses that repair block. The2* branch uses initially valid CA; the3* branch uses newly resolved CA. These are per-player repair rules, not population quotas and not universal limits on all youngsters.

The helperF48DC0 in that condition compares two game dates; it is **not** a population counter. The exact gameplay label of the surrounding date/flag condition remains unresolved.

## 3. Influencing starting attributes without creating clones

The existing Genie role profiles can choose which attributes receive a bonus. **Native mixed-position/foot weights and nonlinear Q** must account for its cost. Equal visible points removed elsewhere do not imply equal cost. Raw attribute+5 usually corresponds to visible+1; preserve the raw remainder.

An experimental bounded policy was exercised offline:

1. Select one or two eligible Genie key attributes at random, with +5/+10 raw bonuses. These example counts/probabilities are proposals, not approved settings.
2. Preserve CA/PA, positions, feet, personality and hidden traits. Only explicitly mapped visible positive-cost attributes participate. Zero-cost attributes are not used to finance changes.
3. Compensate from a random subset of up to four non-highlighted positive-cost attributes, with at most10 raw removed from each. Recompute full nonlinear Q at the unchanged CA after each integer step.
4. Accept only if abs(Qafter-Qbefore)<=0.01. Otherwise return the entire original profile. Limits/tolerance are experimental.
5. Use private deterministic randomness; do not consume extra engine RNG calls. A production seed needs a verified stable career/creation identity. Repeated execution on the same input/seed produces the same result; this is **not** a once-only/save-load guard.

`attribute-experiment.json`:352 synthetic cases over11 roles, including single and mixed positions.231 accepted balanced changes;121 returned the original profile. Protected fields/ranges and deterministic replay checks passed. These counts measure these synthetic cases only, not acceptance rates for real intakes. No native normalizer or match was executed. Q is an equation model, not a complete x87/integer iterator emulator; its tolerance does not prove equal stored/derived CA after subsequent training.

For example a tested DC profile received raw Marking70→75 while several lower-priority visible attributes paid its native cost. The script does not assume one point of Marking costs the same as one point of any donor attribute. A failed compensation does not leave a partially boosted player.

## 4. Implementation boundaries and next concrete step

- Scope only newly created **permanent** normal youth, with an explicit distinction between initial squad-fill and seasonal intake. Leave existing/imported players, virtual replacements, donor/preset creation and staff untouched until separately supported.
- A PA probability policy belongs before the initial CA choice, or must deliberately select a coherent pair before generating attributes. Factory call88236C entersCB1840 with ECX=PLAYER; its stack arguments must be preserved. The subsequent PA call is882375. Do not install a global CB1350/C80440 hook that also changes loading existing profiles.
- Candidate attribute correction point882523 is after finalization and initial training. ESI still points to PLAYER there, before instructions convert it to the PERSON subobject used for the factory return. This is a static candidate, **not a validated hook ABI or installed patch**. Donor/preset eligibility and context need checks.
- First runtime candidate should default to **diagnostic observation only**, recording before/after generation and a subsequent native update on a separate test career. Only then test a bounded correction. Preserve register/FPU state, thread/reentrancy and exact byte/version guards. This work did not open a runtime session.
- Prefer configurable probabilities to mandatory global quotas initially. A quota needs saved counting state, population scope, a stable season/career identity and handling of unloaded leagues, reloads and creation order. Percentages or quotas have not been chosen.
- Remaining uncertainty: full native iterator differential validation, exact mode/date/field labels, once-only creation identity across load/save, and possible remote world-maintenance effects outside the inspected paths. No broad claim that every possible PA population limitation has been ruled out.

Executable experiment: `../newgen_followup_20261116.py`; it creates only a new report directory and refuses to overwrite an existing one. It never patches a process or database.
