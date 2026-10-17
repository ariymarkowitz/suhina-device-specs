# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Looper behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.25-looper.md › Measurement plan.

Almost nothing of the Looper is measurable in a static render: its behaviour is a state machine
driven by button presses during playback (Record, Play, Overdub, Stop, Clear, Undo, x2, /2,
the octave buttons), and none of those can be pressed during the export. The one thing a static
render can show is what the `State` and `Monitor` parameters do from the first sample, so the
single run below samples that. Tempo Control, Song Control and Quantization are set so that the
device cannot move the set's tempo or wait for a bar line.

Left out (cannot be measured this way): maximum length (plan 3), Feedback and Overdub passes (4),
Reverse and Undo semantics (5, 6), tempo guess (7), Quantization offsets (8), Song/Tempo Control (10),
fixed Record Length (11, not a parameter), crossfade lengths (12), Speed against pitch of a recorded
loop (2, needs a recording; Speed does nothing to an empty buffer), Record Length's list (1).
"""

DEVICE = "Looper"

# No tempo or transport changes, act at once.
BASE = {"Tempo Control": {"item": "None"}, "Song Control": {"item": "None"},
        "Quantization": {"item": "None"}}


def case(cid, state, monitor):
    return [cid, {"State": {"item": state}, "Monitor": {"item": monitor}}]


RUNS = [
    {"name": "looper-monitor-states", "plan": "9", "probe": "gap2", "read": ["silence", "static", "raw render (is anything but the input heard?)"], "priority": 3,
     "why": "when the input is audible in each State for each Input -> Output choice, and whether a State set from the start records and plays back anything",
     "question": "output level with the state fixed from the first sample: Stop with Never, Rec/OVR, Rec/OVR/Stop; Record with Never and Rec/OVR; Play with Rec/OVR and Rec/OVR/Stop; Overdub with Rec/OVR/Stop (default: Stop, Always)",
     "base": BASE,
     "cases": [case("stop-never", "Stop", "Never"), case("stop-recovr", "Stop", "Rec/OVR"),
               case("stop-recovrstop", "Stop", "Rec/OVR/Stop"), case("record-never", "Record", "Never"),
               case("record-recovr", "Record", "Rec/OVR"), case("play-recovr", "Play", "Rec/OVR"),
               case("play-recovrstop", "Play", "Rec/OVR/Stop"), case("overdub-recovrstop", "Overdub", "Rec/OVR/Stop")]},
]
