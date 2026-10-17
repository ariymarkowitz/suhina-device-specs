# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Spectral Resonator behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.36-spectral-resonator.md › Measurement plan.

All runs are Internal mode (the loaded one), wet only. Partial positions are read from a long FFT of
the white-noise segment of the render (the 1/6-octave `noise_db` is too coarse for a comb); `read`
says so.

Left out (cannot be measured this way): MIDI mode, Mono/Poly, Polyphony, MIDI Gate, PB, Glide
(plan 7, 8: no MIDI input); the modulation modes (plan 9) because the mode is not an API parameter
(the loaded one is None, so Mod Rate and Pch. Mod do nothing); scale and tuning behaviour (plan 11,
needs a clip scale or tuning file); the spectrogram. The Note form of Freq and Quantize are not
proposed (Freq. Hz covers the pitch law; Quantize needs the scale of plan 11).
"""

DEVICE = "Spectral Resonator"

ON, OFF = 1, 0
BASE = {"Dry Wet": {"display": 100}}

RUNS = [
    {"name": "spectral-resonator-partials", "plan": "2, 3", "probe": "gap2", "read": ["noise (long FFT of the render's noise segment)"], "priority": 1,
     "why": "partial positions against Freq and Stretch (the stretch law, the -100 % limit) and peak widths",
     "question": "peak frequencies of the resonance comb for Freq 55, 220, 880 Hz at Stretch 0, and Stretch -100, -50, +50, +100 % at 110 Hz (Harmonics 256, Decay 222 ms)",
     "base": BASE,
     "cases": [[f"freq-{f}", {"Freq. Hz": {"display": f}}] for f in (55, 220, 880)]
     + [[f"stretch{s:+d}", {"Stretch": {"display": s}}] for s in (-100, -50, 50, 100)]},

    {"name": "spectral-resonator-decay", "plan": "4", "probe": "gap10", "read": ["impulse"], "priority": 1,
     "why": "ring-out time against Decay (unit, is it a T60) up to the 8 s setting; the 10 s probe gap holds the longest tail",
     "question": "T60 of a partial in the impulse response for Decay 40 ms, 313 ms, 1.06 s, 2.5 s, 8.44 s (Freq 110 Hz)",
     "base": BASE,
     "cases": [[f"decay-{d}ms", {"Decay": {"display": d / 1000}}] for d in (40, 313, 1060, 2500, 8440)]},

    {"name": "spectral-resonator-damp-harmonics", "plan": "2, 4", "probe": "gap2", "read": ["impulse", "noise (long FFT)"], "priority": 2,
     "why": "HF and LF Damp slopes (extra loss per partial, split relative to the pitch) and the effect of Harmonics",
     "question": "partial levels and decay per partial at Decay 500 ms for HF Damp 50 and 100 %, LF Damp 50 and 100 %, Harmonics 16 and 4",
     "base": {**BASE, "Decay": {"display": 0.5}},
     "cases": [["hf-50", {"High Damp": {"display": 50}}], ["hf-100", {"High Damp": {"display": 100}}],
               ["lf-50", {"Low Damp": {"display": 50}}], ["lf-100", {"Low Damp": {"display": 100}}],
               ["harm-16", {"Harmonics": {"display": 16}}], ["harm-4", {"Harmonics": {"display": 4}}]]},

    {"name": "spectral-resonator-shift-unison", "plan": "5, 10", "probe": "gap2", "read": ["steady (spectrum)"], "priority": 2,
     "why": "Shift moves the input before resonance (where does a 1 kHz tone land?) and Unison/Uni. Amt detune the partials",
     "question": "spectrum of the 1 kHz tone with a partial series on 100 Hz: Shift +12, -12, +6 st; Unison 2 and 8 voices at Uni. Amt 100 %, 8 voices at 10 %",
     "base": {**BASE, "Freq. Hz": {"display": 100}},
     "cases": [[f"shift{s:+d}", {"Shift": {"display": s}}] for s in (12, -12, 6)]
     + [["uni2-100", {"Unison": 1, "Unison Amount": {"display": 100}}],
        ["uni8-100", {"Unison": 3, "Unison Amount": {"display": 100}}],
        ["uni8-10", {"Unison": 3, "Unison Amount": {"display": 10}}]]},

    {"name": "spectral-resonator-send-mix-latency", "plan": "6, 12, 13", "probe": "gap2", "read": ["static", "impulse"], "priority": 2,
     "why": "Input Send gain and the limiter ceiling, the Dry/Wet law, and the latency of wet and dry",
     "question": "staircase with a partial on 1 kHz (short Decay) for Input Send -12, +12, +24 dB and Dry/Wet 50 and 0 %; impulse delay of wet and dry",
     "base": {**BASE, "Freq. Hz": {"display": 1000}, "Decay": {"display": 0.04}},
     "cases": [["send-12", {"Send Gain": {"display": -12}}], ["send+12", {"Send Gain": {"display": 12}}],
               ["send+24", {"Send Gain": {"display": 24}}], ["dw-50", {"Dry Wet": {"display": 50}}],
               ["dw-0", {"Dry Wet": {"display": 0}}]]},
]
