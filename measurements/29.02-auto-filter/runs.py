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

    # ---- third set (measurements/third/)
    {"name": "autofilter-morph-dj-comb", "plan": "2", "probe": "gap2", "read": ["response"], "priority": 1,
     "why": "the rest of the Morph, DJ, Comb and Vowel shapes: Morph across 0..100 % and its four slopes, DJ's low-pass side, Comb at its ends, Vowel's formant positions",
     "question": "sweep response at Freq 1 kHz, Res 30 %: Morph 0, 25, 75, 100 % (24 dB) and Morph 50 % at 6, 12, 48 dB; DJ Control -100, -50, 50 %; Comb Morph 0 and 100 %; Vowel Formant 0, 25, 75, 100 %; Vowel at Pitch +12 and -12",
     "base": dict(BASE, **{"Resonance": {"display": 30}}),
     "cases": [[f"morph-{m}", {"Filter Type": {"item": "Morph"}, "Filter Morph": {"display": m}}] for m in (0, 25, 75, 100)] +
              [[f"morph50-{s}", {"Filter Type": {"item": "Morph"}, "Filter Morph": {"display": 50}, "Morph Slope": {"item": s}}]
               for s in ("6dB", "12dB", "48dB")] +
              [[f"dj{c:+d}", {"Filter Type": {"item": "DJ"}, "Control": {"display": c}}] for c in (-100, -50, 50)] +
              [[f"comb-morph-{m}", {"Filter Type": {"item": "Comb"}, "Filter Morph": {"display": m}}] for m in (0, 100)] +
              [[f"vowel-formant-{f}", {"Filter Type": {"item": "Vowel"}, "Formant": {"display": f}}] for f in (0, 25, 75, 100)] +
              [[f"vowel-pitch{p:+d}", {"Filter Type": {"item": "Vowel"}, "Pitch": p}] for p in (12, -12)]},

    {"name": "autofilter-freq-res-grid", "plan": "2", "probe": "gap2", "read": ["response"], "priority": 2,
     "why": "the low-pass at other cutoffs and resonances (does the shape scale with Freq; where does self-oscillation start in each circuit)",
     "question": "sweep response of Low-pass 24 dB at Freq 200 Hz and 8 kHz, Res 0, 50, 100 %, SVF; and of each other circuit at Freq 200 Hz, Res 100 %",
     "base": BASE,
     "cases": [[f"lp-{f}-res{r}", {"Frequency": {"display": f}, "Resonance": {"display": r}}]
               for f in (200, 8000) for r in (0, 50, 100)] +
              [[f"{c.lower()}-200-res100", {"Circuit": {"item": c}, "Frequency": {"display": 200}, "Resonance": {"display": 100}}]
               for c in ("DFM", "MS2", "PRD")]},

    {"name": "autofilter-resampling", "plan": "3", "probe": "ext", "read": ["impulse", "ext: tone3k, tone10k peaks"], "priority": 2,
     "why": "Resampling at other Freq values: the hold length against Freq and the alias images of a 3 kHz and a 10 kHz sine",
     "question": "impulse and spectral lines of the 3 and 10 kHz sines through Resampling at Freq 500 Hz, 4 kHz, 16 kHz",
     "base": BASE,
     "cases": [[f"resample-{f}", {"Filter Type": {"item": "Resampling"}, "Frequency": {"display": f}}] for f in (500, 4000, 16000)]},

    {"name": "autofilter-drive", "plan": "4", "probe": "ext", "read": ["ext: stair100, ramp"], "priority": 1,
     "why": "Drive's gain and distortion in each circuit, with the filter wide open (20 kHz low-pass)",
     "question": "100 Hz staircase and 1 kHz ramp at Drive 0, 50, 100 % for SVF, DFM, MS2, PRD, Freq 20 kHz, Res 0",
     "base": dict(BASE, **{"Frequency": {"display": 20000}}),
     "cases": [[f"{c.lower()}-drive-{d}", {"Circuit": {"item": c}, "Drive": {"display": d}}]
               for c in ("SVF", "DFM", "MS2", "PRD") for d in (0, 50, 100)]},

    {"name": "autofilter-lfo-params", "plan": "6, 7", "probe": "gap2", "read": ["modulation", "envelope", "noise"], "priority": 2,
     "why": "LFO Morph, Phase (L/R offset), Spin, Steps, S&H, Smoothing and the synced and time modes, from the steady tone's envelope per channel",
     "question": "envelope of the steady tone (LFO 1 Hz, Amount 100 %, Res 40 %, Freq 1 kHz) for LFO Morph -100 and +100 %, Phase 90 and 180, Spin 25 and 50 %, Steps 4 and 16, S&H 1/8, Smoothing 50 %, Time 0.5 s, Synced, Triplet and Dotted at Rate 12, Sixteenth 3, and the S & H wave",
     "base": LFO,
     "cases": [["morph-100", {"LFO Morph": {"display": -100}}], ["morph+100", {"LFO Morph": {"display": 100}}],
               ["phase-90", {"LFO Phase": {"display": 90}}], ["phase-180", {"LFO Phase": {"display": 180}}],
               ["spin-25", {"LFO S Mode": {"item": "Spin"}, "LFO Spin": {"display": 25}}],
               ["spin-50", {"LFO S Mode": {"item": "Spin"}, "LFO Spin": {"display": 50}}],
               ["steps-4", {"LFO Q Mode": {"item": "Steps"}, "LFO Steps": 4}],
               ["steps-16", {"LFO Q Mode": {"item": "Steps"}, "LFO Steps": 16}],
               ["snh-1-8", {"LFO Q Mode": {"item": "S&H"}, "LFO S&H": -3}],
               ["smooth-50", {"LFO Smoothing": {"display": 50}}],
               ["time-0.5s", {"LFO T Mode": {"item": "Time"}, "LFO Time": {"display": 0.5}}],
               ["synced-r12", {"LFO T Mode": {"item": "Synced"}, "LFO Rate": 12}],
               ["triplet-r12", {"LFO T Mode": {"item": "Triplet"}, "LFO Rate": 12}],
               ["dotted-r12", {"LFO T Mode": {"item": "Dotted"}, "LFO Rate": 12}],
               ["sixteenth-3", {"LFO T Mode": {"item": "Sixteenth"}, "LFO 16th": 3}],
               ["sh-wave", {"LFO Wave": {"item": "S & H"}}]]},

    {"name": "autofilter-depth-up", "plan": "6", "probe": "gap2", "read": ["modulation", "envelope", "dynamics"], "priority": 2,
     "why": "the upward travel of the LFO (cutoff low, so the sine's upper half opens the filter on the 1 kHz tone) and the envelope's +-100 % at Res 70 %",
     "question": "steady tone through Low-pass at Freq 100 Hz, LFO Amount 50 and 100 %; bursts with Env Amount +100 and -100 % at Freq 2 kHz, Res 70 %",
     "base": LFO,
     "cases": [[f"up-amt-{a}", {"Frequency": {"display": 100}, "LFO Amount": {"display": a}}] for a in (50, 100)] +
              [[f"env{a:+d}-res70", dict(ENV, **{"Frequency": {"display": 2000}, "Resonance": {"display": 70},
                                                  "Env Amount": {"display": a}, "LFO Amount": {"display": 0}})]
               for a in (100, -100)]},

    {"name": "autofilter-env-detector", "plan": "8", "probe": "ext", "read": ["ext: shortbursts, bedbursts"], "priority": 2,
     "why": "the envelope's detector (peak or RMS: does a 1 ms burst open the filter as far as a 300 ms one?), Hold with short bursts, and Env S&H",
     "question": "output of 1 to 300 ms bursts at -6 dBFS and of bursts over a -30 dBFS bed, Freq 400 Hz, Env 100 %, Attack 1 ms, Release 100 ms; Hold off (default) and on; Env S&H 1/16",
     "base": ENV,
     "cases": [["hold-on", {"Env Hold On": {"item": "On"}}], ["snh-1-16", {"Env S&H On": {"item": "On"}, "Env S&H": -4}]]},

    {"name": "autofilter-clip-output-mix", "plan": "10, 11", "probe": "gap2", "read": ["static", "impulse", "response"], "priority": 2,
     "why": "the soft clip's curve at high resonance, Output steps, Dry/Wet at 50 % (dry delay, law), and the stored HiQuality switch with Drive",
     "question": "staircase and impulse: Soft Clip on and off with Res 90 % at Freq 1 kHz; Output -12 dB; Dry/Wet 50 % at Freq 500 Hz; MS2 at Drive 100 % with HiQuality stored on and off",
     "base": BASE,
     "cases": [["clip-res90", {"Soft Clip On": {"item": "On"}, "Resonance": {"display": 90}}],
               ["noclip-res90", {"Resonance": {"display": 90}}],
               ["output-12", {"Output": {"display": -12}}],
               ["drywet-50", {"Dry/Wet": {"display": 50}, "Frequency": {"display": 500}}],
               ["ms2-drive-hq", {"Circuit": {"item": "MS2"}, "Drive": {"display": 100}, "Frequency": {"display": 20000}, "@HiQuality": True}],
               ["ms2-drive", {"Circuit": {"item": "MS2"}, "Drive": {"display": 100}, "Frequency": {"display": 20000}}]]},

    {"name": "autofilter-hiquality-alias", "plan": "11", "probe": "ext", "read": ["ext: tone10k, tone15k peaks"], "priority": 2,
     "why": "aliasing of the driven circuits with HiQuality (stored element) off and on",
     "question": "spectral lines of the 10 and 15 kHz sines through MS2 and PRD at Drive 100 %, Freq 20 kHz, HiQuality off and on",
     "base": dict(BASE, **{"Frequency": {"display": 20000}, "Drive": {"display": 100}}),
     "cases": [[f"{c.lower()}-hq-{'on' if q else 'off'}", {"Circuit": {"item": c}, "@HiQuality": q}]
               for c in ("MS2", "PRD") for q in (False, True)]},
]
