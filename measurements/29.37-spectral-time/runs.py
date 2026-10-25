# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Spectral Time behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.37-spectral-time.md › Measurement plan.

API names: `On` is the Freezer's switch, `Delay On` the Delay's, `Dry Wet` the global mix and
`Delay Mix` the Delay section's own. The Freezer is exercised with `Frozen` set from the first sample
(the Freeze button on): in Retrigger mode that makes it freeze at every onset or interval, which a
static render can show on the sweep, staircase and bursts. Manual mode needs the button to be
pressed during the render and is not proposed.

Left out (cannot be measured this way): toggling Freeze in Manual mode and its Fade In/Out (plan 3,
automation); Resolution, the processing order (Frz > Dly) and Zero Dry Signal Latency (not API
parameters; the loaded Mid / Frz > Dly / off are used) so plan 2's per-Resolution latency cannot be
read, only the default's; the spectrogram. The latency at the loaded Resolution is read from the
impulse of the mix run.
"""

DEVICE = "Spectral Time"

ON, OFF = 1, 0
# Delay alone, wet only, Delay Mix 100 %, 250 ms, Feedback 50 %.
DELAY = {"On": OFF, "Delay On": ON, "Dry Wet": {"display": 100}, "Delay Mix": {"display": 100},
         "Delay Mode": {"item": "Time"}, "Delay Time": {"display": 0.25}, "Delay Feedback": {"display": 50}}
# Freezer alone, frozen from the start, retriggering on a 500 ms interval, no fade.
FREEZER = {"On": ON, "Delay On": OFF, "Dry Wet": {"display": 100}, "Frozen": ON, "Mode": {"item": "Retrigger"},
           "Retrigger Mode": {"item": "Sync"}, "Unit": {"item": "Milliseconds"}, "S.Rate ms": {"display": 0.5},
           "Fade Type": {"item": "Crossfade"}, "XFade %": {"display": 0}}

RUNS = [
    {"name": "spectral-time-delay-timing", "plan": "6", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "delay time in each mode (ms, Notes, 16th, triplet, dotted at 120 BPM) and the minimum, as spectral-frame echoes",
     "question": "echo times of an impulse with Feedback 50 %: Time 10, 100, 1000 ms; Synced 1/8; 16th, 16th Triplet, 16th Dotted at 3 (default 250 ms)",
     "base": DELAY,
     "cases": [[f"t-{ms}ms", {"Delay Time": {"display": ms / 1000}}] for ms in (10, 100, 1000)]
     + [["synced-1/8", {"Delay Mode": {"item": "Synced"}, "Delay Synced": 6}],
        ["16th-3", {"Delay Mode": {"item": "16th"}, "Delay 16th": 3}],
        ["triplet-3", {"Delay Mode": {"item": "16th Triplet"}, "Delay 16th": 3}],
        ["dotted-3", {"Delay Mode": {"item": "16th Dotted"}, "Delay 16th": 3}]]},

    {"name": "spectral-time-freeze-sync", "plan": "5", "probe": "gap2", "read": ["sweep (spectrogram)", "static"], "priority": 1,
     "why": "Sync retriggering: how a freeze starts and holds, the crossfade shape against X-Fade, and the Envelope fades",
     "question": "spectrogram of the sweep and level of the staircase with Frozen on, Retrigger Sync 500 ms: X-Fade 0, 50, 100 % (Crossfade); Envelope with Fade 2/40 ms and 300/300 ms; interval 1/8 note (250 ms)",
     "base": FREEZER,
     "cases": [["xfade-50", {"XFade %": {"display": 50}}], ["xfade-100", {"XFade %": {"display": 100}}],
               ["env-2-40ms", {"Fade Type": {"item": "Envelope"}}],
               ["env-300-300ms", {"Fade Type": {"item": "Envelope"}, "Fade In": {"display": 0.3}, "Fade Out": {"display": 0.3}}],
               ["beat-1/8", {"Unit": {"item": "ModulationBeat"}, "Sync Interval": 6}]]},

    {"name": "spectral-time-delay-shift", "plan": "7", "probe": "gap2", "read": ["steady (spectrum over time)"], "priority": 1,
     "why": "Shift is additive in Hz and applied again on every repeat (or not), and its sign",
     "question": "frequency of the 1 kHz tone in each 1 s repeat (Time 1 s, Feedback 70 %) for Shift +10, +50, -50, +200 Hz",
     "base": {**DELAY, "Delay Time": {"display": 1.0}, "Delay Feedback": {"display": 70}},
     "cases": [[f"shift{s:+d}", {"Delay Frequency Shift": {"display": s}}] for s in (10, 50, -50, 200)]},

    {"name": "spectral-time-tilt-spray", "plan": "8", "probe": "gap2", "read": ["sweep (arrival time against frequency)", "impulse"], "priority": 2,
     "why": "how Tilt, Spray, Mask and Stereo shape the delay time per frequency (mapping, range, corner, randomness)",
     "question": "arrival time against frequency in the sweep and impulse with Time 100 ms, Feedback 0: Tilt +-500 ms, Spray 200 ms, Tilt +500 ms with Mask +-0.5, Spray 200 ms with Stereo 100 %",
     "base": {**DELAY, "Delay Time": {"display": 0.1}, "Delay Feedback": {"display": 0}},
     "cases": [["tilt+500ms", {"Delay Tilt": {"display": 0.5}}], ["tilt-500ms", {"Delay Tilt": {"display": -0.5}}],
               ["spray-200ms", {"Delay Spray": {"display": 0.2}}],
               ["tilt+500-mask+0.5", {"Delay Tilt": {"display": 0.5}, "Delay Mask": {"display": 0.5}}],
               ["tilt+500-mask-0.5", {"Delay Tilt": {"display": 0.5}, "Delay Mask": {"display": -0.5}}],
               ["spray-200-stereo100", {"Delay Spray": {"display": 0.2}, "Delay Stereo Spread": {"display": 100}}]]},

    {"name": "spectral-time-freeze-onsets", "plan": "4", "probe": "gap2", "read": ["dynamics", "static", "impulse"], "priority": 2,
     "why": "the onset detector: which signal edges freeze at Sensitivity 0 to 100 %",
     "question": "level over time of the bursts, staircase and impulse with Frozen on, Retrigger Onsets, Sensitivity 0, 25, 75, 100 % (default 50 %), Crossfade 2 ms",
     "base": {**FREEZER, "Retrigger Mode": {"item": "Onsets"}, "Sensitivity": {"display": 50}},
     "cases": [[f"sens-{s}", {"Sensitivity": {"display": s}}] for s in (0, 25, 75, 100)]},

    {"name": "spectral-time-delay-feedback", "plan": "6, 9", "probe": "gap2", "read": ["impulse"], "priority": 2,
     "why": "level per repeat against Feedback, and the Delay section's own Dry/Wet law",
     "question": "echo levels of an impulse for Feedback 0, 25, 75, 100 % and Delay Mix 50 % (default 50 % feedback, Mix 100 %)",
     "base": DELAY,
     "cases": [[f"fb-{f}", {"Delay Feedback": {"display": f}}] for f in (0, 25, 75, 100)]
     + [["mix-50", {"Delay Mix": {"display": 50}}], ["mix-0", {"Delay Mix": {"display": 0}}]]},

    {"name": "spectral-time-mix-latency", "plan": "2, 9", "probe": "gap2", "read": ["impulse", "static"], "priority": 2,
     "why": "latency of the device at the loaded Resolution (idle, Freezer idle, Delay at its minimum), the global Dry/Wet law and Input Send",
     "question": "impulse delay and levels with the sections off, Dry/Wet 50 %, an idle Freezer, the Delay at 10 ms, Input Send -6 and -12 dB",
     "base": {"On": OFF, "Delay On": OFF, "Dry Wet": {"display": 100}},
     "cases": [["dw-50", {"Dry Wet": {"display": 50}}],
               ["freezer-idle", {"On": ON}],
               ["delay-10ms-mix100", {"Delay On": ON, "Delay Mix": {"display": 100}, "Delay Time": {"display": 0.01},
                                      "Delay Feedback": {"display": 0}}],
               ["send-6", {"Send Gain": {"display": -6}}], ["send-12", {"Send Gain": {"display": -12}}]]},

    # ---- third set (measurements/third/). Resolution, ZeroLatencyDry, ProcessingOrder and
    # Freezer_AvoidFreezingOnsets are stored elements (Resolution 1 in the loaded device; only
    # values next to it are tried, as an out-of-range enum could make Live refuse the set)
    {"name": "spectral-time-resolution-order", "plan": "1, 2", "probe": "gap2", "read": ["impulse", "response", "static"], "priority": 1,
     "why": "Resolution's time smearing and frequency resolution, the processing order, Zero Dry Signal Latency, and what AvoidFreezingOnsets does",
     "question": "impulse, sweep and staircase through the Delay alone (250 ms, Feedback 0) at Resolution 0 and 2; ProcessingOrder 1 with Freezer and Delay on; ZeroLatencyDry true at Dry Wet 50 %; the Freezer (onsets) with AvoidFreezingOnsets true",
     "base": dict(DELAY, **{"Delay Feedback": {"display": 0}}),
     "cases": [[f"resolution-{r}", {"@Resolution": r}] for r in (0, 2)] +
              [["order-1", {"@ProcessingOrder": 1, "On": ON, "Frozen": ON, "Mode": {"item": "Retrigger"},
                            "Retrigger Mode": {"item": "Sync"}, "S.Rate ms": {"display": 0.5}}],
               ["zerodry-50", {"@ZeroLatencyDry": True, "Dry Wet": {"display": 50}}],
               ["avoid-onsets", dict(FREEZER, **{"Retrigger Mode": {"item": "Onsets"}, "@Freezer_AvoidFreezingOnsets": True})]]},

    {"name": "spectral-time-freeze-lane", "plan": "3", "probe": "gap2", "read": ["raw render (level and spectrum over time)"], "priority": 1,
     "why": "a manual freeze pressed during the steady tone and released after it: level and spectrum over time, the fades",
     "question": "Frozen on at beat 44 (22 s) and off at beat 62 (31 s, into the noise), Manual mode: Crossfade, and Envelope with Fade In 100 ms, Fade Out 500 ms",
     "base": dict(FREEZER, **{"Mode": {"item": "Manual"}, "Frozen": {"auto": [[0, OFF], [44, ON], [62, OFF]]}}),
     "cases": [["crossfade", {}],
               ["envelope", {"Fade Type": {"item": "Envelope"}, "Fade In": {"display": 0.1}, "Fade Out": {"display": 0.5}}]]},

    {"name": "spectral-time-synced-steps", "plan": "6", "probe": "gap2", "read": ["impulse"], "priority": 3,
     "why": "the other steps of the Delay's Synced list",
     "question": "delay of the impulse in Synced mode at Delay Synced 6, 9, 12, 18",
     "base": dict(DELAY, **{"Delay Mode": {"item": "Synced"}, "Delay Feedback": {"display": 0}}),
     "cases": [[f"synced-{i}", {"Delay Synced": i}] for i in (6, 9, 12, 18)]},

    # ---- candidate after the third set: `order-1` of spectral-time-resolution-order has no render of the other order to compare with
    {"name": "spectral-time-order-reference", "plan": "9", "probe": "gap2", "read": ["raw render (level and spectrum over time)"], "priority": 3,
     "why": "the processing order: the third set rendered Freezer and Delay on with ProcessingOrder 1 only, so the order's effect cannot be read",
     "question": "Freezer (Retrigger, Sync every 500 ms, Frozen) and Delay (250 ms, Feedback 0) both on: ProcessingOrder 0 and 1",
     "base": dict(DELAY, **{"Delay Feedback": {"display": 0}, "On": ON, "Frozen": ON, "Mode": {"item": "Retrigger"},
                            "Retrigger Mode": {"item": "Sync"}, "S.Rate ms": {"display": 0.5}}),
     "cases": [[f"order-{o}", {"@ProcessingOrder": o}] for o in (0, 1)]},
]
