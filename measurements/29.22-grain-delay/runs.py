# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Grain Delay behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.22-grain-delay.md > Measurement plan.

The base is a free delay of 40 ms, Frequency 60 Hz, Pitch 0, Spray 0, Random Pitch 0, Feedback 0,
Dry/Wet 100 %. The pitch of the steady 1 kHz tone is read from the render (not yet in analyse.py):
a spectrum or zero-crossing count of the steady segment. Random Pitch is a unitless 0 to 161
control, so it is set with norm (the quadratic taper gives 161 * norm^2).

Not measurable this way: the X-Y pad assignment (a view setting); plan 5's histogram of arrival times
(a handful of impulses only: grain-delay-spray reads the taps of one impulse at a high grain rate
instead); plan 6's per-grain histogram (grain-delay-random reads the tone's spectrum spread); tempo
changes."""

DEVICE = "Grain Delay"

BASE = {"Delay Mode": {"item": "Off"}, "Time Delay": {"display": 0.04}, "Frequency": {"display": 60},
        "Pitch": 0, "Spray": {"display": 0}, "Random": {"norm": 0}, "Feedback": {"display": 0},
        "DryWet": {"display": 100}}

RUNS = [
    {"name": "grain-delay-pitch", "plan": "4", "probe": "gap2", "read": ["steady tone pitch", "modulation"], "priority": 1,
     "why": "the Pitch law (semitones, fractions, the -36 end) and the artefacts at the default grain rate",
     "question": "Pitch -36, -12, -5, +0.5, +7 and +12 semitones, 1 kHz tone, grain rate 60 Hz",
     "base": BASE,
     "cases": [[f"pitch{v:+g}", {"Pitch": v}] for v in (-36, -12, -5, 0.5, 7, 12)]},

    {"name": "grain-delay-rate", "plan": "3", "probe": "gap2", "read": ["modulation", "steady spectrum"], "priority": 1,
     "why": "grain rate and window: the amplitude modulation period and depth against Frequency, with and without pitch shift",
     "question": "Frequency 1, 4, 12 and 150 Hz at Pitch 0 (60 Hz is the default case); and 4 and 12 Hz at Pitch +12",
     "base": BASE,
     "cases": [[f"f{v}", {"Frequency": {"display": v}}] for v in (1, 4, 12, 150)] + [
         ["f4-p12", {"Frequency": {"display": 4}, "Pitch": 12}],
         ["f12-p12", {"Frequency": {"display": 12}, "Pitch": 12}],
     ]},

    {"name": "grain-delay-time", "plan": "2", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "the delay per millisecond setting and per synced button (120 BPM), the swing scaling, and any fixed latency at 1 ms",
     "question": "free time 1, 10 and 128 ms (40 ms is the default case); synced button 1 and 4 with swing 0 and +33.3 %",
     "base": BASE,
     "cases": [
         ["ms-1", {"Time Delay": {"display": 0.001}}],
         ["ms-10", {"Time Delay": {"display": 0.01}}],
         ["ms-128", {"Time Delay": {"display": 0.128}}],
         ["beat-1", {"Delay Mode": {"item": "On"}, "Beat Delay": {"item": "1"}}],
         ["beat-4", {"Delay Mode": {"item": "On"}, "Beat Delay": {"item": "4"}}],
         ["beat-4-sw+33", {"Delay Mode": {"item": "On"}, "Beat Delay": {"item": "4"}, "Beat Swing": {"display": 33.3}}],
     ]},

    {"name": "grain-delay-feedback", "plan": "7", "probe": "gap2", "read": ["impulse"], "priority": 2,
     "why": "repeat ratio against Feedback (to the 95 % limit) and how pitch accumulates in the loop",
     "question": "100 ms delay, Feedback 25, 50 and 95 %, and 50 % with Pitch +12",
     "base": BASE | {"Time Delay": {"display": 0.1}},
     "cases": [[f"fb-{v}", {"Feedback": {"display": v}}] for v in (25, 50, 95)] + [
         ["fb-50-p12", {"Feedback": {"display": 50}, "Pitch": 12}]]},

    {"name": "grain-delay-spray", "plan": "5", "probe": "gap2", "read": ["impulse", "modulation"], "priority": 2,
     "why": "Spray's range and distribution: the spread of echo arrival times of one impulse against Spray, with grains dense",
     "question": "128 ms delay, Frequency 150 Hz, Spray 5, 20, 60 and 200 ms",
     "base": BASE | {"Time Delay": {"display": 0.128}, "Frequency": {"display": 150}},
     "cases": [[f"spray-{v}", {"Spray": {"display": v / 1000}}] for v in (5, 20, 60, 200)]},

    {"name": "grain-delay-random", "plan": "6", "probe": "gap2", "read": ["steady spectrum", "modulation"], "priority": 2,
     "why": "what unit Random Pitch is in (semitones? cents?) from the spread of the tone's pitch, and its distribution",
     "question": "Frequency 12 Hz, Random Pitch (norm) 0.25, 0.5, 0.75, 1 (display 10, 40, 91 and 161)",
     "base": BASE | {"Frequency": {"display": 12}},
     "cases": [[f"rand-{n}", {"Random": {"norm": v}}] for n, v in (("10", 0.25), ("40", 0.5), ("91", 0.75), ("161", 1.0))]},

    {"name": "grain-delay-stereo-mix", "plan": "8,9", "probe": "gap2", "read": ["modulation", "stereo", "steady spectrum"], "priority": 3,
     "why": "whether Spray and Random Pitch differ between channels, and the Dry/Wet law (Pitch +12 separates dry and wet lines)",
     "question": "L/R correlation with Spray 20 ms and with Random Pitch 40 at Frequency 12 Hz; Dry/Wet 0, 25, 50 and 75 % at Pitch +12",
     "base": BASE,
     "cases": [
         ["spray20", {"Spray": {"display": 0.02}, "Frequency": {"display": 12}}],
         ["rand40", {"Random": {"norm": 0.5}, "Frequency": {"display": 12}}],
         ["dw-0", {"Pitch": 12, "DryWet": {"display": 0}}],
         ["dw-25", {"Pitch": 12, "DryWet": {"display": 25}}],
         ["dw-50", {"Pitch": 12, "DryWet": {"display": 50}}],
         ["dw-75", {"Pitch": 12, "DryWet": {"display": 75}}],
     ]},

    # ---- third set (measurements/third/)
    {"name": "grain-delay-buttons", "plan": "2", "probe": "gap2", "read": ["impulse"], "priority": 2,
     "why": "the other sync buttons and the negative offset",
     "question": "echo time of the impulse for Beat Delay 2, 3, 5, 6, 8 and for 4 with Beat Swing -33.3 %",
     "base": dict(BASE, **{"Delay Mode": {"item": "On"}, "Beat Swing": {"display": 0}}),
     "cases": [[f"beat-{b}", {"Beat Delay": {"item": str(b)}}] for b in (2, 3, 5, 6, 8)] +
              [["beat-4-swing-33", {"Beat Delay": {"item": "4"}, "Beat Swing": -0.333}]]},

    {"name": "grain-delay-window", "plan": "3", "probe": "gap2", "read": ["envelope of the steady tone (grain window shape)"], "priority": 1,
     "why": "the grain window's shape, which shows only when Pitch is not 0, at a low and a high grain rate",
     "question": "envelope and spectrum of the steady tone at Pitch +12, -12 and +7 with Frequency 10 Hz, and +12 at 60 Hz",
     "base": BASE,
     "cases": [[f"pitch{p:+d}-10hz", {"Pitch": p, "Frequency": {"display": 10}}] for p in (12, -12, 7)] +
              [["pitch+12-60hz", {"Pitch": 12}]]},

    {"name": "grain-delay-spray-train", "plan": "5, 6", "probe": "ext", "read": ["ext: impulsetrain (arrival times per impulse)", "glide"], "priority": 1,
     "why": "Spray's distribution of arrival times over twenty impulses, and Random Pitch's per-grain frequencies at a low grain rate",
     "question": "arrival times of each impulse of the train's copies at Spray 20, 60, 200 ms; the 150 Hz saw's partials and the glide at Random 40 and 161, Frequency 10 Hz",
     "base": BASE,
     "cases": [[f"spray-{s}", {"Spray": {"display": s / 1000}}] for s in (20, 60, 200)] +
              [[f"random-{r}-10hz", {"Random": {"display": r}, "Frequency": {"display": 10}}] for r in (40, 161)]},
]
