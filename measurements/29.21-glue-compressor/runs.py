# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Glue Compressor behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.21-glue-compressor.md > Measurement plan.

The base is a plain compressor: Threshold -20 dB, Ratio 4, Attack 0.01 ms, Release 0.1 s, Range at
its widest (70 dB), Makeup 0, Soft clip off, Dry/Wet 100 %, side-chain EQ off. The probe's
staircase gives the static curve and its bursts (-30, -6, -30 dBFS, 1 s each) give Attack and
Release: the middle burst is 14 dB over the threshold, the outer ones 10 dB under.

Not measurable this way: plan 4/5's repeats with other step sizes beyond what glue-attack-amount
covers; 6 (Auto release after 10 ms to 5 s of compression, on a drum loop and a pad: only the
1 s burst exists, see glue-attack-amount); 9's input above 0 dBFS (Makeup is used to push the
signal into the clipper instead, glue-softclip); 10 (Oversampling is not a parameter); 12 (stereo
link: the one-channel segments have no second loud channel); 13 (side-chain: no external input);
14 (burst lengths of 1 to 300 ms)."""

DEVICE = "Glue Compressor"

# Ratio, Attack and Release are stepped displays without items in the API: the internal value is
# the index into these lists.
RATIOS = ["2", "4", "10"]
ATTACKS = ["0.01", "0.1", "0.3", "1", "3", "10", "30"]
RELEASES = ["0.1", "0.2", "0.4", "0.6", "0.8", "1.2", "A"]


def ratio(v):
    return RATIOS.index(v)


def attack(v):
    return ATTACKS.index(v)


def release(v):
    return RELEASES.index(v)


BASE = {"Threshold": {"display": -20}, "Ratio": ratio("4"), "Attack": attack("0.01"),
        "Release": release("0.1"), "Range": {"display": 70}, "Output": {"display": 0},
        "Peak Clip In": {"item": "Off"}, "Dry/Wet": {"display": 100}}

RUNS = [
    {"name": "glue-ratio", "plan": "2,3", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "the gain computer: slope per Ratio and the ratio-dependent knee width (soft at 2:1, hard at 10:1), and threshold offsets",
     "question": "static curve at Threshold -20 dB for Ratio 2, 4 and 10; and Ratio 4 at Threshold -30 and -10 dB",
     "base": BASE,
     "cases": [
         ["ratio-2", {"Ratio": ratio("2")}],
         ["ratio-10", {"Ratio": ratio("10")}],
         ["r4-thr-30", {"Threshold": {"display": -30}}],
         ["r4-thr-10", {"Threshold": {"display": -10}}],
     ]},

    {"name": "glue-attack", "plan": "4", "probe": "gap2", "read": ["dynamics"], "priority": 1,
     "why": "the seven Attack values as times (10-90 % and 63 %), and the shape of the gain reduction",
     "question": "bursts at -30, -6, -30 dBFS with Threshold -20 dB, Ratio 4, Release 0.1 s: Attack 0.1 to 30 ms (0.01 ms is the default case)",
     "base": BASE,
     "cases": [[f"att-{a}", {"Attack": attack(a)}] for a in ("0.1", "0.3", "1", "3", "10", "30")]},

    {"name": "glue-release", "plan": "5,6", "probe": "gap2", "read": ["dynamics"], "priority": 1,
     "why": "the Release values as times, and the Auto setting's time constants (fast and slow stage) after a 1 s compression",
     "question": "bursts as in glue-attack, Attack 0.01 ms: Release 0.2, 0.4, 0.6, 0.8, 1.2 s and A (0.1 s is the default case)",
     "base": BASE,
     "cases": [[f"rel-{r}", {"Release": release(r)}] for r in ("0.2", "0.4", "0.6", "0.8", "1.2", "A")]},

    {"name": "glue-range", "plan": "7", "probe": "gap2", "read": ["static"], "priority": 2,
     "why": "how the Range clamps the gain reduction (hard or soft) and its law against the slider",
     "question": "Ratio 10, Threshold -30 dB, Range 0, 6, 15, 30 and 40 dB (70 dB is the default case)",
     "base": BASE | {"Ratio": ratio("10"), "Threshold": {"display": -30}},
     "cases": [[f"range-{v}", {"Range": {"display": v}}] for v in (0, 6, 15, 30, 40)]},

    {"name": "glue-attack-amount", "plan": "4,6", "probe": "gap2", "read": ["dynamics"], "priority": 2,
     "why": "whether Attack and the Auto release depend on the amount of gain reduction (10-90 % time against overshoot)",
     "question": "Attack 10 ms at Threshold -10, -20 and -40 dB (reduction in the loud burst differs), and Ratio 10; Release A at the same thresholds",
     "base": BASE | {"Attack": attack("10")},
     "cases": [
         ["att10-thr-10", {"Threshold": {"display": -10}}],
         ["att10-thr-40", {"Threshold": {"display": -40}}],
         ["att10-r10", {"Ratio": ratio("10")}],
         ["auto-thr-10", {"Attack": attack("0.01"), "Release": release("A"), "Threshold": {"display": -10}}],
         ["auto-thr-20", {"Attack": attack("0.01"), "Release": release("A")}],
         ["auto-thr-30", {"Attack": attack("0.01"), "Release": release("A"), "Threshold": {"display": -30}}],
     ]},

    {"name": "glue-softclip", "plan": "8,9", "probe": "gap2", "read": ["static"], "priority": 2,
     "why": "the Soft clip waveshaper (curve, -0.5 dB ceiling, harmonics) and where Makeup sits relative to it",
     "question": "no compression (Threshold 0, Range 0 dB), Soft clip on with Makeup 0, 6, 12 and 20 dB (pushing the staircase above 0 dBFS); off with Makeup 12",
     "base": BASE | {"Threshold": {"display": 0}, "Range": {"display": 0}},
     "cases": [
         ["off-mk12", {"Output": {"display": 12}}],
         ["on-mk0", {"Peak Clip In": {"item": "On"}}],
         ["on-mk6", {"Peak Clip In": {"item": "On"}, "Output": {"display": 6}}],
         ["on-mk12", {"Peak Clip In": {"item": "On"}, "Output": {"display": 12}}],
         ["on-mk20", {"Peak Clip In": {"item": "On"}, "Output": {"display": 20}}],
     ]},

    {"name": "glue-makeup-mix", "plan": "8,11", "probe": "gap2", "read": ["static", "impulse"], "priority": 3,
     "why": "Makeup accuracy, and whether Dry/Wet mixes in phase (compressed against dry) with no extra latency",
     "question": "Makeup 10 and 20 dB without compression; Ratio 10, Threshold -30 dB at Dry/Wet 0 and 50 %",
     "base": BASE | {"Threshold": {"display": 0}, "Range": {"display": 0}},
     "cases": [
         ["mk10", {"Output": {"display": 10}}],
         ["mk20", {"Output": {"display": 20}}],
         ["mix-0", {"Ratio": ratio("10"), "Threshold": {"display": -30}, "Range": {"display": 70}, "Dry/Wet": {"display": 0}}],
         ["mix-50", {"Ratio": ratio("10"), "Threshold": {"display": -30}, "Range": {"display": 70}, "Dry/Wet": {"display": 50}}],
     ]},

    # ---- third set (measurements/third/): the extended probe (short bursts, bursts over a bed, a
    # 10 dB/s ramp, split tone, side noise, 10 and 15 kHz sines); Oversample and SideChainListen
    # are stored elements; the side-chain run plays key-duck on a key track
    {"name": "glue-knee-ramp", "plan": "3", "probe": "ext", "read": ["ext: ramp"], "priority": 1,
     "why": "the knee in fine steps (the staircase's 3 dB steps could not resolve it) for each ratio",
     "question": "gain against level on the 1 kHz ramp, Threshold -20 dB, Attack 0.01, Release 0.1, Ratio 2, 4, 10",
     "base": BASE,
     "cases": [[f"ratio-{r}", {"Ratio": ratio(r)}] for r in RATIOS]},

    {"name": "glue-detector-release", "plan": "6, 14", "probe": "ext", "read": ["ext: shortbursts, bedbursts envelope"], "priority": 1,
     "why": "the detector (peak or averaged) from 1 to 300 ms bursts, and Auto release after a click, 100 ms and 3 s of compression at three amounts",
     "question": "peak gain of the short bursts at Threshold -16 dB (10 dB over), Ratio 10; gain over the bed after each bed burst with Release A at Threshold -9, -15, -24 dB",
     "base": dict(BASE, **{"Ratio": ratio("10")}),
     "cases": [["detector-thr-16", {"Threshold": {"display": -16}}]] +
              [[f"auto-thr{t}", {"Threshold": {"display": t}, "Release": release("A")}] for t in (-9, -15, -24)]},

    {"name": "glue-stereo-oversample", "plan": "10, 12", "probe": "ext", "read": ["ext: lrsplit, side, tone10k, tone15k peaks", "impulse"], "priority": 2,
     "why": "stereo linking (does the quiet channel follow the loud one), and Oversample (stored element) against aliasing and the impulse's alignment",
     "question": "per-channel gain of the split tone and of side noise at Threshold -24 dB, Ratio 10; spectral lines of the 10 and 15 kHz sines at Threshold -30 dB, Ratio 10, Peak Clip In on, Oversample off and on",
     "base": dict(BASE, **{"Ratio": ratio("10")}),
     "cases": [["link-thr-24", {"Threshold": {"display": -24}}],
               ["os-off", {"Threshold": {"display": -30}, "Peak Clip In": {"item": "On"}, "@Oversample": False}],
               ["os-on", {"Threshold": {"display": -30}, "Peak Clip In": {"item": "On"}, "@Oversample": True}]]},

    {"name": "glue-sidechain", "plan": "13", "probe": "gap2", "read": ["envelope of the steady tone under the key bursts", "response (Listen)"], "priority": 1,
     "why": "the external side-chain: reduction against key level, S/C Gain, S/C Mix, Dry/Wet with a key, and the S/C EQ heard through Listen",
     "question": "the steady tone under key-duck's bursts, Threshold -30 dB, Ratio 10: S/C Gain 0, +12 dB, S/C Mix 50 %, Dry/Wet 50 %; Listen with the EQ off, Bell 1 kHz +12 dB Q 2, Low pass 1 kHz, High pass 1 kHz",
     "base": dict(BASE, **{"Threshold": {"display": -30}, "Ratio": ratio("10"), "S/C On": {"item": "On"},
                           "S/C EQ On": {"item": "Off"}, "S/C Gain": {"display": 0}, "S/C Mix": {"display": 100},
                           "@SideChain/RoutedInput/Routable/Target": "key:measurements/probe-keys/key-duck.wav"}),
     "cases": [["sc-gain+12", {"S/C Gain": {"display": 12}}], ["sc-mix-50", {"S/C Mix": {"display": 50}}],
               ["drywet-50", {"Dry/Wet": {"display": 50}}], ["listen-eq-off", {"@SideChainListen": True}]] +
              [[f"listen-{n}", {"@SideChainListen": True, "S/C EQ On": {"item": "On"}, "S/C EQ Type": {"item": t},
                                "S/C EQ Freq": {"display": 1000}, "S/C EQ Q": {"display": q}, "S/C EQ Gain": g}]
               for n, t, q, g in (("bell", "Bell", 2, 12), ("lp", "Low pass", 0.71, 0), ("hp", "High pass", 0.71, 0))]},
]
