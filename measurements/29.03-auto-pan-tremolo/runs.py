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

    # ---- third set (measurements/third/): a stored Waveform never reached the audio, so the
    # waveform is set by an automation lane instead (make_als.py: {"auto": ...})
    {"name": "autopan-waveform-lane", "plan": "3, 4", "probe": "gap2", "read": ["envelope", "modulation"],
     "priority": 1,
     "why": "whether the Waveform reaches the audio through an automation lane (a jump before the impulse, or a one-point lane), and whether a stored Waveform works in Panning mode",
     "question": "envelope of the steady tone, Tremolo 1 Hz: Waveform Triangle by a jump at beat 0.5, Saw Up by a one-point lane, Triangle stored (Tremolo and Panning)",
     "base": BASE,
     "cases": [["lane-triangle-jump", {"Waveform": {"auto": [[0, {"item": "Sine"}], [0.5, {"item": "Triangle"}]]}}],
               ["lane-sawup-const", {"Waveform": {"auto": [[0, {"item": "Saw Up"}]]}}],
               ["stored-triangle", {"Waveform": {"item": "Triangle"}}],
               ["stored-triangle-pan", dict(PAN, Waveform={"item": "Triangle"})]]},

    # autopan-waveform-lane (pilot) found that Waveform takes effect in Panning mode only, stored
    # or automated; in Tremolo every waveform renders as the Sine. So the waveforms are read in
    # Panning, whose gain law (sin/cos of the LFO position) is already measured.
    {"name": "autopan-waveforms-pan", "plan": "3, 4", "probe": "gap2", "read": ["envelope", "modulation"],
     "priority": 1,
     "why": "the shape of every Waveform, read through the Panning law; Shark Tooth and the random ones also at 4 and 0.25 Hz",
     "question": "per-channel envelope of the steady tone in Panning, Amount 100 %, 1 Hz, for each Waveform; Shark Tooth, Random, Wander, S & H also at 4 and 0.25 Hz",
     "base": dict(BASE, **PAN),
     "cases": [[f"pan-{w.lower().replace(' & ', 'n').replace(' ', '-')}", {"Waveform": {"item": w}}]
               for w in ("Sine", "Triangle", "Shark Tooth", "Saw Up", "Saw Down", "Square", "Random", "Wander", "S & H")] +
              [[f"pan-{w.lower().replace(' & ', 'n').replace(' ', '-')}-{f}hz", {"Waveform": {"item": w}, "Frequency": {"display": f}}]
               for w in ("Shark Tooth", "Random", "Wander", "S & H") for f in (4, 0.25)]},

    {"name": "autopan-random-width", "plan": "4", "probe": "gap2", "read": ["envelope", "modulation"], "priority": 2,
     "why": "what Phase does to the random shapes (the manual: it becomes a width), and Shape and Invert on non-sine waves",
     "question": "Panning envelopes of Random and Wander at Phase 0 and 90; Saw Up with Invert; Square with Panning Shape 100 %",
     "base": dict(BASE, **PAN),
     "cases": [[f"{w.lower()}-phase-{p}", {"Waveform": {"item": w}, "Phase": {"display": p}}]
               for w in ("Random", "Wander") for p in (0, 90)] +
              [["sawup-invert", {"Waveform": {"item": "Saw Up"}, "Invert": {"item": "On"}}],
               ["square-shape-100", {"Waveform": {"item": "Square"}, "Panning Shape": {"display": 100}}]]},

    {"name": "autopan-sync-offset", "plan": "6, 7", "probe": "gap2", "read": ["envelope"], "priority": 2,
     "why": "where a synced LFO sits against the beat (the render starts on beat 1) for Offset 0, 90, 180, and more entries of the Rate list",
     "question": "Panning envelopes, Synced: Rate 1/4 with Offset 0, 90, 180; Rate 1/8, 1/16, 1/2 and 3/16 at Offset 0",
     "base": dict(BASE, **PAN, **{"Time Mode": {"item": "Synced"}}),
     "cases": [[f"q-offset-{o}", {"Rate": 12, "Offset": {"display": o}}] for o in (0, 90, 180)] +
              [[f"rate-{n}", {"Rate": i}] for n, i in (("1-8", 15), ("1-16", 17), ("1-2", 8), ("3-16", 13))]},

    {"name": "autopan-onset", "plan": "8", "probe": "ext", "read": ["ext: shortbursts, bedbursts envelope"], "priority": 2,
     "why": "the onset detector behind Attack Time: which bursts restart the ramp (after silence, over a -30 dBFS bed) and how loud an onset must be",
     "question": "envelope of the short bursts and of the bursts over a bed, Tremolo 4 Hz, Amount 100 %, Attack Time 0.5 s",
     "base": dict(BASE, **{"Frequency": {"display": 4}, "Attack Time": {"display": 0.5}}),
     "cases": [["attack-0.5", {}], ["attack-0.5-pan", PAN]]},

    {"name": "autopan-harmonic-crossover", "plan": "10", "probe": "ext", "read": ["ext: threetone", "raw render"], "priority": 2,
     "why": "Harmonic's crossover: the 60 Hz, 200 Hz and 2 kHz tones move in opposition; their gains over a cycle give the split",
     "question": "the three-tone segment through Tremolo, Amount 100 %, 1 Hz, Harmonic on (per-tone envelopes)",
     "base": BASE,
     "cases": [["harmonic", {"Harmonic": {"item": "On"}}], ["harmonic-amount-50", {"Harmonic": {"item": "On"}, "Amount": {"display": 50}}]]},
]
