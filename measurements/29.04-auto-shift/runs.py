# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Auto Shift behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.04-auto-shift.md > Measurement plan.

The only pitched probe signal is the 1 kHz tone (B5 plus 21 cents, so every Quantizer run has a
known nearest note), so each run reads the tone's pitch and level in the renders: the steady
tone's frequency over time (FM rate/depth in `modulation`, or a spectrum / zero-crossing read of
the render), and the staircase for the level.

Not taken: MIDI mode, glide, voice count, mod routing (no MIDI input); Pitch Range, Live Mode,
Use Current Scale and the Included Notes (not API parameters, or no clip scale; the three Pitch
Range latencies cannot be switched); pitch accuracy across ranges and the range edges (one input
frequency); hysteresis between two notes and a gliding input (steps 4 and 5: the input never
moves); Smooth Time against a note change (the probe has no pitch change; only the onset is
seen, so the Smoothing Time is left out); voiced/unvoiced speech (step 12); the latency readout
(Live's own, step 2, not an audio measurement); Quantizer's Pitch Scale Deg. (needs a scale and a
second input pitch)."""

DEVICE = "Auto Shift"

# No quantizing, no smoothing, no shift, no vibrato, no LFO, 100 % wet. Mid-scale knob values
# are written out so the runs share a state.
BASE = {"Quantizer On": {"item": "Off"}, "Smooth On": {"item": "Off"}, "Scale Aware": {"item": "Off"},
        "Input Gain": {"display": 0}, "Dry/Wet": {"display": 100}, "Pitch St.": 0, "Pitch Scale Deg.": 0,
        "Pitch Fine": {"display": 0}, "Formant Shift": {"display": 0}, "Formant Follow": {"display": 0},
        "Strength": {"display": 100}, "Root": {"item": "C"}, "Scale": {"item": "Major"},
        "Vibrato Amt": {"display": 0}, "Vibrato Natural": {"item": "Off"}, "Vibrato Fade-In": {"display": 0},
        "LFO On": {"item": "Off"}, "LFO > Pitch": {"display": 0}, "LFO > Form.": {"display": 0},
        "LFO > Vol": {"display": 0}, "LFO > Pan": {"display": 0}}

# LFO on: free-running 1 Hz, no delay or fade-in; Retrig left on, so each run starts it at the onset.
LFO = dict(BASE, **{"LFO On": {"item": "On"}, "LFO Sync": {"item": "Off"}, "LFO Rate": {"display": 1},
                    "LFO Delay": {"display": 0}, "LFO Fade-In": {"display": 0},
                    "LFO Wave": {"item": "Sine"}, "LFO > Pitch": {"display": 6}})

RUNS = [
    {"name": "autoshift-pitch", "plan": "8", "probe": "gap2", "read": ["modulation", "static", "impulse"],
     "priority": 1,
     "why": "exact ratio of Pitch St. and Pitch Fine (output frequency of the 1 kHz tone), level through the shifter, added delay",
     "question": "pitch and level of the tone for Pitch St. -12, -7, +7, +12 and Pitch Fine -100, +100 ct, correction off",
     "base": BASE,
     "cases": [[f"st{s:+d}", {"Pitch St.": {"display": s}}] for s in (-12, -7, 7, 12)] +
              [[f"fine{c:+d}", {"Pitch Fine": {"display": c}}] for c in (-100, 100)]},

    {"name": "autoshift-strength", "plan": "4", "probe": "gap2", "read": ["modulation"], "priority": 1,
     "why": "how Strength scales the correction (1 kHz is 21 cents above B in C major): linear in cents? and the target chosen",
     "question": "output pitch of the tone against Strength 0, 25, 50, 75, 100 % (C major, Smooth off)",
     "base": dict(BASE, **{"Quantizer On": {"item": "On"}}),
     "cases": [[f"strength-{s}", {"Strength": {"display": s}}] for s in (0, 25, 50, 75)]},

    {"name": "autoshift-scale", "plan": "6", "probe": "gap2", "read": ["modulation"], "priority": 3,
     "why": "whether a scale contains B (target B at -21 cents, or C6 at +79 cents): sanity check of Root/Scale selection and the nearest-note rule",
     "question": "target note chosen for the 1 kHz tone with C minor, C minor pentatonic, C whole tone, B Phrygian, C Messiaen 3 and Chromatic",
     "base": dict(BASE, **{"Quantizer On": {"item": "On"}}),
     "cases": [["c-minor", {"Scale": {"item": "Minor"}}],
               ["c-minor-pent", {"Scale": {"item": "Minor Pentatonic"}}],
               ["c-whole-tone", {"Scale": {"item": "Whole Tone"}}],
               ["b-phrygian", {"Scale": {"item": "Phrygian"}, "Root": {"item": "B"}}],
               ["c-messiaen3", {"Scale": {"item": "Messiaen 3"}}],
               ["chromatic", {"Scale": {"item": "Chromatic"}}]]},

    {"name": "autoshift-vibrato", "plan": "9", "probe": "gap2", "read": ["modulation"], "priority": 2,
     "why": "Vibrato depth in cents, rate in Hz, fade-in time and whether Natural varies rate and depth (FM rate/depth, and the FM trace)",
     "question": "FM rate and depth of the tone for Vibrato Amt 200 ct at Rate 2, 6, 15 Hz, Amt 100 ct, Natural on, Fade-In 1 s",
     "base": dict(BASE, **{"Vibrato Amt": {"display": 200}, "Vibrato Rate": {"display": 6}}),
     "cases": [["rate-2", {"Vibrato Rate": {"display": 2}}], ["rate-6", {}],
               ["rate-15", {"Vibrato Rate": {"display": 15}}],
               ["amt-100", {"Vibrato Amt": {"display": 100}}],
               ["natural", {"Vibrato Natural": {"item": "On"}}],
               ["fade-in-1s", {"Vibrato Fade-In": {"display": 1}}]]},

    {"name": "autoshift-lfo-waves", "plan": "10", "probe": "gap2", "read": ["modulation"], "priority": 2,
     "why": "the shape of each LFO waveform as pitch against time, at 1 Hz and 6 st depth (FM trace of the steady tone)",
     "question": "instantaneous frequency of the tone for each LFO Wave (Sine is the default case), LFO > Pitch 6 st",
     "base": LFO,
     "cases": [[f"wave-{w.lower().replace(' ', '-').replace('&', 'n')}", {"LFO Wave": {"item": w}}]
               for w in ("Triangle", "Triangle 8", "Triangle 16", "Saw Up", "Saw Down", "Rectangle", "Random", "Random S&H")]},

    {"name": "autoshift-lfo-depth", "plan": "10", "probe": "gap2", "read": ["modulation"], "priority": 2,
     "why": "units and taper of the LFO depths: Pitch in semitones, Formant, Volume and Pan as % (AM depth, pitch excursion, L/R levels)",
     "question": "FM depth for LFO > Pitch 2, 12 st; AM depth for LFO > Vol 50, 100 %; L/R levels for LFO > Pan 100 %",
     "base": dict(LFO, **{"LFO > Pitch": {"display": 0}}),
     "cases": [["pitch-2", {"LFO > Pitch": {"display": 2}}], ["pitch-12", {"LFO > Pitch": {"display": 12}}],
               ["vol-50", {"LFO > Vol": {"display": 50}}], ["vol-100", {"LFO > Vol": {"display": 100}}],
               ["pan-100", {"LFO > Pan": {"display": 100}}],
               ["form-100", {"LFO > Form.": {"display": 100}}]]},

    {"name": "autoshift-formant", "plan": "8", "probe": "gap2", "read": ["response", "static"], "priority": 3,
     "why": "what Formant Shift and Formant Follow do to a shifted tone and to noise (spectral envelope of the noise segment, level of the tone)",
     "question": "noise spectrum and tone level for Formant Shift -100, +100 % with no pitch shift, and Follow 0, 100 % at +12 st",
     "base": BASE,
     "cases": [["formant-m100", {"Formant Shift": {"display": -100}}],
               ["formant-p100", {"Formant Shift": {"display": 100}}],
               ["up12-follow-0", {"Pitch St.": {"display": 12}, "Formant Follow": {"display": 0}}],
               ["up12-follow-100", {"Pitch St.": {"display": 12}, "Formant Follow": {"display": 100}}]]},

    {"name": "autoshift-gain-mix", "plan": "11", "probe": "gap2", "read": ["static", "modulation", "impulse"],
     "priority": 3,
     "why": "Input Gain's effect on level, and the Dry/Wet law and dry-path alignment (two tones at +12 st, 50 %)",
     "question": "staircase gain for Input Gain -12, +12 dB; spectrum of the tone for Dry/Wet 0, 25, 50, 75 % at +12 st",
     "base": dict(BASE, **{"Pitch St.": {"display": 12}}),
     "cases": [["gain-m12", {"Input Gain": {"display": -12}}], ["gain-p12", {"Input Gain": {"display": 12}}]] +
              [[f"wet-{w}", {"Dry/Wet": {"display": w}}] for w in (0, 25, 50, 75)]},

    # ---- third set (measurements/third/). The extended probe has a 200 to 400 Hz glide (4 s),
    # a 150 Hz saw (a harmonic source with a real fundamental) and tones at 50 Hz, 3 and 10 kHz.
    # The Pitch Range and Live Mode are stored elements (Global_PitchRange, Global_LiveMode).
    {"name": "autoshift-glide", "plan": "4", "probe": "ext", "read": ["ext: glide (instantaneous frequency)"], "priority": 1,
     "why": "the quantizer on a moving input: steps and transitions on the 200 to 400 Hz glide, Smooth off, 50 and 200 ms, Strength 50 %",
     "question": "pitch of the glide through the quantizer (C major, Strength 100 %) with Smooth off, Smooth 50 ms and 200 ms, and Strength 50 % with Smooth off",
     "base": dict(BASE, **{"Quantizer On": {"item": "On"}}),
     "cases": [["smooth-off", {}],
               ["smooth-50ms", {"Smooth On": {"item": "On"}, "Smooth Time": {"display": 0.05}}],
               ["smooth-200ms", {"Smooth On": {"item": "On"}, "Smooth Time": {"display": 0.2}}],
               ["strength-50", {"Strength": {"display": 50}}]]},

    {"name": "autoshift-ranges", "plan": "2, 3", "probe": "ext", "read": ["ext: glide, saw, tone50, tone3k", "impulse"], "priority": 1,
     "why": "pitch detection across the three Pitch Ranges and Live Mode (stored elements): which inputs each range tracks, octave errors, and the alignment of the output",
     "question": "the glide, the 150 Hz saw and the 50 Hz and 3 kHz tones through the quantizer (C major) with Global_PitchRange 0, 1, 2, and range 1 with Live Mode on",
     "base": dict(BASE, **{"Quantizer On": {"item": "On"}}),
     "cases": [[f"range-{r}", {"@Global_PitchRange": r}] for r in (0, 2)] +
              [["range-1-live", {"@Global_LiveMode": True}]]},

    {"name": "autoshift-formant-saw", "plan": "8", "probe": "ext", "read": ["ext: saw (spectral envelope)"], "priority": 2,
     "why": "formant handling on a harmonic source: Follow 50 % with a shift, and Formant Shift at -50 and +50 %",
     "question": "spectrum of the 150 Hz saw at Pitch +12 with Formant Follow 0, 50, 100 %; Formant Shift -50 and +50 % at no shift",
     "base": BASE,
     "cases": [[f"up12-follow-{f}", {"Pitch St.": 12, "Formant Follow": {"display": f}}] for f in (0, 50, 100)] +
              [[f"formant{f:+d}", {"Formant Shift": {"display": f}}] for f in (-50, 50)]},

    {"name": "autoshift-lfo-timing", "plan": "10", "probe": "gap2", "read": ["modulation (FM over time)"], "priority": 2,
     "why": "LFO Delay and Fade-In, Sync, Retrigger and the Formant target, from the steady tone's pitch over time",
     "question": "pitch of the steady tone with the LFO (1 Hz sine, 6 st) at Delay 1 s, Fade-In 2 s, Sync 1/4, Retrig off; and LFO > Form. 50 % with no pitch depth",
     "base": LFO,
     "cases": [["delay-1s", {"LFO Delay": {"display": 1}}], ["fadein-2s", {"LFO Fade-In": {"display": 2}}],
               ["sync-q", {"LFO Sync": {"item": "On"}, "LFO Synced": 12}], ["retrig-off", {"LFO Retrig On": {"item": "Off"}}],
               ["formant-50", {"LFO > Pitch": {"display": 0}, "LFO > Form.": {"display": 50}}]]},

    {"name": "autoshift-vibrato-natural", "plan": "11", "probe": "gap2", "read": ["modulation"], "priority": 3,
     "why": "the Vibrato with Natural on and with a Fade-In (the plain vibrato was measured)",
     "question": "pitch of the steady tone with Vibrato 50 ct at 6 Hz: Natural on; Fade-In 1 s",
     "base": dict(BASE, **{"Vibrato Amt": {"display": 50}, "Vibrato Rate": {"display": 6}}),
     "cases": [["natural", {"Vibrato Natural": {"item": "On"}}], ["fadein-1s", {"Vibrato Fade-In": {"display": 1}}]]},
]
