# FM08 Extended: engine research documentation

English knowledge base, consolidated on 14 November 2026. Thirteen topic chapters,46 registered issues/corrections and81 pinned source files;194 source/report inventory rows. This folder covers the research recorded in this workspace: FM08 engine behaviour, native database formats, launcher integrations, failures and corrections, and the pinned OpenFM2007 reference.

Start with the topic matching your task. Each chapter links its evidence through [SOURCES.md](SOURCES.md). The source manifest preserves paths and SHA256 values; the research inventory also lists historical material that has not been promoted to a current conclusion. This is a synthesis of existing evidence, not a fresh execution of every historical experiment or a reconstruction of all engine functions.

## Chapters

| Chapter | Contents |
|---|---|
| [01. Evidence and architecture](01_EVIDENCE_AND_ENGINE_ARCHITECTURE.md) | Executable identity, object bases, virtual inheritance, proof levels |
| [02. Native database](02_NATIVE_DATABASE_FORMAT.md) | DAT, names, identities, PERSON, contracts, loans, retirement, clubs/stadiums |
| [03. Competitions and seasons](03_COMPETITIONS_AND_SEASONS.md) | Selection versus scheduling, loader changes, country cases, classic/extended variants |
| [04. Match rules](04_MATCH_RULES_AND_RULES_SCREEN.md) | All 29 codes, actual overrides, Rules display, substitution windows |
| [05. New players and ability](05_PLAYER_GENERATION_AND_ABILITY.md) | Permanent/virtual players, PA categories, CA normalization and proposed bonuses |
| [06. Training, aging and staff](06_TRAINING_AGING_AND_STAFF.md) | Fatigue, development, age thresholds, coach/assistant hiring |
| [07. Team talks](07_TEAM_TALK_REACTIONS.md) | Stored reactions, effects, conditions, live-reader/UI limitations |
| [08. Panels and graphics](08_PLAYER_PANELS_SKINS_AND_GRAPHICS.md) | Hidden attributes, role highlighting, language, skin inheritance and asset identity |
| [09. Finance and reputation](09_FINANCES_REPUTATION_SPONSORS.md) | Separate financial quantities, sponsors, Sugar Daddy, UEFA and reputation |
| [10. Persistence](10_SAVE_LOAD_AND_COMPATIBILITY.md) | Career identity, save revisions, companion proposal, existing-save migration |
| [11. OpenFM2007](11_OPENFM2007_CAPABILITIES_AND_PORTING.md) | Implemented reference capabilities, gaps, FM08 port requirements |
| [12. Bugs and errata](12_BUG_REGISTER_AND_ERRATA.md) | Engine preconditions, bad data, our code defects, upstream issues, corrected claims |
| [13. Open work](13_RESEARCH_BACKLOG.md) | What remains unknown, agreed scope and useful next experiments |

Additional indexes: [sources](SOURCES.md), [research inventory](RESEARCH_INVENTORY.csv), [machine-readable bugs](bug-register.json), [native substitution codes](substitution-codes.csv), [runtime attribute names](runtime-attribute-index.csv), [verified DAT offsets](verified-DAT-attribute-offsets.csv).

## Current boundaries

- FM08 research primarily targets 8.0.2f117931, EXE SHA256 `157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d`. Additional launcher-supported executables require their own verified profiles; addresses below are not universal.
- OpenFM2007 means the local reference commit `8395779d64019385153ce2cf451a6621db6db393`. No claim is made about newer upstream revisions.
- TEST_X22: the user reports a successful simulation through 2011 on 14 November. This supersedes the old pending long-test notes. It is not a test of TEST_X23 or every optional launcher feature.
- TEST_X23: England package native write/readback, inverse, 621 selection checks and ZIP verification PASS. SI save and new-career creation are now user-confirmed; season acceptance remains pending.
- Latest verified launcher package: `Launcher_0.1.3_R12`. Player panels R10 and Rules display R12 have scoped user acceptance. Team-talk display is still a private diagnostic project.
- Graphics: 24,095 target PNGs prepared, including 214 new England faces; installation remains blocked while FM is open.

## How to use this knowledge

`STATIC` means the code path was traced, not played. `RUNTIME` means a particular state was observed. `NATIVE` means output files passed technical checks. `SI`, `NEW_CAREER` and `SEASON` are independent acceptance dimensions. `DESIGN` and `UNKNOWN` are not implemented features.

A later correction overrides an older assertion only within the stated scope. Keep the old report for provenance. In particular, read the CA normalizer correction, the personality-order correction, and the save-completion warning before reusing old notes.
