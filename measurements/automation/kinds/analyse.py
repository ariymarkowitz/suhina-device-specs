# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Checks the polled lanes (poll.py) against how Live is supposed to play them.

    tools/.venv/bin/python measurements/automation/kinds/analyse.py

Reads live/kinds.poll.json and live/kinds-negative.poll.json and prints, per lane:

- integer lanes (Resonators I Note, Corpus Transpose): how many samples each way of making the
  moving value whole (floor, truncation toward zero, rounding, ceiling) gets wrong against the
  lane's Bezier (a straight lane is a Bezier on the diagonal);
- frequency lanes (EQ Eight 3 Frequency A, whose API value is the knob position): the largest
  distance from the Bezier in position;
- choice and toggle lanes: the beats at which the value changes.

Numpy is not needed.
"""

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MILD = (0.15234375, 0.54296875, 0.45703125, 0.84765625)  # a medium bend of Live's own family
EASE = (1, 0, 1, 0)                                      # the extreme bend

# lane -> (start, end, length in beats, Bezier controls or None for straight)
INTEGER = {
    "resonators note-line": (36, 72, 32, None),
    "resonators note-bend-ease": (36, 72, 32, EASE),
    "resonators note-bend-mild": (36, 72, 32, MILD),
    "resonators note-up-1": (40, 41, 8, None),
    "resonators note-down-1": (41, 40, 8, None),
    "resonators note-frac-end": (40, 40.5, 8, None),
    "corpus transpose-down": (3, -3, 12, None),
    "corpus transpose-up": (-3, 3, 12, None),
}
FREQUENCY = {"eq-eight freq-line": None, "eq-eight freq-bend-ease": EASE, "eq-eight freq-bend-mild": MILD}
WAYS = {
    "floor": lambda p: math.floor(p + 1e-9),
    "toward zero": lambda p: math.trunc(p + (1e-9 if p >= 0 else -1e-9)),
    "round": lambda p: math.floor(p + 0.5),
    "ceiling": lambda p: math.ceil(p - 1e-9),
}


def bezier(c, x):
    """y of the cubic Bezier (0,0) (x1,y1) (x2,y2) (1,1) at time share x."""
    if c is None or x >= 1:
        return min(x, 1)
    x1, y1, x2, y2 = c
    lo, hi = 0.0, 1.0
    for _ in range(80):
        t = (lo + hi) / 2
        if 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t * t * x2 + t ** 3 < x:
            lo = t
        else:
            hi = t
    t = (lo + hi) / 2
    return 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3


def changes(r):
    out = [(r["beats"][0], r["values"][0])]
    for b, v in zip(r["beats"][1:], r["values"][1:]):
        if v != out[-1][1]:
            out.append((b, v))
    return out


def main():
    lanes = {}
    for f in ("kinds.poll.json", "kinds-negative.poll.json"):
        lanes.update(json.load(open(os.path.join(HERE, "live", f))))
    print("integer lanes: samples wrong (of n) for each way of making the value whole")
    for name, (a0, a1, length, c) in INTEGER.items():
        r = lanes[name]
        wrong = {k: 0 for k in WAYS}
        for b, v in zip(r["beats"], r["values"]):
            p = a0 + (a1 - a0) * bezier(c, min(b / length, 1))
            for k, f in WAYS.items():
                wrong[k] += f(p) != v
        print(f"  {name:28s} n={len(r['beats'])}  " + "  ".join(f"{k} {n}" for k, n in wrong.items()))
    print("frequency lanes: largest distance from the Bezier in position (the knob's 0..1)")
    for name, c in FREQUENCY.items():
        r = lanes[name]
        p0, p1 = r["values"][0], r["values"][-1]
        e = max(abs(v - (p0 + (p1 - p0) * bezier(c, b / 32))) for b, v in zip(r["beats"], r["values"]) if b <= 32)
        print(f"  {name:28s} {e:.5f} of a {p1 - p0:.4f} span")
    print("choice and toggle lanes: (beat, value) at each change")
    for name, r in lanes.items():
        if name.startswith(("auto-pan", "resonators on")):
            print(f"  {name:28s} {changes(r)}")


if __name__ == "__main__":
    main()
