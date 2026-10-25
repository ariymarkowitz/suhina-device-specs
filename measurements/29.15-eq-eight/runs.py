# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""EQ Eight behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.15-eq-eight.md > Measurement plan.

Every run uses band 3 (copy A) as the band under test, with bands 1, 2 and 4 switched off, in
Stereo mode with Adaptive Q off. All gain-and-shape runs read `response.sweep_db` (the device is
time-invariant); the sweep segment of each render can also be re-read at finer than 1/6 octave
for the narrow Q values.

Not measurable this way: plan 5 (Modes) and 6 (Audition), because Mode, Edit and Audition are
not parameters (Live's API and the set map expose only the A copy, i.e. Stereo); 7 (Oversampling,
the `Precision` element has no parameter); 8 (Analyser display); 9 (Smoothing, needs automation);
and the band-by-band 100 Hz / 10 kHz type grid is only sampled (see eq-eight-freq)."""

DEVICE = "EQ Eight"

BASE = {
    "Adaptive Q": {"item": "Off"},
    "1 Filter On A": {"item": "Off"},
    "2 Filter On A": {"item": "Off"},
    "4 Filter On A": {"item": "Off"},
    "3 Filter On A": {"item": "On"},
    "3 Frequency A": {"display": 1000},
    "3 Gain A": {"display": 0},
}


def band(kind, gain=None, q=None, freq=None):
    p = {"3 Filter Type A": {"item": kind}}
    if gain is not None:
        p["3 Gain A"] = {"display": gain}
    if q is not None:
        p["3 Q A"] = {"display": q}
    if freq is not None:
        p["3 Frequency A"] = {"display": freq}
    return p


RUNS = [
    {"name": "eq-eight-types", "plan": "2", "probe": "gap2", "read": ["response.sweep_db"], "priority": 1,
     "why": "the magnitude (and, from the impulse, the phase) of each of the eight filter shapes at Freq 1 kHz, Q 0.71",
     "question": "response of every filter type at 1 kHz with Q 0.71; +12 dB where the type has gain",
     "base": BASE,
     "cases": [
         ["hp48", band("High Pass 48dB")],
         ["hp12", band("High Pass 12dB")],
         ["lowshelf", band("Low Shelf", gain=12)],
         ["bell", band("Bell", gain=12)],
         ["notch", band("Notch")],
         ["highshelf", band("High Shelf", gain=12)],
         ["lp12", band("Low Pass 12dB")],
         ["lp48", band("Low Pass 48dB")],
     ]},

    {"name": "eq-eight-bell-q", "plan": "2", "probe": "gap2", "read": ["response.sweep_db"], "priority": 1,
     "why": "bell bandwidth against Q (the Q law), and whether a boost and a cut of the same size mirror each other",
     "question": "Bell at 1 kHz, +12 dB, Q 0.1 to 18, Adaptive Q off; and -12 dB at Q 2",
     "base": BASE | band("Bell", gain=12),
     "cases": [
         ["q-0.1", {"3 Q A": {"display": 0.1}}],
         ["q-0.71", {"3 Q A": {"display": 0.71}}],
         ["q-2", {"3 Q A": {"display": 2}}],
         ["q-6", {"3 Q A": {"display": 6}}],
         ["q-18", {"3 Q A": {"display": 18}}],
         ["cut-q-2", {"3 Q A": {"display": 2}, "3 Gain A": {"display": -12}}],
     ]},

    {"name": "eq-eight-cut-q", "plan": "2", "probe": "gap2", "read": ["response.sweep_db"], "priority": 1,
     "why": "resonant peak of the 12 and 48 dB cuts against Q, whether the 48 dB filter's Q is global or per section, notch width and depth",
     "question": "low-pass and high-pass at 1 kHz, 12 and 48 dB, Q 2 and 6 and 18; notch Q 6",
     "base": BASE,
     "cases": [
         ["lp12-q2", band("Low Pass 12dB", q=2)],
         ["lp12-q6", band("Low Pass 12dB", q=6)],
         ["lp12-q18", band("Low Pass 12dB", q=18)],
         ["hp12-q6", band("High Pass 12dB", q=6)],
         ["lp48-q2", band("Low Pass 48dB", q=2)],
         ["lp48-q6", band("Low Pass 48dB", q=6)],
         ["hp48-q6", band("High Pass 48dB", q=6)],
         ["notch-q6", band("Notch", q=6)],
     ]},

    {"name": "eq-eight-adaptive-q", "plan": "3", "probe": "gap2", "read": ["response.sweep_db"], "priority": 1,
     "why": "Q_eff against gain: how much Adaptive Q narrows a bell and whether a cut adapts like a boost; whether shelves are touched",
     "question": "Bell at 1 kHz, Q 0.71, Adaptive Q on at +3, +6, +12, -12 dB, off at +12 and -12 dB; a +12 dB high shelf on and off",
     "base": BASE | {"3 Q A": {"display": 0.71}},
     "cases": [
         ["on-g3", band("Bell", gain=3) | {"Adaptive Q": {"item": "On"}}],
         ["on-g6", band("Bell", gain=6) | {"Adaptive Q": {"item": "On"}}],
         ["on-g12", band("Bell", gain=12) | {"Adaptive Q": {"item": "On"}}],
         ["on-g-12", band("Bell", gain=-12) | {"Adaptive Q": {"item": "On"}}],
         ["off-g12", band("Bell", gain=12)],
         ["off-g-12", band("Bell", gain=-12)],
         ["shelf-on-g12", band("High Shelf", gain=12) | {"Adaptive Q": {"item": "On"}}],
         ["shelf-off-g12", band("High Shelf", gain=12)],
     ]},

    {"name": "eq-eight-scale", "plan": "4", "probe": "gap2", "read": ["response.sweep_db"], "priority": 2,
     "why": "Scale's law (linear in dB?), clamping at 200 %, inversion below 0, and that cut/notch bands ignore it",
     "question": "four bands (high-pass, low shelf -9, bell +9, high shelf +6, notch) with Scale 50, 0, -50, -100, 200 % (the default case is 100 %)",
     "base": {
         "Adaptive Q": {"item": "Off"},
         "1 Filter On A": {"item": "On"}, "1 Filter Type A": {"item": "High Pass 12dB"}, "1 Frequency A": {"display": 40},
         "2 Filter On A": {"item": "On"}, "2 Filter Type A": {"item": "Low Shelf"}, "2 Frequency A": {"display": 200},
         "2 Gain A": {"display": -9},
         "3 Filter On A": {"item": "On"}, "3 Filter Type A": {"item": "Bell"}, "3 Frequency A": {"display": 1000},
         "3 Gain A": {"display": 9},
         "4 Filter On A": {"item": "On"}, "4 Filter Type A": {"item": "High Shelf"}, "4 Frequency A": {"display": 5000},
         "4 Gain A": {"display": 6},
         "5 Filter On A": {"item": "On"}, "5 Filter Type A": {"item": "Notch"}, "5 Frequency A": {"display": 8000},
     },
     "cases": [[f"scale-{n}", {"Scale": {"display": v}}] for n, v in
               (("50", 50), ("0", 0), ("m50", -50), ("m100", -100), ("200", 200))]},

    {"name": "eq-eight-shelf-q", "plan": "2", "probe": "gap2", "read": ["response.sweep_db"], "priority": 2,
     "why": "how Q shapes the shelves: slope, overshoot near the corner, and whether low and high shelves are mirror images",
     "question": "low and high shelf at 1 kHz, +12 dB, Q 0.1, 2 and 6; low shelf -12 dB at Q 2",
     "base": BASE,
     "cases": [
         ["ls-q0.1", band("Low Shelf", gain=12, q=0.1)],
         ["ls-q2", band("Low Shelf", gain=12, q=2)],
         ["ls-q6", band("Low Shelf", gain=12, q=6)],
         ["hs-q0.1", band("High Shelf", gain=12, q=0.1)],
         ["hs-q2", band("High Shelf", gain=12, q=2)],
         ["hs-q6", band("High Shelf", gain=12, q=6)],
         ["ls-q2-cut", band("Low Shelf", gain=-12, q=2)],
     ]},

    {"name": "eq-eight-freq", "plan": "2", "probe": "gap2", "read": ["response.sweep_db"], "priority": 2,
     "why": "whether the bands keep their analogue shape near Nyquist (no cramping) and at the bottom of the range",
     "question": "bell +12 dB at 30 Hz, 100 Hz, 10, 16, 20 and 22 kHz; low-pass 12 dB and high shelf at 16 kHz",
     "base": BASE,
     "cases": [
         ["bell-30", band("Bell", gain=12, freq=30)],
         ["bell-100", band("Bell", gain=12, freq=100)],
         ["bell-10k", band("Bell", gain=12, freq=10000)],
         ["bell-16k", band("Bell", gain=12, freq=16000)],
         ["bell-20k", band("Bell", gain=12, freq=20000)],
         ["bell-22k", band("Bell", gain=12, freq=22000)],
         ["lp12-16k", band("Low Pass 12dB", freq=16000)],
         ["hs-16k", band("High Shelf", gain=12, freq=16000)],
     ]},

    # ---- third set (measurements/third/). Mode and Oversampling are stored elements, not
    # parameters: Mode (0 Stereo, then L/R and M/S in the panel's order: [measure] which is 1 and 2)
    # and Precision (Oversampling). In L/R and M/S the A bands act on left or mid and the B bands
    # on right or side.
    {"name": "eq-eight-modes", "plan": "5", "probe": "ext", "read": ["ext: mid, side, lrsplit"], "priority": 1,
     "why": "the L/R and M/S modes: which curve acts on which channel, and the encoding's gains with flat curves",
     "question": "gains of mid-only and side-only noise and of the split tone with Mode 1 and 2 stored: flat, band 3 A at +12 dB (1 kHz bell, Q 0.71), and band 3 B at +12 dB",
     "base": dict(BASE, **{"3 Filter On B": {"item": "On"}, "3 Filter Type B": {"item": "Bell"},
                           "3 Frequency B": {"display": 1000}, "3 Gain B": {"display": 0}, "3 Filter Type A": {"item": "Bell"}}),
     "cases": [[f"mode{m}-{w}", dict({"@Mode": m}, **p)] for m in (1, 2)
               for w, p in (("flat", {}), ("a12", {"3 Gain A": {"display": 12}}), ("b12", {"3 Gain B": {"display": 12}}))]},

    {"name": "eq-eight-freq-gain", "plan": "2, 3", "probe": "gap2", "read": ["response", "impulse"], "priority": 2,
     "why": "the bell and shelves at 100 Hz and 10 kHz and at +-15 dB, the notch's depth, Adaptive Q at -6 dB and on the low shelf",
     "question": "sweep response: Bell at 100 Hz and 10 kHz, +15 and -15 dB, Q 0.71; Notch at 1 kHz Q 0.71 and 6; Bell -6 dB with Adaptive Q on; Low Shelf +12 dB with Adaptive Q on and off",
     "base": BASE,
     "cases": [[f"bell-{f}-{'p' if g > 0 else 'm'}15", band("Bell", g, 0.71, f)] for f in (100, 10000) for g in (15, -15)] +
              [[f"notch-q{q}", band("Notch", None, q)] for q in (0.71, 6)] +
              [["bell-m6-adaptive", dict(band("Bell", -6, 0.71), **{"Adaptive Q": {"item": "On"}})],
               ["lowshelf-12-adaptive", dict(band("Low Shelf", 12, 0.71, 200), **{"Adaptive Q": {"item": "On"}})],
               ["lowshelf-12", band("Low Shelf", 12, 0.71, 200)]]},

    {"name": "eq-eight-oversampling", "plan": "7", "probe": "gap2", "read": ["response", "impulse"], "priority": 2,
     "why": "Oversampling (stored Precision): the response near Nyquist and the impulse's alignment",
     "question": "sweep response and impulse with a 15 kHz bell at +15 dB, Q 18, and a 48 dB low-pass at 18 kHz, Precision 0 and 1",
     "base": BASE,
     "cases": [[f"bell15k-p{p}", dict(band("Bell", 15, 18, 15000), **{"@Precision": p})] for p in (0, 1)] +
              [[f"lp48-18k-p{p}", dict(band("Low Pass 48dB", None, 0.71, 18000), **{"@Precision": p})] for p in (0, 1)]},

    {"name": "eq-eight-freq-glide", "plan": "9", "probe": "gap2", "read": ["raw render over the noise (steps, zipper)"], "priority": 2,
     "why": "smoothing of the band frequency while it moves",
     "question": "the noise through a +12 dB bell, Q 2, whose frequency glides from 100 Hz to 10 kHz over beats 62 to 69",
     "base": dict(BASE, **band("Bell", 12, 2)),
     "cases": [["glide", {"3 Frequency A": {"auto": [[0, {"display": 100}], [62, {"display": 100}], [69, {"display": 10000}]]}}]]},
]
