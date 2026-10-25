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

    # ---- third set (measurements/third/). Stored elements, not parameters: Global_PitchMode (0 in
    # the loaded device: Internal; MIDI tried as 1), MidiPitch_MidiGate, MidiPitch_MonoPolyMode,
    # MidiPitch_Polyphony (stored 3), Modulation_ModMode (0 .. 3 tried: the panel's modes),
    # PartialFrequencies_FrequencyDialMode. MIDI notes come from a MIDI track into the MIDI
    # side-chain; the probe's noise (beats 61.5 to 69.5) excites the partials.
    {"name": "spectral-resonator-midi-mono", "plan": "7", "probe": "gap2", "read": ["noise spectrum over time (partials)"], "priority": 1,
     "why": "MIDI mode: the note sets the fundamental; legato and staccato with MIDI Gate off and on; Glide; note priority with an overlap; two routing forms",
     "question": "partials of the noise with notes A2 (61.5 to 64), C3 (64 to 66), E3 overlapping (65 to 68), G3 staccato (68 to 68.5): Gate off and on, Glide 78 ms, the PostFxOut routing",
     "base": dict(BASE, **{"@Global_PitchMode": 1, "@MidiPitch_MidiGate": 0,
                           "@MidiSideChain/RoutedInput/Routable/Target": {"midi": {"name": "specres-mono", "length": 72, "notes": [
                               [45, 61.5, 2.5, 100], [48, 64, 2, 100], [52, 65, 3, 100], [55, 68, 0.5, 100]]}}}),
     "cases": [["gate-on", {"@MidiPitch_MidiGate": 1}], ["glide-78", {"Glide": {"display": 0.078}}],
               ["postfx-route", {"@MidiSideChain/RoutedInput/Routable/Target": {"midi": {"name": "specres-mono", "length": 72, "notes": [
                   [45, 61.5, 2.5, 100], [48, 64, 2, 100], [52, 65, 3, 100], [55, 68, 0.5, 100]]}, "out": "PostFxOut"}}]]},

    {"name": "spectral-resonator-midi-poly", "plan": "8", "probe": "gap2", "read": ["noise spectrum (partials per voice)"], "priority": 2,
     "why": "Poly mode: a four-note chord at several Polyphony settings (stored 0 .. 3), voice stealing and the split of the harmonics",
     "question": "partials of the noise under a held A2, C3, E3, G3 chord (beats 61.5 to 69.5), MonoPolyMode 1, Polyphony 0, 1, 2, 3",
     "base": dict(BASE, **{"@Global_PitchMode": 1, "@MidiPitch_MonoPolyMode": 1,
                           "@MidiSideChain/RoutedInput/Routable/Target": {"midi": {"name": "specres-chord", "length": 72, "notes": [
                               [45, 61.5, 8, 100], [48, 61.5, 8, 100], [52, 61.5, 8, 100], [55, 61.5, 8, 100]]}}}),
     "cases": [[f"poly-{p}", {"@MidiPitch_Polyphony": p}] for p in (0, 1, 2)]},

    {"name": "spectral-resonator-modulation", "plan": "9", "probe": "gap2", "read": ["modulation", "noise spectrum over time"], "priority": 2,
     "why": "the modulation modes (stored Modulation_ModMode) at Pitch Mod 2.56 st, and Mod Rate's unit",
     "question": "steady tone and noise at Pitch Mod 2.56 st, Mod Rate 10 %, for ModMode 0, 1, 2, 3; ModMode 0 at Mod Rate 1 % and 64 %",
     "base": dict(BASE, **{"Pitch Mod": {"display": 2.56}, "Mod Rate": {"display": 10}}),
     "cases": [[f"mode-{m}", {"@Modulation_ModMode": m}] for m in (0, 1, 2, 3)] +
              [[f"mode-0-rate{r}", {"@Modulation_ModMode": 0, "Mod Rate": {"display": r}}] for r in (1, 64)]},

    {"name": "spectral-resonator-long-decay-unison", "plan": "4, 10, 1", "probe": "gap10", "read": ["impulse (T60)", "steady (spectrum)"], "priority": 3,
     "why": "Decay between 8.44 and 20 s, Unison 4 voices, and the frequency dial's stored mode",
     "question": "T60 at Decay 13.4 and 20 s; Unison 4 at Unison Amount 32 %; FrequencyDialMode 1 with Note A2",
     "base": BASE,
     "cases": [[f"decay-{d}", {"Decay": {"display": d}}] for d in (13.4, 20)] +
              [["unison4-32", {"Unison": 2, "Unison Amount": {"display": 32}}],
               ["dialmode-1", {"@PartialFrequencies_FrequencyDialMode": 1, "Note": 45}]]},

    # ---- fourth set (rendered after the third)
    {"name": "spectral-resonator-mod-rate", "plan": "9", "probe": "gap2", "read": ["noise spectrum over time"], "priority": 3,
     "why": "the third set's modulation run only changed Mod Rate with ModMode None, which does nothing: Mod Rate's effect needs a mode that modulates",
     "question": "noise at Pitch Mod 2.56 st in Chorus (ModMode 1) at Mod Rate 1, 10 and 64 %; Wander (ModMode 2) at 1 and 64 %",
     "base": dict(BASE, **{"Pitch Mod": {"display": 2.56}}),
     "cases": [[f"chorus-rate{r}", {"@Modulation_ModMode": 1, "Mod Rate": {"display": r}}] for r in (1, 10, 64)] +
              [[f"wander-rate{r}", {"@Modulation_ModMode": 2, "Mod Rate": {"display": r}}] for r in (1, 64)]},

    {"name": "spectral-resonator-dialmode-conflict", "plan": "1", "probe": "gap10", "read": ["steady (spectrum)"], "priority": 3,
     "why": "the third set's dial mode case had Note 45 (110 Hz) and Freq. Hz 110 Hz, the same comb: the mode could not be told",
     "question": "the 1 kHz tone through the comb with Freq. Hz 110 and Note 57 (220 Hz): FrequencyDialMode 0 and 1",
     "base": dict(BASE, **{"Freq. Hz": {"display": 110}, "Note": 57}),
     "cases": [[f"dialmode-{m}", {"@PartialFrequencies_FrequencyDialMode": m}] for m in (0, 1)]},
]


def _base(name):
    return next(r for r in RUNS if r["name"] == name)["base"]


def _case(run, case):
    return next(c for r in RUNS if r["name"] == run for c in r["cases"] if c[0] == case)[1]


# ---- fifth set: Mod Rate in Hz and in Granular. The partial at 1 kHz under the steady 1 kHz tone is
# excited whenever the modulation brings it onto the tone, so the output envelope shows the rate
RUNS += [
    {"name": "spectral-resonator-mod-rate-tone", "plan": "9", "probe": "gap2", "read": ["raw render of the steady tone (envelope)"], "priority": 2,
     "why": "the fourth set bounded Mod Rate by the 46 ms frames of the noise; a partial on the steady tone shows each excursion as a burst, so the rate is read in Hz, and Granular's grains are counted",
     "question": "the envelope of the steady 1 kHz tone through the partial at 1 kHz (Freq 1000 Hz, Decay 100 ms, Pitch Mod 2.56 st): Chorus at Mod Rate 1, 10, 30, 64 and 100 %; Wander at 1, 10 and 64 %; Granular at 1, 10, 30, 64 and 100 %; Chorus at Pitch Mod 0 and 0.64 st (Mod Rate 10 %)",
     "base": {"Dry Wet": {"display": 100}, "Freq. Hz": {"display": 1000}, "Decay": {"display": 0.1}, "Pitch Mod": {"display": 2.56}},
     "cases": [[f"{n}-rate{r}", {"@Modulation_ModMode": m, "Mod Rate": {"display": r}}]
               for n, m, rates in (("chorus", 1, (1, 10, 30, 64, 100)), ("wander", 2, (1, 10, 64)), ("granular", 3, (1, 10, 30, 64, 100)))
               for r in rates] +
              [["chorus-pm0", {"@Modulation_ModMode": 1, "Mod Rate": {"display": 10}, "Pitch Mod": {"display": 0}}],
               ["chorus-pm0.64", {"@Modulation_ModMode": 1, "Mod Rate": {"display": 10}, "Pitch Mod": {"display": 0.64}}]]},
]
