# Team-talk reactions: stored effects and safe presentation

## Scope and current implementation

The agreed feature covers the prematch team talk and ordinary halftime talk. Postmatch feedback is excluded. We want to display each player's reaction after execution and after that standard talk can no longer be edited for the current half.

The engine stores reactions and the project has frozen live H1/H2 observations, an offline decoder/model and a bounded private provider. There is no accepted continuous in-game reaction column. The private TEAMTALK_DEV launcher uses offline diagnostics; merely opening it does not run a live capture. [TALK-STATIC](SOURCES.md#talk-static), [TALK-LIVE](SOURCES.md#talk-live), [TALK-TEST](SOURCES.md#talk-test)

## What an entry stores

PLAYER_TEAM_TALK_ENTRY has runtime UID at+08,64-bit action at+10,64-bit effect at+18,64-bit match context at+20,16-bit position at+28 and byte index at+2A. These are offsets from that entry's base, not PERSON or DAT offsets.

The manager embeds TEAM_TALK_HISTORY at+AF4; TEAM_TALK embeds its entry array at+08. They are not pointer fields to dereference blindly. Old M+0C and TEAM_TALK+2C labels have been corrected to raw_identity rather than an unproved UID.

## Effect flags

| Mask | Recorded meaning | Mask | Recorded meaning |
|---|---|---|---|
|0x1|Motivate|0x2|Fire up|
|0x4|Morale boost|0x8|Morale drop|
|0x10|Demotivate|0x20|Relieve pressure|
|0x40|Pressurize|0x80|Lower professionalism/focus|
|0x100|Boost professionalism/focus|0x200|Happy|
|0x400|Unhappy|0x800|Anger|
|0x1000|Victimised|0x2000|Admired|
|0x4000|Jealous of teammate|0x8000|Confused|
|0x10000|Ignore|||

Effects can coexist, and unknown high bits must be retained. Professionalism/focus reaction names do not prove a permanent edit of the player's hidden personality.

The executor prioritizes fire-up, then motivate, then the negative0x5010 branch. Morale prioritizes positive0x2004 over negative0x5008. RNG and clamping can give no net numeric change despite a flag. Do not sum flags into one intuitive good/bad score.

## Concrete conditional findings

There is no universal percentage per menu option. Conditions include score, a manager expectation threshold, previous talks, morale, participation, current match state and mental helper results that can themselves draw randomness. Some helper-to-editor-attribute mappings remain unknown.

| Action | Traced local behaviour, subject to shared overrides |
|---|---|
|Encourage, mask4|Can motivate/relieve pressure, but can also yield admired+demotivate|
|Warn against complacency,64|Context can justify a warning; an unjustified local branch sets confusion, lower focus and demotivation|
|Sympathise,8|A supportive branch requires not leading and losing or a performance test; the opposite branch is negative|
|Wish luck,128|Can help, do nothing net, or yield mixed/negative effects|
|No pressure, team8192 / individual8388608|Can relieve pressure or demotivate|
|For the fans,1024|A local goal-difference>=3 branch can produce confusion|

Full conditions and separate RNG calls are preserved in the source conditions.json; several other speeches and the shared override remain only partly decoded. [TALK-RULES](SOURCES.md#talk-rules)

## Observed real match

One recorded11-player prematch Encourage talk produced5 zero masks,1 motivate,4 masks0x2010 and1 mask0x2011. Ordinary halftime before approval still exposed the old H1 slot; after H2 began, the new Warn talk produced3 zeros,5 masks0x100 and3 motivate.

This demonstrates individual variation, not a population probability table. In0x2010, admiration and demotivation coexist;0x2011 adds motivation, which wins its local branch. The native formatter without later context renders both as Looked delighted. A single motivate flag may still render Nothing specific noted. Neither text predicts a later performance.

## Completion, ownership and invalidation

Counter advancement occurs before copying/mutating all results. Two equal reads filter inconsistency but do not prove executor completion. A queue entry's disappearance is not an established completion signal.

The private bounded observation permits at most768 reads/32768 bytes,4096 bytes per read, with two coherent HUMAN+MATCH snapshots. The remaining candidate completion test needs MATCH+0x5F22C==1 in both, an unambiguous matching event7, timestamp<tick, the correct stored/current phase, own HUMAN/TEAM and standard locked talk state. Old captures did not read that byte; they are not retroactively completion PASS.

The accepted publication concept distinguishes:
- confirmed executed entry with zero flags;
- no entry;
- waiting for execution;
- unavailable/inconsistent read;
- mixed/other reaction.

A failed refresh, different player/team/manager/match, phase transition, halftime before the next talk, replay, fulltime, reload or network context must invalidate stale output. Postmatch is hidden. The present single-observation provider does not establish continuous same-process reload isolation.

A read-only viewer must read the already computed result. Calling the executor, mental RNG helpers or formatter paths that advance state would change the game. No fixed millisecond delay after a click can replace the missing semantic proof.
