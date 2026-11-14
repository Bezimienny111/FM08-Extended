# New players, CA/PA and attribute budgets

## Three distinct systems

1. The game's own permanent-player generation and population maintenance.
2. Temporary VIRTUAL_PLAYER representations and their materialization.
3. Our offline imported-profile estimate model and optional dynamic-PA launcher extension.

An importer JSON policy does not control native youth intake. Changing an existing player's PA does not directly dictate his replacement's potential.

## Permanent-player creation

The traced startup path is46AE00 ->882570 ->881BC0; the seasonal path isD6A7C0 ->883770 ->881BC0. The common factory allocates a new full player, obtains a new UID, generates age/identity/ability and inserts the person. The constructor/finalizer chain includes CB9FF0, CB1B90, CB1840, CB1350 and CB3000.

Startup counts under19 players and position categories. Sixteen is an entry gate in a branch, not a universal target squad size. Eight category targets remain unresolved runtime globals. Seasonal generation depends on country population/baseline counters, clubs and context; there is no verified one-date youth intake for all countries. [NEWGEN](SOURCES.md#newgen)

Club-quality reads use first-TEAM reputation and CLUB+E1/E0. Numerical dependencies are static evidence; mapping every field to an editor control and safe DAT writer is a separate task. No direct balance/budget read was established on the closed CA/PA path. There is no proven global rule that a retiring star returns as the same person or with identical potential.

## Virtual players

The separate match-fill path passes through870560,90B7C0,90B010 and90AD10. VIRTUAL_PLAYER is a76-byte class. Materialization uses a rotating pool of200 full objects, context/seed-driven attributes and sometimes a donor template. The pool size is not a world-population limit.

A contract path through90D570 can turn a pooled representation into an independently registered person. Not every virtual player was proved to be a grey emergency player; UI colour, lifetime and every conversion case remain unverified. Empty confirmed squads can be left to the engine, but the research does not guarantee a particular generated count, CA or PA for every club.

## Native PA categories

C80440 expands negative categories. For sufficiently low CA, the upper endpoint is excluded:

| Category | Basic interval |
|---|---|
|-10|[170,200)|
|-9|[150,180)|
|-8|[130,160)|
|-7|[110,140)|
|-6|[90,120)|
|-5|[70,100)|
|-4|[50,80)|
|-3|[30,60)|
|-2|[10,40)|
|-1|[1,20)|

The lower endpoint may be raised by valid CA; the interval helper sorts its endpoints, so unusual input requires final normalization. For-10, a first result>=190 triggers exactly one reroll, not reroll-until-below190. With CA<=170, the conditional chance of190..199 is1/9. That is not the probability of an elite player across all youth intakes.

CB3000 eventually enforces PA>=CA and1..200; some mode-dependent2x/3xCA limits have unresolved option labels. PA is not a resource spent as CA rises.

## CA is not the sum of visible attributes

CA and PA are signed16 at PLAYER+0x14/+0x16. The runtime80-element attribute array is behind *(PLAYER+0xCC), starting at data+0x1C. Positions/sides0..24 use the position scale; later attributes use internal1..100. This is not the89-byte DAT record or the47-entry UI enum.

Visible scaled attributes use `clamp(trunc((clamp(raw,0,100)+2)*float32(0.2)),1,20)`. A raw+1 is usually invisible. A raw+5 has lower-bound exceptions; setting a visible target can discard the original rounding remainder.

**Erratum:** AD2630 only scales generation values25..79 by5. It does not normalize to CA, despite the earlier new-generation report. The actual later normalizer is A7A860. [ABILITY](SOURCES.md#ability)

## Position-dependent weighting

D23AE0 mixes15 positional rows across80 attributes. In the recovered static equations:

```text
t_r = max(position_familiarity_r - 10, 0)
w_j = sum(t_r * B_rj) / max(10, sum(t_r))
v_j = w_j*(w_j+1)/2 if w_j>1, else 0
u_j = w_j*w_j if w_j>1, else 0
```

Mix base weights before transforming them. Several familiar positions can contribute. A single natural position20 is not the universal whole model. The complete numerical15x80 base table B and its full initializer were not recovered; Genie Scout weights are not a replacement.

D23F00's standard weighted mean is `sum(v*x)/sum(v)`. The normalizer target is mathematically `T=30+clamp(CA,1,200)/4`. The recovered correction also uses:

```text
W = sum(v); n = count(nonzero v)
h = 3.75*W/n
q_j = 0.2*v_j*(x_j-T)
soft(q,h) = max(q-h,0)+min(q+h,0)
Q = [sum(v*x)+3.75*sum(soft(q_j,h))]/W
```

Preserving the simple weighted sum does not preserve Q. Rounding, clamps, a maximum1000 iterations, oscillation handling and selected half-steps mean the iterator need not finish exactly atQ=T. This is recovered static arithmetic, not a complete validated emulator.

Personality is a different payload. Lowering Professionalism does not pay for higher Finishing; it changes development behaviour. Hidden attributes are not automatically cost-free. Feet and additional positions can change weights and should initially stay fixed in a bonus experiment.

## Proposed randomized role bonuses

The user proposed Genie role importance as a choice of attributes to favour, random+1/+2 adjustments and compensating reductions. This is a design, not an installed generator patch. A safe design would:

- apply only once to a proved newly created full player;
- use an independent stable random seed and varied eligibility, avoiding identical profiles;
- preserve CA/PA, feet and positions;
- check raw units, native weighted/nonlinear balance and the subsequent normalizer;
- reject proposals with no acceptable integer compensation.

Candidate882523 lies after initial training in the traced factory. Hooking every setter or common finalizer would also affect existing players or repeat bonuses. The original goalkeeper-only Positioning/Jumping proposal was feasibility work; it has no accepted gameplay patch.

## Imported estimates and dynamic PA

Our offline v2 model adds stable individual CA spread and age-sensitive development margins only for justified estimates; credible native/EA profiles and prior talent awards are protected. Country/real-level calibration is a project policy, not an engine formula. X23 includes479 documented legacy estimate repairs and10 talent awards.

The optional dynamic-PA launcher has its own gate: valid CA/PA, PA<200 and remaining gap0..4; successful eligible training-epoch rolls increase PA by1. Current mentality weights are Professionalism60%, Ambition25%, Determination15%; age multipliers vary. The code uses its own xorshift/rejection sampling rather than consuming the match RNG. This extension is separate from native generation and normal training. [PA-POLICY](SOURCES.md#pa-policy), [PA-PATCH](SOURCES.md#pa-patch)
