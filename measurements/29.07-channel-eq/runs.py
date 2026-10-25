# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Channel EQ behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.07-channel-eq.md > Measurement plan.

Every run is a time-invariant filter: its answer is `response.sweep_db` (magnitude per 1/6
octave, per channel) and, where phase or ringing matters, the impulse and its .ir.wav.

Not taken: phase of the filters beyond what the impulse response gives (step 2 asks for it; the
.ir.wav holds it, but no case is added for it), aliasing of a 15 kHz tone at full boost (the
sweep's 20 kHz end and the staircase stand in), smoothing of parameter jumps (needs automation),
and the display (step 9)."""

DEVICE = "Channel EQ"

# Everything flat, HP off, Output 0 dB, Mid at the default 1.5 kHz.
BASE = {"Highpass On": {"item": "Off"}, "Low Gain": {"display": 0}, "Mid Gain": {"display": 0},
        "Mid Freq": {"display": 1500}, "High Gain": {"display": 0}, "Output": {"display": 0}}


def sgn(v):
    return ("p" if v > 0 else "m") + str(abs(v))


RUNS = [
    {"name": "channeleq-low", "plan": "3", "probe": "gap2", "read": ["response", "impulse"], "priority": 1,
     "why": "the low shelf's corner, slope and overshoot at four gains, and how its shape changes with gain (adaptive curve)",
     "question": "sweep response for Low -15, -6, +6, +15 dB",
     "base": BASE,
     "cases": [[f"low-{sgn(g)}", {"Low Gain": {"display": g}}] for g in (-15, -6, 6, 15)]},

    {"name": "channeleq-high", "plan": "5", "probe": "gap2", "read": ["response"], "priority": 1,
     "why": "the high shelf's corner and the low-pass that joins it for cuts (cutoff and order against High from -3 to -15 dB)",
     "question": "sweep response for High +15, +6, -3, -6, -9, -12, -15 dB",
     "base": BASE,
     "cases": [[f"high-{sgn(g)}", {"High Gain": {"display": g}}] for g in (15, 6, -3, -6, -9, -12, -15)]},

    {"name": "channeleq-mid-gain", "plan": "4", "probe": "gap2", "read": ["response"], "priority": 1,
     "why": "the Mid bell's width against gain (-3 dB points of the bell): fixed Q or gain-dependent, and cut/boost symmetry",
     "question": "sweep response for Mid -12, -6, +6, +12 dB at 1.5 kHz",
     "base": BASE,
     "cases": [[f"mid-{sgn(g)}", {"Mid Gain": {"display": g}}] for g in (-12, -6, 6, 12)]},

    {"name": "channeleq-mid-freq", "plan": "4", "probe": "gap2", "read": ["response"], "priority": 1,
     "why": "the Mid bell's centre against Mid Freq (taper, ends) and whether the width follows the frequency, including the interaction with the shelves at the ends",
     "question": "sweep response for Mid +12 dB at Mid Freq 120 Hz, 400 Hz, 1.5 kHz, 4 kHz, 7.5 kHz",
     "base": dict(BASE, **{"Mid Gain": {"display": 12}}),
     "cases": [[f"freq-{f}", {"Mid Freq": {"display": f}}] for f in (120, 400, 1500, 4000, 7500)]},

    {"name": "channeleq-highpass", "plan": "2", "probe": "gap2", "read": ["response", "impulse"], "priority": 1,
     "why": "the HP 80 Hz filter's -3 dB point, slope and corner peaking, alone and with Low and Mid at +12 near it",
     "question": "sweep response and impulse with Highpass On, alone, with Low +12 dB, and with Mid +12 dB at 120 Hz",
     "base": BASE,
     "cases": [["hp-on", {"Highpass On": {"item": "On"}}],
               ["hp-low-p12", {"Highpass On": {"item": "On"}, "Low Gain": {"display": 12}}],
               ["hp-mid120-p12", {"Highpass On": {"item": "On"}, "Mid Gain": {"display": 12}, "Mid Freq": {"display": 120}}]]},

    {"name": "channeleq-combined", "plan": "6, 7", "probe": "gap2", "read": ["response", "static"], "priority": 3,
     "why": "Output as a plain gain, and whether the sections multiply when all are at their extremes (compare with the single-section runs)",
     "question": "sweep response and staircase for Output +12 and -12 dB, all boosts at maximum, all cuts at maximum with HP on",
     "base": BASE,
     "cases": [["output-p12", {"Output": {"display": 12}}], ["output-m12", {"Output": {"display": -12}}],
               ["all-boost", {"Low Gain": {"display": 15}, "Mid Gain": {"display": 12}, "High Gain": {"display": 15}}],
               ["all-cut-hp", {"Highpass On": {"item": "On"}, "Low Gain": {"display": -15}, "Mid Gain": {"display": -12},
                               "High Gain": {"display": -15}}]]},

    # ---- third set (measurements/third/)
    {"name": "channeleq-alias-boost", "plan": "8", "probe": "ext", "read": ["ext: tone10k, tone15k peaks", "impulse"], "priority": 2,
     "why": "aliasing or added lines with High at full boost (and Low and Mid at full boost), and the impulse's alignment",
     "question": "spectral lines of the 10 and 15 kHz sines at High +15 dB; at Low +15, Mid +12 dB, High +15 dB",
     "base": BASE,
     "cases": [["high-max", {"High Gain": {"display": 15}}],
               ["all-max", {"Low Gain": {"display": 15}, "Mid Gain": {"display": 12}, "High Gain": {"display": 15}}]]},

    {"name": "channeleq-lanes", "plan": "4, 8", "probe": "gap2", "read": ["raw render around the changes"], "priority": 2,
     "why": "smoothing of parameter changes: a Mid Gain jump on the steady tone and a Mid Freq glide over the noise (zipper noise, steps)",
     "question": "steady tone with Mid Gain jumping 0 to +12 dB at beat 46 (23 s), Mid Freq 1 kHz; noise with Mid Freq gliding 120 Hz to 7.5 kHz over beats 62 to 69 at Mid Gain +12 dB",
     "base": BASE,
     "cases": [["mid-gain-jump", {"Mid Freq": {"display": 1000},
                                  "Mid Gain": {"auto": [[0, {"display": 0}], [46, {"display": 0}], [46, {"display": 12}]]}}],
               ["mid-freq-glide", {"Mid Gain": {"display": 12},
                                   "Mid Freq": {"auto": [[0, {"display": 120}], [62, {"display": 120}], [69, {"display": 7500}]]}}]]},
]
