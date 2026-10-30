# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Writes the Reverb's cases files (one per Live run) beside this script.

    tools/.venv/bin/python devices/29.32-reverb/make_cases.py

Each run sets several parameters per case, which `cases.py sweep` cannot, so the cases are listed
here. Every name is checked against the dump. Value specs are those of cases.py: `{"norm": x}`,
`{"display": x}` in base units (s, Hz, dB, %), `{"item": "Lowpass"}`, or a bare internal value.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools", "harness"))
import cases  # noqa: E402

DUMP = os.path.join(ROOT, "measurements", "dump-12.4.6.json")

ON, OFF = 1, 0
# Wet only and time-invariant: what most runs start from.
STATIC = {"Dry/Wet": {"norm": 1.0}, "Chorus On": OFF, "ER Spin On": OFF}
# The early reflections alone (Diffuse at its minimum, -30 dB) or the tail alone.
ER_ONLY = {"Diffuse Level": {"norm": 0.0}}
TAIL_ONLY = {"Reflect Level": {"norm": 0.0}}
SHORT = {"Decay Time": {"norm": 0.0}}  # 200 ms


def run(cases_list, base):
    out = [{"id": "bypass", "params": {"Device On": OFF}},
           {"id": "preset", "params": {}},
           {"id": "default", "params": dict(base)}]
    for cid, params in cases_list:
        p = dict(base)
        p.update(params)
        out.append({"id": cid, "params": p})
    return out


def structure():
    c = []
    for ms in (0.5, 2.5, 10, 50, 250):
        c.append((f"predelay-{ms:g}ms", {**ER_ONLY, **SHORT, "Predelay": {"display": ms / 1000}}))
    c.append(("er-only", ER_ONLY))
    c.append(("tail-only", TAIL_ONLY))
    for s in (0.0, 0.25, 0.5, 0.75, 1.0):
        c.append((f"shape-{s:g}", {"ER Shape": {"display": s}}))
    for s in (0.22, 1.53, 10.54, 100, 500):
        c.append((f"size-{s:g}-er", {**ER_ONLY, "Room Size": {"display": s}}))
    return run(c, STATIC)


def decay():
    base = {**STATIC, **TAIL_ONLY, "Diff. Hi On": OFF, "Diff. Lo On": OFF}
    c = []
    for norm, label in ((0.0, "0.2s"), (0.25, "0.83s"), (0.5, "3.46s"), (0.75, "14.4s"), (1.0, "60s")):
        c.append((f"decay-{label}", {"Decay Time": {"norm": norm}}))
    for s in (1.53, 10.54, 500):
        c.append((f"decay-3.46s-size-{s:g}", {"Decay Time": {"norm": 0.5}, "Room Size": {"display": s}}))
    c.append(("decay-3.46s-filters-preset", {"Decay Time": {"norm": 0.5}, "Diff. Hi On": ON}))
    return run(c, base)


def filters():
    # Input filter: short tail so the sweep shows the filter more than the room.
    inp = {**STATIC, **SHORT, "In Lo Cut On": OFF, "In Hi Cut On": OFF}
    c = [("input-off", {})]
    for f in (100, 1000, 5000):
        c.append((f"input-locut-{f}Hz", {"In Lo Cut On": ON, "Input Freq": {"display": f}}))
        c.append((f"input-hicut-{f}Hz", {"In Hi Cut On": ON, "Input Freq": {"display": f}}))
    for w in (0.5, 4.75, 9.0):
        c.append((f"input-both-1000Hz-w{w:g}",
                  {"In Lo Cut On": ON, "In Hi Cut On": ON, "Input Freq": {"display": 1000},
                   "Input Width": {"display": w}}))
    # Diffusion-network filters: a long enough tail to read decay per band.
    net = {"Decay Time": {"norm": 0.5}, **TAIL_ONLY, "Diff. Hi On": OFF, "Diff. Lo On": OFF}
    c.append(("net-off", net))
    for typ in ("Shelf", "Lowpass"):
        for g in (0.2, 0.6):
            c.append((f"net-hi-{typ.lower()}-1000Hz-g{g:g}",
                      {**net, "Diff. Hi On": ON, "Diff. Hi Type": {"item": typ},
                       "Diff. Hi Freq": {"display": 1000}, "HiShelf Gain": {"display": g}}))
    for g in (0.2, 0.6):
        c.append((f"net-lo-500Hz-g{g:g}",
                  {**net, "Diff. Lo On": ON, "Diff. Lo Freq": {"display": 500}, "LowShelf Gain": {"display": g}}))
    return run(c, inp)


def texture():
    c = []
    mod = {"Decay Time": {"norm": 0.5}}
    for a in (0.5, 2.0, 4.0):
        c.append((f"chorus-amt{a:g}-1Hz", {**mod, **TAIL_ONLY, "Chorus On": ON,
                                            "Chorus Amount": {"display": a}, "Chorus Rate": {"display": 1}}))
    for r in (0.1, 4.0):
        c.append((f"chorus-amt2-{r:g}Hz", {**mod, **TAIL_ONLY, "Chorus On": ON,
                                            "Chorus Amount": {"display": 2}, "Chorus Rate": {"display": r}}))
    for a, r in ((2, 0.3), (17.5, 0.3), (55, 0.3), (17.5, 1.3)):
        c.append((f"spin-amt{a:g}-{r:g}Hz", {**ER_ONLY, "ER Spin On": ON,
                                             "ER Spin Amount": {"display": a}, "ER Spin Rate": {"display": r}}))
    for s in (0, 60, 120):
        c.append((f"stereo-{s}", {"Stereo Image": {"display": s}}))
    for d in ("Sparse", "Low", "Mid", "High"):
        c.append((f"density-{d.lower()}", {"Density": {"item": d}}))
    small = {"Room Size": {"display": 1.53}}
    for v in (0.1, 48, 96):
        c.append((f"diffusion-{v:g}-size1.53", {**small, "Diffusion": {"display": v}}))
    for v in (5, 100):
        c.append((f"scale-{v:g}-size1.53", {**small, "Scale": {"display": v}}))
    return run(c, STATIC)


def size():
    """Rerun of what the first runs could not show: in them Room Size changed nothing (the preset
    has Smooth = Fast), so these cases set Smooth to None. One case keeps Fast as the control."""
    base = {**STATIC, "Size Smoothing": {"item": "None"}}
    c = []
    for s in (0.22, 1.53, 10.54, 100, 500):
        c.append((f"size-{s:g}-er", {**ER_ONLY, "Room Size": {"display": s}}))
    c.append(("size-1.53-er-smooth-fast", {**ER_ONLY, "Room Size": {"display": 1.53},
                                           "Size Smoothing": {"item": "Fast"}}))
    # T60 against Size at Decay 3.46 s, network filters off.
    tail = {**TAIL_ONLY, "Decay Time": {"norm": 0.5}, "Diff. Hi On": OFF, "Diff. Lo On": OFF}
    for s in (1.53, 10.54, 100, 500):
        c.append((f"decay-3.46s-size-{s:g}", {**tail, "Room Size": {"display": s}}))
    # The tail's onset against Shape.
    for sh in (0.0, 0.25, 0.75, 1.0):
        c.append((f"shape-{sh:g}-tail", {**TAIL_ONLY, "ER Shape": {"display": sh}}))
    small = {"Room Size": {"display": 1.53}}
    for v in (0.1, 48, 96):
        c.append((f"diffusion-{v:g}-size1.53", {**small, "Diffusion": {"display": v}}))
    for v in (5, 100):
        c.append((f"scale-{v:g}-size1.53", {**small, "Scale": {"display": v}}))
    return run(c, base)


RUNS = {
    "reverb-structure": structure,
    "reverb-decay": decay,
    "reverb-filters": filters,
    "reverb-texture": texture,
    "reverb-size": size,
}


def main():
    dump = cases.load_dump(DUMP)
    dev = cases.find_device(dump, "Reverb")
    for name, make in RUNS.items():
        cs = make()
        ids = [k["id"] for k in cs]
        if len(set(ids)) != len(ids):
            raise SystemExit(f"{name}: duplicate case ids")
        for k in cs:
            for p in k["params"]:
                cases.find_param(dev, p)
        path = os.path.join(HERE, name + ".json")
        with open(path, "w") as f:
            f.write(json.dumps({"device": "Reverb", "parameter": name, "cases": cs}, indent=1) + "\n")
        print(f"wrote {os.path.relpath(path, ROOT)}: {len(cs)} cases")


if __name__ == "__main__":
    main()
