# Player market and renewals — paused for launcher backup, 17 November2026

No database, launcher or skin changed in this investigation. User has redirected
work to pushing a launcher backup branch. No diagnostic monitor is running.

Confirmed by read-only TEST_X37 scan:76357 registry UIDs matched typed records;
76132 had DAT reputation0/0/0;76261 recognized main contracts ended2010-06-30.
All four user screenshots show the matching2010-07-01 release wave. The shared
date explains synchronisation, not why individual AI clubs failed to renew.

Runtime VM_READ-only PID756 snapshots confirm that zeros are initialized:
Cambiaso current rep8190, Bremer8509, Marcus Thuram8380 in first snapshot.
CB1DA0 fills reputation and multiplies native0..200 values by50. Therefore do
not claim zero database reputation means zero reputation in a loaded career.

Later snapshot found David at Wolves, Nkunku at Rennes, Openda at Standard,
Gimenez at Sampdoria, Cambiaso at Udinese and Bremer at Juventus. There is no
observed blanket inability to hire imported players. The game kept advancing;
snapshots are not all the same game date. Final owner read:2011, zero-day294.

Displayed value: registration player_display_value=P d v a=50647661;
A73FB0 dispatches PLAYER slot20 ->10A9300 ->PLAYER+24. CAFA20 writes this cache,
calling PLAYER slot28 (A36D90). Asking price has a distinct50617072 path via
slot24(A25520). Do not conflate asking price/displayed value/final transfer fee.
A36D90 includes player reputation/age, club/nation/league context and contract
time components. Its full FPU formula is not ported; no modern-value multiplier
or salary-policy change is approved.

Renewal failure news is reached through8DE890 ->5F7E70, within contract processing
9013A0. This is not a complete trace of offer initiation, budgets and refusal
reasons. Present memory after2010 cannot prove whether no offer was sent,
an offer was refused, or club budget prevented renewal. Need pre-expiry save
or a scoped diagnostic event trace to settle individual cases. User was not
asked to recreate that state yet. No fix/import performed.

Artifacts:database-summary.json, imported-profile-audit.json, runtime-market.json,
runtime-market-r2.json, runtime-contract-raw.json, runtime-current-clubs.json.
The first target list filtered by provenance country; r2 adds four players
whose latest package country differs from their Italian club. Current all-UID
database audit was not filtered this way. Runtime r2:78 targets,67 observed.
Missing targets are coverage gaps, not proof of absent database records.

Two read-only contract-layout probes stopped on guards; confirmed specialised
array vtable159CC44/getter50E1A0 uses byte count and no assumed capacity. Final
raw-contract capture succeeded. Do not read the fourth word as capacity here.
Initial output key squad_status_byte59 is an unproven semantic label: treat it
as raw/unmapped contract byte59, not established squad status. Control profiles
outside the import registry also had25 in recognized contracts, so it is not
proven corrupt. No mutation/writer is justified by these read-only offsets.
