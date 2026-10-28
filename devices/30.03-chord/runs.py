# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Chord behaviour runs for tools/harness/midi_set.py (see its docstring for the format).
Plan steps refer to live-12/midi-effects/30.03-chord.md › Measurement plan.

Not taken: Learn (step 7: needs a keyboard and is not a parameter), Play Duplicate Notes When
Strumming (step 9: an option that is not a parameter, so a set cannot be written with it on;
its default state is in the strum cases), the row toggles that switch Velocity and Chance off
(step 3: not parameters), MPE (step 10), and Strum at 60 and 180 BPM (step 4: one tempo per
set). Repeatability across playbacks (step 3) needs a second take; the Chance run has two
identical instances for the instance-to-instance part."""

DEVICE = "Chord"

# clip A: C3 for 1 beat at velocity 100, then 1 and 127, 4 beats apart
A = {"length": 12, "notes": [[60, 0, 1, 100], [60, 4, 1, 1], [60, 8, 1, 127]]}
A_HI = {"length": 4, "notes": [[120, 0, 1, 100]]}
A_LO = {"length": 4, "notes": [[5, 0, 1, 100]]}
# clip B: C3 E3 G3 held together for 2 beats
B = {"length": 4, "notes": [[60, 0, 2, 100], [64, 0, 2, 100], [67, 0, 2, 100]]}
# clip C: the C major scale up, a note per beat, then the chromatic octave
C_NOTES = ([[p, i, 0.5, 100] for i, p in enumerate((60, 62, 64, 65, 67, 69, 71, 72))] +
           [[60 + i, 8 + i, 0.5, 100] for i in range(13)])


def scale_clip(scale):
    return {"length": 22, "notes": C_NOTES, "scale": scale}


# 200 repeats of C3, one per 1/8 note
REPEATS = {"length": 100, "notes": [[60, 0.5 * i, 0.25, 100] for i in range(200)]}
TRIAD = {"Shift1": 4, "Shift2": 7, "Shift3": 12}

RUNS = [
    {"name": "chord-shift", "plan": "2",
     "question": "which pitches come out for Shift +4/+7, a duplicate +7, a Shift of 0, -36/+36, and near pitch 0 and 127",
     "clip": A, "base": {"Shift1": 4, "Shift2": 7},
     "cases": [["dup7", {"Shift3": 7}], ["shift3-zero", {"Shift3": 0}],
               ["minus36-plus36", {"Shift1": -36, "Shift2": 36}],
               ["hi", {"Shift1": 4, "Shift2": 36}, {"clip": A_HI}],
               ["lo", {"Shift1": -4, "Shift2": -36}, {"clip": A_LO}]]},

    {"name": "chord-velocity", "plan": "3",
     "question": "output velocity of Shift +4 at Velocity 50 %, 200 % and 1 % for input velocities 100, 1, 127 (rounding, the 127 limit)",
     "clip": A, "base": {"Shift1": 4},
     "cases": [[f"vel-{v}", {"Velocity1": v / 100}] for v in (50, 200, 1)]},

    {"name": "chord-chance", "plan": "3",
     "question": "Chance 50 % on Shift +4 and +7 over 200 notes: hit rate and independence of the two; a second identical instance",
     "clip": REPEATS, "base": {"Shift1": 4, "Shift2": 7, "Chance1": 0.5, "Chance2": 0.5},
     "cases": [["copy", {}, {"copy": 1}], ["chance-0", {"Chance1": 0.0, "Chance2": 1.0}]]},

    {"name": "chord-strum", "plan": "4",
     "question": "start of each note of a +4/+7/+12 chord for Strum 400, 200, 100, -100, -400 ms; Tension +-50 and +-100 and Crescendo +-100 % at 400 ms; a disabled Shift in the middle and a Chance of 0",
     "clip": A, "base": TRIAD,
     "cases": [[f"strum{ms:+d}", {"Strum": {"display": ms / 1000}}] for ms in (400, 200, 100, -100, -400)] +
              [[f"tension{t:+d}", {"Strum": {"display": 0.4}, "Strum Tension": t}] for t in (50, 100, -50, -100)] +
              [[f"crescendo{c:+d}", {"Strum": {"display": 0.4}, "Strum Crescendo": c}] for c in (100, -100)] +
              [["gap-shift2", {"Strum": {"display": 0.4}, "Shift2": 0}],
               ["chance3-zero", {"Strum": {"display": 0.4}, "Chance3": 0.0}],
               ["dup-strum", {"Strum": {"display": 0.1}, "Shift1": 0, "Shift2": 4, "Shift3": 4}]]},

    {"name": "chord-noteoff", "plan": "5",
     "question": "when each strummed note ends for an input of 1 beat and of 1/32 (Strum 400 ms); a held note while Shift1 steps +4 -> +5 at beat 2 (the pitch of its note-off)",
     "clip": {"length": 8, "notes": [[60, 0, 1, 100], [60, 4, 0.125, 100]]},
     "base": dict(TRIAD, Strum={"display": 0.4}),
     "cases": [["shift-step", {"Strum": 0}, {"clip": {"length": 6, "notes": [[60, 0, 4, 100]]},
                                             "automation": {"Shift1": [[0, 4], [2, 5]]}}],
               ["off-on", {"Strum": 0}, {"clip": {"length": 10, "notes": [[60, 0, 8, 100]]},
                                         "automation": {"Device On": [[0, {"item": "On"}], [3, {"item": "Off"}], [6, {"item": "On"}]]}}]]},

    {"name": "chord-overlap", "plan": "6",
     "question": "C E G with Shift +4 and +7 (pitches that coincide with input notes): note count and the overlapping pitches' note-offs",
     "clip": B, "base": {"Shift1": 4, "Shift2": 7},
     "cases": []},

    {"name": "chord-scale", "plan": "8; common C4",
     "question": "Shift +2 and +4 degrees with Use Current Scale on, over the C major scale and the chromatic octave, in C major, C minor and with no clip scale; +-36 degrees (past 0 and 127)",
     "clip": scale_clip(["C", "Major"]),
     "base": {"Use Current Scale": {"item": "On"}, "Shift1 Scale Degrees": 2, "Shift2 Scale Degrees": 4},
     "cases": [["minor", {}, {"clip": scale_clip(["C", "Minor"])}],
               ["no-scale", {}, {"clip": scale_clip(None)}],
               ["degrees36", {"Shift1 Scale Degrees": 36, "Shift2 Scale Degrees": -36}],
               ["semitone-shifts-ignored", {"Shift3": 12}]]},
]
