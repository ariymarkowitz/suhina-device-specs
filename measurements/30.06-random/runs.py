# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Random behaviour runs for tools/harness/midi_set.py (see its docstring for the format).
Plan steps refer to live-12/midi-effects/30.06-random.md › Measurement plan.

The device loads with Chance 0 % [dump 12.4.6], so every run sets Chance. Not taken: the LED,
a clip whose scale changes during playback (step 7), CCs, pitch bend and MPE (step 8), notes on
two channels (step 5: clips play on one channel). Repeatability across playbacks and after a
transport restart (step 4) needs a second take; `random-repeat` has identical instances for
the instance-to-instance part."""

DEVICE = "Random"

# C3, a note per 1/16, 512 notes (the plan asks for about 2000)
R = {"length": 128, "notes": [[60, 0.25 * i, 0.125, 100] for i in range(512)]}
# the first 64 notes of R, for the sequences of Alt
R64 = {"length": 16, "notes": R["notes"][:64]}
FULL = {"Chance": 1.0}


def ci(c, i):
    return {"Choices": c, "Interval": i}


def repeated(pitches, n, scale=None):
    notes = [[p, 0.25 * (k * len(pitches) + j), 0.125, 100] for k in range(n) for j, p in enumerate(pitches)]
    clip = {"length": 0.25 * n * len(pitches), "notes": notes}
    if scale:
        clip["scale"] = scale
    return clip


RUNS = [
    {"name": "random-pool", "plan": "1",
     "question": "set and frequency of shifts at Chance 100 % for Choices/Interval 1/1, 3/1, 3/2, 12/1, 1/12, 24/12 (does 0 occur, uniform?); Chance 25, 50, 75 % at 12/1",
     "clip": R, "base": dict(FULL, **ci(12, 1)),
     "cases": [[f"c{c}-i{i}", ci(c, i)] for c, i in ((1, 1), (3, 1), (3, 2), (1, 12), (24, 12))] +
              [[f"chance{p}", {"Chance": p / 100}] for p in (25, 50, 75)]},

    {"name": "random-sign", "plan": "2",
     "question": "Sub and Bi at 12/1 and 3/2: pool, symmetry, share of each sign",
     "clip": R, "base": dict(FULL, **ci(12, 1)),
     "cases": [[f"{s.lower()}-c{c}-i{i}", dict(ci(c, i), Sign={"item": s})] for s in ("Sub", "Bi") for c, i in ((12, 1), (3, 2))]},

    {"name": "random-alt", "plan": "3",
     "question": "Alt at Chance 100 %: the sequence for 12/1, 2/2, 3/4 (first output, cycle, restart); Chance 50 % and 0 % (does a failed test advance the counter); Alt with Sub and Bi",
     "clip": R64, "base": dict(FULL, **ci(12, 1), Mode={"item": "Alt"}),
     "cases": [["c2-i2", ci(2, 2)], ["c3-i4", ci(3, 4)], ["chance50", {"Chance": 0.5}], ["chance0", {"Chance": 0.0}],
               ["sub-c3-i1", dict(ci(3, 1), Sign={"item": "Sub"})], ["bi-c3-i1", dict(ci(3, 1), Sign={"item": "Bi"})]]},

    {"name": "random-repeat", "plan": "4",
     "question": "two and three identical instances (Chance 100 %, 12/1, Rnd) on the same clip: the same sequence or not",
     "clip": R64, "base": dict(FULL, **ci(12, 1)),
     "cases": [["copy1", {}, {"copy": 1}], ["copy2", {}, {"copy": 2}]]},

    {"name": "random-noteoff", "plan": "5",
     "question": "C3 held 4 beats with C3 retriggered inside it, and a chord of unequal lengths: each output note-on against its note-off; Choices stepping 12 -> 1 between a note-on and its note-off",
     "clip": {"length": 10, "notes": [[60, 0, 4, 100], [60, 1, 0.5, 100], [60, 2, 0.5, 100], [60, 3, 0.5, 100],
                                      [60, 6, 1, 100], [64, 6, 2, 100], [67, 6, 3, 100]]},
     "base": dict(FULL, **ci(12, 1)),
     "cases": [["choices-step", {}, {"clip": {"length": 6, "notes": [[60, 0, 4, 100]] + [[64, 0.5 * k, 0.25, 100] for k in range(8)]},
                                     "automation": {"Choices": [[0, 12], [2, 1]]}}],
               ["off-on", {}, {"clip": {"length": 10, "notes": [[60, 0, 8, 100]] + [[64, 0.5 * k, 0.25, 100] for k in range(16)]},
                               "automation": {"Device On": [[0, {"item": "On"}], [3, {"item": "Off"}], [6, {"item": "On"}]]}}]]},

    {"name": "random-limits", "plan": "6",
     "question": "input pitches 0, 1, 126, 127 at Choices 24 Interval 12 and 24/1, Add and Sub: dropped, clamped, folded or redrawn",
     "clip": repeated((0, 1, 126, 127), 32), "base": dict(FULL, **ci(24, 12)),
     "cases": [["sub", {"Sign": {"item": "Sub"}}], ["add-c24-i1", ci(24, 1)], ["sub-c24-i1", dict(ci(24, 1), Sign={"item": "Sub"})]]},

    {"name": "random-scale", "plan": "7; common C4",
     "question": "Use Current Scale on, Chance 100 %, Choices 3 and Interval 1 and 2, on C3, D3 and C#3 in C major; then C minor pentatonic and no clip scale",
     "clip": repeated((60, 62, 61), 64, ["C", "Major"]),
     "base": dict(FULL, **ci(3, 1), **{"Use Current Scale": {"item": "On"}}),
     "cases": [["i2", ci(3, 2)],
               ["minor-pentatonic", {}, {"clip": repeated((60, 62, 61), 64, ["C", "Minor Pentatonic"])}],
               ["no-scale", {}, {"clip": repeated((60, 62, 61), 64)}]]},

    {"name": "random-chords", "plan": "9",
     "question": "three simultaneous notes in Alt and Rnd at Chance 100 %: one step per note or per chord",
     "clip": {"length": 16, "notes": [[p, 0.5 * k, 0.25, 100] for k in range(32) for p in (60, 64, 67)]},
     "base": dict(FULL, **ci(12, 1), Mode={"item": "Alt"}),
     "cases": [["rnd", {"Mode": {"item": "Rnd"}}]]},
]
