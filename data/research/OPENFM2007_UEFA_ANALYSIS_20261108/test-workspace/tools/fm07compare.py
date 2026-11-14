"""Compare two openfm07 dumps (mod/src/compdump.c, [comp] dump=1).

  fm07compare.py A B [--comp UID] [--recompute]
  fm07compare.py A B --comp UID --calendar [--baseline C]
  fm07compare.py A B [--comp UID] --structure
  fm07compare.py --record FILE --comp UID DUMP

--record (T17): DUMP's comp against its record in FILE (a data file, tools/fm07compdata.py): per knockout stage and year,
round count, teams and legs per round, entrants (the dump's `entrants` line, else the stage line's teams=) = the record's
round 0 teams. The dump has no round names: printed from the record, not checked. Exit 1 on a difference, each printed.

--calendar (a season does not replay, T8): same pairs by round with dates ignored, tables recomputed clean, same fate
counts and targets; scores and which teams take a fate may differ. Prints each check; exit 0 = all hold, 1 = not.
Round = the date-ordered fixtures of a stage, a new round when a team would play twice (fixture congestion aside, moved
dates inside a round change nothing).

--baseline C: C is a second stock run. A property judges B only if it held between A and C: what stock itself varies
by is reported and not judged. Exit 0 = every property stock keeps, B keeps too.

Prints the differences by section (fixtures, table, entrants, derived fate); exit 0 = same, 1 = differ.
Line format: `comp=<uid> year=<y> stage=<i> <section> k=v ...` (headers start with `#`).
fixtures: key (comp, year, stage, date, home, away) -> scores; a result applied twice collapses to its last line.
table: per (comp, year, stage) the rows by position. entrants: per (comp, year, stage) the team set, repeated stage builds
(throwaway builds, load) collapse to the last. fate (derived): a team's comp(s) in the next season's entrants.
Structure (1.5 T3): cup `stage`/`round`/`bye`/`advance`, group `stage`, `compinfo` lines and `parent=` on entrants. structure(d, comp):
entrants per stage, new entrants / legs / replays / advance counts per round, round count, group count and sizes, the pairs
seen (a set per stage, no dates). --structure prints each name per comp, A against B, exit 1 on a difference; properties()
(so --baseline) judges the same names. A line with `group=<i>` keys its stage as stage + 1000 * (i + 1), so the groups of one
stage keep apart. A cup fixture keys by (comp, year, stage, date, home, away, round, tie, leg, replay): replays and legs do
not collapse; league keys are unchanged, and recompute and the round/calendar views skip cup fixtures (10-tuple keys).
--recompute [--baseline C] (T20): per table row, played, W/D/L (dump c16/c17/c18), goals for and against against the fixture
recount; a mismatch or a missing row is a fault. Points read pts = 3W+D-k: k (nonzero) is a deduction, kept in a map
(comp, year, stage, team) -> k. The map is judged as a property stock keeps: per key, stock is A (and C when given); a key
whose k differs between A and C is reported, not judged; B must carry every judged key's k (absent = 0), else a fault.
--calendar and --calendar --baseline judge the same way (A, B; A, C stock).

  fm07compare.py --rules --comp UID --record FILE DUMP     (T29.c6; UID one of 1301394 1301396 31051584)
  fm07compare.py --roll --record FILE DUMP
--rules: the comp in DUMP against the rules its record (and the `comp eur_access 0` record) in FILE states, in 11 families:
1 entrants, 2 qualifying, 3 draw, 4 fixtures, 5 split, 6 standings, 7 playoff, 8 second_leg, 9 bracket, 10 tie_rule, 11 prizes.
Prints `family <n> <name>: ok` or `family <n> <name>: BROKEN` with each broken rule; exit 0 all hold, 1 one broken, 2 usage.
--roll: the season-end coefficients (compcoef.c arithmetic), ranks, places bands and EPS (compseed.c) recomputed from the
dump's results against its `coeff` / `places` / `eps` lines; `roll <part>: ok|BROKEN`, exit 0 / 1. The line kinds and the
source of every rule: docs/ops/comp_data.md "Rules dump lines (T29.c6)".
"""
import argparse
import re
import shlex
import struct
import sys
from collections import Counter, defaultdict

SECTIONS = ("entrants", "fixture", "table", "fates", "stage", "round", "bye", "advance", "compinfo")
RULE_SECTIONS = ("seat", "transfer", "tie", "pot", "prize", "coeff", "places", "eps", "build_list")  # T29.c6, kept apart in d["rules"]
# T30.8.c7: `build_list i= team= round=`: build_seated's list in its order, round = its entry_round (-1 none)


def parse(path):
    d = {"header": "", "entrants": {}, "fixtures": {}, "table": defaultdict(dict), "fates": {}, "stage": {}, "round": {},
         "bye": set(), "advance": {}, "compinfo": {}, "parent": {}, "rules": defaultdict(list), "tablex": defaultdict(dict),
         "raw": {}, "rule_ln": defaultdict(list), "tie_full": [], "prize_rate": {}, "now": None}  # T37.c3: fixture key -> raw= (fixture +0x88..+0x93 hex), the side records --roll scores by
    # T29.c9: rule_ln[sec] the line numbers of d["rules"][sec], same order (check_roll's sets per places year)
    with open(path, encoding="utf-8") as f:
        for ln, line in enumerate(f):
            line = line.rstrip("\r\n")
            if not line:
                continue
            tok = line.split()
            if "prize_rate" in tok:  # T30.8.c5: `prize_rate curr=<c> div=<float>` (compdump: FUN_00DECA80's divisor per currency)
                kv = dict(t.split("=", 1) for t in tok if "=" in t)
                if "curr" in kv and "div" in kv:  # T30.8: %.9g = a float32 value stored as double (compdump.c prize_rates)
                    v = float(kv["div"])
                    if len(kv["div"].replace(".", "").replace("-", "").lstrip("0").split("e")[0]) <= 9:
                        v = struct.unpack("<f", struct.pack("<f", v))[0]
                    d["prize_rate"][int(kv["curr"])] = v
                continue
            if "prize_rule" in tok:  # T30.8: `# prize_rule amount=trunc(trunc(cash/div)*mul) math=double mul=<R0> round100000=<0|1>`
                kv = dict(t.split("=", 1) for t in tok if "=" in t)
                d["prize_rule"] = (float(kv.get("mul", "nan")), kv.get("round100000", "1") == "1")
                continue
            if line.startswith("#"):
                if not d["header"]:
                    d["header"] = line
                if line.startswith("# dump error tie table full"):  # T30.8.c5: compdump's tie-note table overflowed (C0115)
                    d["tie_full"].append(line)
                continue
            if len(tok) < 4 or tok[3] not in SECTIONS + RULE_SECTIONS:
                continue
            head = dict(t.split("=", 1) for t in tok[:3])
            kv = {}
            for t in tok[4:]:
                if "=" in t:
                    k, v = t.split("=", 1)
                    kv[k] = v
            stage = int(head["stage"])
            if "group" in kv:
                stage += 1000 * (int(kv["group"]) + 1)
            key = (int(head["comp"]), int(head["year"]), stage)
            sec = tok[3]
            if sec in RULE_SECTIONS:
                d["rules"][sec].append(key + (kv,))
                d["rule_ln"][sec].append(ln)
                continue
            if sec == "entrants":
                d["entrants"][key] = [int(x) for x in kv.get("teams", "").split(",") if x]
                if "parent" in kv:
                    d["parent"][key] = int(kv["parent"])
            elif sec == "fixture":
                fk = key + (kv["date"], int(kv["home"]), int(kv["away"]))
                if kv.get("kind") == "cup":
                    fk += (int(kv["round"]), int(kv["tie"]), int(kv["leg"]), int(kv["replay"]))
                d["fixtures"][fk] = kv["score"]
                if "now" in kv and (d["now"] is None or dkey(kv["now"]) > dkey(d["now"])):
                    d["now"] = kv["now"]  # T30.8.c5: the dump's last game date (in-progress stages)
                if "raw" in kv:
                    d["raw"][fk] = kv["raw"]
            elif sec == "stage":
                d["stage"][key] = kv
            elif sec == "round":
                d["round"][key + (int(kv["round"]),)] = {k: int(v) for k, v in kv.items()}
            elif sec == "bye":
                d["bye"].add(key + (int(kv["round"]), int(kv["tie"]), int(kv["team"])))
            elif sec == "advance":
                d["advance"][key + (int(kv["round"]),)] = int(kv["n"])
            elif sec == "compinfo":
                d["compinfo"][int(kv["comp"])] = {k: int(v) for k, v in kv.items()}
            elif sec == "table":
                row = {k: int(kv[k]) for k in ("team", "p", "gf", "ga", "pts")}
                row.update((f, int(kv.get(c, -1))) for f, c in (("w", "c16"), ("d", "c17"), ("l", "c18")))
                d["table"][key][int(kv["pos"])] = row
                d["tablex"][key][row["team"]] = {k: int(kv[k]) for k in ("cards", "coef") if k in kv}  # T29.c6 rank keys
            elif sec == "fates":
                d["fates"][key] = " ".join(tok[4:])
    return d


def dkey(date):
    """`2026.250` -> (2026, 250)."""
    return tuple(int(x) for x in date.split("."))


def fates_of(d):
    """(comp, year, team) -> sorted comps the team's next season entrants have it in ('-' = none)."""
    seasons = defaultdict(lambda: defaultdict(set))  # year -> team -> comps
    for (comp, year, _stage), teams in d["entrants"].items():
        for t in teams:
            seasons[year][t].add(comp)
    out = {}
    for (comp, year, _stage), teams in d["entrants"].items():
        for t in teams:
            nxt = seasons.get(year + 1)
            if nxt:  # the last season of a dump has no next one: no fate to derive
                out[(comp, year, t)] = ",".join(map(str, sorted(nxt[t]))) if t in nxt else "-"
    return out


def recompute(d):
    """per (comp, year, stage): team -> dict(p, w, d, l, gf, ga, pts) from the fixture lines."""
    out = defaultdict(lambda: defaultdict(lambda: {"p": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "pts": 0}))
    for fk, score in d["fixtures"].items():
        if len(fk) != 6:  # a cup fixture: no table to recompute
            continue
        comp, year, stage, _date, home, away = fk
        hg, ag = (int(x) for x in score.split("-"))
        t = out[(comp, year, stage)]
        for team, f, a in ((home, hg, ag), (away, ag, hg)):
            r = t[team]
            r["p"] += 1
            r["gf"] += f
            r["ga"] += a
            r["pts"] += 3 if f > a else 1 if f == a else 0
            r["w" if f > a else "d" if f == a else "l"] += 1
    return out


RECOUNT = ("p", "w", "d", "l", "gf", "ga")


def recount(d, comp=None):
    """(faults, deductions). faults: [(key, team, recount, row or None)], table rows whose p/W/D/L/gf/ga differ from the
    fixtures or that are missing. deductions: {(comp, year, stage, team): k}, k = 3W+D-pts != 0, for rows that match."""
    faults, ded = [], {}
    rc = recompute(d)
    for key in sorted(rc):
        if not keep(key, comp) or key not in d["table"]:
            continue
        dumped = {r["team"]: r for r in d["table"][key].values()}
        for team, r in sorted(rc[key].items()):
            t = dumped.get(team)
            if t is None or any(t[f] != r[f] for f in RECOUNT):
                faults.append((key, team, r, t))
                continue
            k = 3 * t["w"] + t["d"] - t["pts"]
            if k:
                ded[key + (team,)] = k
    return faults, ded


def fmt_recount(tag, fault):
    key, team, r, t = fault
    row = lambda x: " ".join("%s=%d" % (f, x[f]) for f in RECOUNT + ("pts",))
    return "recompute %s %s team %d: fixtures %s | table %s" % (tag, key, team, row(r), "missing" if t is None else row(t))


def judge_deductions(stock, other, hosted):
    """per key: (faults [(key, stock k, hosted k)], varies [keys]); a key is judged only where stock == other (absent = 0)."""
    bad, varies = [], []
    for key in sorted(set(stock) | set(other) | set(hosted)):
        s, o, h = (m.get(key, 0) for m in (stock, other, hosted))
        if s != o:
            varies.append(key)
        elif h != s:
            bad.append((key, s, h))
    return bad, varies


def deduction_report(stock, other, hosted):
    """print the judged deduction map; returns the fault count."""
    bad, varies = judge_deductions(stock, other, hosted)
    print("deductions: %d key(s) stock keeps, %d vary (not judged), %d fault(s)" % (
        len(set(stock) | set(other)) - len(varies), len(varies), len(bad)))
    for key in varies:
        print("deduction %s: stock varies %d/%d, not judged (hosted %d)" % (
            key, stock.get(key, 0), other.get(key, 0), hosted.get(key, 0)))
    for key, s, h in bad:
        print("deduction %s: stock k=%d, hosted k=%d FAULT" % (key, s, h))
    return len(bad)


def rounds(d, comp):
    """(year, stage) -> list of rounds, each a frozenset of (home, away), date order."""
    per = defaultdict(list)
    for fk in d["fixtures"]:
        if len(fk) != 6:
            continue
        c, year, stage, date, home, away = fk
        if c == comp:
            per[(year, stage)].append((date, home, away))
    out = {}
    for key, fx in per.items():
        rs, cur, seen = [], set(), set()
        for _date, home, away in sorted(fx, key=lambda f: (tuple(int(x) for x in f[0].split(".")), f[1], f[2])):
            if home in seen or away in seen:
                rs.append(frozenset(cur))
                cur, seen = set(), set()
            cur.add((home, away))
            seen |= {home, away}
        rs.append(frozenset(cur))
        out[key] = rs
    return out


def recompute_faults(runs, comp):
    """runs: [(tag, d)]: A stock, B judged, C (when given) stock again. Prints the recount faults per run and the judged
    deduction map (stock A and C, or A alone); returns ok."""
    ok, ded = True, {}
    for tag, d in runs:
        faults, ded[tag] = recount(d, comp)
        print("recompute %s: %d fault(s)" % (tag, len(faults)))
        for fault in faults:
            print(fmt_recount(tag, fault))
        ok &= not faults
    tags = [t for t, _d in runs]
    other = ded[tags[2]] if len(tags) == 3 else ded[tags[0]]
    return deduction_report(ded[tags[0]], other, ded[tags[1]]) == 0 and ok


def calendar(A, B, comp):
    ra, rb = rounds(A, comp), rounds(B, comp)
    ok = True
    for key in sorted(set(ra) | set(rb)):
        a, b = ra.get(key, []), rb.get(key, [])
        same_pairs = set().union(*a) == set().union(*b) if a and b else False
        same = [i for i in range(min(len(a), len(b))) if a[i] == b[i]]
        print("pairs %s: rounds %d/%d, pairs %d/%d, same set %s, rounds identical %d" % (
            key, len(a), len(b), sum(map(len, a)), sum(map(len, b)), same_pairs, len(same)))
        ok &= same_pairs and len(a) == len(b) and len(same) == len(a)
    ok &= recompute_faults((("A", A), ("B", B)), comp)
    fa, fb = [Counter((y, v) for (c, y, _t), v in fates_of(d).items() if c == comp) for d in (A, B)]
    print("fates A", sorted(fa.items()))
    print("fates B", sorted(fb.items()))
    ok &= fa == fb
    print("match" if ok else "differ")
    return 0 if ok else 1


def structure(d, comp):
    """name -> value of the competition's shape in one dump (see the module doc)."""
    ent = {(y, s): len(t) for (c, y, s), t in d["entrants"].items() if c == comp}
    rd = {k[1:]: v for k, v in d["round"].items() if k[0] == comp}  # (year, stage, round) -> fields
    st = {k[1:]: v for k, v in d["stage"].items() if k[0] == comp}
    pairs = defaultdict(set)
    for fk in d["fixtures"]:
        if fk[0] == comp:
            pairs[(fk[1], fk[2])].add(frozenset(fk[4:6]))
    nrounds = Counter((y, s) for (y, s, _r) in rd)
    groups = {k: (st[k].get("groups"), st[k].get("sizes")) for k in st if st[k].get("kind") == "group"}
    return {
        "entrants": ent,
        "new by round": {k: v["new"] for k, v in rd.items()},
        "round count": dict(nrounds),
        "legs": {k: v["legs"] for k, v in rd.items()},
        "replays": {k: v["replays"] for k, v in rd.items()},
        "byes": {k: v["byes"] for k, v in rd.items()},
        "groups": groups,
        "advance": {k[1:]: v for k, v in d["advance"].items() if k[0] == comp},
        "pairs seen": {k: frozenset(v) for k, v in pairs.items()},
    }


def structure_comps(*ds):
    out = set()
    for d in ds:
        for sec in ("entrants", "stage", "round", "advance"):
            out |= {k[0] for k in d[sec]}
    return sorted(out)


def compare_structure(A, B, comps):
    """print each structure name per comp; True when all equal."""
    ok = True
    for comp in comps:
        sa, sb = structure(A, comp), structure(B, comp)
        for name in sa:
            same = sa[name] == sb[name]
            ok &= same
            if same:
                print("structure comp %d %s: same" % (comp, name))
            else:
                print("structure comp %d %s: differ A %s | B %s" % (comp, name, sorted(sa[name].items(), key=str), sorted(sb[name].items(), key=str)))
    print("same" if ok else "structure differs")
    return ok


def properties(A, B, comp):
    """name -> does this property hold between runs A and B of competition comp."""
    ra, rb = rounds(A, comp), rounds(B, comp)
    ea = {k: len(v) for k, v in A["entrants"].items() if k[0] == comp}
    eb = {k: len(v) for k, v in B["entrants"].items() if k[0] == comp}
    fa, fb = [Counter((y, v) for (c, y, _t), v in fates_of(d).items() if c == comp) for d in (A, B)]
    games = lambda r: {k: sum(map(len, v)) for k, v in r.items()}
    played = lambda d: Counter(t for k in d["fixtures"] if k[0] == comp for t in k[4:6])
    out = {
        "entrant counts": ea == eb,
        "games per season": games(ra) == games(rb),
        "games per team": played(A) == played(B),
        "fate kinds": {k for k in fa} == {k for k in fb},
        "fate counts": fa == fb,
        "round count": {k: len(v) for k, v in ra.items()} == {k: len(v) for k, v in rb.items()},
        "rounds identical": ra == rb,
    }
    sa, sb = structure(A, comp), structure(B, comp)
    for name in sa:
        out["structure " + name] = sa[name] == sb[name]
    for key in sorted(set(ra) | set(rb)):
        out["pairs %d/%d" % key] = bool(ra.get(key)) and bool(rb.get(key)) and set().union(*ra[key]) == set().union(*rb[key])
    return out


def baseline(A, B, C, comp):
    stock, hosted = properties(A, C, comp), properties(A, B, comp)
    ok = True
    for name in sorted(stock):
        if not stock[name]:
            print("%-20s stock varies, not judged (hosted %s)" % (name, "same" if hosted.get(name) else "differs"))  # a key only C has: absent from hosted
            continue
        print("%-20s stock keeps it, hosted %s" % (name, "keeps it" if hosted[name] else "BREAKS it"))
        ok &= hosted[name]
    ok &= recompute_faults((("A", A), ("B", B), ("C", C)), comp)
    print("match" if ok else "differ")
    return 0 if ok else 1


def keep(key, comp):
    return comp is None or key[0] == comp


def diff_maps(name, a, b, comp, fmt, out):
    n = 0
    for k in sorted(set(a) | set(b)):
        if not keep(k, comp):
            continue
        if k not in b:
            out.append("%s only in A %s: %s" % (name, k, fmt(a[k])))
            n += 1
        elif k not in a:
            out.append("%s only in B %s: %s" % (name, k, fmt(b[k])))
            n += 1
        elif a[k] != b[k]:
            out.append("%s differ %s: A %s | B %s" % (name, k, fmt(a[k]), fmt(b[k])))
            n += 1
    return n


def splice(path, side):
    """T47.c2 --side: the lines of data file `path` with `side`'s records spliced over them as the DLL does (comphost.c:199-243
    comphost_data_read): the first record of `path` whose uid a side record has is replaced by the first side record of that uid
    (at most 16); every other line (a later record of the same uid, `comp eur_access 0`, ..) stays. side None: the file's lines."""
    with open(path, encoding="utf-8") as f:
        base = f.read().splitlines(True)
    if side is None:
        return base
    with open(side, encoding="utf-8") as f:
        sl = f.read().splitlines(True)

    def uid(line):  # comphost.c rec_uid: `comp <class> <uid> ..` -> uid, else -1
        t = line.split(" ")
        return int(re.match(r"\d*", t[2]).group() or -1) if line.startswith("comp ") and len(t) > 2 and t[2][:1].isdigit() else -1

    def rec(lines, at):  # comphost.c rec_end: the record's lines from its comp line through its `end` line
        e = at
        while e < len(lines):
            e += 1
            if lines[e - 1].rstrip("\r\n") == "end":
                break
        return lines[at:e]
    srec = {}
    for i, line in enumerate(sl):
        if uid(line) >= 0:
            srec.setdefault(uid(line), i)
    out, used, at = [], [], 0
    while at < len(base):
        u = uid(base[at])
        if u >= 0 and u not in used and len(used) < 16 and u in srec:
            r = rec(sl, srec[u])
            out += r[:-1] + [r[-1] if r[-1].endswith("\n") else r[-1] + "\n"]
            used.append(u)
            at += len(rec(base, at))
            continue
        out.append(base[at])
        at += 1
    return out


def rec_lines(path):
    """a data file's lines: `path` a file name, or the spliced lines themselves (T47.c2)."""
    if isinstance(path, list):
        return path
    with open(path, encoding="utf-8") as f:
        return f.read().splitlines(True)


def record_rounds(path, comp):
    """{stage: [(round k, {field: int})]} of the knockout stages of record `comp <class> <comp>` in a data file (T17)."""
    out, cur, inrec = {}, None, False
    for line in rec_lines(path):
        tok = line.split()
        if not tok:
            continue
        if tok[0] == "comp" and len(tok) > 2:
            inrec, cur = tok[2] == str(comp), None
        elif not inrec:
            continue
        elif tok[0] == "end":
            inrec = False
        elif tok[0] == "stage":
            cur = out.setdefault(int(tok[1]), {}) if tok[2] == "knockout" else None
        elif tok[0] == "round" and cur is not None and len(tok) > 3:
            try:
                cur.setdefault(int(tok[1]), {})[tok[2]] = int(tok[3])
            except ValueError:
                cur.setdefault(int(tok[1]), {})
    return {s: sorted(r.items()) for s, r in out.items()}


def check_record(d, path, comp):
    """T17: the dump's comp against the record's knockout stages: round count, teams and legs per round, entrants of
    the stage = the record's round 0 teams + the later rounds' `entry` lines (T34.c4). Prints each check and each difference; True when none differs. The dump has no
    round names: their order is printed from the record, not checked."""
    rec = record_rounds(path, comp)
    if not rec:
        print("record: no knockout stage for comp %d in %s" % (comp, "the spliced record" if isinstance(path, list) else path))
        return False
    bad = 0
    for s, rounds in sorted(rec.items()):
        print("record stage %d: %d rounds, names %s (the dump has no round names: not checked)" % (
            s, len(rounds), " ".join(str(f.get("name", "-")) for _, f in rounds)))
        years = sorted(y for (c, y, st) in d["stage"] if c == comp and st == s)
        if not years:
            print("differ stage %d: no stage line in the dump" % s)
            bad += 1
        for y in years:
            got = {k[3]: v for k, v in d["round"].items() if k[:3] == (comp, y, s)}
            st = d["stage"][(comp, y, s)]
            diffs = []
            if len(got) != len(rounds) or int(st.get("rounds", -1)) != len(rounds):
                diffs.append("round count record %d | dump %d round lines, stage rounds=%s" % (len(rounds), len(got), st.get("rounds")))
            for k, f in rounds:
                g = got.get(k, {})
                for name, dn in (("teams", "teams"), ("legs", "legs")):
                    if f.get(name) != g.get(dn):
                        diffs.append("round %d %s record %s | dump %s" % (k, name, f.get(name), g.get(dn)))
            t0 = rounds[0][1].get("teams") if rounds else None
            # T34.c4: later rounds' new entrants (the record's `round <k> entry` lines) join the stage too
            later = sum(f.get("entry") or 0 for _, f in rounds[1:])
            want = t0 + later if t0 is not None else None
            ent = d["entrants"].get((comp, y, s))
            n, src = (len(ent), "entrants") if ent is not None else (int(st.get("teams", -1)), "stage teams=")
            if n != want:
                diffs.append("entrants record round 0 teams %s + later entries %d | dump %s %d" % (t0, later, src, n))
            for x in diffs:
                print("differ stage %d year %d: %s" % (s, y, x))
            print("stage %d year %d: %s (%d rounds, teams %s, legs %s, entrants from %s)" % (
                s, y, "same" if not diffs else "%d difference(s)" % len(diffs), len(got),
                ",".join(str(got[k].get("teams")) for k in sorted(got)), ",".join(str(got[k].get("legs")) for k in sorted(got)), src))
            bad += len(diffs)
    print("same" if not bad else "%d difference(s)" % bad)
    return not bad


# ---- --rules / --roll (T29.c6). Every rule reads a record statement or names the traced code it follows; the line kinds and
# rule sources: docs/ops/comp_data.md "Rules dump lines (T29.c6)".

RULE_COMPS = (1301394, 1301396, 31051584)
# T47.c2: the extra rebalancing draw's route (comphost_generic.c:1219-1220 QD_ROUTE xd 1 / 2; docs/ops/uefa_access.md:60, :68-70):
# CL stage 0 round 0 (CP Q1) losers -> UECL stage 1 round 0 (CP Q2), 16 - C of them (C = the round's ties) -> round 1 (CP Q3).
# (source uid, stage, round, target uid, stage, round xd 1, round xd 2)
XD = (1301394, 0, 0, 31051584, 1, 0, 1)
FAMILIES = ((1, "entrants"), (2, "qualifying"), (3, "draw"), (4, "fixtures"), (5, "split"), (6, "standings"), (7, "playoff"),
            (8, "second_leg"), (9, "bracket"), (10, "tie_rule"), (11, "prizes"))
META = ("status=", "src=", "name=", "note=")
CLUB_BLOCK = 5  # FM07 club +0x1A4 block: 5 season entries s32 x1000 (fm07_comp_contract.md:610); the record's club_ring 10 is FM27's ring
TOL = 1e-3


def rec_tokens(line):
    try:
        tok = shlex.split(line)
    except ValueError:
        tok = line.split()
    return [t for t in tok if not t.startswith(META)]


def to_int(v, default=None):
    try:
        return int(v, 0)
    except (TypeError, ValueError):
        return default


def read_rules(path, comps):
    """(access, {uid: record}) of a data file: the `comp eur_access 0` record and the records of uids `comps`.
    record: stages {i: {kind, teams, rounds {k: {field: values}}, bracket {k: {tie: (hkind, href, akind, aref)}}, f, phase, league}},
    fates [(stage, type, who, round name, {k: v})], entry {seed: (stage, kind, value)}, coeff [values], chain [(stage, src, lo, hi)]."""
    acc = {"bands": defaultdict(list), "totals": {}, "no_rank": set(), "special_row": {}, "rule": {}, "eps": 0, "league_order": {},
           "holder": set()}
    recs, cur, st, league = {}, None, None, False
    for line in rec_lines(path):
        head = line.split(None, 3)
        if not head:
            continue
        if head[0] == "comp" and len(head) > 2:
            cur = "acc" if head[1] == "eur_access" else to_int(head[2]) if to_int(head[2]) in comps else None
            if cur not in (None, "acc") and cur in recs:
                cur = None  # the first record of a uid (as compseed / compcoef read it)
            elif cur not in (None, "acc"):
                recs[cur] = {"stages": {}, "fates": [], "entry": {}, "coeff": [], "chain": []}
            st, league = None, False
            continue
        if cur is None:
            continue
        if head[0] == "end":
            cur = None
            continue
        tok = rec_tokens(line)
        if cur == "acc":
            read_access(acc, tok, line)
            continue
        r = recs[cur]
        k0 = tok[0]
        if k0 == "stage" and len(tok) > 3:
            st = r["stages"].setdefault(int(tok[1]), {"kind": tok[2], "teams": to_int(tok[3]), "rounds": defaultdict(dict),
                                                      "bracket": defaultdict(dict), "f": [], "phase": defaultdict(list), "league": {}})
            league = False
        elif k0 == "league" and len(tok) == 2:
            league = True
        elif k0 == "fate" and len(tok) > 5 and to_int(tok[1]) is not None and tok[4] == "round":
            r["fates"].append((int(tok[1]), to_int(tok[2]), tok[3], to_int(tok[5]), dict(t.split("=", 1) for t in tok[6:] if "=" in t)))
        elif k0 == "entry" and len(tok) > 3:  # T47.c2: `entry <key> stage <s>` (no round) too
            r["entry"][int(tok[1])] = (int(tok[3]), tok[4] if len(tok) > 4 else None, to_int(tok[5]) if len(tok) > 5 else None)
        elif k0 == "coeff":
            r["coeff"].append(tok[1:])
        elif k0 == "chain" and len(tok) > 5 and tok[2] == "ranks":
            r["chain"].append(tuple(int(x) for x in (tok[1], tok[3], tok[4], tok[5])))
        elif st is None:
            continue
        elif k0 == "round" and len(tok) > 3:
            k = int(tok[1])
            if tok[2] == "bracket" and len(tok) >= 10:
                st["bracket"][k][int(tok[3])] = (tok[5], to_int(tok[6]), tok[8], to_int(tok[9]))
            else:
                st["rounds"][k][tok[2]] = tok[3:]
        elif k0 == "phase" and len(tok) > 1:
            st["phase"][tok[1]].append(tok[2:])
        elif k0 == "f":
            st["f"].append(tok[1:])
        elif league and len(tok) >= 2:
            st["league"][k0] = tok[1]
    return acc, recs


def read_access(acc, tok, line):
    k0 = tok[0]
    if k0 == "access" and len(tok) > 3 and tok[2] == "ranks":
        lo, hi = (int(x) for x in tok[3].split("-"))
        acc["bands"][int(tok[1])].append((lo, hi, {a: int(b) for a, b in (t.split("=") for t in tok[4:] if "=" in t)}))
    elif k0 == "access" and len(tok) > 2 and tok[2] == "totals":
        acc["totals"][int(tok[1])] = [(a, int(b)) for a, b in (t.split("=") for t in tok[3:] if "=" in t)]
    elif k0 == "special" and len(tok) > 2 and tok[2] == "no_rank":
        acc["no_rank"].add(int(tok[1]))
    elif k0 == "special" and len(tok) > 3 and tok[2] == "row":
        acc["special_row"][(int(tok[1]), int(tok[3]))] = {a: int(b) for a, b in (t.split("=") for t in tok[4:] if "=" in t)}
    elif k0 == "coeff_rule" and len(tok) > 2:
        acc["rule"][tok[1]] = tok[2:]
    elif k0 == "slot" and len(tok) > 3 and tok[1] == "league_order":
        acc["league_order"][int(tok[2])] = [int(x) for x in tok[3:]]
    elif k0 == "slot" and len(tok) > 2 and tok[1] == "holder":
        acc["holder"].add(int(tok[2]))
    elif k0 == "regulation" and len(tok) > 2 and tok[1] == "eps":
        m = re.search(r"(\d+) associations per season", tok[2])  # compseed.c:44 EPS_COUNT reads the same statement
        acc["eps"] = int(m.group(1)) if m else 0


def round_name(st, k):
    v = st["rounds"].get(k, {}).get("name")
    return to_int(v[0]) if v else None


def round_int(st, k, field):
    v = st["rounds"].get(k, {}).get(field)
    return to_int(v[0]) if v else None


def phase_kv(st, kind, sub):
    """the `phase <kind> <sub> ..` line as {word: the token after it} (`phase draw association own 0 other 2` -> own 0, other 2)."""
    for v in st["phase"].get(kind, []):
        if v and v[0] == sub:
            return {v[i]: v[i + 1] for i in range(len(v) - 1)}, v
    return None, None


def seed_path(name):
    """the access list's seed names (record `access <uid> totals`): CH.. champions path, NC.. league path, the rest main."""
    return "champions" if name.startswith("CH") else "league" if name.startswith("NC") else "main"


def fate_comp(rec, fs, _ftype, who, rn, kvf):
    """a type-51 fate's target comp: its comp=, else that of the record's raw `fate <fs> 58 <who> round <rn> comp=..` twin (the
    same ftac entry; UEL `fate 0 51 0 round 151 stag=2` has comp=1301396 only there)."""
    c = to_int(kvf.get("comp"))
    if c is None:
        c = next((to_int(f[4].get("comp")) for f in rec["fates"] if f[:4] == (fs, 58, who, rn) and "comp" in f[4]), None)
    return c


class Season:
    """one comp, one year of a dump, with its record."""

    def __init__(self, d, comp, year, rec, acc, recs=None):
        self.d, self.comp, self.year, self.rec, self.acc = d, comp, year, rec, acc
        self.spliced = False  # T47.c2: --side given (check_rules sets it)
        self.recs = recs or {comp: rec}  # T37.c2: the transfer sources' records (their fates name the target stage)
        self.lp = next((i for i, s in sorted(rec["stages"].items()) if s["kind"] == "league_phase"), None)
        self.ties = {}  # (stage, round, tie) -> dict
        for c, y, s, kv in d["rules"]["tie"]:
            if c == comp and y == year:
                t = {k: to_int(v, v) for k, v in kv.items()}
                self.ties[(s, t["round"], t["tie"])] = t
        self.cup = defaultdict(list)  # (stage, round, tie) -> [fixture dict]
        self.league = defaultdict(list)  # stage -> [(date, home, away, hg, ag)]
        for fk, score in d["fixtures"].items():
            if fk[0] != comp or fk[1] != year:
                continue
            hg, ag = (int(x) for x in score.split("-"))
            if len(fk) == 10:
                self.cup[(fk[2], fk[6], fk[7])].append({"date": fk[3], "home": fk[4], "away": fk[5], "leg": fk[8], "replay": fk[9],
                                                        "hg": hg, "ag": ag, "raw": d["raw"].get(fk)})
            else:
                self.league[fk[2]].append((fk[3], fk[4], fk[5], hg, ag))
        tb = d["table"].get((comp, year, self.lp), {}) if self.lp is not None else {}
        self.rank = [tb[p]["team"] for p in sorted(tb)]  # rank order (0-based), the dumped table
        self.done = {s: self.stage_done(s) for s in rec["stages"]}  # T30.8.c5: stages judged; the rest in progress

    def stage_done(self, s):
        """T30.8.c5: stage s is complete when the dump has moved past it (a later stage of this comp and year has fixtures or
        tie lines, or the comp has fixtures of a later year), or its own end is in: knockout, the last round's record ties all
        decided (tie lines with a winner) or all their legs played by the dump's now=; league phase, every plan pair played.
        Other kinds: complete. Not complete = in progress, not judged; a complete stage with missing lines still breaks."""
        if any(fk[0] == self.comp and fk[1] > self.year for fk in self.d["fixtures"]):
            return True
        if any(s2 % 1000 > s for s2 in set(self.league) | {k[0] for k in self.cup} | {k[0] for k in self.ties}):
            return True
        st = self.rec["stages"][s]
        if st["kind"] == "league_phase":
            plan = st["phase"].get("plan", [])
            want = sum(1 for v in plan for x in v[1:] if to_int(x, 0) > 0)
            return bool(want) and len(self.league.get(s, [])) >= want
        if st["kind"] != "knockout":
            return True
        if not st["rounds"]:
            return False
        k = max(st["rounds"])
        n, legs = round_int(st, k, "ties"), round_int(st, k, "legs") or 1
        if not n:
            return False
        won = [t for t in self.round_ties(s, k) if self.winner(s, k, t) is not None]
        now = dkey(self.d["now"]) if self.d["now"] else None
        played = [f for t in range(n) for f in self.cup.get((s, k, t), []) if not f["replay"] and now and dkey(f["date"]) <= now]
        return len(won) >= n or len(played) >= n * legs

    def lines(self, sec):
        return [(s, kv) for c, y, s, kv in self.d["rules"][sec] if c == self.comp and y == self.year]

    def winner(self, s, k, t):
        tie = self.ties.get((s, k, t))
        return tie.get("winner") if tie else None

    def loser(self, s, k, t):
        tie = self.ties.get((s, k, t))
        return None if not tie else tie["b"] if tie.get("winner") == tie["a"] else tie["a"]

    def round_ties(self, s, k):
        return sorted(t for (s2, k2, t) in self.ties if (s2, k2) == (s, k))

    def chain_ranks(self, s):
        """stage s team index -> league rank (1-based): the record's `chain <s> ranks <src> <lo> <hi>` lines in order (the
        list FM07 builds the stage from; comp_data.md:625 reads the bracket's team index the same way)."""
        out = []
        for st, _src, lo, hi in self.rec["chain"]:
            if st == s:
                out += list(range(lo, hi + 1))
        return out

    def team_at(self, s, n):
        """stage s team index n -> team as the record lists it (chain ranks -> the dumped table), no draw."""
        cr = self.chain_ranks(s)
        return self.rank[cr[n] - 1] if n is not None and n < len(cr) and cr[n] - 1 < len(self.rank) else None

    def bracket_pairs(self, s):
        """T30.8.c1: the regulation draw's pairs on stage s's bracket (as complg_bracket_pairs; UEFA CL / UEL Regulations
        2026/27 Art 19.02, 19.03): per round, a tie's key = the rank of its seeded side (both sides `team`: the away side, the
        home side drawn; one `team` and one `tie`: the team side, drawn itself); ties keyed k and k + 1 (k the lowest unpaired)
        pair up. [(round, (tie a, tie b), (team index a, team index b))]."""
        st, cr, out = self.rec["stages"].get(s), self.chain_ranks(s), []
        for k, br in sorted((st or {}).get("bracket", {}).items()):
            keyed = []
            for t, (hk, h, ak, a) in sorted(br.items()):
                if hk == "team" and ak == "team":
                    seeded, d = a, h
                elif hk == "team" and ak == "tie":
                    seeded = d = h
                elif ak == "team" and hk == "tie":
                    seeded = d = a
                else:
                    continue
                if seeded is not None and d is not None and seeded < len(cr) and d < len(cr):
                    keyed.append((cr[seeded], t, d))
            keyed.sort()
            i = 0
            while i + 1 < len(keyed):
                if keyed[i + 1][0] == keyed[i][0] + 1:
                    out.append((k, (keyed[i][1], keyed[i + 1][1]), (keyed[i][2], keyed[i + 1][2])))
                    i += 2
                else:
                    i += 1
        return out

    def drawn(self, s):
        """T30.8.c1: team index -> team index after the draw the dump shows: a pair counts as swapped when tie a holds team b's
        team and tie b team a's; nothing else moves (a half swap stays unswapped and breaks the family)."""
        if not hasattr(self, "_drawn"):
            self._drawn = {}
        if s not in self._drawn:
            perm = {}
            for k, (ta, tb), (ia, ib) in self.bracket_pairs(s):
                xa, xb = self.ties.get((s, k, ta)), self.ties.get((s, k, tb))
                if xa and xb and self.team_at(s, ib) in (xa["a"], xa["b"]) and self.team_at(s, ia) in (xb["a"], xb["b"]):
                    perm[ia], perm[ib] = ib, ia
            self._drawn[s] = perm
        return self._drawn[s]

    def side(self, s, k, ref):
        """a bracket side (kind, n) -> team: `team i` the stage's team i (chain ranks -> the dumped table) after the within-pair
        draw (drawn), `tie n` the winner of tie n of round k - 1."""
        kind, n = ref
        if kind == "team":
            return self.team_at(s, self.drawn(s).get(n, n))
        if kind == "tie":
            return self.winner(s, k - 1, n)
        return None

    def fated_winners(self, s):
        """stage s's arrivals from this comp's other stages: the winners of the rounds whose `fate <fs> 51 0 round <r> comp=<self>
        stag=<s>` sends them there."""
        out = set()
        for fs, ftype, who, rn, kvf in self.rec["fates"]:
            if fs != s and ftype == 51 and who == "0" and fate_comp(self.rec, fs, ftype, who, rn, kvf) == self.comp and to_int(kvf.get("stag")) == s:
                st = self.rec["stages"].get(fs, {"rounds": {}})
                for k in [k for k in st["rounds"] if round_name(st, k) == rn]:
                    out |= {self.winner(fs, k, t) for t in self.round_ties(fs, k)}
        return out - {None}

    def fated_transfers(self, s):
        """the teams of `transfer .. to=<self>` lines whose source record's `fate <fs> 51 1 round <r> comp=<self> stag=<s>` (fs, r
        = the line's head stage and round name) sends them to stage s; a transfer without such a fate is not counted."""
        out = set()
        for c, y, fs, kv in self.d["rules"]["transfer"]:
            src = self.recs.get(c)
            if y != self.year or to_int(kv.get("to")) != self.comp or not src or fs not in src["stages"]:
                continue
            rn = round_name(src["stages"][fs], int(kv["round"]))
            if any(f[0] == fs and f[1] == 51 and f[2] == "1" and f[3] == rn and fate_comp(src, *f) == self.comp
                   and to_int(f[4].get("stag")) == s for f in src["fates"]):
                out.add(int(kv["team"]))
        return out


def fam_entrants(S):
    p, acc = [], S.acc
    tot = acc["totals"].get(S.comp)
    seats = S.lines("seat")
    if not tot:
        return ["record: no `access %d totals` line" % S.comp]
    if not seats:
        return ["dump: no seat lines"]
    names = [n for n, _ in tot]
    cnt = Counter(kv["seed"] for _, kv in seats)
    for name, n in ([] if S.spliced else tot):  # `access totals` (T33: FM27's per-seed counts after the fix-up)
        if cnt.get(name, 0) != n:
            p.append("seed %s: %d seat(s), record totals %d" % (name, cnt.get(name, 0), n))
    if S.spliced:
        p += held_seats(S, names, cnt)
    for name in sorted(set(cnt) - set(names)):
        p.append("seed %s is not in the record's totals line" % name)
    for team, n in sorted(Counter(int(kv["team"]) for _, kv in seats).items()):
        if n > 1:
            p.append("team %d seated %d times" % (team, n))
    for s, kv in seats:
        name = kv["seed"]
        if name not in names:
            continue
        e = S.rec["entry"].get(names.index(name))  # `entry <seed index> stage <s> round <name> | rank_level`
        st = S.rec["stages"].get(s)
        if e is None:
            p.append("seed %s (index %d) has no entry line" % (name, names.index(name)))
        elif s != e[0]:
            p.append("team %s seed %s seated in stage %d, entry line stage %d" % (kv["team"], name, s, e[0]))
        elif e[1] == "round" and (st is None or round_name(st, int(kv["round"])) != e[2]):
            p.append("team %s seed %s seated in round %s (name %s), entry line round name %s" % (
                kv["team"], name, kv["round"], st and round_name(st, int(kv["round"])), e[2]))
        if kv.get("path") != seed_path(name):
            p.append("team %s seed %s path %s, the seed's path %s" % (kv["team"], name, kv.get("path"), seed_path(name)))
    order = acc["league_order"].get(S.comp)  # `slot league_order <uid> <seed..>`: a nation's places by domestic position
    if order:
        per = defaultdict(list)
        for _s, kv in seats:
            if int(kv.get("dpos", 0)) > 0 and kv["seed"] in names and names.index(kv["seed"]) in order:
                per[int(kv["nation"])].append((int(kv["dpos"]), order.index(names.index(kv["seed"])), kv))
        for nat, lst in sorted(per.items()):
            lst.sort(key=lambda x: x[0])
            for a, b in zip(lst, lst[1:]):
                if b[1] < a[1]:
                    p.append("nation %d: position %d has seed %s, position %d the earlier seed %s (league_order %s)" % (
                        nat, a[0], a[2]["seed"], b[0], b[2]["seed"], " ".join(map(str, order))))
    if S.lp is not None:  # the league phase: its seats plus the winners of the rounds whose `fate <s> 51 0` sends them there
        want = {int(kv["team"]) for s, kv in seats if s == S.lp} | S.fated_winners(S.lp)
        want |= S.fated_transfers(S.lp)  # T37.c2: other comps' losers whose source `fate <fs> 51 1 .. stag=<lp>` sends them here
        ent = S.d["entrants"].get((S.comp, S.year, S.lp))
        teams = S.rec["stages"][S.lp]["teams"]
        if ent is None:
            p.append("dump: no entrants line for the league phase stage %d" % S.lp)
        else:
            if set(ent) != want:
                p.append("league phase entrants %s, seats + qualifiers %s" % (sorted(ent), sorted(want)))
            if teams is not None and len(ent) != teams:
                p.append("league phase entrants %d, record stage teams %d" % (len(ent), teams))
    return p


def inflow(S, s, rn):
    """T47.c2: teams the spliced record routes into stage s round name rn (None: a stage entry without a round, e.g. rank_level)
    besides its seeds: (losers, winners). losers: per loaded source record's `f fate.cup_continental <name> 1 <self> <key>`
    whose key's `entry` line here is (s, rn), that round's ties (the XD route: 16 - C of the CP Q2 key's to the extra key's
    round); winners: this comp's `fate <fs> 51 0 round <name> .. stag=<s>` (fs != s), that round's ties, into s's first round."""
    los = win = 0
    want = ("round", rn) if rn is not None else None
    xk = xd_key(S) if S.comp == XD[3] else None
    for uid, src in sorted(S.recs.items()):
        if uid == S.comp:
            continue
        for fs, st in sorted(src["stages"].items()):
            for f in st["f"]:
                if f[0] != "fate.cup_continental" or len(f) < 5 or f[2] != "1" or to_int(f[3]) != S.comp:
                    continue
                e = S.rec["entry"].get(to_int(f[4]))
                ks = [k for k in st["rounds"] if round_name(st, k) == to_int(f[1])]
                if e is None or not ks:
                    continue
                n = round_int(st, ks[0], "ties") or 0
                if xk and (uid, fs, ks[0]) == XD[:3] and to_int(f[4]) == xk[0]:
                    n -= 16 - xk[2]
                if e[0] == s and (e[1:] == want if want else e[1] != "round"):
                    los += n
    if xk and s == XD[4] and rn == round_name(S.rec["stages"][s], XD[6]):
        los += 16 - xk[2]
    st = S.rec["stages"].get(s)
    first = round_name(st, min(st["rounds"])) if st and st["rounds"] else None
    if rn == first:
        for fs, ftype, who, frn, kvf in S.rec["fates"]:
            if fs != s and ftype == 51 and who == "0" and fate_comp(S.rec, fs, ftype, who, frn, kvf) == S.comp and to_int(kvf.get("stag")) == s:
                fst = S.rec["stages"].get(fs, {"rounds": {}})
                win += sum(round_int(fst, k, "ties") or 0 for k in fst["rounds"] if round_name(fst, k) == frn)
    return los, win


def held_seats(S, names, cnt):
    """T47.c2 (--side, uefa_access.md:44-58): the seeds' seats against the spliced record's held shape, the seeds of one entry
    round together: its own window `entry - transfers` (a stage entry without a round: the stage's teams); a round with no
    transfers reserve counts the losers routed to it inside its entry (count_check, compseed.c:2615-2619), and a stage's first
    round the winners its other stages send there. Seeds without an entry line: 0 seats."""
    p, grp = [], defaultdict(list)
    for i, name in enumerate(names):
        e = S.rec["entry"].get(i)
        if e is None:
            if cnt.get(name, 0):
                p.append("seed %s: %d seat(s), no entry line in the record" % (name, cnt[name]))
            continue
        grp[(e[0], e[2] if e[1] == "round" else None)].append(name)
    for (s, rn), ns in sorted(grp.items(), key=lambda x: (x[0][0], x[0][1] is not None, x[0][1] or 0)):
        st = S.rec["stages"].get(s)
        ks = [k for k in (st or {"rounds": {}})["rounds"] if round_name(st, k) == rn] if rn is not None else []
        cap = round_int(st, ks[0], "entry") if ks else st and st["teams"] if rn is None else None
        if cap is None or cap < 0:
            p.append("seeds %s (stage %d round %s): the record gives no seat count" % (",".join(ns), s, rn))
            continue
        tr = min(round_int(st, ks[0], "transfers") or 0, cap) if ks else 0
        los, win = inflow(S, s, rn)
        want = cap - (tr if tr else los) - win
        got = sum(cnt.get(n, 0) for n in ns)
        if got != want:
            p.append("seeds %s (stage %d round %s): %d seat(s), record entry %d - transfers %d - losers inside %d - winners %d = %d" % (
                ",".join(ns), s, rn, got, cap, tr, 0 if tr else los, win, want))
    return p


def tie_legs(S, s, k, st, p):
    legs = round_int(st, k, "legs")
    for t in S.round_ties(s, k):
        n = len([f for f in S.cup[(s, k, t)] if not f["replay"]])
        if legs is not None and n != legs:
            p.append("stage %d round %d tie %d: %d fixture(s), record legs %d" % (s, k, t, n, legs))


def sim_seated(st, lst):
    """T30.8.c5: comphost_generic.c build_seated (:523-577) on lst [(team, seat round)] in list order: team -> round (None: no
    seat). Round k's own window = its record `entry` minus its `transfers` reserve (complg_round_entries); first each team into
    its seat round's window, then the rest in list order into the first free seat of the earliest window. None = no seated build
    (a round 0..n-1 without an entry line, or record seats < list, :529-541: the stage is built from the list as before)."""
    n = max((k + 1 for k in st["rounds"] if round_int(st, k, "entry") is not None), default=0)
    ent = [round_int(st, k, "entry") for k in range(n)]
    first = {}
    for t, r in lst:  # a team once, its first seat line
        first.setdefault(t, r)
    lst = list(first.items())
    if not n or None in ent:
        return None
    own = [e - min(round_int(st, k, "transfers") or 0, e) for k, e in enumerate(ent)]
    g = st["teams"] if st["teams"] and st["teams"] > 0 else sum(ent)
    if g < len(lst):
        return None
    at = [sum(ent[:k]) for k in range(n)]
    seat, out = set(), {}
    for team, r in lst:
        if 0 <= r < n:
            x = next((x for x in range(at[r], min(at[r] + own[r], g)) if x not in seat), None)
            if x is not None:
                seat.add(x)
                out[team] = r
    k = x = w = 0
    for team, _r in lst:
        if team in out:
            continue
        while k < n and (x >= w + own[k] or x >= g or x in seat):
            if x >= w + own[k] or x >= g:
                w += ent[k]
                k += 1
                x = w
            else:
                x += 1
        out[team] = k if k < n else None
        if k < n:
            seat.add(x)
            x += 1
    return out


def fam_qualifying(S):
    p = []
    stages = [(s, st) for s, st in sorted(S.rec["stages"].items()) if st["kind"] == "knockout" and not st["bracket"]
              and S.done[s]]  # T30.8.c5: complete stages only
    if stages and not any(s2 == s for s, _st in stages for (s2, _k, _t) in S.ties):
        p.append("dump: no tie lines of the qualifying stages %s" % ",".join(str(s) for s, _ in stages))
    seats = S.lines("seat")
    moved_in = {int(kv["team"]) for c, y, s, kv in S.d["rules"]["transfer"]
                if y == S.year and to_int(kv.get("to")) == S.comp}
    want_tr = set()
    for s, st in stages:
        # T37.c2: `bye` lines are written at the stage build (compdump.c:310), before the draw: a seat whose tie's other side is a
        # feeder shows as a bye. A bye counts only when its team then plays no tie of that round.
        byes = defaultdict(set)
        for (c, y, bs, r, _t, team) in S.d["bye"]:
            if (c, y, bs) == (S.comp, S.year, s):
                byes[r].add(team)
        seat_rd = {int(kv["team"]): int(kv["round"]) for s2, kv in seats if s2 == s}
        arrive = S.fated_winners(s)  # T37.c2: winners another stage's `fate 51 0 .. stag=<s>` sends here
        prev, fresh, first = set(), defaultdict(set), {}  # fresh[k]: round k's new teams; first[team]: the round it entered
        for k in sorted(st["rounds"]):
            here = {t for t, r in seat_rd.items() if r == k} | prev
            ts = S.round_ties(s, k)
            n = round_int(st, k, "ties")
            if n is not None and len(ts) != n and (ts or here):
                p.append("stage %d round %d: %d tie(s), record ties %d" % (s, k, len(ts), n))
            played = Counter()
            for t in ts:
                tie = S.ties[(s, k, t)]
                for side in (tie["a"], tie["b"]):
                    played[side] += 1
                    if side in prev:
                        continue
                    if side not in seat_rd and side not in arrive and side not in moved_in:
                        p.append("stage %d round %d tie %d: team %d is neither seated, a winner of the round before, an arrival "
                                 "(fate 51 0) nor transferred in" % (s, k, t, side))
                    elif side in first:
                        p.append("stage %d round %d tie %d: team %d enters a second time (first round %d)" % (s, k, t, side, first[side]))
                    else:
                        fresh[k].add(side)
                        first[side] = k
            for team, m in played.items():
                if m > 1:
                    p.append("stage %d round %d: team %d in %d ties" % (s, k, team, m))
            bye = {t for t in byes[k] - set(played) if t in prev or (seat_rd.get(t) == k and t not in first)}  # present, no tie
            for t in bye - prev:
                fresh[k].add(t)
                first.setdefault(t, k)
            for team in sorted(prev - set(played) - bye):
                p.append("stage %d round %d: team %d won the round before but is in no tie and no bye" % (s, k, team))
            e = round_int(st, k, "entry")
            if e is not None and (ts or fresh[k]) and len(fresh[k]) != e:
                p.append("stage %d round %d: %d new team(s), record entry %d" % (s, k, len(fresh[k]), e))
            tie_legs(S, s, k, st, p)
            nw = round_int(st, k, "next_winners")
            prev = ({S.winner(s, k, t) for t in ts} | bye) if nw in (None, -1) else set()
            for fargs in st["f"]:  # `f fate.cup_continental <round name> <who 0 winners|1 losers> <comp> <key>` (00cb7a30)
                if fargs[0] != "fate.cup_continental" or len(fargs) < 5 or to_int(fargs[1]) != round_name(st, k):
                    continue
                for t in ts:
                    team = S.loser(s, k, t) if fargs[2] == "1" else S.winner(s, k, t)
                    want_tr.add((s, k, team, int(fargs[3]), int(fargs[4])))
        # the seat line's round is its seed's entry (compseed_entry_index); FM27's access totals can exceed that round's
        # comps.dbc entry, and the mod seats the excess elsewhere: T30.8.c5 simulates build_seated on the seat lines in list order;
        # T30.8.c7: on the stage's `build_list` lines when the dump has them (the list build_seated read, in its order)
        bl = sorted((int(kv["i"]), int(kv["team"]), int(kv["round"])) for s2, kv in S.lines("build_list") if s2 == s)
        sim = sim_seated(st, [(t, r) for _i, t, r in bl] if bl else
                         [(int(kv["team"]), int(kv["round"])) for s2, kv in seats if s2 == s])
        for team, r in sorted(seat_rd.items()):
            if team not in first:
                p.append("stage %d: team %d seated (round %d) but in no tie and no bye" % (s, team, r))
            elif sim is None and first[team] != r:
                p.append("stage %d: team %d seated in round %d enters in round %d (record entries give no seated build)" % (
                    s, team, r, first[team]))
            elif sim is not None and first[team] != sim.get(team):
                p.append("stage %d: team %d seated in round %d enters in round %d, build_seated puts it in round %s" % (
                    s, team, r, first[team], sim.get(team)))
    got = {(s, int(kv["round"]), int(kv["team"]), int(kv["to"]), int(kv["key"])) for s, kv in S.lines("transfer")
           if S.done.get(s, True)}
    got -= extra_draw(S, want_tr, got, p)
    for x in sorted(want_tr - got):
        p.append("stage %d round %d: team %d should move to comp %d key %d (record fate.cup_continental): no such transfer line" % x)
    for x in sorted(got - want_tr):
        p.append("stage %d round %d: transfer of team %d to comp %d key %d has no record fate.cup_continental for it" % x)
    return p


def xd_key(S):
    """T47.c2: (the CP Q2 key, the extra draw's key, C) or None: the XD source round's `f fate.cup_continental <name> 1 <UECL> <key>`
    (key = the CP Q2 seat), C its ties; the extra key = the target record's one `entry <key> stage <s> round <name>` on the round
    after the CP Q2 round, a key that is not one of its access seeds. Not exactly one such key (or no record): None."""
    src, tgt = S.recs.get(XD[0]), S.recs.get(XD[3])
    st = src and src["stages"].get(XD[1])
    if not st or not tgt or XD[4] not in tgt["stages"]:
        return None
    rn, c = round_name(st, XD[2]), round_int(st, XD[2], "ties")
    keys = [int(f[4]) for f in st["f"] if f[0] == "fate.cup_continental" and len(f) >= 5 and to_int(f[1]) == rn and f[2] == "1"
            and to_int(f[3]) == XD[3]]
    tst = tgt["stages"][XD[4]]
    if len(keys) != 1 or c is None or tgt["entry"].get(keys[0]) != (XD[4], "round", round_name(tst, XD[5])):
        return None
    seeds = len(S.acc["totals"].get(XD[3], []))
    x = [k for k, e in tgt["entry"].items() if k >= seeds and e == (XD[4], "round", round_name(tst, XD[6]))]
    return (keys[0], x[0], c) if len(x) == 1 else None


def extra_draw(S, want_tr, got, p):
    """T47.c2 (--side, the XD source comp): the transfers the extra rebalancing draw adds (uefa_access.md:68-70): exactly 16 - C
    losers of the XD source round each with a second transfer, to the extra key, beside its CP Q2 line. Accepted (returned) only
    when all hold; else nothing is returned (each stays a break) and the count is said."""
    if not S.spliced or S.comp != XD[0] or not S.done.get(XD[1], True):
        return set()
    xk = xd_key(S)
    if xk is None:
        return set()
    k2, kx, c = xk
    extra = {x for x in got - want_tr if x[0] == XD[1] and x[1] == XD[2] and x[3] == XD[3] and x[4] == kx}
    losers = {S.loser(XD[1], XD[2], t) for t in S.round_ties(XD[1], XD[2])}
    if not extra:
        return set()
    if len(extra) != 16 - c:
        p.append("stage %d round %d: extra draw: %d transfer(s) to comp %d key %d, 16 - C = 16 - %d = %d" % (
            XD[1], XD[2], len(extra), XD[3], kx, c, 16 - c))
        return set()
    if any(x[2] not in losers or (x[0], x[1], x[2], x[3], k2) not in got for x in extra):
        return set()
    return extra


def lp_parts(S):
    st = S.rec["stages"][S.lp]
    pots = {int(kv["team"]): {k: to_int(v) for k, v in kv.items()} for s, kv in S.lines("pot") if s == S.lp}
    return st, pots


def lp_opponents(S):
    opp = defaultdict(list)  # team -> [(opponent, home)]
    for _date, h, a, _hg, _ag in S.league.get(S.lp, []):
        opp[h].append((a, 1))
        opp[a].append((h, 0))
    return opp


def fam_draw(S):
    if S.lp is None:
        return []
    p = []
    st, pots = lp_parts(S)
    pk, _ = phase_kv(st, "draw", "pots")
    sk, _ = phase_kv(st, "draw", "seed")
    ak, _ = phase_kv(st, "draw", "association")
    if not pk:
        return ["record: no `phase draw pots` line"]
    if not pots:
        return ["dump: no pot lines"]
    P, B, k, split = int(pk["pots"]), int(pk["block"]), int(pk["per_pot"]), to_int(pk.get("split"))
    holder = sk is not None and sk.get("holder") == "1"  # `phase draw seed club_coefficient holder 1`: the titleholder tops pot 1
    if len(pots) != P * B:
        p.append("%d pot lines, record pots %d x block %d" % (len(pots), P, B))
    # T29.c7: at most one; none in a season whose holder seat is vacant (the first season: compseed logs `holder seat vacant`)
    if holder and sum(1 for v in pots.values() if v.get("holder")) > 1:
        p.append("record holder 1: %d pot line(s) with holder=1" % sum(1 for v in pots.values() if v.get("holder")))
    order = sorted(pots, key=lambda t: (-(holder and pots[t].get("holder", 0)), -pots[t]["coef"], t))  # compdraw.h:30, FUN_00CD1640
    for i, t in enumerate(order):
        if pots[t]["pot"] != i // B:
            p.append("team %d (coef %d) in pot %d, by coefficient pot %d" % (t, pots[t]["coef"], pots[t]["pot"], i // B))
        if pots[t]["slot"] // B != pots[t]["pot"]:
            p.append("team %d slot %d is outside pot %d's block" % (t, pots[t]["slot"], pots[t]["pot"]))
    # T29.c9: each pot coef = the dump's coeff club value of year Y-1 (rolled by the year-Y 30 May block) when that line exists
    cv = {int(kv["team"]): int(kv["value"]) for c, y, s, kv in S.d["rules"]["coeff"] if y == S.year - 1 and kv.get("kind") == "club"}
    for t in sorted(pots):
        if t in cv and pots[t]["coef"] != cv[t]:
            p.append("team %d pot coef %d, coeff club value %d (year %d)" % (t, pots[t]["coef"], cv[t], S.year - 1))
    own =to_int(ak.get("own")) if ak else None
    other = to_int(ak.get("other")) if ak else None
    for t, lst in sorted(lp_opponents(S).items()):
        if t not in pots:
            p.append("team %d plays the league phase without a pot line" % t)
            continue
        per, home = Counter(), Counter()
        for o, h in lst:
            q = pots.get(o, {}).get("pot")
            per[q] += 1
            home[q] += h
        for q in range(P):
            if per[q] != k:
                p.append("team %d meets %d of pot %d, record per_pot %d" % (t, per[q], q, k))
            elif split is not None and home[q] != split:
                p.append("team %d is at home to %d of pot %d, record split %d" % (t, home[q], q, split))
        nat = pots[t]["nation"]
        nats = Counter(pots.get(o, {}).get("nation") for o, _ in lst)
        if own is not None and nats.get(nat, 0) > own:
            p.append("team %d meets %d club(s) of its own association %d (record own %d)" % (t, nats[nat], nat, own))
        for n2, m in sorted(nats.items(), key=lambda x: str(x)):
            if n2 != nat and other is not None and m > other:
                p.append("team %d meets %d clubs of association %s (record other %d)" % (t, m, n2, other))
    return p


def lp_rounds(S):
    return rounds(S.d, S.comp).get((S.year, S.lp), [])


def fam_fixtures(S):
    if S.lp is None:
        return []
    p = []
    st, pots = lp_parts(S)
    plan = sorted((int(v[0]), [int(x) for x in v[1:]]) for v in st["phase"].get("plan", []))
    _, dv = phase_kv(st, "draw", "days")  # `phase draw days home <h> run <r> ..`
    dk = {"home": dv[dv.index("home") + 1], "run": dv[dv.index("run") + 1]} if dv else None
    mt = st["phase"].get("matches")
    if not plan:
        return ["record: no `phase plan` lines"]
    slot = {v["slot"]: t for t, v in pots.items()}
    # T30.8.c5: each fixture to its plan row by pair (a pair is in one row), so a postponed fixture stays in its matchday; the
    # rows' date order is a check of its own (a real fault seen in game: rows played 2,0,1,3..7, T30.8.c3)
    want, row_of = [], {}
    for r, (_row, cells) in enumerate(plan):  # `phase plan`: slot t's signed 1-based opponent, + = t at home (complg.h:135)
        want.append({(slot.get(t), slot.get(abs(v) - 1)) for t, v in enumerate(cells) if v > 0})
        row_of.update((pr, r) for pr in want[-1])
    fx = sorted(S.league.get(S.lp, []), key=lambda f: (dkey(f[0]), f[1], f[2]))
    if not fx:
        p.append("dump: no league phase fixtures")
    got, dates = [set() for _ in plan], [Counter() for _ in plan]
    for pr, n in sorted(Counter((h, a) for _d, h, a, _hg, _ag in fx).items()):
        if n > 1:
            p.append("pair %d v %d played %d times" % (pr + (n,)))
    for date, h, a, _hg, _ag in fx:
        r = row_of.get((h, a))
        if r is None:
            p.append("fixture %s %d v %d is not a plan pair%s" % (date, h, a, " (plan: %d at home)" % a if (a, h) in row_of else ""))
            continue
        got[r].add((h, a))
        dates[r][date] += 1
    for r, w in enumerate(want):
        if got[r] != w:
            p.append("plan row %d: %d of %d pair(s) played, not played %s" % (r, len(got[r] & w), len(w), sorted(w - got[r], key=str)))
    main = sorted((dkey(min(c, key=lambda x: (-c[x], dkey(x)))), r) for r, c in enumerate(dates) if c)  # a row's most played date
    order = [r for _d, r in main]
    if order != sorted(order):
        p.append("matchday date order: plan rows played %s (main dates %s), plan order %s" % (
            ",".join(map(str, order)), ",".join("%d.%d" % d for d, _r in main), ",".join(map(str, sorted(order)))))
    rds = [got[r] for r in range(len(plan))]  # venues and runs in plan row order
    venue = defaultdict(list)
    for rd in rds:
        for h, a in rd:
            venue[h].append(1)
            venue[a].append(0)
    lo, hi = (int(mt[0][1]), int(mt[0][2])) if mt and len(mt[0]) > 2 else (None, None)  # `phase matches <stag> <mnmt> <mxmt>`
    for t, v in sorted(venue.items()):
        if lo is not None and not lo <= len(v) <= hi:
            p.append("team %d plays %d matches, record matches %d-%d" % (t, len(v), lo, hi))
        if dk and sum(v) != int(dk["home"]):
            p.append("team %d has %d home matches, record days home %s" % (t, sum(v), dk["home"]))
        run = cur = 0
        for i, x in enumerate(v):
            cur = cur + 1 if i and x == v[i - 1] else 1
            run = max(run, cur)
        if dk and run > int(dk["run"]):
            p.append("team %d has a run of %d at home or away, record run %s" % (t, run, dk["run"]))
    return p


def fam_split(S):
    if S.lp is None:
        return []
    st, _ = lp_parts(S)
    _, v = phase_kv(st, "draw", "days")  # `phase draw days home <h> run <r> first <w> <n> last <w> <n>`
    if not v:
        return ["record: no `phase draw days` line"]
    i, j = v.index("first"), v.index("last")
    fw, fn, lw, ln = int(v[i + 1]), int(v[i + 2]), int(v[j + 1]), int(v[j + 2])
    rds = lp_rounds(S)
    if not rds or rds == [frozenset()]:
        return ["dump: no league phase fixtures"]
    seq = defaultdict(list)
    for rd in rds:
        for h, a in rd:
            seq[h].append(1)
            seq[a].append(0)
    p = []
    # The record's count, not UCL Art 17's "every club": the CL / EL plans split 18 / 24 of 36 (comp_data.md:618).
    for what, w, n, part in (("first", fw, fn, lambda s: s[:fw]), ("last", lw, ln, lambda s: s[-lw:])):
        bad = sorted(t for t, s in seq.items() if set(part(s)) != {0, 1})
        if len(seq) - len(bad) != n:
            p.append("%d clubs split their %s %d matchdays one home one away, record %d (not split: %s)" % (
                len(seq) - len(bad), what, w, n, ",".join(map(str, bad))))
    return p


def lp_recount(S, pw, pd, pl):
    out = defaultdict(lambda: Counter())
    for _date, h, a, hg, ag in S.league.get(S.lp, []):
        for team, f, g, home in ((h, hg, ag, 1), (a, ag, hg, 0)):
            r = out[team]
            r["p"] += 1
            r["gf"] += f
            r["ga"] += g
            r["w" if f > g else "d" if f == g else "l"] += 1
            r["pts"] += pw if f > g else pd if f == g else pl
            if not home:
                r["agf"] += f
                r["aw"] += f > g
    return out


def fam_standings(S):
    if S.lp is None:
        return []
    p = []
    st = S.rec["stages"][S.lp]
    lg = st["league"]
    pw, pd, pl = (to_int(lg.get(k), dv) for k, dv in (("points_win", 3), ("points_draw", 1), ("points_loss", 0)))
    rb = st["phase"].get("rank_by")  # `phase rank_by` (T27), else the `f league.tie_breaker 0 <id>` list
    keys = rb[0] if rb else [f[2] for f in st["f"] if f[0] == "league.tie_breaker" and len(f) > 2]
    tb = S.d["table"].get((S.comp, S.year, S.lp))
    if not tb:
        return ["dump: no table lines for the league phase stage %d" % S.lp]
    rc = lp_recount(S, pw, pd, pl)
    rows = [tb[q] for q in sorted(tb)]
    for r in rows:
        c = rc.get(r["team"], Counter())
        for f in ("p", "w", "d", "l", "gf", "ga", "pts"):
            if r[f] != c[f]:
                p.append("team %d %s: table %d, fixtures %d" % (r["team"], f, r[f], c[f]))
    x = S.d["tablex"].get((S.comp, S.year, S.lp), {})

    def val(team, key):  # FM07 tie ids (fm07_comp_contract.md 21(l):517-536, 21(m)); None = not in the dump / not checked
        c = rc.get(team, Counter())
        return {"0": c["gf"] - c["ga"], "1": c["gf"], "2": c["w"], "5": c["agf"], "away_won": c["aw"],
                "cards": -x.get(team, {}).get("cards") if "cards" in x.get(team, {}) else None,
                "7": x.get(team, {}).get("coef")}.get(key)

    for i, (a, b) in enumerate(zip(rows, rows[1:])):
        ka = [rc[a["team"]]["pts"]] + [val(a["team"], k) for k in keys]
        kb = [rc[b["team"]]["pts"]] + [val(b["team"], k) for k in keys]
        for n, (u, v) in enumerate(zip(ka, kb)):
            if u is None or v is None:
                break  # key 3 (head-to-head) and keys the dump lacks: not judged from here on
            if u != v:
                if u < v:
                    p.append("positions %d / %d: team %d above team %d, but %s %s < %s" % (
                        i, i + 1, a["team"], b["team"], "points" if n == 0 else "key " + keys[n - 1], u, v))
                break
    return p


def ko_stage(S, kind):
    """(stage, round name) of `phase direct|playoff <n> stage <s> round <name>`, and n. T47.c2: the stage is the one the
    record's `chain <s> ranks <lp> ..` lines build from the league ranks (what the DLL builds); the phase value is FM27's `stag`."""
    st = S.rec["stages"].get(S.lp)
    v = st["phase"].get(kind) if st else None
    if not v or len(v[0]) < 5:
        return None, None, None
    s, cs = int(v[0][2]), ko_chain(S)
    return (cs[0] if len(cs) == 1 else s), int(v[0][4]), int(v[0][0])


def ko_chain(S):
    """T47.c2: the stages the record's `chain <s> ranks <lp> <lo> <hi>` lines fill from the league phase's ranks (sorted)."""
    return sorted({c[0] for c in S.rec["chain"] if c[1] == S.lp}) if S.lp is not None else []


def ko_check(S):
    """T47.c2: (notes, problems) of the phase stage against the chain stage, for families 7 / 9. Same: nothing. The phase names the
    league stage itself (FM27 `stag`, UEL `stage 3`): a record note, the chain stage judged. Any other phase stage, or chain lines
    naming more than one stage: a problem (the phase stage judged when the chain names several)."""
    notes, probs, cs = [], [], ko_chain(S)
    st = S.rec["stages"].get(S.lp)
    for kind in ("direct", "playoff"):
        v = st["phase"].get(kind) if st else None
        if not v or len(v[0]) < 5 or not cs:
            continue
        s = int(v[0][2])
        if len(cs) > 1:
            probs.append("record: chain ranks lines from league stage %d name stages %s; phase %s says stage %d" % (
                S.lp, ",".join(map(str, cs)), kind, s))
        elif s == S.lp and cs[0] != s:
            notes.append("record: phase %s stage %d is the league stage itself (FM27 stag); chain ranks stage %d judged" % (kind, s, cs[0]))
        elif s != cs[0]:
            probs.append("record: phase %s stage %d, chain ranks stage %d (chain judged)" % (kind, s, cs[0]))
    return notes, probs


def fam_playoff(S):
    s, name, n = ko_stage(S, "playoff")
    if s is None:
        return []
    _, _, nd = ko_stage(S, "direct")
    st = S.rec["stages"].get(s)
    p = ko_check(S)[1]  # T47.c2
    if not S.rank:
        return p + ["dump: no league phase table (ranks)"]
    if st is None:
        return p + ["record: play-off stage %d has no stage line" % s]
    cr = S.chain_ranks(s)
    for k in [k for k in st["rounds"] if round_name(st, k) == name]:
        br = st["bracket"].get(k, {})
        refs = {x for (hk, h, ak, a) in br.values() for x in ((hk, h), (ak, a))}
        ranks = sorted(cr[i] for kind, i in refs if kind == "team" and i is not None and i < len(cr))
        lo = (nd or 0) + 1
        if ranks != list(range(lo, lo + n)):  # `phase direct <nd>` ranks 1..nd, `phase playoff <n>` the next n
            p.append("round %d draws ranks %s, record playoff %d after direct %s (ranks %d-%d)" % (k, ranks, n, nd, lo, lo + n - 1))
        ts = S.round_ties(s, k)
        if len(ts) != len(br):
            p.append("round %d: %d tie(s), record bracket %d" % (k, len(ts), len(br)))
        for t, (hk, h, ak, a) in sorted(br.items()):
            want = {S.side(s, k, (hk, h)), S.side(s, k, (ak, a))}
            tie = S.ties.get((s, k, t))
            if not tie or {tie["a"], tie["b"]} != want:
                p.append("round %d tie %d: dump %s, bracket %s %s v %s %s = teams %s" % (
                    k, t, tie and sorted((tie["a"], tie["b"])), hk, h, ak, a, sorted(want, key=str)))
    return p


def bracket_stages(S):
    return [(s, st) for s, st in sorted(S.rec["stages"].items()) if st["kind"] == "knockout" and st["bracket"] and S.done[s]]


def fam_second_leg(S):
    p = []
    if any(round_int(st, k, "legs") == 2 for _s, st in bracket_stages(S) for k in st["bracket"]) and \
            not any(S.cup[(s, k, t)] for s, st in bracket_stages(S) for k in st["bracket"] for t in st["bracket"][k]):
        return ["dump: no fixtures of the bracket rounds"]
    for s, st in bracket_stages(S):
        for k, br in sorted(st["bracket"].items()):
            if round_int(st, k, "legs") != 2:
                continue
            for t, (hk, h, ak, a) in sorted(br.items()):
                home, away = S.side(s, k, (hk, h)), S.side(s, k, (ak, a))  # complg.h:110: home side 0, the seeded away side 1
                for f in S.cup[(s, k, t)]:
                    if f["replay"]:
                        continue
                    want = away if f["leg"] else home
                    if f["home"] != want:
                        p.append("stage %d round %d tie %d leg %d: home %d, the bracket's %s side %s" % (
                            s, k, t, f["leg"] + 1, f["home"], "seeded (away)" if f["leg"] else "home", want))
    return p


def fam_bracket(S):
    p = ko_check(S)[1]  # T47.c2
    ps, pname, _ = ko_stage(S, "playoff")
    _, _, nd = ko_stage(S, "direct")
    for s, st in bracket_stages(S):
        cr = S.chain_ranks(s)
        ks = sorted(st["rounds"])
        for k in ks:
            if s == ps and round_name(st, k) == pname:
                continue  # family 7
            br = st["bracket"].get(k, {})
            ts = S.round_ties(s, k)
            n = round_int(st, k, "ties")
            if n is not None and len(ts) != n:
                p.append("stage %d round %d: %d tie(s), record ties %d" % (s, k, len(ts), n))
            for t, (hk, h, ak, a) in sorted(br.items()):
                for kind, i in ((hk, h), (ak, a)):
                    if kind == "team" and nd and (i is None or i >= len(cr) or cr[i] > nd):
                        p.append("stage %d round %d tie %d: team %s is not a direct place (ranks 1-%d)" % (s, k, t, i, nd))
                want = {S.side(s, k, (hk, h)), S.side(s, k, (ak, a))}
                tie = S.ties.get((s, k, t))
                if not tie or {tie["a"], tie["b"]} != want:
                    p.append("stage %d round %d tie %d: dump %s, bracket %s %s v %s %s = %s" % (
                        s, k, t, tie and sorted((tie["a"], tie["b"])), hk, h, ak, a, sorted(want, key=str)))
            tie_legs(S, s, k, st, p)
        if ks:
            last = ks[-1]
            if round_int(st, last, "ties") != 1:
                p.append("stage %d: last round %d has %s ties, a final has 1" % (s, last, round_int(st, last, "ties")))
            elif S.winner(s, last, 0) is None:
                p.append("stage %d: the final (round %d) has no winner in the dump" % (s, last))
    return p


def fam_tie_rule(S):
    """`round <k> tie_rule <word>` bits (comp_data.md:547): 0x1 extra time, 0x2 penalties, 0x4 away goals (two legs)."""
    ties = {key: tie for key, tie in S.ties.items() if S.done.get(key[0], True)}  # T30.8.c5: complete stages only
    p = [] if ties or not any(st["kind"] == "knockout" and S.done[s] for s, st in S.rec["stages"].items()) else ["dump: no tie lines"]
    for (s, k, t), tie in sorted(ties.items()):
        st = S.rec["stages"].get(s)
        w = round_int(st, k, "tie_rule") if st else None
        if w is None:
            p.append("stage %d round %d: no decoded tie_rule in the record" % (s, k))
            continue
        a, b = tie["a"], tie["b"]
        g, ag = Counter(), Counter()
        fx = [f for f in S.cup[(s, k, t)] if not f["replay"]]
        for f in fx:
            g[f["home"]] += f["hg"]
            g[f["away"]] += f["ag"]
            ag[f["away"]] += f["ag"]
        pens = tie.get("pens", "-")
        et = tie.get("et", 0)
        win = tie.get("winner")
        why = None
        if et and not w & 1:
            why = "extra time played, the rule has no extra time"
        elif pens != "-" and not w & 2:
            why = "penalties taken, the rule has no penalties"
        elif g[a] != g[b]:
            if win != (a if g[a] > g[b] else b):
                why = "aggregate %d-%d, winner %s" % (g[a], g[b], win)
            elif pens != "-":
                why = "penalties after an aggregate %d-%d" % (g[a], g[b])
        elif w & 4 and len(fx) == 2 and ag[a] != ag[b]:
            if win != (a if ag[a] > ag[b] else b) or pens != "-":
                why = "level %d-%d, away goals %d-%d decide, winner %s pens %s" % (g[a], g[b], ag[a], ag[b], win, pens)
        elif pens == "-":
            why = "level %d-%d and no penalties (rule word %d)" % (g[a], g[b], w)
        else:
            pa, pb = (int(x) for x in str(pens).split("-"))
            if w & 1 and not et:
                why = "level %d-%d went to penalties without the rule's extra time" % (g[a], g[b])
            elif pa == pb or win != (a if pa > pb else b):
                why = "penalties %s, winner %s" % (pens, win)
        if why:
            p.append("stage %d round %d tie %d (%d v %d): %s" % (s, k, t, a, b, why))
    return p


def cash_of(vals, i=0):
    """a record cash value (token i of a `round <k> <field>` / `phase <field>` value list) and its `curr=` (None: none)."""
    v = to_int(vals[i]) if vals and len(vals) > i else None
    return v, next((to_int(t[5:]) for t in (vals or [])[i + 1:] if t.startswith("curr=")), None)


def paid(S, cash, curr, miss):
    """T30.8.c5: the amount the game pays for record cash in currency curr, FUN_00DECA80(cash, 0, curr, 0) as observed
    (T30.8.c4 disassembly, C0115): base = trunc(cash / div), amount = trunc(base * mul), x87 double, div from the dump's
    `prize_rate curr=<c> div=<f>` line, mul from `# prize_rule ... mul=<R0> round100000=<0|1>`. round100000=1 (a further rounding
    step, not decoded) or no rule line: None (not judged). No curr = the cash itself; a curr without its line: None, added to miss."""
    if not cash or curr is None:
        return cash or 0
    div, rule = S.d["prize_rate"].get(curr), S.d.get("prize_rule")
    if div is None or rule is None or rule[1] or not rule[0] == rule[0]:
        miss.add(curr)
        return None
    return int(int(cash / div) * rule[0])


def fam_prizes(S):
    want, miss, p = Counter(), set(), []
    if S.lp is not None and S.done[S.lp]:
        st = S.rec["stages"][S.lp]
        ph = st["phase"]
        app = paid(S, *cash_of(ph.get("appearance", [None])[0]), miss)
        pwin = paid(S, *cash_of(ph.get("prize_win", [None])[0]), miss)
        pdraw = paid(S, *cash_of(ph.get("prize_draw", [None])[0]), miss)
        pos = {int(v[0]): paid(S, *cash_of(v, 1), miss) for v in ph.get("prize_position", [])}
        ent = S.d["entrants"].get((S.comp, S.year, S.lp))
        if app != 0 and ent is None:
            p.append("dump: no entrants line for the league phase stage %d (appearance prizes)" % S.lp)
        for team in ent or []:  # T30.8.c5: paid at the stage's attach (comphost_generic.c:777): its entrants, not the table
            if app != 0:
                want[(S.lp, team, "appearance", -1, app)] += 1
        for i, team in enumerate(S.rank):
            if pos.get(i) != 0 and i in pos:
                want[(S.lp, team, "position", -1, pos[i])] += 1
        for _date, h, a, hg, ag in S.league.get(S.lp, []):
            for team, f, g in ((h, hg, ag), (a, ag, hg)):
                if f > g and pwin != 0:
                    want[(S.lp, team, "win", -1, pwin)] += 1
                elif f == g and pdraw != 0:
                    want[(S.lp, team, "draw", -1, pdraw)] += 1
    for (s, k, t), tie in S.ties.items():
        st = S.rec["stages"].get(s)
        if not st or not S.done[s]:
            continue
        for kind, field, team in (("appearance", "appearance", tie["a"]), ("appearance", "appearance", tie["b"]),
                                  ("winner", "prize_winner", tie.get("winner")), ("loser", "prize_loser", S.loser(s, k, t))):
            v = paid(S, *cash_of(st["rounds"].get(k, {}).get(field)), miss)
            if v != 0:
                want[(s, team, kind, k, v)] += 1
    unj = {(s, kind, r) for (s, _t, kind, r, v) in want if v is None}  # amounts not judged (no rate): payee and count still are
    got = Counter((s, int(kv["team"]), kv["kind"], int(kv["round"]),
                   None if (s, kv["kind"], int(kv["round"])) in unj else int(kv["amount"]))
                  for s, kv in S.lines("prize") if S.done.get(s, True))
    p += ["dump: no prize_rate line for curr=%d, or no / undecoded `# prize_rule` (round100000=1): record cash not converted, "
          "amounts not judged" % c for c in sorted(miss)]
    if not got and want:
        return p + ["dump: no prize lines"]
    p += ["stage %d team %d %s round %d amount %s: record wants %d, dump pays %d" % (k + (want[k], got[k]))
          for k in sorted(set(want) | set(got), key=lambda x: (x[0], x[1] or 0, x[2], x[3], -1 if x[4] is None else x[4]))
          if want[k] != got[k]]
    return p


FAMILY_FN = (fam_entrants, fam_qualifying, fam_draw, fam_fixtures, fam_split, fam_standings, fam_playoff, fam_second_leg,
             fam_bracket, fam_tie_rule, fam_prizes)
WHOLE = (1, 3, 4, 5, 6, 7)  # T30.8.c5: judged only when all their stages are complete; 2, 8-11 judge their complete stages


def fam_stages(S, n):
    """T30.8.c5: the stages family n reads (their completeness decides what is judged; [] = always judged)."""
    sts = S.rec["stages"]
    if n == 1:
        return [s for s in sts if S.lp is not None and s < S.lp]  # the league phase's feeders (its entrants line)
    if n == 2:
        return [s for s, st in sts.items() if st["kind"] == "knockout" and not st["bracket"]]
    if n in (3, 4, 5, 6):
        return [S.lp] if S.lp is not None else []
    if n == 7:
        s = ko_stage(S, "playoff")[0]
        return [s] if s in sts else []
    if n in (8, 9):
        return [s for s, st in sts.items() if st["kind"] == "knockout" and st["bracket"]]
    if n == 10:
        return [s for s, st in sts.items() if st["kind"] == "knockout"]
    return list(sts)


def tie_trust(S):
    """T30.8.c5 (C0115): tie lines a dump marks as untrusted: `# dump error tie table full` (compdump's tie-note table full) or tie
    lines tagged src=bytes (the fallback from the tie's bytes). Families 1, 2, 10, 11 read the tie lines: they break."""
    p = ["dump: tie lines not trusted: %s" % x.lstrip("# ") for x in S.d["tie_full"][:1]]
    bad = sorted(key for key, tie in S.ties.items() if tie.get("src") == "bytes")
    if bad:
        p.append("dump: tie lines not trusted: %d tie line(s) src=bytes (stage, round, tie %s)" % (
            len(bad), " ".join("%d/%d/%d" % x for x in bad[:8]) + (" .." if len(bad) > 8 else "")))
    return p


def check_rules(d, path, comp, fams=None, side=None):
    srcs = {c for c, _y, _s, kv in d["rules"]["transfer"] if to_int(kv.get("to")) == comp}  # T37.c2: their fates
    if side is not None and comp == XD[0]:
        srcs.add(XD[3])  # T47.c2: the extra draw's target record names its key
    acc, recs = read_rules(splice(path, side) if side is not None else path, {comp} | srcs)
    if comp not in recs:
        print("record: no record of comp %d in %s" % (comp, path if side is None else "%s + side %s" % (path, side)))
        return False
    years = sorted({y for (c, y, *_r) in d["fixtures"] if c == comp} | {y for c, y, *_r in d["rules"]["seat"] if c == comp})
    if not years:
        print("dump: no fixtures or seats of comp %d" % comp)
        return False
    bad = 0
    for y in years:
        S = Season(d, comp, y, recs[comp], acc, recs)
        S.spliced = side is not None  # T47.c2: families 1 / 2 judge the side records' held shape
        for (n, name), fn in zip(FAMILIES, FAMILY_FN):
            if fams is not None and n not in fams:  # T29.c8 --families: only the listed run, print and decide
                continue
            stages = fam_stages(S, n)
            wait = sorted(s for s in stages if not S.done[s])
            idle = bool(wait) and (n in WHOLE or len(wait) == len(stages))
            trust = tie_trust(S) if n in (1, 2, 10, 11) else []
            if idle and not trust:  # T30.8.c5: a season in progress
                print("family %d %s: in progress, not judged (year %d, stage(s) %s, now=%s)" % (
                    n, name, y, ",".join(map(str, wait)), d["now"]))
                continue
            probs = trust + ([] if idle else fn(S))
            print("family %d %s: %s (year %d)" % (n, name, "BROKEN" if probs else "ok", y))
            if wait and not idle:
                print("  stage(s) %s in progress, not judged" % ",".join(map(str, wait)))
            for x in (ko_check(S)[0] if n in (7, 9) and not idle else []):  # T47.c2: a known record quirk, named
                print("  %s" % x)
            for x in probs[:20]:
                print("  %s" % x)
            if len(probs) > 20:
                print("  .. %d more" % (len(probs) - 20))
            bad += bool(probs)
    print("rules hold" if not bad else "%d family(ies) broken" % bad)
    return not bad


def coeff_entries(rec):
    """record `coeff` lines -> [(stage, kind, round name | None, key, pts, targets)]; kind win/draw/round/position/qual_exit."""
    out = []
    for v in rec["coeff"]:
        rn = next((to_int(t[6:]) for t in v if t.startswith("round=")), None)
        v = [t for t in v if not t.startswith("round=")]
        tg = {"nation": {"n"}, "club": {"c"}, "both": {"n", "c"}}.get(v[-1])
        if len(v) < 4 or tg is None:
            continue
        st, kind = int(v[0]), v[1]
        if kind in ("win", "draw"):
            out.append((st, kind, rn, None, float(v[2]), tg))
        elif kind in ("round", "position", "qual_exit") and len(v) >= 5:
            out.append((st, kind, int(v[2]) if kind == "round" else None, int(v[2]), float(v[3]), tg))
    return out


def pick(ents, st, kind, name):
    """compcoef.c pick(): the stage's line for the round name first, else (not for `round`) its plain line."""
    for e in ents:
        if e[0] == st and e[1] == kind and name is not None and e[2] == name:
            return e
    if kind == "round":
        return None
    return next((e for e in ents if e[0] == st and e[1] == kind and e[2] is None), None)


def side_won(hg, ag):
    """compcoef.c accrue() (T39.c2): win / draw by the match score, FUN_00C40330(side,1,0) = the dump's score= (hg / ag): side 0
    higher -> 0, side 1 higher -> 1, equal -> None (draw; a leg level on goals and decided on penalties is a draw, extra-time
    goals count). FM23 FUN_1430577b0. was: the side records' LOST code (raw= byte 5 / 11 == 10), the tie's outcome on a
    deciding leg; raw= stays in the dump but no longer decides."""
    return 0 if hg > ag else 1 if hg < ag else None


def roll_points(d, year, recs, acc):
    """season points per nation / club and matches per club, compcoef.c accrue() + compcoef_stage_done() over the dump.
    T39.c2: a match's win / draw comes from its score (side_won), as accrue() reads it (was T37.c3: the LOST code)."""
    nat_of = {}
    for c, y, s, kv in d["rules"]["coeff"]:
        if y == year and kv.get("kind") == "club":
            nat_of[int(kv["team"])] = int(kv["nation"])
    npts, cpts, cm, seen = Counter(), Counter(), Counter(), set()

    def add(team, e):
        if "n" in e[5] and team in nat_of:
            npts[nat_of[team]] += e[4]
        if "c" in e[5]:
            cpts[team] += e[4]

    for comp, rec in recs.items():
        ents = coeff_entries(rec)
        S = Season(d, comp, year, rec, acc)
        matches = [(s, round_name(rec["stages"][s], k), f["home"], f["away"], side_won(f["hg"], f["ag"]))
                   for (s, k, _t), fl in S.cup.items() if s in rec["stages"] for f in fl]
        matches += [(s, None, h, a, side_won(hg, ag))
                    for s, fl in S.league.items() for dt, h, a, hg, ag in fl]
        for s, name, h, a, won in matches:
            for side, team in enumerate((h, a)):
                cm[team] += 1
                e = pick(ents, s, "draw" if won is None else "win", name) if won in (None, side) else None
                if e:
                    add(team, e)
                e = pick(ents, s, "round", name) if name is not None else None
                if e and (team, comp, name) not in seen:
                    seen.add((team, comp, name))
                    add(team, e)
        for e in ents:
            if e[1] == "position" and e[0] == S.lp and e[3] < len(S.rank):  # league_phase done: row r gets `position r`
                add(S.rank[e[3]], e)
            elif e[1] == "qual_exit":
                st = rec["stages"].get(e[0], {"rounds": {}})
                for k in [k for k in st["rounds"] if round_name(st, k) == e[3]]:
                    for t in S.round_ties(e[0], k):
                        if S.loser(e[0], k, t) is not None:
                            add(S.loser(e[0], k, t), e)
    return nat_of, npts, cpts, cm


def floats(v):
    return [float(x) for x in v.split(",") if x]


def check_roll(d, path):
    acc, recs = read_rules(path, RULE_COMPS)
    rule = acc["rule"]
    try:
        sums, keep, floor = int(rule["sums"][0]), int(rule["nation_history"][0]), float(rule["club_floor"][0])
    except (KeyError, IndexError, ValueError):
        print("record: the eur_access coeff_rule lines sums / nation_history / club_floor are missing")
        return False
    years = sorted({y for c, y, s, kv in d["rules"]["coeff"]})
    if not years:
        print("dump: no coeff lines")
        return False
    bad = 0
    for year in years:
        nat_of, npts, cpts, cm = roll_points(d, year, recs, acc)
        part = defaultdict(list)
        nl = {int(kv["nation"]): kv for c, y, s, kv in d["rules"]["coeff"] if y == year and kv.get("kind") == "nation"}
        cl = {int(kv["team"]): kv for c, y, s, kv in d["rules"]["coeff"] if y == year and kv.get("kind") == "club"}
        for team in sorted(t for t in cm if t not in cl):
            part["club"].append("team %d played %d match(es) but has no coeff club line" % (team, cm[team]))
        value = {}
        for nat, kv in sorted(nl.items()):  # compcoef_rollover: season = points / its clubs that played; +0x10 = sum of the last `sums`
            played = sum(1 for t, n in nat_of.items() if n == nat and cm[t] > 0)
            pts, hist = float(kv["points"]), floats(kv["hist"])
            value[nat] = float(kv["value"])
            exp = {"points": npts[nat], "clubs": played, "season": npts[nat] / played if played else 0.0}
            got = {"points": pts, "clubs": int(kv["clubs"]), "season": float(kv["season"])}
            for f in ("points", "clubs", "season"):
                if abs(exp[f] - got[f]) > TOL:
                    part["nation"].append("nation %d %s: dump %s, recomputed %s" % (nat, f, got[f], round(exp[f], 4)))
            if not hist or abs(hist[-1] - exp["season"]) > TOL:
                part["nation"].append("nation %d: hist's last %s, season value %s" % (nat, hist[-1:] or "-", round(exp["season"], 4)))
            if len(hist) > keep:
                part["nation"].append("nation %d keeps %d seasons, record nation_history %d" % (nat, len(hist), keep))
            if abs(sum(hist[-sums:]) - value[nat]) > TOL:
                part["nation"].append("nation %d value %s, sum of the last %d %s" % (nat, value[nat], sums, round(sum(hist[-sums:]), 4)))
            if "prev" in kv and len(hist) < keep and abs(sum(hist[:-1][-sums:]) - float(kv["prev"])) > TOL:
                part["nation"].append("nation %d prev %s, the last %d before the push %s" % (nat, kv["prev"], sums, sum(hist[:-1][-sums:])))
        for team, kv in sorted(cl.items()):  # FUN_00BE57D0 push trunc(pts x 1000), FUN_00BE5810 sum x 0.001, floor x association
            pts, ring, val = float(kv["points"]), [int(x) for x in kv["ring"].split(",") if x], int(kv["value"])
            if abs(pts - cpts[team]) > TOL or int(kv["matches"]) != cm[team]:
                part["club"].append("team %d points %s matches %s, recomputed %s / %d" % (team, pts, kv["matches"], round(cpts[team], 4), cm[team]))
            if not ring or abs(ring[-1] - int(cpts[team] * 1000)) > 1 or len(ring) > CLUB_BLOCK:
                part["club"].append("team %d ring %s: last must be trunc(%s x 1000), at most %d entries" % (team, kv["ring"], cpts[team], CLUB_BLOCK))
            nat = int(kv["nation"])
            want = int(max(sum(ring) * 0.001, floor * value.get(nat, 0.0)) * 1000)
            if abs(val - want) > 1:
                part["club"].append("team %d value %d, max(sum %d x 0.001, %s x association %s) x 1000 = %d" % (
                    team, val, sum(ring), floor, value.get(nat), want))
        for name in ("nation", "club"):
            print("roll %s: %s (year %d)" % (name, "BROKEN" if part[name] else "ok", year))
            for x in part[name][:20]:
                print("  %s" % x)
            bad += bool(part[name])
    # T39.c1: rank / places / eps per places year P. In game the year-P block rolls season P-1 (coeff lines year P-1) then computes
    # places P, so P ranks by coeff P-1's `value` (last season hist[-1]); a dump without coeff P-1 (the world test computes places
    # 2024 before its 2024 roll) ranks by coeff P's pre-roll `prev` (last season hist[:-1][-1]).
    pyears = sorted({y for c, y, s, kv in d["rules"]["places"]})
    if not pyears:
        for name in ("rank", "eps"):
            print("roll %s: BROKEN (places year -)" % name)
            print("  no places lines")
        bad += 2
    for P in pyears:
        part = defaultdict(list)
        src = {}  # nation -> (ranking value, last season)
        for y, post in ((P - 1, True), (P, False)):
            nl = {int(kv["nation"]): kv for c, yy, s, kv in d["rules"]["coeff"] if yy == y and kv.get("kind") == "nation"}
            if nl:
                for nat, kv in nl.items():
                    hist = floats(kv["hist"])
                    if post:
                        src[nat] = (float(kv["value"]), hist[-1] if hist else 0.0)
                    elif "prev" in kv:
                        src[nat] = (float(kv["prev"]), hist[:-1][-1] if len(hist) > 1 else 0.0)
                    else:
                        part["rank"].append("nation %d (coeff %d, pre-roll): no prev" % (nat, y))
                break
        else:
            part["rank"].append("places year %d: no coeff nation lines of %d or %d" % (P, P - 1, P))
        value = {n: v for n, (v, _) in src.items()}
        ranked = sorted((n for n in src if n not in acc["no_rank"]), key=lambda n: -value[n])
        # T29.c9: the last set of year P (compseed_compute writes one per call: the pre-roll one at the picks, then the block's post-roll
        # one); a set restarts where a (comp, nation) repeats; the eps lines after the last set's first places line are its own
        pls = [(ln, c, kv) for (c, y, s, kv), ln in zip(d["rules"]["places"], d["rule_ln"]["places"]) if y == P]
        start, seen = 0, set()
        for i, (_ln, c, kv) in enumerate(pls):
            if (c, int(kv["nation"])) in seen:
                start, seen = i, set()
            seen.add((c, int(kv["nation"])))
        pl = [(c, kv) for _ln, c, kv in pls[start:]]
        first = pls[start][0] if pls else -1
        rank_of = {}
        for c, kv in pl:
            rank_of.setdefault(int(kv["nation"]), int(kv["rank"]))
        rk = sorted(rank_of.items(), key=lambda x: x[1])
        if [r for _, r in rk] != list(range(1, len(rk) + 1)) or len(rk) != len(ranked):
            part["rank"].append("ranks %s, want 1..%d over the ranked associations" % ([r for _, r in rk], len(ranked)))
        for (n1, r1), (n2, r2) in zip(rk, rk[1:]):  # stock row compare 0x00CBCEB0: +0x10 descending (ties: the exe's qsort)
            if value.get(n1, 0) < value.get(n2, 0):
                part["rank"].append("rank %d nation %d value %s below rank %d nation %d value %s" % (r1, n1, value.get(n1), r2, n2, value.get(n2)))
        for c, kv in pl:  # compseed_compute: the band of the rank (`access <uid> ranks`) or the nation's `special row` line
            nat, r = int(kv["nation"]), int(kv["rank"])
            names = [n for n, _ in acc["totals"].get(c, [])]
            sp = acc["special_row"].get((nat, c))
            band = sp if sp is not None else next((b for lo, hi, b in acc["bands"].get(c, []) if lo <= r <= hi), {})
            want = [band.get(n, 0) for n in names]
            got = [int(x) for x in kv["band"].split(",")]
            if want != got:
                part["places"].append("comp %d nation %d rank %d: band %s, record %s" % (c, nat, r, got, want))
        el = [kv for (c, y, s, kv), ln in zip(d["rules"]["eps"], d["rule_ln"]["eps"]) if y == P and ln > first]
        eps = {int(kv["nation"]) for kv in el}
        last = {n: src[n][1] for n in ranked}
        order = sorted(ranked, key=lambda n: (-last[n], rank_of.get(n, 0)))  # compseed.c:647-660: best season value, tie the better rank
        want = set(order[:acc["eps"]])
        if eps != want:
            part["eps"].append("EPS %s, record %d association(s) by the best season value %s" % (sorted(eps), acc["eps"], sorted(want)))
        for kv in el:
            nat = int(kv["nation"])
            if nat in src and abs(float(kv["season"]) - src[nat][1]) > TOL:
                part["eps"].append("eps nation %d season %s, source last season %s" % (nat, kv["season"], round(src[nat][1], 4)))
        for name in ("rank", "places", "eps"):
            print("roll %s: %s (places year %d)" % (name, "BROKEN" if part[name] else "ok", P))
            for x in part[name][:20]:
                print("  %s" % x)
            bad += bool(part[name])
    print("roll holds" if not bad else "%d roll part(s) broken" % bad)
    return not bad


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("a")
    ap.add_argument("b", nargs="?")
    ap.add_argument("--record", help="T17: a data file; check the dump `a`'s --comp against its record (structure only)")
    ap.add_argument("--comp", type=int, default=None, help="only this competition uid")
    ap.add_argument("--recompute", action="store_true", help="tables recomputed from fixture lines vs the dumped tables")
    ap.add_argument("--calendar", action="store_true", help="stock vs hosted: pairs by round, recompute, fate counts (needs --comp)")
    ap.add_argument("--structure", action="store_true", help="structure per comp (entrants, rounds, legs, groups, advance, pairs); exit 1 on a difference")
    ap.add_argument("--baseline", help="with --calendar or --recompute: a second stock run; judge only what stock keeps")
    ap.add_argument("--rules", action="store_true", help="T29.c6: the 11 rule families of --comp against --record; exit 1 when one breaks")
    ap.add_argument("--roll", action="store_true", help="T29.c6: season-end coefficients, ranks, bands, EPS against --record")
    ap.add_argument("--families", help="T29.c8: with --rules, a comma list of family numbers (default all 11); only those run")
    ap.add_argument("--side", help="T47.c2: with --record (and --rules): a side file whose records replace --record's first record "
                    "of each uid, as the DLL splices them under cl_prelim=0; families 1 / 2 then judge its held shape")
    args = ap.parse_args(argv)
    if args.side is not None and (not args.record or args.roll):
        ap.error("--side needs --record (with --rules or alone), not --roll")
    if args.rules or args.roll:
        if not args.record or args.b is not None or (args.rules and args.roll):
            ap.error("--rules / --roll need --record and one dump")
        if args.rules and args.comp not in RULE_COMPS:
            ap.error("--rules needs --comp one of %s" % " ".join(map(str, RULE_COMPS)))
        fams = None
        if args.families is not None:
            try:
                fams = {int(x) for x in args.families.split(",")}
            except ValueError:
                fams = {0}
            if not args.rules or not fams <= {n for n, _ in FAMILIES}:
                ap.error("--families needs --rules and numbers 1-%d" % len(FAMILIES))
        d = parse(args.a)
        return 0 if (check_rules(d, args.record, args.comp, fams, args.side) if args.rules else check_roll(d, args.record)) else 1
    if args.record:
        if args.comp is None or args.b is not None:
            ap.error("--record needs --comp and one dump")
        rec = splice(args.record, args.side) if args.side is not None else args.record
        return 0 if check_record(parse(args.a), rec, args.comp) else 1
    if args.b is None:
        ap.error("two dumps needed")
    A, B = parse(args.a), parse(args.b)
    if args.structure:
        return 0 if compare_structure(A, B, [args.comp] if args.comp is not None else structure_comps(A, B)) else 1
    if args.calendar:
        if args.comp is None:
            ap.error("--calendar needs --comp")
        if args.baseline:
            return baseline(A, B, parse(args.baseline), args.comp)
        return calendar(A, B, args.comp)
    out, total = [], 0
    # fixtures: dict key -> score; the key carries the date, so a moved fixture shows as only-in-A plus only-in-B
    total += diff_maps("fixture", A["fixtures"], B["fixtures"], args.comp, str, out)
    ta = {k: [v[p] for p in sorted(v)] for k, v in A["table"].items()}
    tb = {k: [v[p] for p in sorted(v)] for k, v in B["table"].items()}
    total += diff_maps("table", ta, tb, args.comp, lambda rows: " ".join("%d:%d/%d-%d/%d" % (r["team"], r["p"], r["gf"], r["ga"], r["pts"]) for r in rows), out)
    total += diff_maps("entrants", A["entrants"], B["entrants"], args.comp, lambda t: "%d teams %s" % (len(t), ",".join(map(str, t))), out)
    total += diff_maps("fate", fates_of(A), fates_of(B), args.comp, str, out)
    for line in out:
        print(line)
    if args.recompute:
        runs = [("A", A), ("B", B)] + ([("C", parse(args.baseline))] if args.baseline else [])
        rf = not recompute_faults(runs, args.comp)
        print("recompute: %s" % ("FAULTS" if rf else "0 faults"))
        total += rf
    print("same" if total == 0 else "%d difference(s)" % total)
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
