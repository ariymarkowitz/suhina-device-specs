# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Auto Pan-Tremolo behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.03-auto-pan-tremolo.md > Measurement plan.

The LFO shows in the steady 1 kHz tone (8 s, -12 dBFS): `modulation` gives its AM rate and depth
and the L/R envelope correlation; the renders also hold the envelope itself, which the runs on
shapes and waveforms read directly (gain against time, per channel).

Not taken: transport restart repeatability of Random/Wander (step 4: one render per case, no
restart), Phase Offset in beat modes against a click (step 7: no click in the probe; the run
autopan-time-modes only checks periods), tempo ramps and transport stop, Time = 200 s limits,
the latency impulse of step 12 (every run's impulse segment gives it), and the Frequency
Modulation measured at levels other than the bursts' -30 and -6 dBFS (no level steps at constant
LFO in the probe)."""

DEVICE = "Auto Pan-Tremolo"

# Tremolo, sine, 1 Hz free-running, full depth, no shaping, no attack, no dynamic modulation.
BASE = {"Mode": {"item": "Tremolo"}, "Amount": {"display": 100}, "Waveform": {"item": "Sine"},
        "Invert": {"item": "Off"}, "Time Mode": {"item": "Rate"}, "Frequency": {"display": 1},
        "Phase": {"display": 180}, "Offset": {"display": 0}, "Stereo Mode": {"item": "Phase"},
        "Spin": {"display": 0}, "Panning Shape": {"display": 0}, "Tremolo Shape": {"display": 0},
        "Attack Time": {"display": 0}, "Dyn Mod": {"display": 0}, "Harmonic": {"item": "Off"},
        "Vintage": {"item": "Off"}}

PAN = {"Mode": {"item": "Panning"}}

RUNS = [
    {"name": "autopan-amount", "plan": "2", "probe": "gap2", "read": ["modulation", "envelope", "stereo"],
     "priority": 1,
     "why": "how Amount maps to gain depth in Tremolo and to the L/R gains in Panning (law, trough value, L/R correlation)",
     "question": "AM depth and per-channel envelope of the steady tone for Amount 25, 50, 100 % in Tremolo and in Panning (Phase 180)",
     "base": BASE,
     "cases": [[f"trem-{a}", {"Amount": {"display": a}}] for a in (25, 50)] +
              [[f"pan-{a}", dict(PAN, Amount={"display": a})] for a in (25, 50, 100)]},

    {"name": "autopan-waveforms", "plan": "3, 4", "probe": "gap2", "read": ["envelope", "modulation"],
     "priority": 1,
     "why": "gain-against-time shape of every Waveform (Sine is the default case), including Shark Tooth and the random ones",
     "question": "per-channel envelope of the steady tone for each Waveform in Tremolo, 1 Hz, Amount 100 %",
     "base": BASE,
     "cases": [[f"wave-{w.lower().replace(' & ', 'n').replace(' ', '-')}", {"Waveform": {"item": w}}]
               for w in ("Triangle", "Shark Tooth", "Saw Up", "Saw Down", "Square", "Random", "Wander", "S & H")]},

    {"name": "autopan-shape", "plan": "3", "probe": "gap2", "read": ["envelope", "modulation"],
     "priority": 1,
     "why": "the Shape curve in Tremolo (both signs) and Panning, and what Invert does to ramps",
     "question": "envelope of the steady tone for Tremolo Shape -100, -50, 50, 100 %, Panning Shape 50, 100 %, and Invert on Sine and Saw Up",
     "base": BASE,
     "cases": [[f"trem-shape-{s}", {"Tremolo Shape": {"display": s}}] for s in (-100, -50, 50, 100)] +
              [[f"pan-shape-{s}", dict(PAN, **{"Panning Shape": {"display": s}})] for s in (50, 100)] +
              [["invert-sine", {"Invert": {"item": "On"}}],
               ["invert-saw-up", {"Invert": {"item": "On"}, "Waveform": {"item": "Saw Up"}}]]},

    {"name": "autopan-stereo-offset", "plan": "5", "probe": "gap2", "read": ["modulation", "envelope", "stereo"],
     "priority": 2,
     "why": "Phase between L and R LFOs, and Spin's frequency ratio (L and R LFO rates from each channel's envelope)",
     "question": "per-channel envelope in Panning for Phase 0, 90, 270 and Spin 25, 50 % (Stereo Mode Spin)",
     "base": dict(BASE, **PAN),
     "cases": [[f"phase-{p}", {"Phase": {"display": p}}] for p in (0, 90, 270)] +
              [[f"spin-{s}", {"Stereo Mode": {"item": "Spin"}, "Spin": {"display": s}}] for s in (25, 50)]},

    {"name": "autopan-time-modes", "plan": "6", "probe": "gap2", "read": ["modulation", "envelope"],
     "priority": 2,
     "why": "LFO period in each Time mode at 120 BPM: Hz, Time, Synced, Triplet, Dotted, 16th (and the triplet and dotted factors)",
     "question": "AM rate of the steady tone for Rate 2 Hz, Time 0.5 s, Synced 1/4, Triplet 1/4, Dotted 1/4, 16th 4",
     "base": BASE,
     "cases": [["rate-2hz", {"Frequency": {"display": 2}}],
               ["time-0.5s", {"Time Mode": {"item": "Time"}, "Time": {"display": 0.5}}],
               ["synced-quarter", {"Time Mode": {"item": "Synced"}, "Rate": 12}],
               ["triplet-quarter", {"Time Mode": {"item": "Triplet"}, "Rate": 12}],
               ["dotted-quarter", {"Time Mode": {"item": "Dotted"}, "Rate": 12}],
               ["sixteenth-4", {"Time Mode": {"item": "16th"}, "16th": 4}]]},

    {"name": "autopan-attack", "plan": "8", "probe": "gap2", "read": ["envelope", "modulation"],
     "priority": 2,
     "why": "Attack Time: how the modulation depth ramps up after the tone's onset (time to full depth, shape)",
     "question": "envelope of the steady tone (8 s, onset after silence) for Attack Time 50 ms, 0.5 s, 2 s, 5 s, Tremolo 4 Hz Amount 100 %",
     "base": dict(BASE, **{"Frequency": {"display": 4}}),
     "cases": [[f"attack-{t}", {"Attack Time": {"display": t}}] for t in (0.05, 0.5, 2, 5)]},

    {"name": "autopan-dynmod", "plan": "9", "probe": "gap2", "read": ["envelope", "modulation"],
     "priority": 2,
     "why": "Dyn Mod's scaling of the LFO rate with level (rate during the -30 and -6 dBFS bursts and the -12 dBFS steady tone)",
     "question": "LFO rate read from the bursts' and steady tone's envelope for Dyn Mod -100, -50, 50, 100 % at 2 Hz",
     "base": dict(BASE, **{"Frequency": {"display": 2}}),
     "cases": [[f"dynmod-{d}", {"Dyn Mod": {"display": d}}] for d in (-100, -50, 50, 100)]},

    {"name": "autopan-harmonic-vintage", "plan": "10, 11", "probe": "gap2",
     "read": ["response", "static", "modulation"], "priority": 3,
     "why": "Harmonic: crossover and flatness at Amount 0 (sweep); Vintage: added harmonics and level curve (staircase, steady tone spectrum)",
     "question": "sweep and staircase with Harmonic on at Amount 0 and 100 %, Vintage on at Amount 0 and 100 %",
     "base": BASE,
     "cases": [["harmonic-amount-0", {"Harmonic": {"item": "On"}, "Amount": {"display": 0}}],
               ["harmonic-100", {"Harmonic": {"item": "On"}}],
               ["vintage-amount-0", {"Vintage": {"item": "On"}, "Amount": {"display": 0}}],
               ["vintage-100", {"Vintage": {"item": "On"}}]]},
]
