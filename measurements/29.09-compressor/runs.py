# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Compressor behaviour runs for tools/harness/batch.py (see its docstring for the format).
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
]
