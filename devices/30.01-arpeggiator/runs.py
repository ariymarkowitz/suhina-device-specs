# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Arpeggiator behaviour runs for tools/harness/midi_set.py (see its docstring for the format).
Plan steps refer to live-12/midi-effects/30.01-arpeggiator.md › Measurement plan.

Every run starts from the plan's neutral settings: Rate 1/16 Sync, Gate 50 %, everything else
as loaded (Offset 0, Retrigger Off, Repeats inf, Steps 0, Hold off, Velocity off, Groove
Straight, Use Current Scale off). The Synced Rate and Ret. Interval lists are indices into the
dump's lists (Synced Rate 6 = 1/16, Ret. Interval 8 = 1).

Not taken: Free rate at 60 BPM and tempo automation (A2, A7: one tempo per set), the Global
Groove Amount and a Groove Pool groove (A3: the device's own Groove list only), the LED (A4),
a transport stop and a start from bar 5 (A7: the user's), MPE (A8), racks and CCs (A9). The
random styles' repeatability across playbacks needs a second take."""

DEVICE = "Arpeggiator"

STYLES = ["Down", "UpDown", "DownUp", "Up & Down", "Down & Up", "Converge", "Diverge",
          "Con & Diverge", "Pinky Up", "Pinky UpDown", "Thumb Up", "Thumb UpDown", "Play Order",
          "Chord Trigger", "Random", "Random Other", "Random Once"]
NEUTRAL = {"Synced Rate": 6, "Gate": 50}


def held(pitches, start, length, velocity=100):
    return [[p, start, length, velocity] for p in pitches]


def slug(s):
    return s.lower().replace(" & ", "-and-").replace(" ", "-")


# A1: one note, two, three, four and five notes in turn, each held 8 beats (32 steps), 2 beats
# apart so the held list empties between them
CHORDS = [(60,), (60, 67), (60, 64, 67), (60, 64, 67, 71), (60, 64, 67, 71, 74)]
STYLE_CLIP = {"length": 50, "notes": [n for i, c in enumerate(CHORDS) for n in held(c, 10 * i, 8)]}
# Play Order: G3, C3, B3, E3 pressed a 1/16 apart, then the same four together
ORDER_CLIP = {"length": 20, "notes": [[p, 0.25 * k, 8 - 0.25 * k, 100] for k, p in enumerate((67, 60, 71, 64))] +
                                     held((67, 60, 71, 64), 10, 8)}
# the random styles: C E G B held 32 beats (128 steps), then C E G B D held 16 beats
RANDOM_CLIP = {"length": 50, "notes": held((60, 64, 67, 71), 0, 32) + held((60, 64, 67, 71, 74), 34, 16)}
ONE = {"length": 16, "notes": [[60, 0, 16, 100]]}
CEG = {"length": 16, "notes": held((60, 64, 67), 0, 16)}
CEGB = {"length": 16, "notes": held((60, 64, 67, 71), 0, 16)}


def ceg(scale, pitches=(60, 64, 67)):
    return {"length": 16, "notes": held(pitches, 0, 16), "scale": scale}


RUNS = [
    {"name": "arp-style", "plan": "A1",
     "question": "the order of the first steps of every Style for 1, 2, 3, 4 and 5 held notes (Up is the default case): Diverge, the '&' names, pattern lengths",
     "clip": STYLE_CLIP, "base": NEUTRAL,
     "cases": [[slug(s), {"Style": {"item": s}}] for s in STYLES]},

    {"name": "arp-play-order", "plan": "A1",
     "question": "Play Order (and Up for comparison) for G3, C3, B3, E3 pressed in that order, then pressed together",
     "clip": ORDER_CLIP, "base": NEUTRAL,
     "cases": [["play-order", {"Style": {"item": "Play Order"}}]]},

    {"name": "arp-random", "plan": "A1",
     "question": "Random (repeats, distribution), Random Other (no repeat until all used), Random Once (a fixed order, a new one when the chord changes) over 128 + 64 steps; two instances of each",
     "clip": RANDOM_CLIP, "base": NEUTRAL,
     "cases": [[f"{slug(s)}{'-copy' if c else ''}", {"Style": {"item": s}}, {"copy": c}]
               for s in ("Random", "Random Other", "Random Once") for c in (0, 1)] +
              [["random-steps2", {"Style": {"item": "Random"}, "Transp. Steps": 2}]]},

    {"name": "arp-rate", "plan": "A2",
     "question": "the interval between steps for every Synced Rate (1/128 .. 1/1), and Free at 10, 20 (default), 100, 500 ms and 1 s",
     "clip": ONE, "base": NEUTRAL,
     "cases": [[f"sync{i}", {"Synced Rate": i}] for i in range(14) if i != 6] +
              [[f"free-{int(s * 1000)}ms", {"Sync On": {"item": "Off"}, "Free Rate": {"display": s}}] for s in (0.01, 0.1, 0.5, 1.0)] +
              [["free-default", {"Sync On": {"item": "Off"}}]]},

    {"name": "arp-gate", "plan": "A2",
     "question": "note length for Gate 1, 25, 75, 100, 150, 200 % on one held note (overlap of same-pitch notes above 100 %), and on two notes",
     "clip": ONE, "base": NEUTRAL,
     "cases": [[f"gate{g}", {"Gate": g}] for g in (1, 25, 75, 100, 150, 200)] +
              [["gate150-two", {"Gate": 150}, {"clip": {"length": 16, "notes": held((60, 67), 0, 16)}}]]},

    {"name": "arp-first-note", "plan": "A2",
     "question": "time of the first output for a note starting on a 1/16 grid point and 1, 4, 6 and 60 ms after one (the 5 ms grace period of 12.4)",
     "clip": {"length": 20, "notes": [[60, 4 * k + d, 2, 100] for k, d in enumerate((0, 0.002, 0.008, 0.012, 0.12))]},
     "base": NEUTRAL,
     "cases": [["rate-1-8", {"Synced Rate": 8}], ["free-100ms", {"Sync On": {"item": "Off"}, "Free Rate": {"display": 0.1}}]]},

    {"name": "arp-groove", "plan": "A3",
     "question": "step offsets and velocities with Swing 8, 16, 32 at Rate 1/16, Gate 50 and 90 %; Swing 8 at Rate 1/8; Swing 16 at 1/32; Swing 16 with a Free rate",
     "clip": CEG, "base": NEUTRAL,
     "cases": [[f"{slug(g)}-gate{gt}", {"Groove": {"item": g}, "Gate": gt}] for g in ("Swing 8", "Swing 16", "Swing 32") for gt in (50, 90)] +
              [["swing-8-rate-1-8", {"Groove": {"item": "Swing 8"}, "Synced Rate": 8}],
               ["swing-16-rate-1-32", {"Groove": {"item": "Swing 16"}, "Synced Rate": 4}],
               ["swing-16-free", {"Groove": {"item": "Swing 16"}, "Sync On": {"item": "Off"}, "Free Rate": {"display": 0.125}}]]},

    {"name": "arp-hold", "plan": "A4",
     "question": "Hold: C3 E3 held then released, G3 pressed alone (replaces), C3 E3 added while G3 is held, E3 pressed again (removed); then Hold switched off at beat 16",
     "clip": {"length": 20, "notes": held((60, 64), 0, 4) + [[67, 6, 4, 100]] + held((60, 64), 8, 1) + [[64, 12, 0.5, 100]]},
     "base": dict(NEUTRAL, **{"Hold On": {"item": "On"}}),
     "cases": [["hold-off-at-16", {}, {"automation": {"Hold On": [[0, {"item": "On"}], [16, {"item": "Off"}]]}}]]},

    {"name": "arp-offset", "plan": "A4",
     "question": "Up on C E G B with Offset 1, 2, 3, 4, 5, -1, -8 and 8; Offset 1 with Steps 2, and with Converge",
     "clip": CEGB, "base": NEUTRAL,
     "cases": [[f"offset{o:+d}", {"Offset": o}] for o in (1, 2, 3, 4, 5, -1, -8, 8)] +
              [["offset+1-steps2", {"Offset": 1, "Transp. Steps": 2}],
               ["offset+1-converge", {"Offset": 1, "Style": {"item": "Converge"}}]]},

    {"name": "arp-retrigger", "plan": "A4",
     "question": "notes arriving at 0, 1.3 and 2.6 beats (off the grid), held to beat 34: Retrigger Note, and Beat at each Interval: where each restarted pattern starts",
     "clip": {"length": 36, "notes": [[60, 0, 34, 100], [64, 1.3, 32.7, 100], [67, 2.6, 31.4, 100]]},
     "base": NEUTRAL,
     "cases": [["note", {"Retrigger Mode": {"item": "Note"}}]] +
              [[f"beat-int{i}", {"Retrigger Mode": {"item": "Beat"}, "Ret. Interval": i}] for i in range(15)]},

    {"name": "arp-repeats", "plan": "A4",
     "question": "Repeats 1, 2, 3 with Retrigger Off, Note and Beat (1 bar) on C E G B with Steps 1, and a D4 pressed at beat 8: what counts as a repeat and what restarts it",
     "clip": {"length": 16, "notes": held((60, 64, 67, 71), 0, 16) + [[74, 8, 4, 100]]},
     "base": dict(NEUTRAL, **{"Transp. Steps": 1}),
     "cases": [[f"rep{r}-{m.lower()}", {"Repeats": r, "Retrigger Mode": {"item": m}}]
               for r in (1, 2, 3) for m in ("Off", "Note", "Beat")]},

    {"name": "arp-transpose", "plan": "A5",
     "question": "Up on C E G with Distance +12, -12, +7, +1 st and Steps 1, 2, 8: the pitch sequence and what follows the last step; near 0 and 127",
     "clip": CEG, "base": NEUTRAL,
     "cases": [[f"d{d:+d}-s{s}", {"Transp. Dist.": d, "Transp. Steps": s}]
               for d, s in ((12, 1), (12, 2), (12, 8), (-12, 2), (7, 2), (1, 8))] +
              [["top", {"Transp. Steps": 8}, {"clip": {"length": 16, "notes": held((120, 124, 127), 0, 16)}}],
               ["bottom", {"Transp. Steps": 8, "Transp. Dist.": -12}, {"clip": {"length": 16, "notes": held((0, 3, 7), 0, 16)}}]]},

    {"name": "arp-transpose-scale", "plan": "A5; common C4",
     "question": "Distance +1, +2, -1 with Steps 2 in C major (Root/Scale choosers), on C E G and on C# E G; then Use Current Scale with the clip in D Dorian, C minor pentatonic and with no clip scale",
     "clip": CEG, "base": dict(NEUTRAL, **{"Transp. Steps": 2, "Tranpose Mode": {"item": "Major"}}),
     "cases": [[f"major{d:+d}", {"Transp. Dist.": d}] for d in (1, 2, -1)] +
              [["major+1-out-of-scale", {"Transp. Dist.": 1}, {"clip": ceg(None, (61, 64, 67))}],
               ["major+1-root-d", {"Transp. Dist.": 1, "Tranpose Key": {"item": "D"}}]] +
              [[f"current-{n}", {"Transp. Dist.": 1, "Use Current Scale": {"item": "On"}, "Tranpose Mode": {"item": "Chromatic"}},
                {"clip": ceg(sc)}] for n, sc in (("d-dorian", ["D", "Dorian"]), ("c-minor-pentatonic", ["C", "Minor Pentatonic"]),
                                                 ("no-scale", None))]},

    {"name": "arp-velocity", "plan": "A6",
     "question": "velocity of each output over 32 beats with Velocity on: Target 0 at Decay 1 s and 10 s, Target 127 from input velocity 20, Target 64 at the shortest Decay; the velocity Retrigger with Beat retrigger; Velocity off at input 20",
     "clip": {"length": 32, "notes": [[60, 0, 32, 100]]},
     "base": dict(NEUTRAL, **{"Velocity On": {"item": "On"}}),
     "cases": [["target0-1s", {"Velocity Target": 0, "Velocity Decay": {"display": 1.0}}],
               ["target0-10s", {"Velocity Target": 0, "Velocity Decay": {"display": 10.0}}],
               ["target127-in20", {"Velocity Target": 127}, {"clip": {"length": 32, "notes": [[60, 0, 32, 20]]}}],
               ["target64-min", {"Velocity Decay": {"norm": 0.0}}],
               ["target0-1s-retrigger-beat", {"Velocity Target": 0, "Velocity Decay": {"display": 1.0},
                                              "Vel. Retrigger": {"item": "On"}, "Retrigger Mode": {"item": "Beat"}}],
               ["off-in20", {"Velocity On": {"item": "Off"}}, {"clip": {"length": 32, "notes": [[60, 0, 32, 20]]}}]]},

    {"name": "arp-noteoff", "plan": "A7; common C1",
     "question": "a note released in the middle of a long gate (Rate 1/4, Gate 200 %); the device switched off at beat 4 and on at beat 6 while a chord is held",
     "clip": {"length": 12, "notes": [[60, 0, 1.5, 100], [64, 4, 2.25, 100]]},
     "base": dict(NEUTRAL, **{"Synced Rate": 10, "Gate": 200}),
     "cases": [["off-on", {"Synced Rate": 6, "Gate": 50}, {"clip": {"length": 12, "notes": held((60, 64, 67), 0, 10)},
                                                         "automation": {"Device On": [[0, {"item": "On"}], [4, {"item": "Off"}], [6, {"item": "On"}]]}}]]},
]
