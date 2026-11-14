# Evidence, executable identity and engine architecture

## What the research corpus contains

The retained Ghidra R5 project and exports belong to the hash-pinned FM08 executable identified in the [index](README.md). The base export reports 91,403 recognized functions and 91,120 C files; three supplemental entry points brought the corresponding totals to 91,406 and 91,123. These are analysis/export counts. They do not mean that every function boundary, prototype or semantic interpretation is correct, or that we possess recompilable engine source. [R5](SOURCES.md#r5)

The executable is a native 32-bit program with MSVC-style RTTI, multiple and virtual inheritance. A complete object, a secondary interface pointer, PERSON, PLAYER, CLIENT proxy and serialized record are different bases. An offset without a named base and version is incomplete evidence.

The dynamic PA crash demonstrated this directly. A normal PLAYER reaches PERSON at +0xEC; the combined player/non-player variant reaches it at +0x124. Applying the normal player's name offsets to the combined variant treated 0x10 as a pointer. The fix follows the native virtual-base conversion, then reads identity/name fields relative to the corrected PERSON. [ARCH](SOURCES.md#arch)

## Stable identities and temporary locations

Use typed identity, not a remembered address:

| Value | Scope |
|---|---|
| Person UID | Persistent person identity |
| PERSON index | Index in this source's person table |
| TEAM index / UID | Team identity and table reference |
| CLUB/FAMILY index / UID | Shared club container, contracts and membership |
| Name-table index / UID | Separate dictionary reference and identity |
| COMP index / UID | Competition table position and identity |
| Runtime pointer | Current allocation in one process/world generation |

Do not add or subtract one to derive a person UID from an attribute index. The old `pid+1` shortcut is superseded by typed PERSON/footer linkage. Do not infer a contract family from a UI name-family index.

Native competition replacement/merging can destroy an allocation and install another object with the same UID. Poland R9.2 failed when its guard expected the original address. Loaders and UI rebuilds likewise invalidate previously observed pointers. [POLAND](SOURCES.md#poland)

## Hierarchy of evidence

1. Exact byte identity, instruction boundaries, calling convention and typed record boundaries.
2. Controlled SI samples changing one field, independently decoded.
3. Native output reloaded from disk; unaffected bytes and complete inverse checked.
4. Bounded runtime observations with process creation time, EXE hash, object types and identities.
5. User-visible behaviour in a stated career, phase, date and build.
6. Separate save/load and season-transition acceptance.

A reader/writer round-trip can preserve an incorrectly named field. The eight distinct Del Piero personality values exposed a shared reader/writer mistake that round-tripping alone had hidden. Conversely, a successful synthetic UI fixture did not prove that real cells had the same class or viewer context.

## Decompiler and disassembly limitations

- Verify argument counts in assembly: the new-player factory at 0x00881BC0 uses `ret 0x1C`, despite incomplete exported prototypes.
- A nearest preceding Ghidra function label is not proof of method ownership. The rule-map audit corrected four league labels using RTTI, vtable slot 88 and constructor UID arguments.
- BSS globals do not have initialized values to read from the PE file. Missing youth targets and CA weight tables remain unknown.
- A list of stack return-looking addresses is not an unwound call stack. Crash diagnoses distinguish validated exception records/call instructions from candidates.
- Preserve registers, flags, calling convention, stack cleanup and FP/SIMD state in hooks. Check all incoming branches to overwritten bytes, not only the nominal entry.
- `Installed` proves a jump/payload readback. It does not prove the feature's semantics in every match.

## Research practice

Existing projects, exports, immutable samples and raw provider responses should be reused. Run a new experiment to resolve a concrete gap, not to recreate an already settled identity. Reading reactions must not call executors or RNG. A read-only handle does not make an observation atomic: take bounded coherent snapshots and reject stale/ambiguous context.

The documentation update itself does not install hooks, modify the executable, migrate saves or authorize new gameplay experiments.
