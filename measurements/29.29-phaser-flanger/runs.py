# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Phaser-Flanger behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.29-phaser-flanger.md > Measurement plan.

The base is a static Phaser: Amount 0 (no modulation), Feedback 0, Warmth 0, Dry/Wet 100 %, Output 0
dB, Notches 4, Center 1 kHz, Spread 50 %, envelope follower off, LFO a 1 Hz sine in Hz mode, Phase 0,
Spin off, Duty Cycle 0, LFO2 mix 0, Safe Bass at its lowest (5 Hz). With Amount 0 the device is time-invariant
and `response.sweep_db` and the impulse show the static comb or notch layout; with Amount above 0
the steady 1 kHz tone's `modulation` (FM depth in cents, rate) shows the delay excursion; the L/R
instantaneous frequency of the steady segment can be re-read from the renders for the stereo runs.

Not measurable this way: plan 8's synced rate list (the 22 rates could each be a case, but only the
LFO rate is read from a single tone, so they are left out); plan 10 (Safe Bass needs a two-tone
input; the probe has one tone at 1 kHz and broadband noise only: its effect on the phaser notches
below 200 Hz could be read from the noise, but it is left out); plan 6's Triangle Analog at several
rates (one rate here); toggling during the render."""

DEVICE = "Phaser-Flanger"

BASE = {
    "Mode": {"item": "Phaser"}, "Amount": {"display": 0}, "Feedback": {"display": 0}, "FB Invert": {"item": "Off"},
    "Warmth": {"display": 0}, "Dry/Wet": {"display": 100}, "Output": {"display": 0},
    "Notches": 4, "Center Freq": {"display": 1000}, "Spread": {"display": 50}, "Mod Blend": {"norm": 0.0},
    "Flanger Time": {"display": 0.0025}, "Doubler Time": {"display": 0.08},
    "Mod Sync": {"item": "Off"}, "Mod Freq": {"display": 1}, "Mod Wave": {"item": "Sine"},
    "Mod Phase": {"display": 0}, "Spin Enabled": {"item": "Off"}, "Spin": {"display": 0},
    "Duty Cycle": {"display": 0}, "Lfo Blend": {"display": 0}, "Mod Sync 2": {"item": "Off"},
    "Mod Freq 2": {"display": 4}, "Env Enabled": {"item": "Off"}, "Env Amount": {"display": 0},
    "Safe Freq": {"display": 5},
}
FLANGER = {"Mode": {"item": "Flanger"}}
DOUBLER = {"Mode": {"item": "Doubler"}}
MOD = {"Amount": {"display": 100}}


def ms(v):
    return {"display": v / 1000}


RUNS = [
    {"name": "phaser-flanger-notches", "plan": "4", "probe": "gap2", "read": ["response.sweep_db", "response.noise_db"], "priority": 1,
     "why": "the Phaser's notch layout: how many notches Notches gives, where they sit against Center, and how Spread moves them (all-pass chain model)",
     "question": "static Phaser (Amount 0): Notches 1, 2, 8 and 42 (4 is the default case) at Center 1 kHz, Spread 50 %; Spread 0 and 100 % at 4 notches; Center 300 Hz",
     "base": BASE,
     "cases": [[f"n{n}", {"Notches": n}] for n in (1, 2, 8, 42)] + [
         ["spread-0", {"Spread": {"display": 0}}],
         ["spread-100", {"Spread": {"display": 100}}],
         ["center-300", {"Center Freq": {"display": 300}}],
     ]},

    {"name": "phaser-flanger-delay", "plan": "2", "probe": "gap2", "read": ["impulse", "response.sweep_db"], "priority": 1,
     "why": "the Flanger and Doubler base delay against Time (impulse tap and comb spacing), and what the dry path contributes",
     "question": "Flanger Time 0.1, 1, 5 and 20 ms (2.5 ms from base) and Doubler Time 20, 80 and 150 ms at Amount 0, Feedback 0",
     "base": BASE,
     "cases": [[f"flanger-{v:g}ms", FLANGER | {"Flanger Time": ms(v)}] for v in (0.1, 1, 5, 20)]
              + [[f"doubler-{v}ms", DOUBLER | {"Doubler Time": ms(v)}] for v in (20, 80, 150)]},

    {"name": "phaser-flanger-feedback", "plan": "11", "probe": "gap2", "read": ["impulse", "response.sweep_db"], "priority": 1,
     "why": "Feedback's law and the Ø invert (echo ratios, comb peak heights), the 99 % limit, and the Phaser's feedback",
     "question": "Flanger at 5 ms: Feedback 50, 90 and 99 %, and 50 % inverted; Phaser (4 notches) at 50 % and 50 % inverted; Doubler 20 ms at 50 %",
     "base": BASE | FLANGER | {"Flanger Time": ms(5)},
     "cases": [
         ["fl-fb50", {"Feedback": {"display": 50}}],
         ["fl-fb90", {"Feedback": {"display": 90}}],
         ["fl-fb99", {"Feedback": {"display": 99}}],
         ["fl-fb50-inv", {"Feedback": {"display": 50}, "FB Invert": {"item": "On"}}],
         ["ph-fb50", {"Mode": {"item": "Phaser"}, "Feedback": {"display": 50}}],
         ["ph-fb50-inv", {"Mode": {"item": "Phaser"}, "Feedback": {"display": 50}, "FB Invert": {"item": "On"}}],
         ["db-fb50", DOUBLER | {"Doubler Time": ms(20), "Feedback": {"display": 50}}],
     ]},

    {"name": "phaser-flanger-depth", "plan": "3,5", "probe": "gap2", "read": ["modulation"], "priority": 1,
     "why": "the modulation depth in time (from the tone's FM depth in cents) against Amount and mode, the unipolar/bipolar sweep, the LFO rate accuracy, and what Blend does in Phaser",
     "question": "1 kHz tone, 1 Hz sine LFO: Flanger Amount 25, 50, 100 % and 100 % at 5 Hz; Doubler Amount 50 and 100 %; Phaser Amount 100 % at Blend 0 and 1",
     "base": BASE,
     "cases": [
         ["fl-a25", FLANGER | {"Amount": {"display": 25}}],
         ["fl-a50", FLANGER | {"Amount": {"display": 50}}],
         ["fl-a100", FLANGER | MOD],
         ["fl-a100-5hz", FLANGER | MOD | {"Mod Freq": {"display": 5}}],
         ["db-a50", DOUBLER | {"Amount": {"display": 50}}],
         ["db-a100", DOUBLER | MOD],
         ["ph-a100-blend0", MOD],
         ["ph-a100-blend1", MOD | {"Mod Blend": {"norm": 1.0}}],
     ]},

    {"name": "phaser-flanger-lfo-shape", "plan": "6", "probe": "gap2", "read": ["modulation", "steady tone pitch over time"], "priority": 2,
     "why": "eight of the LFO shapes beyond Sine as the tone's instantaneous frequency: Triangle Analog, 8 and 16 step, saws, rectangle, sample-and-hold (smooth Random is left out)",
     "question": "Flanger Amount 100 %, 1 Hz LFO (Sine is the Flanger Amount 100 % case of phaser-flanger-depth): Triangle, Triangle Analog, Triangle 8, Triangle 16, Saw Up, Saw Down, Rectangle, Random S&H",
     "base": BASE | FLANGER | MOD,
     "cases": [[f"wave-{w.lower().replace(' ', '-').replace('&', '')}", {"Mod Wave": {"item": w}}] for w in
               ("Triangle", "Triangle Analog", "Triangle 8", "Triangle 16", "Saw Up", "Saw Down", "Rectangle", "Random S&H")]},

    {"name": "phaser-flanger-lfo-stereo", "plan": "6,7,8", "probe": "gap2", "read": ["modulation", "steady tone pitch over time", "stereo"], "priority": 2,
     "why": "Duty Cycle's warp, the L/R phase offset (Phase), Spin's detune of the right LFO, and LFO2's Mix and rate",
     "question": "Flanger Amount 100 %, 1 Hz sine: Duty Cycle +100 and -100 %; Phase 90 and 180 degrees; Spin 25 and 50 %; LFO2 (4 Hz) Mix 50 and 100 %",
     "base": BASE | FLANGER | MOD,
     "cases": [
         ["duty+100", {"Duty Cycle": {"display": 100}}],
         ["duty-100", {"Duty Cycle": {"display": -100}}],
         ["phase-90", {"Mod Phase": {"display": 90}}],
         ["phase-180", {"Mod Phase": {"display": 180}}],
         ["spin-25", {"Spin Enabled": {"item": "On"}, "Spin": {"display": 25}}],
         ["spin-50", {"Spin Enabled": {"item": "On"}, "Spin": {"display": 50}}],
         ["lfo2-50", {"Lfo Blend": {"display": 50}}],
         ["lfo2-100", {"Lfo Blend": {"display": 100}}],
     ]},

    {"name": "phaser-flanger-envelope", "plan": "9", "probe": "gap2", "read": ["modulation", "steady tone pitch over time"], "priority": 3,
     "why": "the envelope follower: sign and scale of its modulation against level (the -30 / -6 / -30 dBFS bursts) and its attack and release",
     "question": "Flanger, Amount 100 %, LFO at its slowest: Env Amount +1, -1, +0.5; Env +1 with Attack 30 ms; with Release 400 ms",
     "base": BASE | FLANGER | MOD | {"Mod Freq": {"display": 0.01}, "Env Enabled": {"item": "On"},
                                    "Env Attack": {"display": 0.001}, "Env Release": {"display": 0.12}},
     "cases": [
         ["env+1", {"Env Amount": {"display": 1}}],
         ["env-1", {"Env Amount": {"display": -1}}],
         ["env+0.5", {"Env Amount": {"display": 0.5}}],
         ["env+1-att30", {"Env Amount": {"display": 1}, "Env Attack": {"display": 0.03}}],
         ["env+1-rel400", {"Env Amount": {"display": 1}, "Env Release": {"display": 0.4}}],
     ]},

    {"name": "phaser-flanger-warmth-output", "plan": "11,12", "probe": "gap2", "read": ["static", "impulse"], "priority": 3,
     "why": "Warmth's distortion and filtering, Output in real dB, and the Dry/Wet law of the static phaser (Center 4 kHz keeps the tone off a notch)",
     "question": "static Phaser at Center 4 kHz: Warmth 50 and 100 %; Output +6 dB and -12 dB; Dry/Wet 0 and 50 %",
     "base": BASE | {"Center Freq": {"display": 4000}},
     "cases": [
         ["warmth-50", {"Warmth": {"display": 50}}],
         ["warmth-100", {"Warmth": {"display": 100}}],
         ["out+6", {"Output": {"norm": 1.0}}],
         ["out-12", {"Output": {"display": -12}}],
         ["dw-0", {"Dry/Wet": {"display": 0}}],
         ["dw-50", {"Dry/Wet": {"display": 50}}],
     ]},

    # ---- third set (measurements/third/)
    {"name": "phaser-flanger-blend-amount", "plan": "5", "probe": "gap2", "read": ["noise", "modulation", "envelope"], "priority": 2,
     "why": "Blend 0.5 (Center and Spread moving together) and Amounts below 100 %",
     "question": "noise and steady tone through the Phaser, 1 Hz sine: Mod Blend 0.5 at Amount 100 %; Amount 25 and 50 % at Blend 0",
     "base": BASE,
     "cases": [["blend-0.5", {"Amount": {"display": 100}, "Mod Blend": {"norm": 0.5}}]] +
              [[f"amount-{a}", {"Amount": {"display": a}}] for a in (25, 50)]},

    {"name": "phaser-flanger-lfo2-sync", "plan": "8", "probe": "ext", "read": ["ext: impulsetrain (delay per impulse)"], "priority": 2,
     "why": "LFO2's rate at other settings and the sync lists, read from the Flanger's delay at each impulse of the train",
     "question": "Flanger delay per impulse, Amount 100 %: LFO2 alone (Lfo Blend 100 %) at 1 and 8 Hz; LFO1 synced at Rate 8, 12, 15",
     "base": dict(BASE, **FLANGER, **MOD),
     "cases": [[f"lfo2-{f}hz", {"Lfo Blend": {"display": 100}, "Mod Freq 2": {"display": f}}] for f in (1, 8)] +
              [[f"sync-r{r}", {"Mod Sync": {"item": "On"}, "Mod Rate": r}] for r in (8, 12, 15)]},

    {"name": "phaser-flanger-env-times", "plan": "9", "probe": "ext", "read": ["ext: impulsetrain, shortbursts, bedbursts"], "priority": 2,
     "why": "the envelope follower's attack and release at the ends of their ranges, read through the Flanger's delay",
     "question": "Flanger delay under the bed bursts and short bursts, Env Amount +1: Attack 0.1 and 30 ms with Release 100 ms; Release 0.1 and 400 ms with Attack 1 ms",
     "base": dict(BASE, **FLANGER, **{"Env Enabled": {"item": "On"}, "Env Amount": {"display": 1}}),
     "cases": [[f"att{a}", {"Env Attack": {"display": a / 1000}, "Env Release": {"display": 0.1}}] for a in (0.1, 30)] +
              [[f"rel{r}", {"Env Attack": {"display": 0.001}, "Env Release": {"display": r / 1000}}] for r in (0.1, 400)]},

    {"name": "phaser-flanger-safe-warmth", "plan": "10, 11", "probe": "ext", "read": ["ext: threetone, ramp"], "priority": 2,
     "why": "Safe Bass: how much of the 60 and 200 Hz tones escapes the modulation at three cut-offs; Warmth's curve on the slow ramp",
     "question": "per-tone sidebands of the 60 Hz, 200 Hz and 2 kHz tones through the Phaser at Amount 100 %, Safe Freq 5, 200 Hz, 3 kHz; the ramp at Warmth 25, 75, 100 %",
     "base": BASE,
     "cases": [[f"safe-{f}", dict(MOD, **{"Safe Freq": {"display": f}})] for f in (5, 200, 3000)] +
              [[f"warmth-{w}", {"Warmth": {"display": w}}] for w in (25, 75, 100)]},

    # ---- fourth set: the +1 runs clamped the delay at its shortest for the bed and the burst
    {"name": "phaser-flanger-env-times-small", "plan": "9", "probe": "ext", "read": ["ext: bedbursts, shortbursts"], "priority": 3,
     "why": "the envelope follower's attack and release with the delay in its linear range: Env Amount +1 clamped the Flanger's delay for the bed and the burst alike",
     "question": "Flanger delay under the bed bursts, Time 20 ms, Env Amount +0.1: Attack 0.1 and 30 ms with Release 100 ms; Release 0.1 and 400 ms with Attack 1 ms",
     "base": dict(BASE, **FLANGER, **{"Flanger Time": {"display": 0.02}, "Env Enabled": {"item": "On"}, "Env Amount": {"display": 0.1}}),
     "cases": [[f"att{a}", {"Env Attack": {"display": a / 1000}, "Env Release": {"display": 0.1}}] for a in (0.1, 30)] +
              [[f"rel{r}", {"Env Attack": {"display": 0.001}, "Env Release": {"display": r / 1000}}] for r in (0.1, 400)]},
]
