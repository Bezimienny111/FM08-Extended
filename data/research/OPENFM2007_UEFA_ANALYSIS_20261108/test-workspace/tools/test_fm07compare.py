"""Tests of tools/fm07compare.py on the checked-in samples mod/test/sample_dump_{a,b}.txt. Exit 0 = all passed."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "fm07compare.py")
A = os.path.join(HERE, "..", "mod", "test", "sample_dump_a.txt")
B = os.path.join(HERE, "..", "mod", "test", "sample_dump_b.txt")
C = os.path.join(HERE, "..", "mod", "test", "sample_dump_c.txt")
D = os.path.join(HERE, "..", "mod", "test", "sample_dump_d.txt")
fail = 0


def run(*args):
    p = subprocess.run([sys.executable, TOOL, *args], capture_output=True, text=True)
    return p.returncode, p.stdout


def check(what, ok):
    global fail
    print("%s: %s" % ("PASS" if ok else "FAIL", what))
    fail |= not ok


rc, out = run(A, A)
check("same file: exit 0, 'same'", rc == 0 and out.strip().endswith("same"))
rc, out = run(A, B)
check("A vs B: exit 1", rc == 1)
check("A vs B: the changed score is a fixture difference", "fixture differ (11, 2026, 0, '2026.200', 1, 2): A 2-1 | B 1-1" in out)
check("A vs B: the table differs", "table differ (11, 2026, 0)" in out)
check("A vs B: the fate of team 2 differs (A: relegated to 12, B: stays in 11)", "fate differ (11, 2026, 2): A 12 | B 11" in out)
check("A vs B: duplicate entrants lines collapse (no entrants difference for 2026)", "entrants differ (11, 2026, 0)" not in out)
rc, out = run(A, B, "--comp", "12")
check("--comp 12: only comp 12 lines", rc == 1 and "(11," not in out and "entrants only in A (12, 2027, 0)" in out)
rc, out = run(A, A, "--recompute")
check("recompute on A: tables equal fixtures, exit 0", rc == 0)
rc, out = run(A, B, "--recompute")
check("recompute stock A vs hosted B: stale points of team 2 (gap 1, stock keeps none) found, exit 1",
      rc == 1 and "deduction (11, 2026, 0, 2): stock k=0, hosted k=1 FAULT" in out)
# structure (1.5 T3): sample C has a cup with a bye and a replay, a two-group stage and a child comp; D changes one group size
# and loses a round
rc, out = run(C, C, "--structure")
check("structure C vs C: exit 0", rc == 0 and out.strip().endswith("same"))
rc, out = run(C, D, "--structure")
check("structure C vs D: exit 1", rc == 1)
check("structure C vs D: the group size shows", "comp 31 groups: differ" in out and "3,3" in out and "3,2" in out)
check("structure C vs D: the lost round shows (round count, advance, new, legs)", "comp 21 round count: differ" in out and
      "comp 21 advance: differ" in out and "comp 21 legs: differ" in out)
check("structure C vs D: untouched names stay same", "comp 21 entrants: same" in out and "comp 21 replays: differ" in out)
rc, out = run(C, C, "--structure", "--comp", "21")
check("structure C: bye and replay are read (byes and replays per round)", rc == 0 and "comp 21 byes: same" in out and "comp 31" not in out)
rc, out = run(A, A, "--structure")
check("structure on the old sample A vs A: exit 0", rc == 0)
rc, out = run(C, D, "--calendar", "--comp", "21", "--baseline", C)
check("baseline judges the structure names: C vs D on comp 21 breaks one", rc == 1 and "BREAKS it" in out)
rc, out = run(C, C, "--recompute")
check("recompute skips cup fixtures and reads group tables: exit 0", rc == 0)
rc, out = run(C, D)
check("plain compare: replay and leg fixtures stay apart (no only-in line for them)", "only in" not in out and rc == 1 or rc == 0)
# --record (T17): sample C's cup 21 against a record of it (teams 5 3 2, legs 1 2 1), then one round's legs changed
REC = os.path.join(HERE, "..", ".run", "1.5", "t17", "test_record.dat")
os.makedirs(os.path.dirname(REC), exist_ok=True)


def record(legs1, entry1=None):
    rows = ["openfm07_comps 1", "comp CUP 21 \"cup\"", "stage 0 knockout 5 src=dbc:stgs/0"]
    for k, (t, lg) in enumerate(((5, 1), (3, legs1), (2, 1))):
        rows += ["round %d name %d status=decoded" % (k, 6 + k), "round %d teams %d status=decoded" % (k, t),
                 "round %d legs %d status=decoded" % (k, lg)]
        if k == 1 and entry1 is not None:  # T34.c4: round 1 takes new entrants
            rows.append("round 1 entry %d status=decoded" % entry1)
    with open(REC, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(rows + ["end", ""]))


record(2)
rc, out = run("--record", REC, "--comp", "21", C)
check("--record: sample C cup 21 = its record, exit 0", rc == 0 and out.strip().endswith("same"))
record(1)
rc, out = run("--record", REC, "--comp", "21", C)
check("--record: round 1 legs 1 against the dump's 2: exit 1, printed", rc == 1 and "round 1 legs record 1 | dump 2" in out)
os.remove(REC)
# --rules / --roll (T29.c6): the synthetic valid sample passes every family; one mutated copy per family breaks it
RD = os.path.join(HERE, "..", "mod", "test", "sample_dump_rules.txt")
RR = os.path.join(HERE, "..", "mod", "test", "sample_rules_record.dat")
TMP = os.path.join(HERE, "..", ".run", "1.5.1", "t29c6")
os.makedirs(TMP, exist_ok=True)
rc, out = run("--rules", "--comp", "1301394", "--record", RR, RD)
check("--rules: the valid sample, every family ok, exit 0", rc == 0 and out.count(": ok (year 2026)") == 11 and "rules hold" in out)
rc, out = run("--roll", "--record", RR, RD)
check("--roll: the valid sample, every part ok, exit 0", rc == 0 and out.count(": ok (year 2026)") == 2
      and out.count(": ok (places year 2027)") == 3 and "roll holds" in out)
rc, _ = run("--rules", "--record", RR, RD)
check("--rules without --comp: usage, exit 2", rc == 2)
rc, _ = run("--rules", "--comp", "11", "--record", RR, RD)
check("--rules on a comp that is not one of the three: usage, exit 2", rc == 2)
# --families (T29.c8): a sample with family 8 broken passes when 8 is left out, fails when it is in; an unknown number is usage
m6 = os.path.join(TMP, "fam8_dump.txt")
with open(RD, encoding="utf-8") as f:
    t6 = f.read()
with open(m6, "w", encoding="utf-8", newline="\n") as f:
    f.write(t6.replace("home=7 away=5 score=2-0", "home=5 away=7 score=0-2", 1))
rc, out = run("--rules", "--comp", "1301394", "--families", "1,2,3,4,5,10,11", "--record", RR, m6)
check("--families 1-5,10,11: family 8 broken but left out: exit 0, 7 families ok, no family 8 line",
      rc == 0 and out.count(": ok (year 2026)") == 7 and "family 8" not in out and "rules hold" in out)
rc, out = run("--rules", "--comp", "1301394", "--families", "1,8", "--record", RR, m6)
check("--families 1,8: family 8 broken and included: exit 1, 'family 8 second_leg: BROKEN'", rc == 1 and "family 8 second_leg: BROKEN" in out)
rc, _ = run("--rules", "--comp", "1301394", "--families", "1,12", "--record", RR, m6)
check("--families with an unknown number 12: usage, exit 2", rc == 2)
os.remove(m6)


def mutate(src, edits):
    with open(src, encoding="utf-8") as f:
        text = f.read()
    for old, new in edits:
        if old not in text:
            return None
        text = text.replace(old, new, 1)
    dst = os.path.join(TMP, os.path.basename(src))
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return dst


MUT = [  # (family, what, file, edits)
    ("family 1 entrants", "a CLG seat line dropped", RD, [("comp=1301394 year=2026 stage=1 seat round=0 slot=5 seed=CLG path=main team=7 "
                                                         "nation=1004 nrank=4 dpos=1\n", "")]),
    ("family 2 qualifying", "a loser's transfer key 24 -> 40", RD, [("transfer round=0 team=8 to=1301396 key=24", "transfer round=0 team=8 to=1301396 key=40")]),
    ("family 3 draw", "team 7's association = team 1's", RD, [("pot team=7 nation=1004", "pot team=7 nation=1001")]),
    ("family 4 fixtures", "matchday 2: 1 v 4 played at 4", RD, [("home=1 away=4 score=3-0", "home=4 away=1 score=0-3")]),
    ("family 5 split", "matchdays 1 and 2 swapped", RD, [("date=2026.274 now=2026.274", "date=X now=X")] * 4 +
     [("date=2026.288 now=2026.288", "date=2026.274 now=2026.274")] * 4 + [("date=X now=X", "date=2026.288 now=2026.288")] * 4),
    ("family 6 standings", "positions 4 and 5 swapped", RD, [("row=4 pos=4 team=3", "row=5 pos=5 team=3"), ("row=5 pos=5 team=5", "row=4 pos=4 team=5")]),
    # T30.8.c1: was the homes 5 / 6 swapped, now the allowed draw (below); the seeded sides 3 / 4 traded is no draw of Art 19.02
    ("family 7 playoff", "record: play-off bracket rows trade the seeded ranks 3 and 4", RR, [("round 0 bracket 0 home team 3 away team 0", "round 0 bracket 0 home team 3 away team 1"),
                                                                                         ("round 0 bracket 1 home team 2 away team 1", "round 0 bracket 1 home team 2 away team 0")]),
    ("family 8 second_leg", "play-off tie 0 second leg at the unseeded side", RD, [("home=7 away=5 score=2-0", "home=5 away=7 score=0-2")]),
    ("family 9 bracket", "record: the final two legs", RR, [("round 2 legs 1 status=decoded", "round 2 legs 2 status=decoded")]),
    ("family 10 tie_rule", "a level tie to penalties without extra time", RD, [("a=10 b=6 et=1", "a=10 b=6 et=0")]),
    ("family 11 prizes", "the winner's prize 5000 -> 4000", RD, [("kind=winner round=2 amount=5000", "kind=winner round=2 amount=4000")]),
]
for fam, what, src, edits in MUT:
    m = mutate(src, edits)
    args = ("--rules", "--comp", "1301394", "--record", m if src == RR else RR, m if src == RD else RD)
    rc, out = run(*args) if m else (None, "")
    check("--rules negative: %s: exit 1, '%s: BROKEN'" % (what, fam), m is not None and rc == 1 and fam + ": BROKEN" in out)
    if m:
        os.remove(m)
# T30.8.c1: families 7 / 8 / 9 accept the regulation draw on the record's bracket (UCL / UEL Regulations 2026/27 Art 19.02 / 19.03:
# the unseeded sides of two play-off ties seeded k, k + 1 swap; the direct places of two R16 ties seeded k, k + 1 swap), nothing else.
# The sample: team index 0..3 = ranks 3..6, 4 / 5 = ranks 1 / 2; play-off 6 v 3, 5 v 4 (one pair), R16 tie 0 v 1, tie 1 v 2 (one pair).
# A record row edited = the dump drawn the other way round against it.
DRAWS = [  # (what, record edits, dump edits, families that must break, "" = all 11 ok)
    ("record: play-off homes 5 / 6 swapped (the 19.02 draw)", [("round 0 bracket 0 home team 3", "round 0 bracket 0 home team 2"),
                                                               ("round 0 bracket 1 home team 2", "round 0 bracket 1 home team 3")], [], ""),
    ("record: R16 direct places 1 / 2 swapped (the 19.03 draw)", [("round 1 bracket 0 home tie 0 away team 4", "round 1 bracket 0 home tie 0 away team 5"),
                                                                  ("round 1 bracket 1 home tie 1 away team 5", "round 1 bracket 1 home tie 1 away team 4")], [], ""),
    ("record: both draws swapped", [("round 0 bracket 0 home team 3", "round 0 bracket 0 home team 2"),
                                    ("round 0 bracket 1 home team 2", "round 0 bracket 1 home team 3"),
                                    ("round 1 bracket 0 home tie 0 away team 4", "round 1 bracket 0 home tie 0 away team 5"),
                                    ("round 1 bracket 1 home tie 1 away team 5", "round 1 bracket 1 home tie 1 away team 4")], [], ""),
    ("record: half a play-off swap (tie 0 home 5, tie 1 home 5)", [("round 0 bracket 0 home team 3", "round 0 bracket 0 home team 2")], [],
     "family 7 playoff"),
    ("record: R16 feeders traded (tie 0 v the winner of play-off tie 1): no 19.03 draw",
     [("round 1 bracket 0 home tie 0", "round 1 bracket 0 home tie 1"), ("round 1 bracket 1 home tie 1", "round 1 bracket 1 home tie 0")], [],
     "family 9 bracket"),
    ("record: play-off homes swapped, dump: tie 0 second leg at the unseeded side",
     [("round 0 bracket 0 home team 3", "round 0 bracket 0 home team 2"), ("round 0 bracket 1 home team 2", "round 0 bracket 1 home team 3")],
     [("home=7 away=5 score=2-0", "home=5 away=7 score=0-2")], "family 8 second_leg"),
]
for what, rec_edits, dump_edits, fam in DRAWS:
    mr = mutate(RR, rec_edits)
    md = mutate(RD, dump_edits) if dump_edits else RD
    rc, out = run("--rules", "--comp", "1301394", "--record", mr, md) if mr and md else (None, "")
    if fam:
        check("--rules draw negative: %s: exit 1, '%s: BROKEN'" % (what, fam), rc == 1 and fam + ": BROKEN" in out)
    else:
        check("--rules draw: %s: every family ok, exit 0" % what, rc == 0 and out.count(": ok (year 2026)") == 11)
    for x in (mr, md):
        if x and x != RD:
            os.remove(x)
# T37.c2: families 1 / 2 on a qualifying chain. Stage 0: round 0 (149) entry 2 takes CHQ1 11 v 12 (13, the third CHQ1 seat, overflows
# into the full round 1); round 1 (150) entry 3: CHQ2 14 (a stage-build `bye` line: seat v feeder) v winner 11, 13 v 15. Stage 1: the
# round-150 winners 14 15 by `fate 0 51 0 round 150 stag=1` (comp only on its raw 58 twin). League phase stage 2: CLG 1 2, the stage 1
# winner 14 and team 20, a 1301396 loser whose source `fate 0 51 1 round 21 stag=2` sends it there.
QH = "comp=1301394 year=2026 stage=%d "
QD = "".join(QH % s + x + "\n" for s, x in [
    (2, "seat round=0 slot=0 seed=CLG path=main team=1 nation=1001 nrank=1 dpos=1"),
    (2, "seat round=0 slot=1 seed=CLG path=main team=2 nation=1002 nrank=2 dpos=1"),
    (0, "seat round=0 slot=0 seed=CHQ1 path=champions team=11 nation=1011 nrank=3 dpos=1"),
    (0, "seat round=0 slot=1 seed=CHQ1 path=champions team=12 nation=1012 nrank=4 dpos=1"),
    (0, "seat round=0 slot=2 seed=CHQ1 path=champions team=13 nation=1013 nrank=5 dpos=1"),
    (0, "seat round=1 slot=0 seed=CHQ2 path=champions team=14 nation=1014 nrank=6 dpos=1"),
    (0, "seat round=1 slot=1 seed=CHQ2 path=champions team=15 nation=1015 nrank=7 dpos=1"),
    (0, "bye round=1 tie=0 team=14"),
    (0, "tie round=0 tie=0 a=11 b=12 et=0 pens=- winner=11"),
    (0, "tie round=1 tie=0 a=14 b=11 et=0 pens=- winner=14"),
    (0, "tie round=1 tie=1 a=13 b=15 et=0 pens=- winner=15"),
    (1, "tie round=0 tie=0 a=14 b=15 et=0 pens=- winner=14"),
    (2, "entrants n=4 teams=1,2,14,20")]) + "comp=1301396 year=2026 stage=0 transfer round=0 team=20 to=1301394 key=48\n"
QR = "\n".join([
    "openfm07_comps 1", 'comp eur_access 0 "uefa_access"', "access 1301394 totals CLG=2 CHQ1=3 CHQ2=2 status=decoded src=sample", "end",
    'comp eur_champions_cup_2024 1301394 "qual_cl"', "entry 0 stage 2 rank_level 6", "entry 1 stage 0 round 149",
    "entry 2 stage 0 round 150", "stage 0 knockout -1 src=sample", "fate 0 51 0 round 150 stag=1 status=named",
    "fate 0 58 0 round 150 comp=1301394 stag=1 status=raw", "round 0 name 149", "round 0 ties 1", "round 0 entry 2",
    "round 0 next_winners -1", "round 1 name 150", "round 1 ties 2", "round 1 entry 3", "round 1 next_winners -1",
    "stage 1 knockout -1 src=sample", "fate 1 51 0 round 151 comp=1301394 stag=2 status=named", "round 0 name 151", "round 0 ties 1",
    "round 0 entry 2", "stage 2 league_phase 4 src=sample", "end",
    'comp eur_uefa_cup_2024 1301396 "qual_el"', "stage 0 knockout -1 src=sample", "fate 0 51 1 round 21 comp=1301394 stag=2 status=named",
    "round 0 name 21", "end", ""])
QDF, QRF = os.path.join(TMP, "qual_dump.txt"), os.path.join(TMP, "qual_record.dat")


def qual(dump_edits=(), rec_edits=()):
    """write the T37.c2 fixture with the edits applied (each old string must be there); run --rules on it."""
    files = []
    for path, text, edits in ((QDF, QD, dump_edits), (QRF, QR, rec_edits)):
        for old, new in edits:
            if old not in text:
                return None, "edit not applied: " + old
            text = text.replace(old, new, 1)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        files.append(path)
    out = run("--rules", "--comp", "1301394", "--record", QRF, QDF)
    for path in files:
        os.remove(path)
    return out


rc, out = qual()
check("--rules qualifying chain: family 1 entrants ok, family 2 qualifying ok",
      "family 1 entrants: ok" in out and "family 2 qualifying: ok" in out)
QNEG = [  # (family, what, dump edits, record edits, the problem line's text)
    ("family 2 qualifying", "a round-0 loser with a stage-build bye line plays round 1",
     [(QH % 0 + "bye round=1 tie=0 team=14", QH % 0 + "bye round=1 tie=0 team=14\n" + QH % 0 + "bye round=0 tie=0 team=12"),
      ("a=13 b=15", "a=12 b=15")], [], "team 12 enters a second time"),
    ("family 2 qualifying", "a stage 1 side that no fate 51 0 sends there", [("a=14 b=15 et=0 pens=- winner=14", "a=14 b=12 et=0 pens=- winner=14")],
     [], "team 12 is neither seated"),
    ("family 2 qualifying", "the fate 51 0 without comp= and without its 58 twin", [], [("fate 0 58 0 round 150 comp=1301394 stag=1", "x")],
     "team 14 is neither seated"),
    ("family 2 qualifying", "CHQ1 12 and CHQ2 14 swap rounds (each window full, each holds the other's seat)",
     [("a=11 b=12", "a=11 b=14"), ("a=14 b=11 et=0 pens=- winner=14", "a=12 b=11 et=0 pens=- winner=12")], [],
     "team 12 seated in round 0 enters in round 1"),
    ("family 1 entrants", "the transfer source's fate sends its losers to stage 1, not the league phase", [],
     [("fate 0 51 1 round 21 comp=1301394 stag=2", "fate 0 51 1 round 21 comp=1301394 stag=1")], "seats + qualifiers [1, 2, 14]"),
]
for fam, what, de, re_, msg in QNEG:
    rc, out = qual(de, re_)
    check("--rules negative: %s: exit 1, '%s: BROKEN', '%s'" % (what, fam, msg), rc == 1 and fam + ": BROKEN" in out and msg in out)
# T30.8.c7: `build_list` lines (build_seated's list in its order) replace the seat-line order in the simulation
BL = "".join(QH % 0 + "build_list i=%d team=%d round=%d\n" % (i, t, r) for i, (t, r) in enumerate(((11, 0), (12, 0), (13, 0), (14, 1), (15, 1))))
rc, out = qual([(QH % 0 + "bye round=1", BL + QH % 0 + "bye round=1")])
check("--rules: build_list 11 12 13 14 15 (the seat order): family 2 qualifying ok", "family 2 qualifying: ok" in out)
BL2 = BL.replace("i=0 team=11", "i=9 team=11").replace("i=2 team=13", "i=0 team=13")
rc, out = qual([(QH % 0 + "bye round=1", BL2 + QH % 0 + "bye round=1")])
check("--rules negative: build_list 13 12 11 (13 first takes a round-0 seat, 11 overflows): family 2 BROKEN, 'team 11 seated in round 0 "
      "enters in round 0, build_seated puts it in round 1'", rc == 1 and "family 2 qualifying: BROKEN" in out and
      "team 11 seated in round 0 enters in round 0, build_seated puts it in round 1" in out)
m = mutate(RD, [("coeff kind=club team=9 nation=1005 points=", "coeff kind=club team=9 nation=1005 points=1")])
rc, out = run("--roll", "--record", RR, m) if m else (None, "")
check("--roll negative: a club's season points changed: exit 1, 'roll club: BROKEN'", m is not None and rc == 1 and "roll club: BROKEN" in out)
if m:
    os.remove(m)
# --roll (T39.c1): places / eps relabelled to the coeff year 2026 (no coeff 2025): ranked by the pre-roll `prev` order
# (80 60 40 32 20, the same order), EPS season = hist[:-1][-1] (1001 20, 1002 15): ok; ranks 1 and 2 swapped against `prev`: BROKEN
PRE = ([("year=2027 stage=-1 places", "year=2026 stage=-1 places")] * 5 +
       [("year=2027 stage=-1 eps nation=1001 season=24.7500", "year=2026 stage=-1 eps nation=1001 season=20.0000"),
        ("year=2027 stage=-1 eps nation=1002 season=18.0000", "year=2026 stage=-1 eps nation=1002 season=15.0000")])
m = mutate(RD, PRE)
rc, out = run("--roll", "--record", RR, m) if m else (None, "")
check("--roll: places / eps of the coeff year, ranked by prev: rank, places, eps ok (places year 2026), exit 0",
      m is not None and rc == 0 and out.count(": ok (places year 2026)") == 3)
m = mutate(RD, PRE + [("places nation=1001 rank=1", "places nation=1001 rank=2"), ("places nation=1002 rank=2", "places nation=1002 rank=1")])
rc, out = run("--roll", "--record", RR, m) if m else (None, "")
check("--roll negative: places of the coeff year, ranks 1 and 2 swapped against prev: exit 1, 'roll rank: BROKEN'",
      m is not None and rc == 1 and "roll rank: BROKEN" in out)
if m:
    os.remove(m)
# --roll (T29.c9): two sets of places year 2027 (the pre-roll compute at the picks, then the block's post-roll one): the last judged.
# A stale set (ranks 1 / 2 swapped against value, EPS 1005) before the valid one: ok; after it: rank and eps BROKEN
P27 = "comp=1301394 year=2027 stage=-1 "
STALE = "".join(P27 + x + "\n" for x in ["places nation=1002 rank=1 band=2,0", "places nation=1001 rank=2 band=2,0",
                                         "places nation=1003 rank=3 band=1,1", "places nation=1004 rank=4 band=1,1",
                                         "places nation=1005 rank=5 band=0,2", "eps nation=1005 season=1.0000"])
GOOD1 = P27 + "places nation=1001 rank=1 band=2,0\n"
GOODE = P27 + "eps nation=1002 season=18.0000\n"
m = mutate(RD, [(GOOD1, STALE + GOOD1)])
rc, out = run("--roll", "--record", RR, m) if m else (None, "")
check("--roll: a stale places / eps set of 2027 before the post-roll one: the last set judged, rank, places, eps ok, exit 0",
      m is not None and rc == 0 and out.count(": ok (places year 2027)") == 3)
m = mutate(RD, [(GOODE, GOODE + STALE)])
rc, out = run("--roll", "--record", RR, m) if m else (None, "")
check("--roll negative: the stale set last: exit 1, 'roll rank: BROKEN', 'roll eps: BROKEN'",
      m is not None and rc == 1 and "roll rank: BROKEN" in out and "roll eps: BROKEN" in out)
if m:
    os.remove(m)
# --rules family 3 (T29.c9): each pot coef = the coeff club value of year Y-1 when the dump has that line (team 2, coef 100000)
C25 = "comp=-1 year=2025 stage=-1 coeff kind=club team=2 nation=1001 points=0.0000 matches=0 ring=100000 value=%d\n"
C26 = "comp=-1 year=2026 stage=-1 coeff kind=club team=1 "
for v, want in ((100000, True), (99000, False)):
    m = mutate(RD, [(C26, C25 % v + C26)])
    rc, out = run("--rules", "--comp", "1301394", "--families", "3", "--record", RR, m) if m else (None, "")
    if want:
        check("--rules family 3: the pot coef equals the coeff club value of 2025 (100000): ok, exit 0",
              m is not None and rc == 0 and "family 3 draw: ok (year 2026)" in out)
    else:
        check("--rules negative: family 3: the coeff club value of 2025 99000 against pot coef 100000: exit 1, 'family 3 draw: BROKEN'",
              m is not None and rc == 1 and "family 3 draw: BROKEN" in out and "team 2 pot coef 100000, coeff club value 99000" in out)
    if m:
        os.remove(m)
# --roll (T39.c2): win / draw by the score (compcoef.c accrue, FUN_00C40330(side,1,0) = score=), not the LOST code. The play-off
# round 18 deciding leg 2 v 4 made level (0-0) and won on penalties (raw side 1, team 4, LOST): a draw, 2 and 4 one point each,
# their nations 1001 / 1002; season, hist, value, ring kept consistent: ok
PEN = ("home=2 away=4 score=1-0 raw=0100FFFFFF010000FFFFFF0A", "home=2 away=4 score=0-0 raw=0000FFFFFF030000FFFFFF0A")
DRAW = [PEN, ("points=24.5000 matches=7 ring=5000,5000,5000,5000,24500 value=44500",
              "points=23.5000 matches=7 ring=5000,5000,5000,5000,23500 value=43500"),
        ("points=18.0000 matches=8 ring=5000,5000,5000,5000,18000 value=38000",
         "points=19.0000 matches=8 ring=5000,5000,5000,5000,19000 value=39000"),
        ("points=49.5000 clubs=2 season=24.7500 hist=20.0000,20.0000,20.0000,20.0000,24.7500 value=104.7500",
         "points=48.5000 clubs=2 season=24.2500 hist=20.0000,20.0000,20.0000,20.0000,24.2500 value=104.2500"),
        ("points=36.0000 clubs=2 season=18.0000 hist=15.0000,15.0000,15.0000,15.0000,18.0000 value=78.0000",
         "points=37.0000 clubs=2 season=18.5000 hist=15.0000,15.0000,15.0000,15.0000,18.5000 value=78.5000")]
m = mutate(RD, DRAW)
rc, out = run("--roll", "--record", RR, m) if m else (None, "")
check("--roll: a deciding leg level on the score, won on penalties, scored a draw: nation, club ok",
      m is not None and "roll nation: ok" in out and "roll club: ok" in out)
if m:
    os.remove(m)
# negative: the same leg paid as a win to 2 by the tie outcome (the LOST rule; 2 and 4 points as before) must break
m = mutate(RD, [PEN])
rc, out = run("--roll", "--record", RR, m) if m else (None, "")
check("--roll negative: the penalties leg paid as a win by the tie outcome (LOST): exit 1, 'roll nation: BROKEN', 'roll club: BROKEN'",
      m is not None and rc == 1 and "roll nation: BROKEN" in out and "roll club: BROKEN" in out)
if m:
    os.remove(m)
# --record (T34.c4): a stage whose round 1 takes 2 new entrants: the dump's stage teams= 7 = round 0's 5 + 2; 5 + 1 differs
m = mutate(C, [("comp=21 year=2026 stage=0 stage kind=cup rounds=3 teams=5", "comp=21 year=2026 stage=0 stage kind=cup rounds=3 teams=7")])
record(2, 2)
rc, out = run("--record", REC, "--comp", "21", m) if m else (None, "")
check("--record: stage teams 7 = round 0 teams 5 + round 1 entry 2: exit 0", m is not None and rc == 0 and out.strip().endswith("same"))
record(2, 1)
rc, out = run("--record", REC, "--comp", "21", m) if m else (None, "")
check("--record negative: round 1 entry 1 (5 + 1 = 6) against stage teams 7: exit 1, printed",
      rc == 1 and "entrants record round 0 teams 5 + later entries 1 | dump stage teams= 7" in out)
os.remove(REC)
if m:
    os.remove(m)


def rules(rec_edits=(), dump_edits=()):
    """T30.8.c5: --rules on the sample with the edits applied (each old string must be there); (rc, out), (None, '') if not."""
    mr = mutate(RR, rec_edits) if rec_edits else RR
    md = mutate(RD, dump_edits) if dump_edits else RD
    rc, out = run("--rules", "--comp", "1301394", "--record", mr, md) if mr and md else (None, "")
    for x in (mr, md):
        if x and x not in (RR, RD):
            os.remove(x)
    return rc, out


# T30.8.c5 (1): dump error markers (C0115) break families 1, 2, 10, 11 with the reason
FAM_TIE = ("family 1 entrants", "family 2 qualifying", "family 10 tie_rule", "family 11 prizes")
for what, de in (("a `# dump error tie table full` line", [("comp=1301394 year=2026 stage=0 tie round=0 tie=0",
                                                            "# dump error tie table full\ncomp=1301394 year=2026 stage=0 tie round=0 tie=0")]),
                 ("a tie line tagged src=bytes", [("a=9 b=8 et=0 pens=- winner=9", "a=9 b=8 et=0 pens=- winner=9 src=bytes")])):
    rc, out = rules((), de)
    check("--rules negative: %s: exit 1, families 1, 2, 10, 11 BROKEN, 'tie lines not trusted'" % what,
          rc == 1 and all(f + ": BROKEN" in out for f in FAM_TIE) and "tie lines not trusted" in out and "family 9 bracket: ok" in out)
# (2): prize amounts converted as the game does, trunc(trunc(cash / div) * mul) in double (T30.8.c4, FUN_00DECA80) (T30.8.c3: 2175000 -> 1499999 at curr 7, 1.45)
RATE = "# prize_rule amount=trunc(trunc(cash/div)*mul) math=double mul=1 round100000=0\ncomp=-1 year=2026 stage=-1 prize_rate curr=7 div=1.45\n"
CURR = [("round 2 prize_winner 5000 status=decoded", "round 2 prize_winner 2175000 curr=7 status=decoded")]
WIN = "kind=winner round=2 amount=5000"
rc, out = rules(CURR, [(WIN, "kind=winner round=2 amount=1499999"), ("comp=1301394 year=2026 stage=0 seat", RATE + "comp=1301394 year=2026 stage=0 seat")])
check("--rules family 11: cash 2175000 curr=7, prize_rate div 1.45, amount 1499999: ok", rc == 0 and "family 11 prizes: ok" in out)
for what, de, msg in (("no prize_rate line for curr 7", [(WIN, "kind=winner round=2 amount=1499999")], "no prize_rate line for curr=7"),
                      ("amount 1500000 (float32 quotient)", [(WIN, "kind=winner round=2 amount=1500000"),
                                                             ("comp=1301394 year=2026 stage=0 seat", RATE + "comp=1301394 year=2026 stage=0 seat")],
                       "amount 1499999: record wants 1, dump pays 0"),
                      ("a prize_rule with round100000=1 (undecoded rounding)", [(WIN, "kind=winner round=2 amount=1499999"),
                        ("comp=1301394 year=2026 stage=0 seat", RATE.replace("round100000=0", "round100000=1") + "comp=1301394 year=2026 stage=0 seat")],
                       "amounts not judged"),
                      ("no prize_rule line", [(WIN, "kind=winner round=2 amount=1499999"),
                        ("comp=1301394 year=2026 stage=0 seat", RATE.split("\n", 1)[1] + "comp=1301394 year=2026 stage=0 seat")],
                       "amounts not judged"),
                      ("mul 2 ignored (amount 1499999 where 2999998 is due)", [(WIN, "kind=winner round=2 amount=1499999"),
                        ("comp=1301394 year=2026 stage=0 seat", RATE.replace("mul=1 ", "mul=2 ") + "comp=1301394 year=2026 stage=0 seat")],
                       "amount 2999998: record wants 1, dump pays 0"),
                      ("the unconverted cash 2175000", [(WIN, "kind=winner round=2 amount=2175000"),
                                                        ("comp=1301394 year=2026 stage=0 seat", RATE + "comp=1301394 year=2026 stage=0 seat")],
                       "amount 2175000: record wants 0, dump pays 1")):
    rc, out = rules(CURR, de)
    check("--rules negative: family 11 %s: exit 1, BROKEN, '%s'" % (what, msg), rc == 1 and "family 11 prizes: BROKEN" in out and msg in out)
rc, out = rules((), [("comp=1301394 year=2026 stage=1 prize team=1 kind=appearance round=-1 amount=1000\n", "")])
check("--rules negative: family 11: a league phase entrant without its appearance line: exit 1, BROKEN",
      rc == 1 and "family 11 prizes: BROKEN" in out and "stage 1 team 1 appearance round -1 amount 1000: record wants 1, dump pays 0" in out)
# (3): league phase fixtures to plan rows by pair: a postponed fixture keeps its row; a pair twice, rows out of date order break
LP1 = "stage=1 fixture date=2026.260 now=2026.260 home=1 away=3 score=2-1"
rc, out = rules((), [(LP1, "stage=1 fixture date=2026.316 now=2026.316 home=1 away=3 score=2-1")])
check("--rules family 4: one fixture postponed past the last matchday: ok", "family 4 fixtures: ok" in out)
rc, out = rules((), [(LP1, LP1.replace("2026.260", "2026.316") + " raw=0200FFFFFF010100FFFFFF0A leg=0 mode=0\ncomp=1301394 year=2026 " + LP1)])
check("--rules negative: family 4: pair 1 v 3 played twice: exit 1, BROKEN", rc == 1 and "family 4 fixtures: BROKEN" in out
      and "pair 1 v 3 played 2 times" in out)
rc, out = rules((), MUT[4][3])
check("--rules negative: family 4: matchdays 1 and 2 dates swapped: BROKEN, 'matchday date order: plan rows played 0,2,1,3'",
      rc == 1 and "family 4 fixtures: BROKEN" in out and "matchday date order: plan rows played 0,2,1,3" in out)
# (4): build_seated's transfer reserve: round 1 keeps 1 of its 3 seats for transfers, the overflow CHQ1 13 has no seat left
rc, out = qual([], [("round 1 entry 3", "round 1 entry 3\nround 1 transfers 1")])
check("--rules negative: family 2: round 1 transfers 1 leaves no seat for 13: exit 1, BROKEN, 'build_seated puts it in round None'",
      rc == 1 and "family 2 qualifying: BROKEN" in out and "team 13 seated in round 0 enters in round 1, build_seated puts it in round None" in out)
# (5): a season in progress: the final not played yet (no fixture, tie or prize lines): its stage is not judged, the rest is
FINAL = ["comp=1301394 year=2026 stage=2 fixture date=2026.358 now=2026.358 home=2 away=1 score=2-1 raw=0200FFFFFF010100FFFFFF0A leg=0 mode=0 "
         "kind=cup round=2 tie=0 replay=0\n", "comp=1301394 year=2026 stage=2 tie round=2 tie=0 a=2 b=1 et=0 pens=- winner=2\n",
         "comp=1301394 year=2026 stage=2 prize team=2 kind=winner round=2 amount=5000\n",
         "comp=1301394 year=2026 stage=2 prize team=1 kind=loser round=2 amount=3000\n"]
rc, out = rules((), [(x, "") for x in FINAL])
check("--rules: the final not played yet: exit 0, family 9 'in progress, not judged', families 1-6 ok, 10 / 11 judge stages 0-1",
      rc == 0 and "family 9 bracket: in progress, not judged" in out and "family 7 playoff: in progress, not judged" in out
      and out.count(": ok (year 2026)") == 8 and "stage(s) 2 in progress, not judged" in out)
rc, out = rules((), [(x, "") for x in FINAL] + [("comp=1301394 year=2026 stage=0 tie round=0 tie=0 a=9 b=8 et=0 pens=- winner=9\n", "")])
check("--rules negative: in progress elsewhere, a complete stage's tie line missing: exit 1, 'family 2 qualifying: BROKEN'",
      rc == 1 and "family 2 qualifying: BROKEN" in out)
# T47.c2 (1) --side: the side file's records replace the first record of each uid (comphost.c:199-243); the rest stays, a side
# record whose uid the file lacks is dropped. Negative control: no side file = the file unchanged.
sys.path.insert(0, HERE)
import fm07compare  # noqa: E402
SM, SS = os.path.join(TMP, "splice_main.dat"), os.path.join(TMP, "splice_side.dat")
with open(SM, "w", encoding="utf-8", newline="\n") as f:
    f.write("openfm07_comps 1\ncomp a 1 \"a1\"\nround 0 ties 1\nend\ncomp eur_access 0 \"acc\"\naccess x\nend\n"
            "comp a 1 \"a1 again\"\nround 0 ties 2\nend\ncomp b 2 \"b\"\nend\n")
with open(SS, "w", encoding="utf-8", newline="\n") as f:
    f.write("comp a 1 \"side a1\"\nround 0 ties 9\nend\ncomp c 3 \"side c\"\nend")
sp = "".join(fm07compare.splice(SM, SS))
check("--side splice: uid 1's first record replaced by the side's, eur_access / the second uid 1 record / uid 2 kept, uid 3 dropped",
      sp == "openfm07_comps 1\ncomp a 1 \"side a1\"\nround 0 ties 9\nend\ncomp eur_access 0 \"acc\"\naccess x\nend\n"
            "comp a 1 \"a1 again\"\nround 0 ties 2\nend\ncomp b 2 \"b\"\nend\n")
check("--side splice negative control: no side file: the file's lines unchanged (round 0 ties 1 kept, no 'side a1')",
      "".join(fm07compare.splice(SM, None)) == open(SM, encoding="utf-8").read())
rc, out = run("--rules", "--roll", "--record", SM, "--side", SS, A)
check("--side with --roll: usage, exit 2", rc == 2)
for x in (SM, SS):
    os.remove(x)
# T47.c2 (2) family 1 with --side: per entry round, the seeds' seats = entry - transfers, the round's routed losers counted inside
# (no transfers) and the winners other stages send there taken off. The side's CL record: CHQ1 round 149 entry 3, CHQ2 round 150
# entry 2, entry 48 = the league stage; the side's UEL record sends round 21's 1 loser there by key 48: CLG = 4 - 1 loser - 1 winner.
SIDE = QR.split("end\n", 1)[1].replace("round 0 entry 2\nround 0 next_winners", "round 0 entry 3\nround 0 next_winners").replace(
    "round 1 entry 3", "round 1 entry 2").replace("entry 2 stage 0 round 150", "entry 2 stage 0 round 150\nentry 48 stage 2").replace(
    "round 0 name 21", "f fate.cup_continental 21 1 1301394 48\nround 0 name 21\nround 0 ties 1")
QSF = os.path.join(TMP, "qual_side.dat")


def qside(dump_edits=(), side_edits=(), side=True):
    """the T37.c2 fixture, family 1 with the T47.c2 side file (edits applied); --side omitted when side is False."""
    text = SIDE
    for old, new in side_edits:
        if old not in text:
            return None, "edit not applied: " + old
        text = text.replace(old, new, 1)
    with open(QSF, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    d = QD
    for old, new in dump_edits:
        if old not in d:
            return None, "edit not applied: " + old
        d = d.replace(old, new, 1)
    for path, t in ((QDF, d), (QRF, QR)):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(t)
    out = run("--rules", "--comp", "1301394", "--families", "1", "--record", QRF, *(("--side", QSF) if side else ()), QDF)
    for path in (QDF, QRF, QSF):
        os.remove(path)
    return out


rc, out = qside()
check("--rules --side family 1: CHQ1 3 = entry 3, CHQ2 2 = entry 2, CLG 2 = 4 - 1 loser - 1 winner: ok, exit 0",
      rc == 0 and "family 1 entrants: ok" in out)
for what, de, se, msg in (
        ("one CHQ2 seat removed (team 15)", [(QH % 0 + "seat round=1 slot=1 seed=CHQ2 path=champions team=15 nation=1015 nrank=7 dpos=1\n", "")],
         [], "seeds CHQ2 (stage 0 round 150): 1 seat(s), record entry 2"),
        ("one CHQ1 seat added (team 16)", [(QH % 0 + "seat round=1 slot=0", QH % 0 + "seat round=0 slot=3 seed=CHQ1 path=champions team=16 "
                                            "nation=1016 nrank=8 dpos=1\n" + QH % 0 + "seat round=1 slot=0")],
         [], "seeds CHQ1 (stage 0 round 149): 4 seat(s), record entry 3"),
        ("the side's UEL round 21 has 2 ties (2 losers inside the league stage)", [], [("round 0 ties 1\nend", "round 0 ties 2\nend")],
         "seeds CLG (stage 2 round None): 2 seat(s), record entry 4 - transfers 0 - losers inside 2 - winners 1 = 1")):
    rc, out = qside(de, se)
    check("--rules --side negative: family 1 %s: exit 1, BROKEN, '%s'" % (what, msg), rc == 1 and "family 1 entrants: BROKEN" in out and msg in out)
rc, out = qside([], [("round 0 entry 3\nround 0 next_winners", "round 0 entry 2\nround 0 next_winners")])
check("--rules --side negative control: the side's CHQ1 round back to entry 2 (the main record's): 3 seats break family 1",
      rc == 1 and "seeds CHQ1 (stage 0 round 149): 3 seat(s), record entry 2" in out)
# T47.c2 (3) family 2 with --side: the extra rebalancing draw. CL CP Q1 (stage 0 round 0) C = 15 ties, losers to UECL key 40 (its
# entry: stage 1 round 1003); 16 - C = 1 loser also to key 41 (the UECL entry on the next round 1004). Accepted only so.
XH = "comp=1301394 year=2026 stage=0 "
XDD = "".join(XH + "seat round=0 slot=%d seed=CHQ1 path=champions team=%d nation=%d nrank=1 dpos=0\n" % (i, 101 + i, 1001 + i) for i in range(30)) + \
    "".join(XH + "tie round=0 tie=%d a=%d b=%d et=0 pens=- winner=%d\n" % (t, 101 + 2 * t, 102 + 2 * t, 101 + 2 * t) for t in range(15)) + \
    "".join(XH + "transfer round=0 team=%d to=31051584 key=40\n" % (102 + 2 * t) for t in range(15)) + \
    XH + "transfer round=0 team=102 to=31051584 key=41\n"
XDR = "\n".join([
    "openfm07_comps 1", 'comp eur_access 0 "uefa_access"', "access 1301394 totals CHQ1=30", "access 31051584 totals CC0=1", "end",
    'comp eur_champions_cup_2024 1301394 "xd_cl"', "entry 0 stage 0 round 149", "stage 0 knockout -1 src=sample",
    "f fate.cup_continental 149 1 31051584 40", "round 0 name 149", "round 0 ties 15", "round 0 entry 30", "round 0 next_winners -1", "end",
    'comp eur_conference_cup_2024 31051584 "xd_uecl"', "entry 0 stage 0 round 1009", "entry 40 stage 1 round 1003",
    "entry 41 stage 1 round 1004", "stage 0 knockout -1 src=sample", "round 0 name 1009", "stage 1 knockout -1 src=sample",
    "round 0 name 1003", "round 0 entry 12", "round 1 name 1004", "round 1 entry 1", "end", ""])
XDF, XRF, XSF = os.path.join(TMP, "xd_dump.txt"), os.path.join(TMP, "xd_record.dat"), os.path.join(TMP, "xd_side.dat")


def xd(dump_edits=(), side=True):
    d = XDD
    for old, new in dump_edits:
        if old not in d:
            return None, "edit not applied: " + old
        d = d.replace(old, new, 1)
    for path, t in ((XDF, d), (XRF, XDR), (XSF, XDR.split("end\n", 1)[1])):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(t)
    out = run("--rules", "--comp", "1301394", "--families", "2", "--record", XRF, *(("--side", XSF) if side else ()), XDF)
    for path in (XDF, XRF, XSF):
        os.remove(path)
    return out


K41 = XH + "transfer round=0 team=102 to=31051584 key=41\n"
rc, out = xd()
check("--rules --side family 2: C = 15, 16 - C = 1 CP Q1 loser to key 41 beside its key 40 line: ok, exit 0", rc == 0 and "family 2 qualifying: ok" in out)
for what, de, side, msg in (
        ("no --side", [], False, "transfer of team 102 to comp 31051584 key 41 has no record fate.cup_continental"),
        ("16 - C + 1 = 2 key-41 transfers (104 too)", [(K41, K41 + XH + "transfer round=0 team=104 to=31051584 key=41\n")], True,
         "extra draw: 2 transfer(s) to comp 31051584 key 41, 16 - C = 16 - 15 = 1"),
        ("a stray transfer without a fate (winner 101 to key 40)", [(K41, K41 + XH + "transfer round=0 team=101 to=31051584 key=40\n")], True,
         "transfer of team 101 to comp 31051584 key 40 has no record fate.cup_continental"),
        ("the key-41 team without its key-40 line", [(XH + "transfer round=0 team=102 to=31051584 key=40\n", "")], True,
         "transfer of team 102 to comp 31051584 key 41 has no record fate.cup_continental"),
        ("the extra transfer to key 42 (no UECL entry)", [(K41, K41.replace("key=41", "key=42"))], True,
         "transfer of team 102 to comp 31051584 key 42 has no record fate.cup_continental")):
    rc, out = xd(de, side)
    check("--rules --side negative: family 2 %s: exit 1, BROKEN, '%s'" % (what, msg), rc == 1 and "family 2 qualifying: BROKEN" in out and msg in out)
# T47.c2 (4) families 7 / 9: the knockout stage = the chain ranks stage (2). The phase naming the league stage itself (1, FM27's
# UEL quirk): named, ok; an unrelated phase stage (0), or chain lines naming two stages: BROKEN.
PH = [("phase direct 2 stage 2", "phase direct 2 stage %d"), ("phase playoff 4 stage 2", "phase playoff 4 stage %d")]
rc, out = rules([(a, b % 1) for a, b in PH])
check("--rules: phase stage 1 = the league stage: families 7 / 9 ok, 'record: phase playoff stage 1 is the league stage itself', exit 0",
      rc == 0 and "family 7 playoff: ok" in out and "family 9 bracket: ok" in out and
      "record: phase playoff stage 1 is the league stage itself (FM27 stag); chain ranks stage 2 judged" in out)
rc, out = rules([(a, b % 0) for a, b in PH])
check("--rules negative: phase stage 0 (neither chain nor league stage): families 7 and 9 BROKEN, 'record: phase playoff stage 0, chain "
      "ranks stage 2'", rc == 1 and "family 7 playoff: BROKEN" in out and "family 9 bracket: BROKEN" in out and
      "record: phase playoff stage 0, chain ranks stage 2 (chain judged)" in out)
rc, out = rules([("chain 2 ranks 1 1 2", "chain 0 ranks 1 1 2")])
check("--rules negative: chain ranks lines naming stages 0 and 2: families 7 and 9 BROKEN, 'name stages 0,2'",
      rc == 1 and "family 7 playoff: BROKEN" in out and "family 9 bracket: BROKEN" in out and "name stages 0,2" in out)
os.rmdir(TMP)
sys.exit(fail)
