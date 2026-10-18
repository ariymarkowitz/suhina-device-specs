# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Velocity behaviour runs for tools/harness/midi_set.py (see its docstring for the format).
Plan steps refer to live-12/midi-effects/30.08-velocity.md › Measurement plan.

The device loads with Operation Both, Lowest 1 and Out Low 1 [dump 12.4.6]; the runs keep that
unless they say otherwise. Not taken: two Gate devices in a Rack (step 3: the set builder puts
one device on a track), the display (step 8). Repeatability across playbacks (step 4) needs a
second take; the run has two identical instances for the instance-to-instance part."""

DEVICE = "Velocity"

# C3, a note per 1/16 with velocities 1 .. 127 (clip V); and the copy whose release velocity
# is the same number
V = {"length": 32, "notes": [[60, i * 0.25, 0.125, i + 1] for i in range(127)]}
VR = {"length": 32, "notes": [[60, i * 0.25, 0.125, i + 1, i + 1] for i in range(127)]}
# 512 notes of constant velocity, one per 1/16 (the plan asks for 2000)
CONST100 = {"length": 128, "notes": [[60, i * 0.25, 0.125, 100] for i in range(512)]}
CONST60 = {"length": 128, "notes": [[60, i * 0.25, 0.125, 60] for i in range(512)]}

LEVELS = (-1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1)


def tag(x):
    return f"{x:+g}".replace(".", "p")


RUNS = [
    {"name": "velocity-drive", "plan": "1",
     "question": "output against input velocity for Drive -1 .. 1; Out Low 0 / Out Hi 127, and Out Low 40 / Out Hi 100 at Drive 0 and 0.5",
     "clip": V, "base": {},
     "cases": [[f"drive{tag(d)}", {"Drive": d}] for d in LEVELS] +
              [["out-0-127", {"Out Low": 0}], ["out-40-100", {"Out Low": 40, "Out Hi": 100}],
               ["out-40-100-drive+0p5", {"Out Low": 40, "Out Hi": 100, "Drive": 0.5}]]},

    {"name": "velocity-compand", "plan": "2",
     "question": "Compand -1 .. 1, and Drive 0.5 with Compand +0.5 and -0.5 (do they commute)",
     "clip": V, "base": {},
     "cases": [[f"compand{tag(c)}", {"Compand": c}] for c in LEVELS] +
              [["drive+0p5-compand+0p5", {"Drive": 0.5, "Compand": 0.5}],
               ["drive+0p5-compand-0p5", {"Drive": 0.5, "Compand": -0.5}]]},

    {"name": "velocity-window", "plan": "3",
     "question": "Lowest 40 Range 40 in Clip, Gate and Fixed; Lowest 0 Range 80, Lowest 80 Range 127, Range 1 and 0: which velocities pass, inclusive edges, what the outside velocities become",
     "clip": V, "base": {"Lowest": 40, "Range": 40},
     "cases": [[f"{m.lower()}-40-40", {"Mode": {"item": m}}] for m in ("Clip", "Gate", "Fixed")] +
              [[f"{m.lower()}-{lo}-{r}", {"Mode": {"item": m}, "Lowest": lo, "Range": r}]
               for m in ("Clip", "Gate") for lo, r in ((0, 80), (80, 127), (40, 1), (40, 0))] +
              [["fixed-out-100", {"Mode": {"item": "Fixed"}, "Out Hi": 100}]]},

    {"name": "velocity-random", "plan": "4",
     "question": "histogram of outputs for input 100 (and 60) with Out Low 60, Out Hi 127 and Random 50, 10, 64; Random with Fixed and Gate; two identical instances",
     "clip": CONST100, "base": {"Out Low": 60, "Out Hi": 127, "Random": 50},
     "cases": [["random10", {"Random": 10}], ["random64", {"Random": 64}],
               ["in60", {}, {"clip": CONST60}],
               ["fixed", {"Mode": {"item": "Fixed"}}], ["gate", {"Mode": {"item": "Gate"}, "Lowest": 80, "Range": 40}],
               ["copy", {}, {"copy": 1}]]},

    {"name": "velocity-operation", "plan": "5",
     "question": "Operation Velocity, Rel. Vel. and Both on clip V with release velocity = velocity: which of the two values each changes (Drive 0.5, Out 40 .. 100)",
     "clip": VR, "base": {"Drive": 0.5, "Out Low": 40, "Out Hi": 100},
     "cases": [[op.lower().replace(". ", "-").replace(".", ""), {"Operation": {"item": op}}]
               for op in ("Velocity", "Rel. Vel.", "Both")]},

    {"name": "velocity-release", "plan": "6",
     "question": "release velocities 0, 1, 64, 127 through Rel. Vel. in Gate mode with a window of 40 .. 80: do the note-ons pass and the note-offs vanish, or are both dropped",
     "clip": {"length": 8, "notes": [[60, i, 0.5, 100, r] for i, r in enumerate((0, 1, 64, 127, 40, 80, 81))]},
     "base": {"Operation": {"item": "Rel. Vel."}, "Mode": {"item": "Gate"}, "Lowest": 40, "Range": 40},
     "cases": [["clip-mode", {"Mode": {"item": "Clip"}}], ["fixed-mode", {"Mode": {"item": "Fixed"}, "Out Hi": 90}]]},

    {"name": "velocity-extremes", "plan": "7",
     "question": "Out Hi below Out Low (100 / 20), with Random 20 and with Drive 0.5; Out Hi = Out Low = 64; Lowest 127 Range 0 in Clip and Gate",
     "clip": V, "base": {},
     "cases": [["inverted", {"Out Low": 100, "Out Hi": 20}],
               ["inverted-random20", {"Out Low": 100, "Out Hi": 20, "Random": 20}],
               ["inverted-drive+0p5", {"Out Low": 100, "Out Hi": 20, "Drive": 0.5}],
               ["out-64-64", {"Out Low": 64, "Out Hi": 64}],
               ["clip-127-0", {"Lowest": 127, "Range": 0}],
               ["gate-127-0", {"Lowest": 127, "Range": 0, "Mode": {"item": "Gate"}}]]},

    {"name": "velocity-held", "plan": "9; common C1",
     "question": "a note held over a step of Out Hi 127 -> 40 (its release velocity), and the device switched off and on under held notes with Out 40 .. 60",
     "clip": {"length": 10, "notes": [[60, 0, 4, 100, 100], [64, 0, 8, 100, 100], [67, 5, 1, 100, 100]]},
     "base": {},
     "cases": [["out-hi-step", {}, {"automation": {"Out Hi": [[0, 127], [2, 40]]}}],
               ["off-on", {"Out Low": 40, "Out Hi": 60},
                {"automation": {"Device On": [[0, {"item": "On"}], [3, {"item": "Off"}], [6, {"item": "On"}]]}}]]},
]
