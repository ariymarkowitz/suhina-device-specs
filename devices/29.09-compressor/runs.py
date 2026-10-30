# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Compressor behaviour runs for tools/harness/measure.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.09-compressor.md › Measurement plan.

Not taken: the RMS window from bursts of 1 to 300 ms (step 5: the probe's bursts are 1 s long),
Auto release against click/burst length and a drum loop (step 8: only the probe's three
bursts), the side-chain and its EQ (steps 12 and 13: no external input, and the S/C EQ only acts
on a side-chain signal), the Peak-mode 50 Hz buzz (step 14: the probe has no 50 Hz tone),
sample-rate dependence (step 15: one rate) and stereo linking (step 12: the probe's one-sided
tones leave a silent channel). Threshold at Knee 6 dB is already measured (compressor-threshold),
and compressor-gen.* only checked the set builder."""

DEVICE = "Compressor"

# Peak detection, hard knee, fastest attack and release, no lookahead: the static curve itself.
STATIC = {"Model": {"item": "Peak"}, "Knee": 0, "Attack": {"norm": 0.0}, "Release": {"norm": 0.0},
          "LookAhead": {"item": "0 ms"}, "Threshold": {"display": -20}}

# Burst-step test: Peak, hard knee, Lin envelope, Lookahead 0, Release 100 ms, Attack 1 ms,
# Threshold -24 dB, Ratio 10. The probe's bursts step -30 -> -6 -> -30 dBFS, 18 dB over the
# threshold at the top.
DYN = {"Model": {"item": "Peak"}, "Knee": 0, "Env Mode": {"item": "Lin"}, "Auto Release On/Off": {"item": "Off"},
       "LookAhead": {"item": "0 ms"}, "Threshold": {"display": -24}, "Ratio": {"display": 10},
       "Attack": {"display": 0.001}, "Release": {"display": 0.1}}

RUNS = [
    {"name": "compressor-ratio", "plan": "2", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "the gain computer's slope per Ratio, and whether Threshold and Output add offsets",
     "question": "slope above a -20 dB threshold for Ratio 2, 4, 10 and inf, Peak, hard knee",
     "base": STATIC,
     "cases": [[f"ratio-{r}", {"Ratio": {"display": v}}] for r, v in
               (("2", 2), ("4", 4), ("10", 10))] + [["ratio-inf", {"Ratio": {"norm": 1.0}}]]},

    {"name": "compressor-knee", "plan": "3", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "whether the Knee half-width and the quadratic soft knee hold over the range (0, 10, 14, 18 dB) in Peak mode",
     "question": "static curve at Threshold -20 dB, Ratio 4, Peak, for Knee 3, 6, 10, 18 dB (the default case is Knee 0)",
     "base": dict(STATIC, Ratio={"display": 4}),
     "cases": [[f"knee-{k}", {"Knee": k}] for k in (3, 6, 10, 18)]},

    {"name": "compressor-detector", "plan": "2, 4", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "Peak vs RMS level offset (3 dB on a sine?) and the Expand curve for Expansion Ratio 1 to 2",
     "question": "static curve at Threshold -20 dB, Ratio 4, hard knee: RMS, and Expand with Expansion Ratio 1, 1.5, 2 (Peak is the default case)",
     "base": dict(STATIC, Ratio={"display": 4}),
     "cases": [["rms", {"Model": {"item": "RMS"}}],
               ["expand-1", {"Model": {"item": "Expand"}, "Expansion Ratio": 1}],
               ["expand-1.5", {"Model": {"item": "Expand"}, "Expansion Ratio": 1.5}],
               ["expand-2", {"Model": {"item": "Expand"}, "Expansion Ratio": 2}]]},

    {"name": "compressor-attack", "plan": "6", "probe": "gap2", "read": ["dynamics"], "priority": 1,
     "why": "how the Attack knob maps to the measured attack time (63 % and 90 %), exponential shape, and Peak vs RMS",
     "question": "attack t63 and t90 of the -30 to -6 dBFS step for Attack 0.1, 1, 10, 100 ms in Peak and 1, 10 ms in RMS (Lin, Release 100 ms, Threshold -24 dB, Ratio 10)",
     "base": DYN,
     "cases": [[f"attack-{a}ms", {"Attack": {"display": a / 1000}}] for a in (0.1, 1, 10, 100)] +
              [[f"rms-attack-{a}ms", {"Model": {"item": "RMS"}, "Attack": {"display": a / 1000}}] for a in (1, 10)]},

    {"name": "compressor-release", "plan": "6", "probe": "gap2", "read": ["dynamics"], "priority": 1,
     "why": "how the Release knob maps to the measured release time and the release shape (Lin, Peak)",
     "question": "release t63 and t90 after the -6 to -30 dBFS step down for Release 10, 50, 200, 1000 ms (Attack 1 ms, Lin)",
     "base": dict(DYN, Attack={"display": 0.001}),
     "cases": [[f"release-{r}ms", {"Release": {"display": r / 1000}}] for r in (10, 50, 200, 1000)]},

    {"name": "compressor-env-mode", "plan": "7, 8", "probe": "gap2", "read": ["dynamics"], "priority": 2,
     "why": "Log vs Lin: whether release gets faster with deeper reduction, and what Auto release does (at 6 and 18 dB of reduction)",
     "question": "attack and release times of the burst step in Lin, Log and Auto release for Ratio 2 (about 9 dB of reduction) and Ratio 10 (about 16 dB), Attack 10 ms, Release 300 ms",
     "base": dict(DYN, Attack={"display": 0.01}, Release={"display": 0.3}),
     "cases": [[f"{m}-ratio-{r}", {"Env Mode": {"item": m.capitalize()}, "Ratio": {"display": r}}]
               for m in ("lin", "log") for r in (2, 10)] +
              [["auto-lin", {"Auto Release On/Off": {"item": "On"}}],
               ["auto-log", {"Auto Release On/Off": {"item": "On"}, "Env Mode": {"item": "Log"}}]]},

    {"name": "compressor-lookahead", "plan": "9, 11", "probe": "gap2", "read": ["impulse", "dynamics"], "priority": 2,
     "why": "the delay added by Lookahead 1 and 10 ms, and whether Dry/Wet's dry path is delayed to match; its effect on an attack that is too slow",
     "question": "impulse delay for Lookahead 1 and 10 ms, Dry/Wet 50 % at Lookahead 10 ms (comb or not), and burst attack at Lookahead 10 ms",
     "base": dict(DYN, Attack={"display": 0.001}),
     "cases": [["look-1", {"LookAhead": {"item": "1 ms"}}], ["look-10", {"LookAhead": {"item": "10 ms"}}],
               ["look-10-wet-50", {"LookAhead": {"item": "10 ms"}, "Dry/Wet": {"display": 50}}],
               ["look-10-attack-10ms", {"LookAhead": {"item": "10 ms"}, "Attack": {"display": 0.01}}]]},

    {"name": "compressor-makeup", "plan": "10", "probe": "gap2", "read": ["static"], "priority": 2,
     "why": "the Makeup rule: output gain added for Threshold and Ratio (compare level of the staircase's top with the no-makeup case)",
     "question": "static curve with Makeup on for Threshold -20 dB at Ratio 2, 4, inf and Threshold -40 dB at Ratio 4",
     "base": dict(STATIC, Makeup={"item": "On"}),
     "cases": [["makeup-r2", {"Ratio": {"display": 2}}], ["makeup-r4", {"Ratio": {"display": 4}}],
               ["makeup-rinf", {"Ratio": {"norm": 1.0}}],
               ["makeup-r4-t40", {"Ratio": {"display": 4}, "Threshold": {"display": -40}}]]},

    # ---- third set. The extended probe has 1 kHz bursts of 1, 5, 10, 30,
    # 100 and 300 ms at -6 dBFS with silence between (detector windows), bursts of 1 ms, 100 ms and
    # 3 s over a -30 dBFS bed (release after short and long compression), a loud left and quieter
    # right channel, mid-only and side-only noise, and a 50 Hz tone. The side-chain runs play the
    # main probe with key-duck on a key track (signals.py --kind key-duck): silence under the
    # staircase, the probe's own sweep and noise, and 1 kHz key bursts at -36 to 0 dBFS under
    # the steady tone.
    {"name": "compressor-rms-window", "plan": "5", "probe": "ext", "read": ["ext: shortbursts"], "priority": 1,
     "why": "the RMS detector's window: the reduction a burst gets against its length, Peak against RMS",
     "question": "peak gain of 1 to 300 ms bursts at 6 dB over a -12 dB threshold, ratio 10, hard knee, fastest attack, Release 100 ms, RMS and Peak, Lin",
     "base": dict(DYN, **{"Threshold": {"display": -12}, "Attack": {"norm": 0.0}}),
     "cases": [["rms", {"Model": {"item": "RMS"}}], ["peak", {}], ["rms-log", {"Model": {"item": "RMS"}, "Env Mode": {"item": "Log"}}]]},

    {"name": "compressor-auto-release-bursts", "plan": "8", "probe": "ext", "read": ["ext: bedbursts envelope"], "priority": 1,
     "why": "Auto release after a click, a 100 ms burst and a 3 s burst (18 dB over the threshold), Lin and Log, against a fixed 300 ms release",
     "question": "gain over the -30 dBFS bed after each burst, Threshold -24 dB, ratio 10, Attack 1 ms: Auto on in Lin and Log; Release 300 ms Lin",
     "base": DYN,
     "cases": [["auto-lin", {"Auto Release On/Off": {"item": "On"}}],
               ["auto-log", {"Auto Release On/Off": {"item": "On"}, "Env Mode": {"item": "Log"}}],
               ["fixed-300-lin", {"Release": {"display": 0.3}}]]},

    {"name": "compressor-log-lin-amounts", "plan": "7", "probe": "gap2", "read": ["dynamics"], "priority": 2,
     "why": "how the release time depends on the amount of reduction in Lin and Log (reductions of about 3, 6, 12 and 21 dB on the -6 dBFS burst)",
     "question": "attack and release of the bursts at ratio inf with Threshold -9, -12, -18, -27 dB, Release 100 ms, Lin and Log",
     "base": dict(DYN, **{"Ratio": {"norm": 1.0}}),
     "cases": [[f"{m.lower()}-thr{t}", {"Env Mode": {"item": m}, "Threshold": {"display": t}}]
               for m in ("Lin", "Log") for t in (-9, -12, -18, -27)]},

    {"name": "compressor-makeup-more", "plan": "10", "probe": "gap2", "read": ["static", "noise level"], "priority": 2,
     "why": "whether Knee, the times or Lookahead change the makeup, and the makeup on noise",
     "question": "static curve and noise level with Makeup on, Threshold -20 dB, Ratio 4: Knee 6 and 18 dB, Attack 30 ms with Release 300 ms, Lookahead 10 ms",
     "base": dict(STATIC, **{"Makeup": {"item": "On"}, "Ratio": {"display": 4}}),
     "cases": [["knee-6", {"Knee": 6}], ["knee-18", {"Knee": 18}],
               ["slow", {"Attack": {"display": 0.03}, "Release": {"display": 0.3}}],
               ["lookahead-10", {"LookAhead": {"item": "10 ms"}}]]},

    {"name": "compressor-drywet", "plan": "11", "probe": "gap2", "read": ["static", "impulse"], "priority": 2,
     "why": "Dry/Wet at 50 %: the law with and without compression, and whether the dry path is delayed with Lookahead 10 ms",
     "question": "staircase and impulse at Dry/Wet 50 %, Threshold 0 and -30 dB (Peak, ratio 10); and at Lookahead 10 ms",
     "base": dict(STATIC, **{"Ratio": {"display": 10}, "Dry/Wet": {"display": 50}}),
     "cases": [["thr0", {"Threshold": {"display": 0}}], ["thr-30", {"Threshold": {"display": -30}}],
               ["thr-30-la10", {"Threshold": {"display": -30}, "LookAhead": {"item": "10 ms"}}]]},

    {"name": "compressor-stereo", "plan": "12", "probe": "ext", "read": ["ext: lrsplit, mid, side"], "priority": 1,
     "why": "stereo linking: whether the quieter channel is reduced with the louder one, and whether the detector hears the sum (side-only noise would then not compress)",
     "question": "gain of each channel of the left -6 / right -18 dBFS tone, and of mid-only and side-only noise, Threshold -24 dB, ratio 10, Peak and RMS",
     "base": dict(STATIC, **{"Threshold": {"display": -24}, "Ratio": {"display": 10}}),
     "cases": [["peak", {}], ["rms", {"Model": {"item": "RMS"}}]]},

    {"name": "compressor-sidechain", "plan": "10, 13", "probe": "gap2", "read": ["modulation (steady tone under the key bursts)", "response (Listen)"], "priority": 1,
     "why": "the external side-chain: reduction against key level, S/C Gain, S/C Mix, the S/C EQ's shapes heard through Listen, and makeup with an external key",
     "question": "the steady tone under key-duck's bursts, Threshold -30, ratio 10, Peak: S/C Gain 0, +12, -12 dB, S/C Mix 50 %, Makeup on; with Listen on, the key sweep through S/C EQ off, Bell 1 kHz +12 dB Q 2, Low pass 1 kHz, High pass 1 kHz, Low Shelf 200 Hz -12 dB, High Shelf 5 kHz +12 dB, Peak 1 kHz",
     "base": dict(STATIC, **{"Threshold": {"display": -30}, "Ratio": {"display": 10}, "S/C On": {"item": "On"},
                             "S/C EQ On": {"item": "Off"}, "S/C Gain": {"display": 0}, "S/C Mix": {"display": 100},
                             "@SideChain/RoutedInput/Routable/Target": "key:key-duck"}),
     "cases": [["sc-gain+12", {"S/C Gain": {"display": 12}}], ["sc-gain-12", {"S/C Gain": {"display": -12}}],
               ["sc-mix-50", {"S/C Mix": {"display": 50}}], ["sc-makeup", {"Makeup": {"item": "On"}}],
               ["listen-eq-off", {"S/C Listen": {"item": "On"}}]] +
              [[f"listen-{n}", dict({"S/C Listen": {"item": "On"}, "S/C EQ On": {"item": "On"}, "S/C EQ Type": {"item": t},
                                     "S/C EQ Freq": {"display": f}, "S/C EQ Q": {"display": q}, "S/C EQ Gain": g})]
               for n, t, f, q, g in (("bell", "Bell", 1000, 2, 12), ("lp", "Low pass", 1000, 0.71, 0),
                                     ("hp", "High pass", 1000, 0.71, 0), ("lowshelf", "Low Shelf", 200, 0.71, -12),
                                     ("highshelf", "High Shelf", 5000, 0.71, 12), ("peak", "Peak", 1000, 2, 0))]},

    {"name": "compressor-peak-buzz", "plan": "14", "probe": "ext", "read": ["ext: tone50 thd and peaks"], "priority": 2,
     "why": "gain modulation at the signal period with the fastest times (the manual's buzz in Peak mode)",
     "question": "distortion of the 50 Hz tone at 10 dB over a -16 dB threshold, ratio 10, fastest attack and release, Peak, RMS, and Peak with Release 100 ms",
     "base": dict(STATIC, **{"Threshold": {"display": -16}, "Ratio": {"display": 10}}),
     "cases": [["peak-fast", {}], ["rms-fast", {"Model": {"item": "RMS"}}], ["peak-rel100", {"Release": {"display": 0.1}}]]},

    {"name": "compressor-peak-buzz-eq-off", "plan": "14", "probe": "ext", "read": ["ext: tone50 thd and peaks"], "priority": 2,
     "why": "the third set's peak-buzz run had the loaded preset's side-chain EQ (a high-pass at 80 Hz) on, which hid most of a 50 Hz tone from the detector; this repeats it with the EQ off",
     "question": "distortion of the 50 Hz tone at 10 dB over a -16 dB threshold, ratio 10, fastest attack and release, side-chain EQ off: Peak, RMS, and Peak with Release 100 ms",
     "base": dict(STATIC, **{"Threshold": {"display": -16}, "Ratio": {"display": 10}, "S/C EQ On": {"item": "Off"}}),
     "cases": [["peak-fast", {}], ["rms-fast", {"Model": {"item": "RMS"}}], ["peak-rel100", {"Release": {"display": 0.1}}]]},
]
