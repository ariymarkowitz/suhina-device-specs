# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""CC Control behaviour runs for tools/harness/midi_set.py (see its docstring for the format).
Plan steps refer to live-12/midi-effects/30.02-cc-control.md › Measurement plan.

The device's output is CCs, pitch bend and pressure, which a recording keeps as the recorded
clips' envelopes, not as notes: `midi_set.py read` gives only the notes (B7's pass-through), and
the messages are read from the set saved after the recording (its recorder tracks' clip
envelopes; no reader for them yet). Custom B .. M keep the CC Types they load with, which are
stored state, not parameters.

Not taken: the CC Type list and other CC Types (B0, B1: not parameters), Send and Learn (B3,
B6: buttons, UI), a clip's own Mod Wheel envelope merged with the device's (B5) and CCs in the
input (B7: the set builder writes no clip envelopes), very fast ramps (B8: automation steps
only)."""

DEVICE = "CC Control"

NOTES = {"length": 16, "notes": [[60 + 2 * i, i, 0.5, 100] for i in range(16)]}


def steps(values):
    """An envelope stepping through `values`, one per beat from beat 0."""
    return [[i, v] for i, v in enumerate(values)]


RUNS = [
    {"name": "cc-control-static", "plan": "B4, B7",
     "question": "what the device sends when the take starts with Mod Wheel 64, Pitch Bend +32, Pressure 100, Custom A on and Custom B 90 (nothing moved); notes pass unchanged",
     "clip": NOTES, "base": {},
     "cases": [["set", {"Mod Wheel": 64, "Pitch Bend": 32, "Pressure": 100, "Custom A": {"item": "On"}, "Custom B": 90}]]},

    {"name": "cc-control-steps", "plan": "B1, B2, B8",
     "question": "the messages for each control stepped through 0, 1, 64, 127 (Pitch Bend -64, 0, 64), and Custom A off/on: type, number, value, timing",
     "clip": NOTES, "base": {},
     "cases": [["mod-wheel", {}, {"automation": {"Mod Wheel": steps((0, 1, 64, 127, 0))}}],
               ["pitch-bend", {}, {"automation": {"Pitch Bend": steps((0, -64, 0, 64, 0))}}],
               ["pressure", {}, {"automation": {"Pressure": steps((0, 1, 64, 127, 0))}}],
               ["custom-a", {}, {"automation": {"Custom A": steps(({"item": "Off"}, {"item": "On"}, {"item": "Off"}, {"item": "On"}))}}],
               ["custom-b", {}, {"automation": {"Custom B": steps((0, 1, 64, 127, 0))}}],
               ["custom-m", {}, {"automation": {"Custom M": steps((0, 1, 64, 127, 0))}}]]},
]
