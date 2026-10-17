# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Dynamic Tube behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.13-dynamic-tube.md > Measurement plan.

The 1 kHz staircase (-60 to 0 dBFS, 3 dB steps) is the transfer-curve test: output gain, THD and
the even/odd harmonics at every level. The renders also hold the silence segment, where a biased
curve would show a DC offset. The Envelope runs read the burst steps' harmonic content over time
from the renders (a short-time spectrum of the second harmonic during the -30 and -6 dBFS
bursts), which analyse.py does not do yet.

Not taken: the 200 Hz test tone of step 1 (the probe's tone is 1 kHz), the Hi-Quality
oversampling option and its alias products (a context-menu option, not a parameter: step 6),
peak versus RMS detection from a click (no click-and-sine pair in the probe; the bursts only
show the follower's level response), tube switching clicks, and stereo linking of the follower
(one-sided tones leave a silent channel)."""

DEVICE = "Dynamic Tube"

# Tube A, no bias, no envelope, flat tone and output, 100 % wet.
BASE = {"Tube Type": {"item": "A"}, "Drive": {"display": 0}, "Bias": {"display": 0}, "Tone": {"display": 0},
        "Envelope": {"display": 0}, "Attack": {"display": 0.005}, "Release": {"display": 0.035},
        "Output": {"display": 0}, "Dry/Wet": {"display": 100}}

RUNS = [
    {"name": "dyntube-types-bias", "plan": "1", "probe": "gap2", "read": ["static", "silence"], "priority": 1,
     "why": "the transfer curve of tubes A, B and C against Bias: A's threshold, C's low-level distortion, even/odd harmonics, DC offset",
     "question": "staircase output, THD and harmonics for tube A at Bias 25, 50, 100 %, B at 0 and 50 %, C at 0, 50, 100 % (Drive 0)",
     "base": BASE,
     "cases": [[f"a-bias-{b}", {"Bias": {"display": b}}] for b in (25, 50, 100)] +
              [[f"b-bias-{b}", {"Tube Type": {"item": "B"}, "Bias": {"display": b}}] for b in (0, 50)] +
              [[f"c-bias-{b}", {"Tube Type": {"item": "C"}, "Bias": {"display": b}}] for b in (0, 50, 100)]},

    {"name": "dyntube-drive", "plan": "1", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "Drive as gain into the tube (dB): the level at which each tube starts to distort, and the compression above it",
     "question": "staircase gain and THD for tube C at Bias 50 % with Drive -15, -6, +6, +15 dB, and tubes A and B at Drive +6",
     "base": dict(BASE, **{"Tube Type": {"item": "C"}, "Bias": {"display": 50}}),
     "cases": [[f"c-drive-{n}", {"Drive": {"display": d}}] for n, d in (("m15", -15), ("m6", -6), ("p6", 6), ("p15", 15))] +
              [["a-drive-p6", {"Tube Type": {"item": "A"}, "Drive": {"display": 6}}],
               ["b-drive-p6", {"Tube Type": {"item": "B"}, "Drive": {"display": 6}}]]},

    {"name": "dyntube-tone", "plan": "4", "probe": "gap2", "read": ["static", "response"], "priority": 1,
     "why": "what Tone does: the harmonic spectrum and the small-signal tilt for Tone -1, -0.5, +0.5, +1",
     "question": "staircase harmonics and sweep response for Tone -1, -0.5, +0.5, +1 on tube C at Bias 50 %, Drive +6 dB",
     "base": dict(BASE, **{"Tube Type": {"item": "C"}, "Bias": {"display": 50}, "Drive": {"display": 6}}),
     "cases": [[f"tone-{n}", {"Tone": {"display": t}}] for n, t in (("m1", -1), ("m0.5", -0.5), ("p0.5", 0.5), ("p1", 1))]},

    {"name": "dyntube-envelope", "plan": "3", "probe": "gap2", "read": ["static", "dynamics"], "priority": 1,
     "why": "how Envelope moves the Bias with level: staircase THD against level for -300 to +300 % (positive dirtier when loud, negative cleaner)",
     "question": "staircase THD and burst harmonics for Envelope -300, -100, +100, +300 % on tube A at Bias 30 %, Drive +6 dB",
     "base": dict(BASE, **{"Bias": {"display": 30}, "Drive": {"display": 6}}),
     "cases": [[f"env-{n}", {"Envelope": {"display": e}}] for n, e in (("m300", -300), ("m100", -100), ("p100", 100), ("p300", 300))]},

    {"name": "dyntube-env-time", "plan": "3", "probe": "gap2", "read": ["dynamics"], "priority": 2,
     "why": "the follower's Attack and Release times: how fast the harmonic level follows the -30 to -6 dBFS burst step and back",
     "question": "2nd-harmonic level against time through the bursts for Attack 1, 50, 400 ms and Release 1, 300, 1500 ms at Envelope +300 %",
     "base": dict(BASE, **{"Tube Type": {"item": "C"}, "Drive": {"display": 6}, "Envelope": {"display": 300}}),
     "cases": [[f"attack-{a}ms", {"Attack": {"display": a / 1000}}] for a in (1, 50, 400)] +
              [[f"release-{r}ms", {"Release": {"display": r / 1000}}] for r in (1, 300, 1500)]},

    {"name": "dyntube-output-wet", "plan": "5", "probe": "gap2", "read": ["static", "impulse"], "priority": 3,
     "why": "Output as a plain dB gain, the Dry/Wet law with a distorting wet path, and any added delay (impulse)",
     "question": "level and impulse for Output -15 and +15 dB, Dry/Wet 0 and 50 % on tube C at Bias 50 %, Drive +12 dB",
     "base": dict(BASE, **{"Tube Type": {"item": "C"}, "Bias": {"display": 50}, "Drive": {"display": 12}}),
     "cases": [["out-m15", {"Output": {"display": -15}}], ["out-p15", {"Output": {"display": 15}}],
               ["wet-0", {"Dry/Wet": {"display": 0}}], ["wet-50", {"Dry/Wet": {"display": 50}}]]},
]
