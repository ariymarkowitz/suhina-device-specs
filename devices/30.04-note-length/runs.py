# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Note Length behaviour runs for tools/harness/midi_set.py (see its docstring for the format).
Plan steps refer to live-12/midi-effects/30.04-note-length.md › Measurement plan.

Trigger Source shows Off / On [dump 12.4.6] and loads Off; which of the two is Note Off is
open (step 1), so the runs say `on` for the state the device does not load with and the
recording settles which one it is (the output starts at the input's note-off in Note Off mode).

Not taken: tempo automation (step 4: one tempo per set), CC 64 around the Latch keys (step 9:
the set builder writes no clip envelopes), a note held across a clip's loop end and a transport
stop (step 11: no looped clips; stopping is the user's), MPE (step 12). Synced lengths at a
second tempo (step 3) need a second set at 90 BPM."""

DEVICE = "Note Length"

ON = {"Trigger Source": {"item": "On"}}
# clip A: C3 for 1 beat, 1/16 and 2 beats, 12 beats apart (room for a 5 s output at 120 BPM)
A = {"length": 36, "notes": [[60, 0, 1, 100], [60, 12, 0.0625, 100], [60, 24, 2, 100]]}
# clip B: octaves of C, each 1 beat, 4 beats apart
B = {"length": 28, "notes": [[24 + 12 * i, 4 * i, 1, 100] for i in range(7)]}
# clip C: velocity 1, 64, 127 against release velocity 1, 64, 127, 2 beats apart
C = {"length": 18, "notes": [[60, 2 * (3 * i + j), 1, v, r]
                             for i, v in enumerate((1, 64, 127)) for j, r in enumerate((1, 64, 127))]}
# held for 100 ms, 250 ms, 500 ms and 1 s at 120 BPM, 4 beats apart, release velocity 64
HOLDS = {"length": 16, "notes": [[60, 4 * i, d, 100] for i, d in enumerate((0.2, 0.5, 1, 2))]}
# clip D: a chord played together, two notes overlapping, then a separate gesture
D = {"length": 20, "notes": [[60, 0, 4, 100], [64, 0, 4, 100], [67, 0, 4, 100],
                             [60, 8, 2, 100], [64, 9, 2, 100], [67, 14, 1, 100]]}
# the same pitch every 1/8 note
REPEAT = {"length": 8, "notes": [[60, 0.5 * i, 0.25, 100] for i in range(8)]}

RUNS = [
    {"name": "note-length-time", "plan": "2",
     "question": "output length against Length (100 ms, 500 ms, 1 s, 5 s, the minimum) and Gate (1, 25, 50, 200 % at 500 ms) in the loaded trigger mode",
     "clip": A, "base": {},
     "cases": [[f"len-{int(s * 1000)}ms", {"Time Length": {"display": s}}] for s in (0.5, 1.0, 5.0)] +
              [["len-min", {"Time Length": {"norm": 0.0}}]] +
              [[f"gate-{g}", {"Time Length": {"display": 0.5}, "Gate": g}] for g in (1, 25, 50, 200)]},

    {"name": "note-length-sync", "plan": "3",
     "question": "output length in beats at each of the 10 Synced Length steps (0, 1/64 .. 1/4) at 120 BPM",
     "clip": A, "base": {"Sync On": {"item": "On"}},
     "cases": [[f"step{i}", {"Synced Length": i}] for i in (0, 1, 2, 3, 5, 6, 7, 8, 9)]},

    {"name": "note-length-trigger", "plan": "5",
     "question": "the other Trigger Source state with Length 200 ms: does the output start at the input's note-off, for inputs of 1 beat, 1/16 and 2 beats",
     "clip": A, "base": {"Time Length": {"display": 0.2}},
     "cases": [["on", ON]]},

    {"name": "note-length-velocity", "plan": "6",
     "question": "Note Off mode output velocity against note-on and release velocity for Release Velocity 0, 50, 100 % (no decay); Decay 100 ms .. 2 s against held times 100 ms .. 1 s; both together",
     "clip": C, "base": dict(ON, **{"Time Length": {"display": 0.2}}),
     "cases": [[f"relvel-{r}", {"Release Velocity": r}] for r in (50, 100)] +
              [[f"decay-{int(s * 1000)}ms", {"Decay Time": {"display": s}}, {"clip": HOLDS}] for s in (0.1, 0.5, 1.0, 2.0)] +
              [["relvel-50-decay-500ms", {"Release Velocity": 50, "Decay Time": {"display": 0.5}}, {"clip": HOLDS}]]},

    {"name": "note-length-keyscale", "plan": "7, 8",
     "question": "Decay Key Scale -1, -0.5, 0.5, 1 on the octaves of C in Note Off mode with Decay 500 ms: output length and velocity per pitch (pivot and law); Key Scale, Release Velocity and Decay at extremes in Note On mode",
     "clip": B, "base": dict(ON, **{"Time Length": {"display": 0.5}, "Decay Time": {"display": 0.5}}),
     "cases": [[f"keyscale{k:+g}".replace(".", "p"), {"Decay Key Scale": k}] for k in (-1, -0.5, 0.5, 1)] +
              [["noteon-extremes", {"Trigger Source": {"item": "Off"}, "Decay Key Scale": 1, "Release Velocity": 100, "Decay Time": {"display": 0.1}}],
               ["noteon-extremes-c", {"Trigger Source": {"item": "Off"}, "Decay Key Scale": 1, "Release Velocity": 100, "Decay Time": {"display": 0.1}}, {"clip": C}]]},

    {"name": "note-length-latch", "plan": "9",
     "question": "Latch in both trigger modes on a chord played together, two overlapping notes and a separate note: start and end of each output",
     "clip": D, "base": {"Latch": {"item": "On"}, "Time Length": {"display": 0.5}},
     "cases": [["on", ON]]},

    {"name": "note-length-repeat", "plan": "10",
     "question": "the same pitch every 1/8 note with Length 500 ms (outputs overlap): how the overlapping same-pitch notes are ended, in both modes",
     "clip": REPEAT, "base": {"Time Length": {"display": 0.5}},
     "cases": [["on", ON]]},

    {"name": "note-length-held", "plan": "11; common C1",
     "question": "the device switched off at beat 2 and on at beat 4 while a 5 s output note sounds (in Note On mode), and while the input is held (Note Off mode)",
     "clip": {"length": 16, "notes": [[60, 0, 1, 100], [64, 0, 6, 100]]},
     "base": {"Time Length": {"display": 5.0}},
     "cases": [["off-on", {}, {"automation": {"Device On": [[0, {"item": "On"}], [2, {"item": "Off"}], [4, {"item": "On"}]]}}],
               ["on-off-on", ON, {"automation": {"Device On": [[0, {"item": "On"}], [2, {"item": "Off"}], [4, {"item": "On"}]]}}]]},
]
