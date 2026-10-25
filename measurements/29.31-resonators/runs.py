# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Resonators behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.31-resonators.md › Measurement plan.

All runs are wet only (Dry/Wet 100 %), with the input filter off unless it is the question, and
with the resonators not under test switched off, so one resonator is read at a time. Resonator I
takes L + R, II and IV take L, III and V take R.

Left out (cannot be measured this way): scale and tuning-system behaviour (plan 9: needs the clip
scale or a loaded tuning); changing Note or Mode during ringing (automation); latency is read for
free from the impulse of any case at Dry/Wet 100 % (plan 10). Gain steps of the five gains and the
output Gain are a plain level read of a linear stage and are not proposed.
"""

DEVICE = "Resonators"

OFF, ON = 0, 1
ONLY_I = {"II On": OFF, "III On": OFF, "IV On": OFF, "V On": OFF}
# Wet only, the input filter out of the way, Resonator I alone.
BASE = {"Dry/Wet": {"display": 100}, "Filter On": OFF, **ONLY_I}
# The same, with every resonator off: a case then switches on the one it asks about.
ALL_OFF = {"Dry/Wet": {"display": 100}, "Filter On": OFF, "I On": OFF, **ONLY_I}

RUNS = [
    {"name": "resonators-tuning", "plan": "2", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "Note-name to Hz mapping across C-1..C5 and the Fine Tuning range in cents",
     "question": "ringing frequency of Resonator I against Note (C-1 to C5) and Fine Tuning (+-50 ct)",
     "base": BASE,
     "cases": [[f"note-{n}", {"I Note": n}] for n in (12, 24, 60, 69, 84)]
     + [["tune-+50", {"I Tune": 50}], ["tune--50", {"I Tune": -50}]]},

    {"name": "resonators-decay", "plan": "3", "probe": "gap10", "read": ["impulse"], "priority": 1,
     "why": "T60 against Decay (unit, maximum, stability), the main time control of the device",
     "question": "ring-out time of Resonator I against Decay 0..100, Const on, Mode A, Note C2",
     "base": BASE,
     "cases": [[f"decay-{d}", {"Decay": d}] for d in (0, 15, 30, 70, 85, 100)]},

    {"name": "resonators-modes", "plan": "3, 4", "probe": "gap10", "read": ["impulse"], "priority": 1,
     "why": "Mode B against A (octave, partial series) and Const off (T60 against pitch)",
     "question": "partials and decay of Mode A and B at Note C2 and C0; Const off at C2 and C0",
     "base": BASE,
     "cases": [["modeB-C2", {"Mode": {"item": "Mode B"}}],
               ["modeB-C0", {"Mode": {"item": "Mode B"}, "I Note": 24}],
               ["modeA-C0", {"I Note": 24}],
               ["constoff-C2", {"Const": OFF}],
               ["constoff-C0", {"Const": OFF, "I Note": 24}]]},

    {"name": "resonators-color", "plan": "5", "probe": "gap2", "read": ["response"], "priority": 2,
     "why": "the Color loop filter: tilt and corner of the resonance peaks against Color",
     "question": "level of the resonance peaks against frequency for Color 0, 25, 50, 75, 100 at short Decay",
     "base": {**BASE, "Decay": 20},
     "cases": [[f"color-{c}", {"Color": c}] for c in (0, 25, 50, 75, 100)]},

    {"name": "resonators-filter", "plan": "6", "probe": "gap2", "read": ["response"], "priority": 2,
     "why": "the input filter's shape (corner, slope, Q, notch depth) for the four types",
     "question": "sweep response of the input filter alone (Decay 0) for LP, HP, BP and Notch",
     "base": {**BASE, "Decay": 0, "Filter On": ON, "Frequency": {"display": 1000}},
     "cases": [["lp-1k", {"Filter Type": {"item": "low pass"}}],
               ["hp-1k", {"Filter Type": {"item": "high pass"}}],
               ["bp-1k", {"Filter Type": {"item": "band pass"}}],
               ["notch-1k", {"Filter Type": {"item": "notch"}}],
               ["lp-200", {"Filter Type": {"item": "low pass"}, "Frequency": {"display": 200}}],
               ["bp-4k", {"Filter Type": {"item": "band pass"}, "Frequency": {"display": 4000}}]]},

    {"name": "resonators-routing", "plan": "7", "probe": "gap2", "read": ["stereo"], "priority": 2,
     "why": "which input channel each resonator hears, where its output sits, and the Width law",
     "question": "2x2 level matrix (left-only and right-only 1 kHz) with one resonator at a time, Width 100/50/0 %",
     "base": {**ALL_OFF, "I Note": 84},
     "cases": [["only-I", {"I On": ON}],
               ["only-II", {"II On": ON}],
               ["only-III", {"III On": ON}],
               ["only-II-w50", {"II On": ON, "Width": {"display": 50}}],
               ["only-II-w0", {"II On": ON, "Width": {"display": 0}}],
               ["only-III-w0", {"III On": ON, "Width": {"display": 0}}]]},

    # ---- third set (measurements/third/)
    {"name": "resonators-others", "plan": "2, 3", "probe": "gap2", "read": ["impulse (ring frequency, T30)"], "priority": 1,
     "why": "Resonators II to V: their Pitch relative to I, Tune, and their decay with Const on and off",
     "question": "ring frequency and decay of each of II to V alone at Pitch +12 (I at C2); II at Pitch -24 and +24 and Tune +50; II at Pitch +12 with Const off",
     "base": ALL_OFF,
     "cases": [[f"{r.lower()}-p12", {f"{r} On": ON, f"{r} Pitch": 12}] for r in ("II", "III", "IV", "V")] +
              [[f"ii-p{p:+d}", {"II On": ON, "II Pitch": p}] for p in (-24, 24)] +
              [["ii-tune+50", {"II On": ON, "II Tune": 50}], ["ii-p12-constoff", {"II On": ON, "II Pitch": 12, "Const": OFF}]]},

    {"name": "resonators-notes-const", "plan": "2, 3", "probe": "gap2", "read": ["impulse (ring frequency, T30)"], "priority": 2,
     "why": "more Note values over the range and Const off at more pitches (a law needs more than two points)",
     "question": "Resonator I alone: Note 30, 60, 72, 84; Const off at Note 36, 60, 72",
     "base": BASE,
     "cases": [[f"note-{n}", {"I Note": n}] for n in (30, 60, 72, 84)] +
              [[f"constoff-{n}", {"I Note": n, "Const": OFF}] for n in (36, 60, 72)]},

    {"name": "resonators-gain-mix", "plan": "8, 10", "probe": "gap2", "read": ["impulse", "static"], "priority": 2,
     "why": "a resonator's Gain, the output Gain and Dry/Wet at 50 %, and whether the dry is delayed",
     "question": "impulse and staircase: I Gain -12 dB; Output +6 dB; Dry/Wet 50 % and 0 %",
     "base": BASE,
     "cases": [["i-gain-12", {"I Gain": {"display": -12}}], ["output+6", {"Output": {"display": 6}}],
               ["drywet-50", {"Dry/Wet": {"display": 50}}], ["drywet-0", {"Dry/Wet": {"display": 0}}]]},
]
