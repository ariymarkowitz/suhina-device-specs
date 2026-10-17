# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Amp behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.01-amp.md > Measurement plan.

Not taken: step 1's 100 Hz sine (the probe's tone is 1 kHz only; the 1 kHz staircase and the
sweep at -12 dBFS stand in for it), the full model x Bass/Middle/Treble grid of step 2 (one model
here; the sweep of every model at the middle settings is in amp-models), noise and DC per model
at high Gain (step 7 is read from the `silence` segment of the Gain run), model-switch state
(needs a parameter change during the render)."""

DEVICE = "Amp"

# Panel values are 0..10 (display = stored). Mono, 100 % wet, Volume low enough that the power
# amp stays out of the way unless the run is about it.
BASE = {"Amp Type": {"item": "Rock"}, "Input Gain": {"display": 5}, "Bass": {"display": 5},
        "Middle": {"display": 5}, "Treble": {"display": 5}, "Presence": {"display": 5},
        "Volume": {"display": 5}, "Dual Mono": {"item": "Off"}, "Dry/Wet": {"display": 100}}

MODELS = ["Clean", "Boost", "Blues", "Rock", "Lead", "Heavy", "Bass"]

RUNS = [
    {"name": "amp-models", "plan": "1, 2", "probe": "gap2", "read": ["static", "response", "stereo"],
     "priority": 1,
     "why": "level, harmonics and tone of each of the seven models at the same panel settings",
     "question": "static curve (gain, THD, harmonics vs level) and sweep response of every Amp Type, all knobs at 5, Volume 5",
     "base": BASE,
     "cases": [[f"model-{m.lower()}", {"Amp Type": {"item": m}}] for m in MODELS]},

    {"name": "amp-gain", "plan": "1", "probe": "gap2", "read": ["static", "silence"], "priority": 1,
     "why": "how Gain moves the preamp from clean to clipping (output vs input level, THD, even/odd harmonics)",
     "question": "static curve of Rock at Input Gain 0, 2.5, 5, 7.5, 10",
     "base": BASE,
     "cases": [[f"gain-{g}", {"Input Gain": {"display": g}}] for g in (0, 2.5, 5, 7.5, 10)]},

    {"name": "amp-tone-stack", "plan": "2", "probe": "gap2", "read": ["response"], "priority": 1,
     "why": "Bass, Middle and Treble at their extremes: tone-stack shape and cross-coupling (low Gain, no clipping)",
     "question": "sweep response of Rock at low Gain with each of Bass, Middle, Treble at 0 and 10, the others at 5",
     "base": dict(BASE, **{"Input Gain": {"display": 1}}),
     "cases": [["flat", {}]] + [[f"{n.lower()}-{v}", {n: {"display": v}}]
                                for n in ("Bass", "Middle", "Treble") for v in (0, 10)]},

    {"name": "amp-volume", "plan": "1", "probe": "gap2", "read": ["static"], "priority": 2,
     "why": "which models distort from Volume (the manual says Blues, Heavy, Bass) and how output level follows Volume",
     "question": "static curve of Blues at Volume 0, 5, 9, 10, plus Clean, Heavy and Bass at Volume 10, low Gain",
     "base": dict(BASE, **{"Input Gain": {"display": 2}, "Amp Type": {"item": "Blues"}}),
     "cases": [[f"blues-vol-{v}", {"Volume": {"display": v}}] for v in (0, 5, 9, 10)] +
              [[f"{m.lower()}-vol-10", {"Amp Type": {"item": m}, "Volume": {"display": 10}}]
               for m in ("Clean", "Heavy", "Bass")]},

    {"name": "amp-presence", "plan": "3", "probe": "gap2", "read": ["response"], "priority": 2,
     "why": "Presence's effect on the high end, and how much the effect differs between models",
     "question": "sweep response of Rock and Lead at low Gain with Presence 0, 5, 10",
     "base": dict(BASE, **{"Input Gain": {"display": 1}}),
     "cases": [[f"{m.lower()}-pres-{p}", {"Amp Type": {"item": m}, "Presence": {"display": p}}]
               for m in ("Rock", "Lead") for p in (0, 5, 10)]},

    {"name": "amp-dual-mono", "plan": "5, 6", "probe": "gap2", "read": ["stereo", "impulse", "static"],
     "priority": 2,
     "why": "Mono vs Dual: whether Mono sums left and right, how a one-sided input comes out, and the latency",
     "question": "2x2 level matrix and impulse of Blues in Mono and Dual, and at Dry/Wet 50 % in Mono",
     "base": dict(BASE, **{"Amp Type": {"item": "Blues"}}),
     "cases": [["mono", {"Dual Mono": {"item": "Off"}}], ["dual", {"Dual Mono": {"item": "On"}}],
               ["dual-wet-50", {"Dual Mono": {"item": "On"}, "Dry/Wet": {"display": 50}}],
               ["mono-wet-50", {"Dry/Wet": {"display": 50}}]]},
]
