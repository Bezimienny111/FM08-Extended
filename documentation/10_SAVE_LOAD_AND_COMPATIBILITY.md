# Save/load, companion files and compatibility
## Launcher settings, R17 update (16 November 2026)

R17 removes manual Save/Reload from the footer. PLAY persists validated settings before starting FM; closing persists only changed valid settings. Changes to optional INI-only fields count even if excluded from JSON. An unchanged close does not create another backup. A failed read never overwrites the original with defaults; Settings provides a recovery reread only in that state. A failed write is reported and closure is cancelled so edits remain available.

The existing INI schema1,29rule numbers, unknown section/key/comment preservation and compatible JSON mirror remain mandatory. The optional team-talk flag stays INI-only for strict earlier JSON readers. Unsupported newer schemas are preserved. R17 passed20 focused UI/configuration checks, including actual FormClosing and a fake PLAY start callback; no FM was started for these checks. This concerns launcher settings, not FM save transactions described below.


## A database folder is not an existing career

DAT updates affect a newly created world. An existing save already has teams, stages, fixtures, contracts and histories. Changing its source folder does not migrate that world or repair a generated invalid playoff stage.

Memory hooks vanish with the process, but some resulting data can persist when FM saves: earned PA and changed reputations are examples. Turning a feature off is not a rollback. Rule changes may affect newly built fixtures and leave existing caches untouched.

## Existing career identity

CareerIdentity reads a bounded structure at0x01911160 and verifies markers/build. Its token is constrained to fewer than10 million possibilities. A user test retained the token after Save As and restart; another career had a different token.

This is a useful career identity component, not a unique save-file revision. Copies/branches can share the token, and collisions are possible. Path, filename, PID and modification time alone are insufficient as a transactional binding. [CAREER](SOURCES.md#career), [COMPANION](SOURCES.md#companion)

## Existing lifecycle hooks and the important correction

The recorded loader entry is465210, with a normal return at466978. A loader entry invalidates old maps and a return result helps track generations, but preliminary/header reads and incomplete world setup still need distinction.

The existing hook labelled SaveCompleted at467F23 is not proved to mean durable archive completion. The exported4669A0 procedure reaches a common success-looking epilogue during intermediate phases and even a refusal path. Therefore the name is stronger than the evidence. Do not commit a companion just because this hook fired.

A custom unrelated member added to a controlled FM archive could be read, then disappeared on native resave. Simply inserting our JSON into the archive is not an accepted persistence mechanism.

## Proposed companion contract

The user proposed a separate file for additional UEFA state. This remains a design. It should include a schema/mod version, rules version, career identity, source/save-revision binding, season identity and integrity information.

The state must cover at least:
- current-season coefficient points and already-awarded bonuses;
- access-list inputs, fixed round sizes and titleholder/vacancy decisions;
- unresolved winner/loser-of-tie bindings and stage identities;
- bracket routes, draw decisions, dates and one-time prizes;
- lifecycle/reset information sufficient to rebuild UID-based maps.

Do not serialize raw pointers as durable identifiers. Reset global state before loading another world, then rebuild against verified UID/type objects when the world is ready.

The write protocol needs a snapshot aligned to the actual game serialization, temporary file creation/flush, a proved final save outcome, and final matching to the particular completed FM save. A standalone atomic JSON rename does not create a transaction with FM's archive. Failed/cancelled saves, autosave rotation and Save As require explicit handling.

On load, an exact compatible companion may restore state; reconstructible state may be rebuilt only from sufficient native evidence. Missing/ambiguous state must not silently invent coefficients or replay prizes. A companion cannot correct a wrong qualification algorithm by itself.

## Updating during an existing European campaign

Default new formats to new careers. A running old tournament already has a stage layout, entrant lists, draw bindings and results. Installing a new host midway can leave incompatible shapes or attach new logic to old data.

A separately approved migration would need a verified season boundary, no conflicting active stages, compatible histories and rules versions, a full mapping of affected competitions, and rollback to the untouched save if validation fails. Mid-tie conversion is not automatically supported.

A sane future test matrix includes two careers in the same process, two seasons each, save before/after draws, unresolved ties, points/prizes, rollover, failed writes, Save As and reload without the companion. These requirements arise from observed reference lifecycle gaps, not from hypothetical certainty that every save is broken.

## Current project status

The native save and data import paths are useful foundations. The complete UEFA companion transaction and old-career migration are not implemented. The private team-talk provider also still needs same-process reload/session invalidation before a continuous display.

TEST_X22 has user acceptance through2011. TEST_X23 now has separately confirmed SI save and new-career creation; its season test remains pending. X24 retirement cleanup is separately requested and must use a fresh protected X23-after-SI copy. None of those statuses proves a new companion mechanism.
