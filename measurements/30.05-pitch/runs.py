# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Pitch behaviour runs for tools/harness/midi_set.py (see its docstring for the format).
Plan steps refer to live-12/midi-effects/30.05-pitch.md › Measurement plan.

Not taken: the LED (step 6, view only), Step Up / Down (step 7: buttons, not parameters; a set
must not be changed through set_device_parameter), MPE pitch bend (step 10: the set builder
writes no per-note expression). Latency (step 11) is every run's `bypass` against `default`."""

DEVICE = "Pitch"

# every pitch 0 .. 127 once, a note every half beat (clip A, at twice the plan's rate)
ALL = {"length": 64, "notes": [[p, p / 2, 0.25, 100] for p in range(128)]}
# C3 to C4 chromatic, a note per half beat (clip B)
CHROMATIC = [[60 + i, i / 2, 0.25, 100] for i in range(13)]


def chromatic(scale):
    return {"length": 7, "notes": CHROMATIC, "scale": scale}


RUNS = [
    {"name": "pitch-transpose", "plan": "2",
     "question": "output pitch per input pitch for Pitch +1, +12, -12, +127, -128, +128 (Range 127): which notes are lost at the ends",
     "clip": ALL, "base": {},
     "cases": [[f"pitch{v:+d}", {"Pitch": v}] for v in (1, 12, -12, 127, -128, 128)]},

    {"name": "pitch-block", "plan": "3",
     "question": "Block window Lowest C3 Range 12: pass band and inclusive edges; with Pitch +24, does the window test the input or the output; Range 0",
     "clip": ALL, "base": {"Lowest": 60, "Range": 12},
     "cases": [["pitch+24", {"Pitch": 24}], ["range0", {"Range": 0}]]},

    {"name": "pitch-fold", "plan": "4",
     "question": "Fold law for Lowest C3 and Range 11, 7, 12, 0, 24; the order of fold and transposition at Pitch +5 and +12",
     "clip": ALL, "base": {"Mode": {"item": "Fold"}, "Lowest": 60, "Range": 11},
     "cases": [[f"range{r}", {"Range": r}] for r in (7, 12, 0, 24)] +
              [[f"range11-pitch+{p}", {"Pitch": p}] for p in (5, 12)]},

    {"name": "pitch-limit", "plan": "5",
     "question": "Limit law for Lowest C3 and Range 11, 7, 12, 0, 24, and with Pitch +5 and +12",
     "clip": ALL, "base": {"Mode": {"item": "Limit"}, "Lowest": 60, "Range": 11},
     "cases": [[f"range{r}", {"Range": r}] for r in (7, 12, 0, 24)] +
              [[f"range11-pitch+{p}", {"Pitch": p}] for p in (5, 12)]},

    {"name": "pitch-degrees", "plan": "8; common C4",
     "question": "scale-degree transposition with Use Current Scale on: +1, +2, +7, -1 degrees in C major on C3..C4 chromatic (out-of-scale notes), then D Dorian, C minor pentatonic and no clip scale; Lowest and Range in semitones or degrees",
     "clip": chromatic(["C", "Major"]), "base": {"Use Current Scale": {"item": "On"}},
     "cases": [[f"major{d:+d}", {"Pitch Scale Degrees": d}] for d in (1, 2, 7, -1)] +
              [[f"dorian{d:+d}", {"Pitch Scale Degrees": d}, {"clip": chromatic(["D", "Dorian"])}] for d in (1, 7)] +
              [[f"minpent{d:+d}", {"Pitch Scale Degrees": d}, {"clip": chromatic(["C", "Minor Pentatonic"])}] for d in (1, 5)] +
              [[f"noscale{d:+d}", {"Pitch Scale Degrees": d}, {"clip": chromatic(None)}] for d in (1, 2)] +
              [["window-62-5", {"Lowest": 62, "Range": 5}]]},

    {"name": "pitch-noteoff", "plan": "9; common C1",
     "question": "a held C3 (and a held chord) while Pitch steps 0 -> +5 at beat 2: the pitch and time of the note-off; the device switched off at beat 4 and on at beat 6 with Pitch +12 under a held chord",
     "clip": {"length": 12, "notes": [[60, 0, 4, 100], [48, 0, 8, 100], [64, 0, 8, 100], [67, 0, 8, 100]]},
     "base": {},
     "cases": [["pitch-step", {}, {"automation": {"Pitch": [[0, 0], [2, 5]]}}],
               ["off-on", {"Pitch": 12}, {"automation": {"Device On": [[0, {"item": "On"}], [4, {"item": "Off"}], [6, {"item": "On"}]]}}]]},
]
