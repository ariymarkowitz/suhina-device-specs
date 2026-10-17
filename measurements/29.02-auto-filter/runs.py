# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Auto Filter behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.02-auto-filter.md > Measurement plan.

Not taken: the side-chain (step 9: no external input); Comb, Vowel and Resampling beyond one
snapshot each (steps 2 and 3 would need a grid of Freq x Morph x Formant that costs tracks; the
first sweep of each in autofilter-types-other tells which to follow up); S&H, Wander and Steps
statistics (step 7: only the waveforms' shape at one rate, from the steady tone's envelope);
LFO rates in synced modes and the Phase/Spin L/R offset beyond the AM read of the steady tone;
Hold with a 5 ms burst (the probe has no such burst); the display (step 12) and the clip LED
(step 10)."""

DEVICE = "Auto Filter"

# Low-pass, 24 dB, SVF, no resonance, no drive, no modulation, 100 % wet.
BASE = {"Filter Type": {"item": "Low-pass"}, "Filter Slope": {"item": "24dB"},
        "Circuit": {"item": "SVF"}, "Frequency": {"display": 1000}, "Resonance": {"display": 0},
        "Drive": {"display": 0}, "LFO Amount": {"display": 0}, "Env Amount": {"display": 0},
        "Soft Clip On": {"item": "Off"}, "Dry/Wet": {"display": 100}}

# LFO set to something steady: 1 Hz free-running, zero Phase so L and R agree.
LFO = dict(BASE, **{"LFO T Mode": {"item": "Rate"}, "LFO Freq": {"display": 1}, "LFO Phase": {"display": 0},
                    "LFO Offset": {"display": 0}, "LFO S Mode": {"item": "Phase"}, "LFO Spin": {"display": 0},
                    "LFO Morph": {"display": 0}, "LFO Smoothing": {"display": 0}, "LFO Q Mode": {"item": "None"},
                    "LFO Amount": {"display": 100}, "Resonance": {"display": 40}})

# Envelope follower: low cutoff so the loud burst opens the filter on the 1 kHz tone.
ENV = dict(BASE, **{"Frequency": {"display": 400}, "Env Hold On": {"item": "Off"},
                    "Env S&H On": {"item": "Off"}, "Env Amount": {"display": 100},
                    "Env Attack": {"display": 0.001}, "Env Release": {"display": 0.1}})

RUNS = [
    {"name": "autofilter-types-svf", "plan": "2", "probe": "gap2", "read": ["response"], "priority": 1,
     "why": "response shape and slope of Low-pass, High-pass, Band-pass and Notch at 12 and 24 dB (SVF), with some resonance",
     "question": "sweep response of the four basic types at Freq 1 kHz, Res 30 %, slope 12 and 24 dB",
     "base": dict(BASE, **{"Resonance": {"display": 30}}),
     "cases": [[f"{t.lower().replace('-', '')}-{s}", {"Filter Type": {"item": t}, "Filter Slope": {"item": f"{s}dB"}}]
               for t in ("Low-pass", "High-pass", "Band-pass", "Notch") for s in (12, 24)]},

    {"name": "autofilter-circuits", "plan": "2", "probe": "gap2", "read": ["response", "static"], "priority": 1,
     "why": "how the SVF, DFM, MS2 and PRD circuits differ in slope, resonance peak and level",
     "question": "sweep response of Low-pass 24 dB at Freq 1 kHz and Res 60 % for each Circuit, and at 12 dB for DFM and PRD",
     "base": dict(BASE, **{"Resonance": {"display": 60}}),
     "cases": [[f"circuit-{c.lower()}", {"Circuit": {"item": c}}] for c in ("SVF", "DFM", "MS2", "PRD")] +
              [[f"circuit-{c.lower()}-12", {"Circuit": {"item": c}, "Filter Slope": {"item": "12dB"}}]
               for c in ("DFM", "PRD")]},

    {"name": "autofilter-resonance", "plan": "2, 5", "probe": "gap2", "read": ["response", "impulse"],
     "priority": 1,
     "why": "the peak height and width against Res, and whether and how long Res 100 % rings after the impulse (SVF only; other circuits not taken)",
     "question": "sweep response and impulse of Low-pass 24 dB at Freq 440 Hz and Res 0, 25, 50, 75, 100 % (SVF)",
     "base": dict(BASE, **{"Frequency": {"display": 440}}),
     "cases": [[f"res-{r}", {"Resonance": {"display": r}}] for r in (0, 25, 50, 75, 100)]},

    {"name": "autofilter-types-other", "plan": "2, 3", "probe": "gap2", "read": ["response"], "priority": 2,
     "why": "one snapshot each of Morph, DJ, Comb, Resampling, Notch+LP and Vowel to see which need a follow-up grid",
     "question": "sweep response of the six non-basic filter types at Freq 1 kHz, Res 30 %, Morph 50 %, DJ Control +50 %",
     "base": dict(BASE, **{"Resonance": {"display": 30}, "Filter Morph": {"display": 50}}),
     "cases": [["morph", {"Filter Type": {"item": "Morph"}}],
               ["dj-plus", {"Filter Type": {"item": "DJ"}, "Control": {"display": 50}}],
               ["comb", {"Filter Type": {"item": "Comb"}}],
               ["resampling", {"Filter Type": {"item": "Resampling"}}],
               ["notch-lp", {"Filter Type": {"item": "Notch+LP"}}],
               ["vowel", {"Filter Type": {"item": "Vowel"}, "Formant": {"display": 50}}]]},

    {"name": "autofilter-env-amount", "plan": "8", "probe": "gap2", "read": ["static", "dynamics"],
     "priority": 1,
     "why": "how Env Amount maps level to cutoff (gain against input level on the staircase), both signs",
     "question": "static curve and bursts of Low-pass 24 dB at 400 Hz with Env Amount -100, -50, 50, 100 % and 0",
     "base": ENV,
     "cases": [[f"env-{a}", {"Env Amount": {"display": a}}] for a in (-100, -50, 0, 50)]},

    {"name": "autofilter-env-time", "plan": "8", "probe": "gap2", "read": ["dynamics"], "priority": 1,
     "why": "Env Attack and Release time constants and their shape (63 % and 90 % times of the filtered burst)",
     "question": "bursts through Low-pass 400 Hz with Env Amount 100 % and Attack/Release of (1, 100 ms), (50, 100 ms), (1, 1 s), (50, 1 s)",
     "base": ENV,
     "cases": [["a1-r100", {"Env Attack": {"display": 0.001}, "Env Release": {"display": 0.1}}],
               ["a50-r100", {"Env Attack": {"display": 0.05}, "Env Release": {"display": 0.1}}],
               ["a1-r1000", {"Env Attack": {"display": 0.001}, "Env Release": {"display": 1}}],
               ["a50-r1000", {"Env Attack": {"display": 0.05}, "Env Release": {"display": 1}}],
               ["hold-on", {"Env Hold On": {"item": "On"}, "Env Release": {"display": 0.1}}]]},

    {"name": "autofilter-lfo-waves", "plan": "7", "probe": "gap2", "read": ["modulation", "envelope"],
     "priority": 2,
     "why": "the shape of each LFO waveform, from the steady tone's envelope through a resonant low-pass at 1 Hz",
     "question": "AM envelope of the steady tone for each LFO Wave at 1 Hz, Amount 100 %, Phase 0",
     "base": LFO,
     "cases": [[f"wave-{w.lower().replace(' ', '').replace('&', 'n')}", {"LFO Wave": {"item": w}}]
               for w in ("Sine", "Triangle", "Saw", "Square", "Ramp Up", "Ramp Down", "Wander", "S & H")]},

    {"name": "autofilter-lfo-amount", "plan": "6, 7", "probe": "gap2", "read": ["modulation", "envelope"],
     "priority": 2,
     "why": "how LFO Amount (and its taper) maps to the cutoff's travel in octaves, and the actual rate for LFO Freq 1 Hz and 4 Hz",
     "question": "AM depth and rate of the steady tone for LFO Amount 10, 25, 50, 100 % with a sine, and at Freq 4 Hz",
     "base": dict(LFO, **{"LFO Wave": {"item": "Sine"}}),
     "cases": [[f"amount-{a}", {"LFO Amount": {"display": a}}] for a in (10, 25, 50)] +
              [["freq-4hz", {"LFO Freq": {"display": 4}}]]},
]
