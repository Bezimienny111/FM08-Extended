# Training, fatigue, aging and staff limits

## Training and accumulated fatigue

TRAINING_MANAGER::update_player begins at8D3D60. An older note called an interior instruction8D3DF0 the entry; that label is superseded. Weekly training and the broader monthly player update are different paths.

The recorded training categories are Strength, Aerobic, Goalkeeping, Tactics, Ball Control, Defending, Attacking, Shooting and Set Pieces. Outfield and goalkeeper paths filter different categories. Progress arrows use attribute history and differences, not a direct statement that PA increased.

Tracked inputs include workload, facilities, category coach quality, position training and contract context. Constants0.005,0.01,0.2,0.7 and a position-training0.5 factor appear in the traced code. They are components of paths, not a complete universal development-rate formula. Full-time/part-time/no-club branches must not be generalized to all possible development.

Jadedness is distinct from condition, morale and physical attributes. Its recorded clamp is-1500..1500. The traced training penalty is1.0 at<=250, about0.8 at375 and about0.6 at>=500. A getter with its update argument enabled can mutate fatigue; a display reader must not invoke it as a harmless query. [ARCH](SOURCES.md#arch), [SKIN-ARCH](SOURCES.md#skin-arch)

The workload-unhappiness message has a separate path through8CF600/8CF725. Future Training Efficiency or Max Safe Workload panels remain designs: a proposed percentage is not an exact recovered engine property, and absence of an unhappiness flag is not proof of zero injury risk.

## Monthly aging

Event0x2BC reaches85BC40. Qualified players are distributed across days1..28 by an internal identifier modulo28; aging is not simply a birthday event. A34E00 combines training, aging and other changes.

The statically recovered thresholds are:

```text
A = age from the native getter
B = 31 if goalkeeper ability >=15, otherwise29
F = max(1, NaturalFitness - max(0,A-B))
T = 28 + trunc_toward_zero((F-InjuryProneness+Professionalism)/10)
S = (F+2)/6 using integer division
```

F is temporary; this code does not subtract one from stored Natural Fitness every year. The traced decline selectors cover Acceleration, Strength, Stamina, Pace and Agility; Strength has a threshold offset+4. Do not substitute Jumping.

Some branches subtract0..1 or0..2 internal units, not necessarily visible1..20 points. CA has additional age modifiers; its final update atA3605F clamps to0..PA. Training may offset some losses. There is no single universal retirement/decline age or fixed annual CA loss in this evidence.

## Optional delayed aging and dynamic PA

The implemented default-OFF aging extension delays the physical/CA penalty thresholds by three years while preserving young-player development branches, real DOB, age display and retirement dates. Its eight-hook execution/installation tests do not establish every long-running career scenario.

One old hook layout crashed because original jumps entered the middle of overwritten instructions atA359C1 andA3563E. The fix preserves shared entry targets and tests both incoming paths. Hook entry validation alone would not have caught this. [AGING-CODE](SOURCES.md#aging-code), [ARCH](SOURCES.md#arch)

Dynamic PA is a separate optional extension, not native training. Its current eligible-week chance is:

```text
W = 60*Professionalism +25*Ambition +15*Determination
chanceBasisPoints = min(10000,
    (8*agePercent*(W+850)+950)/1900 using integer division)
```

AgePercent is125 through18,110 through21,100 through24,70 through27,40 through30,15 through33, then5. An18-year-old with20/20/20 has15% in an eligible update. Success adds1 PA, bounded at200, with gap0..4; no seasonal+5 allowance is implemented. The old PaChance configuration field is compatibility-only. Saved PA changes persist; switching the feature off does not undo them. [PA-POLICY](SOURCES.md#pa-policy), [PA-PATCH](SOURCES.md#pa-patch)

## Coach recommendations versus recruitment blocking

The common quota function88F0F0 groups general, GK, fitness, first-team and youth coaches. It excludes managers, assistants, scouts and physios from this coach total.

| First-team reputation | Recommended coach total | Ordinary new-hire refusal threshold |
|---|---:|---:|
|<2000|1|3|
|2000..3999|3|5|
|4000..5999|6|8|
|6000..7999|8|10|
|>=8000|10|12|

The hiring path adds2 to the recommendation before testing the current total. These are not five independent hard role caps. Context flags, renewals/same-job paths and exceptional cache branches still matter.

The finance+0x0C flag adds one to each of five coach categories and four physios, but not assistants/scouts. Earlier notes did not know its UI identity; later SI/finance evidence establishes the Sugar Daddy mapping. This does not quantify every financial contribution.

## Assistant manager is a different gate

The ordinary recommendation is one. C8C010 recognizes the assistant role, including its player/assistant variant. The hiring gate at8DA0E6 tests whether C62B80 finds an existing assistant, and refuses with reason0x35. Changing the displayed quota alone cannot permit a second assistant.

C62B80 visits a club's teams; its helpers can find the same assistant through several team paths. Its positive result is an occupancy test, not necessarily a count of distinct people. Do not apply the coach+2 tolerance to assistants or infer a shared quota across separate B-club objects.

These limits were statically audited; a larger assistant limit has not been implemented or accepted in gameplay.

## Native staff data and current modernization status

Staff PERSON type1, its49-byte attribute table,17-byte personality and contract relationships differ from player rosters. Ranieri samples establish an existing staff wage field at supported contract+35, release from the manager link and a separate17-byte staff-membership table. A new free-manager SI sample establishes a138-byte minimal PERSON plus personality/staff attributes; it is not a completed generic staff creator.

The coaches/assistants source report is a partial collection with unresolved IDs/seasons and no completed mass importer. Do not claim X23 contains a complete current coaching update simply because current player squads were imported. [STAFF](SOURCES.md#staff), [STAFF-COLLECTION](SOURCES.md#staff-collection)
