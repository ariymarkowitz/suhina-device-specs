# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Compares two sets of measurements (from analyse.py): Live's renders against Suhina's.

    python compare.py results/live results/suhina [--cases cases.built.json] [--tol-db 0.5]
    python compare.py live/thr-12.json suhina/thr-12.json

Pairs files by name; with --cases, a file whose name ends with a case id (Live adds the set's
name or a track number to exported files) pairs with the other side's file for that id. Prints
one block per pair, a line per measurement with both values and whether it is within tolerance,
and exits 1 when any pair is out of tolerance.
"""

import argparse
import json
import math
import os
import sys


def within_band(centres, lo=30.0, hi=16000.0):
    return [i for i, c in enumerate(centres) if lo <= c <= hi]


def max_abs_diff(a, b, idx):
    d = [abs(a[i] - b[i]) for i in idx if a[i] is not None and b[i] is not None]
    return max(d) if d else None


def rel(a, b):
    if a is None or b is None:
        return None
    base = max(abs(a), abs(b), 1e-9)
    return abs(a - b) / base


class Report:
    def __init__(self, tol_db, tol_rel, tol_ms):
        self.rows = []
        self.fail = False
        self.tol_db, self.tol_rel, self.tol_ms = tol_db, tol_rel, tol_ms

    def add(self, what, a, b, diff, tol, unit=""):
        if diff is None:
            ok = (a is None) == (b is None)
        else:
            ok = diff <= tol
        self.fail |= not ok
        fmt = lambda v: "-" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))
        self.rows.append((what, fmt(a), fmt(b), fmt(diff) + unit if diff is not None else "-", "ok" if ok else "DIFF"))


def compare(a, b, rep):
    ra, rb = a["response"], b["response"]
    idx = within_band(ra["centres_hz"])
    for kind in ("sweep_db", "noise_db"):
        for ch, name in enumerate(["left", "right"]):
            d = max_abs_diff(ra[kind][ch], rb[kind][ch], idx)
            rep.add(f"response {kind[:-3]} {name}, max |dB| 30 Hz-16 kHz", None, None, d, rep.tol_db, " dB")

    sa, sb = a["static"], b["static"]
    diffs, thd = [], []
    for x, y in zip(sa, sb):
        if x["left_out_db"] > -90 and y["left_out_db"] > -90:
            diffs.append(abs(x["left_gain_db"] - y["left_gain_db"]))
            if x.get("left_thd_pct") is not None and y.get("left_thd_pct") is not None:
                thd.append(abs(x["left_thd_pct"] - y["left_thd_pct"]))
    rep.add("static gain, max |dB| over the staircase", None, None, max(diffs) if diffs else None, rep.tol_db, " dB")
    rep.add("THD at 1 kHz, max |difference| (percentage points)", None, None, max(thd) if thd else None, 1.0, " pt")

    for phase in ("attack", "release"):
        for key in ("t63_ms", "t90_ms"):
            x, y = a["dynamics"][phase][key], b["dynamics"][phase][key]
            rep.add(f"{phase} {key}", x, y, rel(x, y), rep.tol_rel)

    ta, tb = a["impulse"]["taps"], b["impulse"]["taps"]
    rep.add("impulse taps (count)", len(ta), len(tb), float(abs(len(ta) - len(tb))), 0.0)
    for i, (x, y) in enumerate(zip(ta, tb)):
        rep.add(f"tap {i + 1} time", x["time_ms"], y["time_ms"], abs(x["time_ms"] - y["time_ms"]), rep.tol_ms, " ms")
        rep.add(f"tap {i + 1} level", x["level_db"], y["level_db"], abs(x["level_db"] - y["level_db"]), rep.tol_db, " dB")
    x, y = a["impulse"].get("rt60_s"), b["impulse"].get("rt60_s")
    rep.add("RT60", x, y, rel(x, y), rep.tol_rel)

    for ch in ("left", "right"):
        ma, mb = a["modulation"].get(ch), b["modulation"].get(ch)
        if not ma or not mb:
            continue
        rep.add(f"AM depth {ch}", ma["am"]["depth_db"], mb["am"]["depth_db"],
                abs(ma["am"]["depth_db"] - mb["am"]["depth_db"]), rep.tol_db, " dB")
        if max(ma["am"]["depth_db"], mb["am"]["depth_db"]) > 1:
            rep.add(f"AM rate {ch}", ma["am"]["rate_hz"], mb["am"]["rate_hz"],
                    rel(ma["am"]["rate_hz"], mb["am"]["rate_hz"]), rep.tol_rel)
        fa, fb = ma["fm"]["depth_cents"], mb["fm"]["depth_cents"]
        rep.add(f"FM depth {ch} (cents)", fa, fb, None if fa is None or fb is None else abs(fa - fb), 2.0)

    for k in ("left_to_left_db", "left_to_right_db", "right_to_left_db", "right_to_right_db"):
        x, y = a["stereo"][k], b["stereo"][k]
        tol = rep.tol_db if max(x, y) > -60 else 20.0
        rep.add(f"stereo {k[:-3]}", x, y, abs(x - y), tol, " dB")

    for ch in range(2):
        x, y = a["silence"]["rms_db"][ch], b["silence"]["rms_db"][ch]
        tol = 3.0 if max(x, y) > -100 else 200.0
        rep.add(f"silence RMS ch{ch + 1}", x, y, abs(x - y), tol, " dB")


def pairs(da, db_, ids):
    fa = {os.path.splitext(f)[0]: f for f in os.listdir(da) if f.endswith(".json")}
    fb = {os.path.splitext(f)[0]: f for f in os.listdir(db_) if f.endswith(".json")}
    out = [(k, os.path.join(da, fa[k]), os.path.join(db_, fb[k])) for k in sorted(fa) if k in fb]
    if ids:
        def by_id(files):
            m = {}
            for stem, f in files.items():
                hits = [i for i in ids if stem == i or stem.endswith(i) or stem.endswith(i + "]")]
                if hits:
                    m[max(hits, key=len)] = f
            return m
        ma, mb = by_id(fa), by_id(fb)
        seen = {k for k, _, _ in out}
        out += [(i, os.path.join(da, ma[i]), os.path.join(db_, mb[i])) for i in ids
                if i in ma and i in mb and i not in seen]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a", help="Live's results (folder or one .json)")
    ap.add_argument("b", help="Suhina's results (folder or one .json)")
    ap.add_argument("--cases", help="cases.built.json, to pair files by case id")
    ap.add_argument("--tol-db", type=float, default=0.5)
    ap.add_argument("--tol-rel", type=float, default=0.1, help="relative tolerance for times and rates")
    ap.add_argument("--tol-ms", type=float, default=0.5)
    ap.add_argument("-v", "--verbose", action="store_true", help="print passing lines too")
    x = ap.parse_args(argv)
    if os.path.isdir(x.a) and os.path.isdir(x.b):
        ids = []
        if x.cases:
            with open(x.cases) as f:
                ids = [c["id"] for c in json.load(f).get("cases", [])]
        todo = pairs(x.a, x.b, ids)
        if not todo:
            print("no pairs of results with matching names", file=sys.stderr)
            return 2
    else:
        todo = [(os.path.basename(x.a), x.a, x.b)]
    failed = 0
    for name, pa, pb in todo:
        with open(pa) as f:
            a = json.load(f)
        with open(pb) as f:
            b = json.load(f)
        rep = Report(x.tol_db, x.tol_rel, x.tol_ms)
        compare(a, b, rep)
        failed += rep.fail
        print(f"== {name}: {'DIFFERENT' if rep.fail else 'match'}")
        for what, va, vb, d, ok in rep.rows:
            if x.verbose or ok != "ok":
                print(f"   {ok:4}  {what:52} {va:>10} {vb:>10}  {d}")
    print(f"{len(todo) - failed} of {len(todo)} within tolerance")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
