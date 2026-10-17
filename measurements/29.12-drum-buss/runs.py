# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Drum Buss behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.12-drum-buss.md > Measurement plan.

Every run starts from a neutral state (Comp off, Crunch 0, Transients 0, Boom 0, Damp wide open,
Trim and Output 0 dB, 100 % wet) and changes one section, so a section's effect is the difference
from the `default` case (Drive 20 %, Soft).

Not taken: the distortion at 100 Hz and 5 kHz (step 2: the probe's staircase is 1 kHz only; the
sweep at -12 dBFS shows how the shaped signal looks across frequency), the 100 Hz split of the
transient shaper (step 6: needs a low-frequency burst train; only the 1 kHz bursts are read),
Force To Note (a button, not a parameter), the Bass Meter, sample-rate aliasing near Nyquist
(step 11: one rate; the 20 kHz end of the sweep is the only trace) and stereo linking (step 12:
the probe's one-sided tones leave a silent channel)."""

DEVICE = "Drum Buss"

BASE = {"Compressor On": {"item": "Off"}, "Drive": {"display": 20}, "Drive Type": {"item": "Soft"},
        "Crunch": {"display": 0}, "Damping Freq": {"display": 20000}, "Transients": {"display": 0},
        "Boom Freq": {"display": 50}, "Boom Amt": {"display": 0}, "Boom Decay": {"display": 100},
        "Boom Audition": {"item": "Off"}, "Trim": {"display": 0}, "Output": {"display": 0},
        "Dry/Wet": {"display": 100}}

RUNS = [
    {"name": "drumbuss-drive", "plan": "2", "probe": "gap2", "read": ["static", "response"], "priority": 1,
     "why": "the Soft, Medium and Hard distortion curves (gain and harmonics against level) and Hard's bass boost (sweep)",
     "question": "staircase output, THD and harmonics, and sweep response for each Drive Type at Drive 50 and 100 %, and Soft at Drive 0",
     "base": BASE,
     "cases": [["soft-d0", {"Drive": {"display": 0}}]] +
              [[f"{t.lower()}-d{d}", {"Drive Type": {"item": t}, "Drive": {"display": d}}]
               for t in ("Soft", "Medium", "Hard") for d in (50, 100)]},

    {"name": "drumbuss-comp", "plan": "3", "probe": "gap2", "read": ["static", "dynamics"], "priority": 1,
     "why": "the fixed compressor: threshold and ratio (gain against level), attack and release (bursts), makeup, and how Trim shifts it",
     "question": "static curve and burst attack/release with Comp on at Drive 0, and with Trim -6 and -12 dB (Comp off is the default case with Drive 0 too)",
     "base": dict(BASE, **{"Drive": {"display": 0}}),
     "cases": [["comp-on", {"Compressor On": {"item": "On"}}],
               ["comp-on-trim-6", {"Compressor On": {"item": "On"}, "Trim": {"display": -6}}],
               ["comp-on-trim-12", {"Compressor On": {"item": "On"}, "Trim": {"display": -12}}],
               ["trim-6", {"Trim": {"display": -6}}]]},

    {"name": "drumbuss-boom", "plan": "7, 8, 9", "probe": "gap2", "read": ["impulse", "response"],
     "priority": 1,
     "why": "the Boom resonator: frequency, Q and decay time against Boom, Freq and Decay (ring of the impulse), and the Audition solo",
     "question": "impulse response (ring frequency, decay, level) for Boom 50 and 100 %, Freq 30 and 90 Hz, Decay 0 and 50 %, and Boom Audition on",
     "base": dict(BASE, **{"Drive": {"display": 0}}),
     "cases": [["boom-50", {"Boom Amt": {"display": 50}}], ["boom-100", {"Boom Amt": {"display": 100}}],
               ["boom-100-f30", {"Boom Amt": {"display": 100}, "Boom Freq": {"display": 30}}],
               ["boom-100-f90", {"Boom Amt": {"display": 100}, "Boom Freq": {"display": 90}}],
               ["boom-100-decay-0", {"Boom Amt": {"display": 100}, "Boom Decay": {"display": 0}}],
               ["boom-100-decay-50", {"Boom Amt": {"display": 100}, "Boom Decay": {"display": 50}}],
               ["boom-100-audition", {"Boom Amt": {"display": 100}, "Boom Audition": {"item": "On"}}]]},

    {"name": "drumbuss-transients", "plan": "6", "probe": "gap2", "read": ["dynamics", "static"],
     "priority": 1,
     "why": "the transient shaper: attack gain and sustain change for positive and negative Transients (response to the burst steps)",
     "question": "burst steps (-30 to -6 dBFS and back) through Transients -1, -0.5, +0.5, +1 (the sign changes sustain, not only attack)",
     "base": dict(BASE, **{"Drive": {"display": 0}}),
     "cases": [[f"transients-{n}", {"Transients": {"display": v}}]
               for n, v in (("m1", -1), ("m0.5", -0.5), ("p0.5", 0.5), ("p1", 1))]},

    {"name": "drumbuss-damp-crunch", "plan": "4, 5", "probe": "gap2", "read": ["response", "static"],
     "priority": 2,
     "why": "Damp's low-pass corner and slope, and Crunch's band, level and harmonic content",
     "question": "sweep response for Damp 500, 2000, 9200 Hz; sweep and THD for Crunch 50 and 100 % at Drive 0, Damp wide open",
     "base": dict(BASE, **{"Drive": {"display": 0}}),
     "cases": [[f"damp-{f}", {"Damping Freq": {"display": f}}] for f in (500, 2000, 9200)] +
              [[f"crunch-{c}", {"Crunch": {"display": c}}] for c in (50, 100)]},

    {"name": "drumbuss-mix-output", "plan": "10, 11", "probe": "gap2", "read": ["static", "impulse"],
     "priority": 3,
     "why": "Dry/Wet law and whether the dry path is aligned with the processed one; whether Output Gain also moves the dry share",
     "question": "level and impulse taps for Dry/Wet 0 and 50 % with Hard at Drive 100 %, Output -10 and +3 dB",
     "base": dict(BASE, **{"Drive Type": {"item": "Hard"}, "Drive": {"display": 100}}),
     "cases": [["wet-0", {"Dry/Wet": {"display": 0}}], ["wet-50", {"Dry/Wet": {"display": 50}}],
               ["wet-50-out-m10", {"Dry/Wet": {"display": 50}, "Output": {"display": -10}}],
               ["out-m10", {"Output": {"display": -10}}], ["out-p3", {"Output": {"display": 3}}]]},
]
