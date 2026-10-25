# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Corpus behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.10-corpus.md > Measurement plan.

Corpus rings when excited, so the impulse (one sample at -6 dBFS) is the excitation and its 2 s
response (`.ir.wav`, spectrum by a long FFT) gives the partials, their decay and the two
channels' tuning. Decays are kept under about 1 s so the ring ends inside the probe's 2 s gap.
The device has two parameters named Width; make_als.py keys them in dump order, so "Width" is the
filter's bandwidth (0.5 to 9) and "Width #2" the stereo Width (0 to 100 %).

Not taken: everything driven by MIDI (Frequency on, Transpose in MIDI mode, Last/Low, PB Range,
Off Decay: step 11), Decay times longer than the 2 s window (the Decay knob's top of 35 s and
the Pipe/Tube maxima are read only as far as the first 2 s show), switching Resonance Type
while ringing, the limiter's timing with a loud burst (only the staircase's top is seen) and
dropping Dry/Wet during a ring (step 10: no changes during the render)."""

DEVICE = "Corpus"

# Beam, High quality, wet only, nothing added around the resonators, mid positions.
BASE = {"Resonance Type": {"item": "Beam"}, "Resonator Quality": {"item": "High"},
        "Tune": {"display": 261.63}, "Transpose": {"display": 0}, "Fine": {"display": 0},
        "Spread": {"display": 0}, "Decay": {"display": 0.8}, "Material": {"display": 0},
        "Radius": {"display": 50}, "Brightness": {"display": 0}, "Inharmonics": {"display": 0},
        "Opening": {"display": 100}, "Ratio": {"display": 50}, "Hit": {"display": 50},
        "Listening L": {"display": 10}, "Listening R": {"display": 90},
        "LFO On/Off": {"item": "Off"}, "Filter On/Off": {"item": "Off"}, "Bleed": {"display": 0},
        "Gain": {"display": 0}, "Dry Wet": {"display": 100}, "Width #2": {"display": 100},
        "MIDI Frequency": {"item": "Off"}}

TYPES = ["Beam", "Marimba", "String", "Membrane", "Plate", "Pipe", "Tube"]

RUNS = [
    {"name": "corpus-types", "plan": "2", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "the partial frequencies, amplitudes and decays of each of the seven Resonance Types (long FFT of the impulse response)",
     "question": "impulse response spectrum of every Resonance Type at Tune C4, Decay 0.8 s, defaults otherwise",
     "base": BASE,
     "cases": [[f"type-{t.lower()}", {"Resonance Type": {"item": t}}] for t in TYPES[1:]]},

    {"name": "corpus-decay-material", "plan": "3", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "the Decay-to-time mapping and how Material tilts the damping of low and high partials",
     "question": "per-partial decay of Beam for Decay 0.2, 0.5, 1.0 s and for Material -100, -50, +100 % at 0.8 s",
     "base": BASE,
     "cases": [[f"decay-{d}", {"Decay": {"display": d}}] for d in (0.2, 0.5, 1.0)] +
              [[f"material-{n}", {"Material": {"display": m}}]
               for n, m in (("m100", -100), ("m50", -50), ("p100", 100))]},

    {"name": "corpus-tune-spread", "plan": "2, 6", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "Tune's frequency law, Spread's detuning in cents (L raised, R lowered), and whether Transpose and Fine act without MIDI",
     "question": "fundamental of the left and right resonators for Tune C3, C5, C6, Spread +100, -100 %, Transpose +12, Fine +50 ct",
     "base": BASE,
     "cases": [["tune-c3", {"Tune": {"display": 130.81}}], ["tune-c5", {"Tune": {"display": 523.25}}],
               ["tune-c6", {"Tune": {"display": 1046.5}}],
               ["spread-p100", {"Spread": {"display": 100}}], ["spread-m100", {"Spread": {"display": -100}}],
               ["transpose-12", {"Transpose": {"display": 12}}], ["fine-p50", {"Fine": {"display": 50}}]]},

    {"name": "corpus-hit-inharm", "plan": "2, 4", "probe": "gap2", "read": ["impulse"], "priority": 2,
     "why": "how Hit, Pos. L/R, Bright and Inharm reshape the partial amplitudes and frequencies of Beam",
     "question": "partial amplitudes and frequencies for Hit 0 and 100 %, Pos. L/R 0 and 100 %, Bright -100 and +100 %, Inharm -100 and +100 %",
     "base": BASE,
     "cases": [["hit-0", {"Hit": {"display": 0}}], ["hit-100", {"Hit": {"display": 100}}],
               ["pos-0", {"Listening L": {"display": 0}, "Listening R": {"display": 0}}],
               ["pos-100", {"Listening L": {"display": 100}, "Listening R": {"display": 100}}],
               ["bright-m100", {"Brightness": {"display": -100}}], ["bright-p100", {"Brightness": {"display": 100}}],
               ["inharm-m100", {"Inharmonics": {"display": -100}}], ["inharm-p100", {"Inharmonics": {"display": 100}}]]},

    {"name": "corpus-type-params", "plan": "2, 3", "probe": "gap2", "read": ["impulse"], "priority": 2,
     "why": "the controls only some types use: Opening (Pipe), Radius (Pipe, Tube), Ratio (Membrane, Plate)",
     "question": "partials of Pipe at Opening 0 %, Pipe and Tube at Radius 0 and 100 %, Membrane and Plate at Ratio 0 and 100 %",
     "base": BASE,
     "cases": [["pipe-open-0", {"Resonance Type": {"item": "Pipe"}, "Opening": {"display": 0}}],
               ["pipe-radius-0", {"Resonance Type": {"item": "Pipe"}, "Radius": {"display": 0}}],
               ["pipe-radius-100", {"Resonance Type": {"item": "Pipe"}, "Radius": {"display": 100}}],
               ["tube-radius-0", {"Resonance Type": {"item": "Tube"}, "Radius": {"display": 0}}],
               ["tube-radius-100", {"Resonance Type": {"item": "Tube"}, "Radius": {"display": 100}}],
               ["membrane-ratio-0", {"Resonance Type": {"item": "Membrane"}, "Ratio": {"display": 0}}],
               ["membrane-ratio-100", {"Resonance Type": {"item": "Membrane"}, "Ratio": {"display": 100}}],
               ["plate-ratio-100", {"Resonance Type": {"item": "Plate"}, "Ratio": {"display": 100}}]]},

    {"name": "corpus-quality-width", "plan": "5, 6", "probe": "gap2", "read": ["impulse", "stereo"],
     "priority": 3,
     "why": "how many partials each Quality keeps, and the stereo Width law (L/R mix of the two resonators from a mono impulse)",
     "question": "partial count for Quality Eco, Low, Med (High is the default case), and L/R levels for Width #2 0 and 50 %",
     "base": BASE,
     "cases": [[f"quality-{q.lower()}", {"Resonator Quality": {"item": q}}] for q in ("Eco", "Low", "Med")] +
              [["width-0", {"Width #2": {"display": 0}}], ["width-50", {"Width #2": {"display": 50}}]]},

    {"name": "corpus-filter-bleed", "plan": "8, 9, 10", "probe": "gap2", "read": ["response", "static", "impulse"],
     "priority": 3,
     "why": "the band-pass on the resonated signal (noise spectrum), Bleed's dry share, Gain and its limiter (staircase), Dry/Wet at 50 %",
     "question": "noise spectrum for Filter at 300 Hz, 3 kHz and Width 1 and 9, staircase for Bleed 100 %, Gain +15 dB, impulse for Dry/Wet 50 %",
     "base": dict(BASE, **{"Decay": {"display": 0.3}}),
     "cases": [["filter-300", {"Filter On/Off": {"item": "On"}, "Mid Freq": {"display": 300}}],
               ["filter-3000", {"Filter On/Off": {"item": "On"}, "Mid Freq": {"display": 3000}}],
               ["filter-w1", {"Filter On/Off": {"item": "On"}, "Width": 1}],
               ["filter-w9", {"Filter On/Off": {"item": "On"}, "Width": 9}],
               ["bleed-100", {"Bleed": {"display": 100}}], ["gain-p15", {"Gain": {"display": 15}}],
               ["wet-50", {"Dry Wet": {"display": 50}}]]},

    # ---- third set (measurements/third/)
    {"name": "corpus-tune-types", "plan": "2", "probe": "gap2", "read": ["impulse (partials)"], "priority": 2,
     "why": "Tune on the types besides Beam (the earlier Tune values rendered sharp; is that type-dependent?), and intermediate Inharmonics and Ratio",
     "question": "partials of the impulse response at Tune 110 and 880 Hz for Marimba, String, Membrane, Plate, Pipe, Tube; Beam at Inharmonics -50 and +50 %; Membrane at Ratio 25 and 75 %",
     "base": BASE,
     "cases": [[f"{t.lower()}-{f}", {"Resonance Type": {"item": t}, "Tune": {"display": f}}]
               for t in TYPES if t != "Beam" for f in (110, 880)] +
              [[f"inharm{v:+d}", {"Inharmonics": {"display": v}}] for v in (-50, 50)] +
              [[f"membrane-ratio-{v}", {"Resonance Type": {"item": "Membrane"}, "Ratio": {"display": v}}] for v in (25, 75)]},

    {"name": "corpus-decay-radius", "plan": "3", "probe": "gap10", "read": ["impulse (T60 per partial)"], "priority": 2,
     "why": "the ends of Decay and Radius's effect on decay, with a 10 s tail",
     "question": "T60 of the partials at Decay 50 ms and 5 s on Beam; Pipe and Tube at Radius 0 and 100 % (Decay 0.8 s)",
     "base": BASE,
     "cases": [["decay-0.05", {"Decay": {"display": 0.05}}], ["decay-5", {"Decay": {"display": 5}}]] +
              [[f"{t.lower()}-radius-{r}", {"Resonance Type": {"item": t}, "Radius": {"display": r}}]
               for t in ("Pipe", "Tube") for r in (0, 100)]},

    {"name": "corpus-hit-listening", "plan": "4", "probe": "gap2", "read": ["impulse (partials per channel)"], "priority": 2,
     "why": "Hit and the listening positions at intermediate values (comb pattern of the partials)",
     "question": "partials of the impulse response on Beam at Hit 10, 25, 75 %; Listening L/R at 30/70 and 50/50 %",
     "base": BASE,
     "cases": [[f"hit-{h}", {"Hit": {"display": h}}] for h in (10, 25, 75)] +
              [["listen-30-70", {"Listening L": {"display": 30}, "Listening R": {"display": 70}}],
               ["listen-50-50", {"Listening L": {"display": 50}, "Listening R": {"display": 50}}]]},

    {"name": "corpus-lfo", "plan": "7", "probe": "ext", "read": ["ext: impulsetrain (pitch of each ring)"], "priority": 1,
     "why": "the LFO: depth against Amount, shapes, Spin and Phase, read from the pitch of the ring after each impulse of the train",
     "question": "fundamental of each 100 ms ring (Decay 0.2 s, Tune 440 Hz) with the LFO at 1 Hz free: Amount 50 and 100 % Sine, 100 % Square, Triangle, SawUp, Sample & Hold; Spin 25 %; Phase 0",
     "base": dict(BASE, **{"Decay": {"display": 0.2}, "Tune": {"display": 440}, "LFO On/Off": {"item": "On"},
                           "LFO Sync": {"item": "Free"}, "LFO Rate": {"display": 1}, "LFO Shape": {"item": "Sine"},
                           "LFO Amount": {"display": 100}, "Phase": {"display": 180}, "Offset": {"display": 0}}),
     "cases": [["sine-50", {"LFO Amount": {"display": 50}}], ["sine-100", {}]] +
              [[f"{s.lower().replace(' & ', '-')}", {"LFO Shape": {"item": s}}] for s in ("Square", "Triangle", "SawUp", "Sample & Hold")] +
              [["spin-25", {"LFO Stereo Mode": {"item": "Spin"}, "Spin": {"display": 25}}], ["phase-0", {"Phase": {"display": 0}}]]},

    {"name": "corpus-bleed-limiter", "plan": "9", "probe": "ext", "read": ["ext: bedbursts envelope, stair100", "response"], "priority": 2,
     "why": "Bleed with the filter on, and the output limiter's timing on loud bursts",
     "question": "Filter on (1 kHz, width 4) with Bleed 0, 50, 100 %; the bed bursts at Gain +15 dB with the filter off",
     "base": BASE,
     "cases": [[f"filter-bleed-{b}", {"Filter On/Off": {"item": "On"}, "Bleed": {"display": b}}] for b in (0, 50, 100)] +
              [["gain15", {"Gain": {"display": 15}}]]},

    {"name": "corpus-drywet-ring", "plan": "10", "probe": "gap2", "read": ["raw render after the impulse"], "priority": 3,
     "why": "whether dropping Dry/Wet cuts a ringing resonator (the manual says the ring is not cut)",
     "question": "the impulse's ring (Decay 3 s) with Dry Wet jumping from 100 to 0 % at beat 2 (1 s)",
     "base": dict(BASE, **{"Decay": {"display": 3}}),
     "cases": [["drop", {"Dry Wet": {"auto": [[0, {"display": 100}], [2, {"display": 100}], [2, {"display": 0}]]}}]]},

    # MIDI: a MIDI track plays notes into Corpus's MIDI side-chain (make_als.py {"midi": ...}).
    # The probe excites the resonator: the impulse at beat 1, the noise from beat 61.5 to 69.5.
    {"name": "corpus-midi", "plan": "11", "probe": "gap2", "read": ["impulse (partials)", "noise spectrum over time"], "priority": 1,
     "why": "MIDI Frequency: the note sets the tune (and Transpose and Fine on top), Last and Low with overlapping notes, Note Off with Off Decay; two routing forms are tried",
     "question": "fundamental of the impulse's ring with A3 held (beats 0 to 4); then the noise with C4 held from beat 61 and E4 from 63 to 67: Last and Low; Note Off on with Off Decay 0, 50, 100 % (A3 released at beat 1.5)",
     "base": dict(BASE, **{"MIDI Frequency": {"item": "On"}, "Decay": {"display": 2},
                           "@SideChain/RoutedInput/Routable/Target": {"midi": {"name": "corpus", "length": 72, "notes": [
                               [57, 0, 4, 100], [60, 61, 8, 100], [64, 63, 4, 100]]}}}),
     "cases": [["postfx-route", {"@SideChain/RoutedInput/Routable/Target": {"midi": {"name": "corpus", "length": 72, "notes": [
                   [57, 0, 4, 100], [60, 61, 8, 100], [64, 63, 4, 100]]}, "out": "PostFxOut"}}],
               ["transpose+12", {"Transpose": 12}], ["fine+50", {"Fine": 50}], ["low", {"MIDI Mode": {"item": "Low"}}]] +
              [[f"offdecay-{d}", {"Note Off": {"item": "On"}, "Off Decay": {"display": d},
                                  "@SideChain/RoutedInput/Routable/Target": {"midi": {"name": "corpus-short", "length": 72, "notes": [
                                      [57, 0, 1.5, 100], [60, 61, 8, 100], [64, 63, 4, 100]]}}}] for d in (0, 50, 100)]},
]
