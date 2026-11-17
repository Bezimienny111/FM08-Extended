# Team-talk reactions: stored effects and safe presentation
## R16 substitution fix, 16 November 2026

User acceptance update: the requested substitution test now passes in the actual game. The user confirmed that reactions remain visible after substituting and resuming play. Evidence `R16_UI_ACCEPTANCE_SUBSTITUTION.json` records the tested DLL hash. This supersedes the earlier pending substitution status below; it does not establish every half/skin/language combination or cold mid-half reconstruction.

R16 fixes loss of reaction display after substitutions by retaining an execution receipt for the exact previously proven talk. Every frame still uses fresh coherent history and live native checks. A retired phase255 queued event is accepted only with the earlier receipt, matching timestamp, process generation, current owner/match/talk/half/counter, monotonic time and unchanged UID/action/context/effect entries. Phase255 alone never establishes completion. Context/read failures or phase changes invalidate the receipt. A torn snapshot never yields a frame; only a narrow same-talk, monotonic, two-snapshot case retains the prior completion fact for the next coherent read.

Drive captions follow the native executor precedence: fire-up, otherwise motivate, otherwise demotivate. Raw effects remain unchanged. Therefore motive+demotive+admired is shown as motivation+admired, while fire-up+pressure remains mixed.

42 focused checks and22 earlier diagnostic/frozen checks pass. The native UI payload, four installed skin panels and INI/JSON configuration are unchanged from R15. Actual substitution rendering in game remains **PENDING**. See `Launcher_0.1.3_R16/R16_BUILD_RECEIPT.json`.

Limitation: loading an already retired phase255 talk mid-half without observing its earlier completion does not reconstruct an execution receipt. The feature waits for the next normally confirmed talk. This preserves completion and reload guards.

Earlier R15 defect/status paragraphs below are historical.

## R15 UI candidate, 16 November 2026

Known defect found after initial acceptance: a user substitution in H1 leaves all11 reaction history entries intact, but the matching queued talk payload has phase255. R15 requires an equal event/history phase, loses the event timestamp and clears the UI packet. This is a confirmed admission defect; no fix has been applied. The exact phase255 writer is not attributed. Accepting255 globally would weaken admission and is not authorized by this observation alone. See `VALIDATION_H1_AFTER_SUBSTITUTION_R15.json`.

Latest acceptance: the user also confirmed that old H1 reactions disappear before approving the halftime talk and become available again after the approved halftime talk and H2 start. Both agreed talk periods are now confirmed in the rendered game panel. Evidence: `R15_UI_ACCEPTANCE_HALFTIME.json`. Fulltime and save-reload rendering and every skin/language combination remain unconfirmed separately; earlier pending statements are historical.

Update: the user has now confirmed that the R15 column and reactions work in the actual game after the requested prematch/H1 test. Status **PASS_USER_CONFIRMED_H1_COLUMN**; evidence `R15_UI_ACCEPTANCE_H1.json`. The pending statements below describe the earlier installation checkpoint. Halftime transition, fulltime and reload behaviour of the rendered UI have not yet been separately confirmed.

The new dev launcher `Launcher_0.1.3_R15` now installs an optional reaction column after the player name on Match > Player Ratings, in all four supported Ext skins. It displays computed reactions for the local human manager's team after the prematch or ordinary halftime talk is executed and locked. Opponents and invalid, stale or unavailable contexts show a dash. Postmatch reactions remain excluded. Mixed effects are listed separately; the tooltip retains the full caption. Polish FM language selects Polish captions; other game languages use English.

The bounded reader, session invalidation and live-state evidence below remain the basis for admission. The UI getter independently validates current ownership, match, talk phase/counter and the player's actual effect against the launcher's cached frame. Four column-specific hooks leave other columns on their original paths. Only launcher-owned caption data is published; talk results and saves are not edited.

Validation: 36 managed integration checks, an original R14 strict JSON compatibility check and 25 native payload checks in an owned suspended fixture passed. The four XML overrides were installed with backup and readback. **Actual game rendering and user UI acceptance remain pending.** Fixture checks do not establish live UI acceptance. See `TEAM_TALK_IMPLEMENTATION_20261116/R15_UI_CHECKPOINT.txt` and the R15 build/install receipt.

The optional setting `Features.TeamTalkReactionsEnabled` is INI schema1 only, defaults false and is deliberately omitted from the JSON mirror so older strict R14 readers can still load that mirror. Unknown INI keys/comments and the29 rule codes are preserved.

The installer never deletes files. Rollback of a newly-created override restores its inherited baseline XML into that file. Original skins and Noche are unchanged.

Earlier implementation-status paragraphs below are historical; this section supersedes statements that no column implementation exists. User acceptance is still required.


## Refresh policy and observed reload —16 November2026

The private TeamTalkReactionSession now clears old rows before every read and
on invalid/failed/cancelled observations. Revision checks reject late results
from an older refresh.22fake/frozen checks pass, including populated-frame
clearing and all four real frozen match states. A120s same-process reload
recording observed109bounded reads and loading/ordinary-screen transitions,
with no retained reaction rows. That recording began after fulltime, so it does
not prove a live nonempty-to-load transition; this part is tested offline.
The policy is not yet bound to an installed in-game panel. No unique save
revision or load hook is claimed. [Full reload scope and evidence](../FmLauncher/data/research/TEAM_TALK_IMPLEMENTATION_20261116/RELOAD_ACCEPTANCE.md).

## Implementation resumed —16 November2026

The one-shot diagnostic entry to the existing bounded provider/backend is now
compiled. A first rejected read exposed an invalid TEAM vtable in the old C#
port and its fixture. It is corrected from015AA00C to015A9E0C, checked against
original RTTI;17class checks and10focused fake-memory checks pass.
The subsequent H1 live capture passes the bounded admission conditions: two
equal own HUMAN/MATCH snapshots, both completion-fence bytes1, current standard
talk, matching event7 and later tick.234reads/2738bytes,11player entries.
An additional ordinary-halftime capture BEFORE approval passes stale-H1
invalidation: phase1/stored0/counter1, old rows present but Relevantfalse and
CompletionCandidatefalse, even with fence1. Same match/owner,234reads/2738bytes.
H2 admission now also passes: phase1/stored1/counter2, new talk/event19522,
tick21269, both fence1,246reads/2770bytes,11new entries. Fulltime before any
postmatch approval correctly rejects the old H2 talk: phase5/stored1/counter2,
Relevantfalse/CompletionCandidatefalse. No postmatch-talk evaluation.
Continuous-refresh/reload and game UI acceptance remain pending. The user was
released from the match; no more pauses are currently required.
See [four-state runtime acceptance](../FmLauncher/data/research/TEAM_TALK_IMPLEMENTATION_20261116/RUNTIME_ACCEPTANCE.md).
Stable R14/skins are unchanged; publication remains disabled. Use the
[current checkpoint](../FmLauncher/data/research/TEAM_TALK_IMPLEMENTATION_20261116/CHECKPOINT.md)
for the executable command and admission criteria. Do not launch the old private
launcher GUI for this diagnostic. This entry does not provide an in-game column.

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
