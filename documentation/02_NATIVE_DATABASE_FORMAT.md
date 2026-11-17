# Native database formats and identity contracts

## Containers and versioning

FM08 DAT samples use a nine-byte SI header and version 0x0477. Ordinary main tables are in zlib-compressed payloads following that header. OpenFM2007's 0x0430 schemas operate on decompressed streams and cannot simply open the FM08 compressed file as equivalent input.

`lang_db.dat` is different: byte 9 is the language count; the index beginning at byte 10 contains language-ID/relative-offset pairs. Each language is its own complete zlib stream, starting at `9 + relativeOffset`. The examined profiles have 20 languages; English is 8, Polish 18. Changing lengths requires rebuilding each affected stream and the archive index. Preserve unparsed trailing data. [FM07-COMPARE](SOURCES.md#fm07-compare), [NAMES](SOURCES.md#names)

Names use length-prefixed UTF-16LE, with lengths in UTF-16 code units and schema-dependent separators/terminators. Do not transplant one object's string schema into another. COMP full name, short name and abbreviation are separate fields; changing a full English name does not update other languages or short names.

## PERSON, attributes and names

PERSON records have variable prefixes, optional sections and contracts. A generated free-player fixture is 234 bytes, and its contracted counterpart is 299 bytes; historical records can be much larger. These fixture sizes are not a universal parser.

Player attribute records are 89 bytes: 81 bytes of payload plus table index and UID. Personality records are 17 bytes: structural byte, eight values, index at +9 and UID at +13. Staff attributes use a distinct 49-byte format. None of these table identities can be substituted for the person's UID.

Names involve shared first/surname/known-as tables and reference counts. Reusing a surname requires updating its count in SERVER and CLIENT. Some historical persons legitimately use a missing first/surname reference with a known-as name; an audit reader's guessed fallback text is not the physical identity. Preserve those names unless independently resolved.

### Verified personality order

The SI control TEST_X12, Del Piero UID8074, sets eight different values:

| Byte within 17-byte record | Attribute | Control |
|---|---|---:|
| +1 | Adaptability | 2 |
| +2 | Ambition | 4 |
| +3 | Loyalty | 6 |
| +4 | Pressure | 8 |
| +5 | Professionalism | 10 |
| +6 | Sportsmanship | 12 |
| +7 | Temperament | 14 |
| +8 | Controversy | 16 |

The old codec put Controversy at +3 and shifted the next five traits. The corrected codec was applied to the main source and used for later builds. This does not retroactively repair every existing profile; that requires a separate proven inventory. [PERSONALITY](SOURCES.md#personality)

## Attribute-offset erratum and export

The old compendium section3.2 labels an89-byte window with identity at0..7 and GK at9. Do not use that historical reader-window table as offsets from a typed serialized record. Current native-creation/readback evidence places GK at1, Crossing26, Concentration80, index81 and UID85. This is also why a raw attribute index cannot produce a person UID by+1.

[verified-DAT-attribute-offsets.csv](verified-DAT-attribute-offsets.csv) exports the fields actually asserted by the current independent disk checker. It deliberately does not assign names to every remaining byte. [runtime-attribute-index.csv](runtime-attribute-index.csv) separately lists51 proven runtime parser names. The numerical native CA table was subsequently captured on15November2026; see [the ability continuation](05_PLAYER_GENERATION_AND_ABILITY.md#numerical-weights-and-highlighting-continuation15november2026). That does not supply missing DAT field mappings. Do not subtract a guessed header to convert one numbering system to the other. [NATIVE-BUILDER](SOURCES.md#native-builder), [ABILITY](SOURCES.md#ability)

## Club assignment and contracts

A player's ownership, the owner's roster, the contract block and its FAMILY reference must agree. The borrower of a loan is separate. TEAM and FAMILY indices can differ, especially for reserve teams sharing their parent's contracts.

Controlled contract samples corrected the interpretation of `payload+31`: it is a FAMILY/name-tree reference, not a generic status flag. `payload+26` links the person index; the supported contract wage field is +35. Fixed offsets into a complete historical PERSON are unsafe. Contract creation/removal changes record lengths and shifts following data.

A data-editor save can renumber names, reorder sections and reserialize large buffers. Never mix SERVER from one save with PEOPLE from another by assuming their references are still aligned. The present imports use fresh typed family boundaries, owner proofs and full inverse verification.

## Loan records

The controlled Buffon samples established a 32-byte LOAN record:

| Offset | Meaning |
|---|---|
| +0 | Structural byte |
| +1 | PERSON index |
| +5 | Borrowing TEAM/club table reference in the verified profile |
| +9/+11 | Zero-based day-of-year / start year |
| +13/+15 | Zero-based day-of-year / end year |
| +17 | Raw options; recall bit 0x04 verified |
| +18 | Loan shirt number; 255 means unspecified |
| +19 | Signed Fee To Buy; -1 disables the option |
| +23 | Wage contribution; 0,50,75 verified; 255 is an unresolved sentinel |
| +24 | Loan-table index |
| +28 | Entry UID; old records may contain -1, SI-created records can have a unique positive UID |

The old reader incorrectly required -1 in every footer. It now supports the observed positive UIDs without relaxing date, index, uniqueness or ambiguity checks. The samples preserve the owner contract and owner roster; loan membership is represented separately. Dates must be validated across leap years. [LOANS](SOURCES.md#loans)

Optional buy fees require a confirmed currency conversion. Unknown is not zero. Mandatory purchase obligations are deliberately excluded: the project does not invent an unsupported FM08 equivalent.

## Clubs, teams, stadiums and cities

A CLUB/FAMILY owns a collection of TEAM records and shared club data. TEAM carries its sporting assignment and stadium; STADIUM links to CITY. The club-city getter follows the first TEAM's stadium, which explains the absence of a simple club-city edit field.

New entities require consistent identities in SERVER, CLIENT and language streams. Parent membership, native team kind, sporting country and contract family need separate validation. A Welsh club playing in England does not automatically require changing its native sporting affiliation.

New-club embedded full/short names must be populated alongside EN/PL names. An unresolved localization lookup can otherwise leave a blank name even when the language entries exist. Preserve typed family order and proven lookups; the three-club repair did not justify a global UID sort. [CLUBS](SOURCES.md#clubs), [BLANK-NAMES](SOURCES.md#blank-names)

Cross-version findings: CLIENT STADIUM19B round-tripped unchanged with FM07; SERVER STADIUM is 62B in FM08 versus 53B consumed by the FM07 schema. CITY needs an extra int32 before its identity footer. CLIENT CLUB requires four extra uninterpreted bytes per kit. The first 12 language tables match the reference, but FM08 retains a further unparsed language tail.

## Retirement and historical cleanup

Retirement is a separate SERVER table of 18-byte entries with person UID, zero-based day/year, an activity byte, ordinal and preserved extra fields. The section flag and per-entry activity flag are different. A scheduled future retirement is not a day-zero release from a club.

A controlled SI retirement of Buffon on 30 September 2007 was observed by the user. The original interpretation that a retirement date universally and immediately clears a squad is false. Updating all project-scheduled dates later is technically a bounded data operation, but its target UID set and all affected records must be enumerated first. It does not rewrite existing careers.

Historical R6025 experiments, unsupported layouts and unresolved extra retirement fields remain in the bug register; successful modern imports do not retrospectively prove each old experiment.

## Non-negotiable validation

Resolve source identity and references before writing; check all planned UID collisions across relevant tables; write a new output; read it independently; prove the complete inverse and preservation of unrelated data. New source values do not require rebuilding an unchanged main editor. A validated CSV or policy JSON is not itself a universal importer.
