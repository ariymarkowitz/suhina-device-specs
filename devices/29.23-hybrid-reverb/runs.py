# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Hybrid Reverb behaviour runs for tools/harness/measure.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.23-hybrid-reverb.md > Measurement plan.

The base isolates the algorithm engine: Routing Algorithm, Dry/Wet 100 %, Send 0 dB, no predelay or
algorithm delay, Decay 3.5 s (the default), EQ off, Vintage off, Width 100 %, Bass Mono off. The
runs that need only a short tail use Decay 0.1 to 1 s and the 2 s gap; the ones that read a decay
use the 10 s gap (`probe: gap10`, 4 s of reverb in the 10 s gap is enough for RT60 up to about 6 s;
longer Decay values only show their start).

Not measurable this way: the impulse response (category, file, Attack, Decay, Size and the time
shaping switch of the convolution) is not a parameter, so Convolution always plays the default IR
(plan 4 and 5); the IR attack/decay/size cannot be varied. Toggling Freeze during the render and
Tides' tempo retuning are not possible (plan 9's fade times); the Tides modulator's waveform and
rate list are only seen statically (plan 8's spectrogram can be read from any Tides case).
Sixth and Seventh of Prism, EQ Pre Algo (order only changes anything for non-linear engines) and
the Vintage rates and bit depths beyond the five steps are left out."""

DEVICE = "Hybrid Reverb"

INF = {"norm": 0.0}
BASE = {
    "Routing": {"item": "Algorithm"}, "Dry/Wet": {"display": 100}, "Send Gain": {"norm": 1.0},
    "Predelay Sync": {"item": "Off"}, "Predelay": {"display": 0}, "Algo Delay": {"display": 0},
    "Predelay FB": {"display": 0}, "Predel. FB 16th": {"display": 0},
    "Algo Type": {"item": "Dark Hall"}, "Decay": {"display": 3.5}, "Size": {"display": 50},
    "Freeze": {"item": "Off"}, "Freeze In": {"item": "Off"},
    "EQ On": {"item": "Off"}, "Vintage": 0, "Width": {"display": 100}, "Bass Mono": {"item": "Off"},
}
SHORT = {"Decay": {"display": 0.1}}


def algo(name, **kw):
    return {"Algo Type": {"item": name}, **kw}


RUNS = [
    {"name": "hybrid-reverb-algorithms", "plan": "6", "probe": "gap10", "read": ["impulse", "response.noise_db"], "priority": 1,
     "why": "how the five algorithms differ at the same Decay and Size: echo density, onset, early reflections, tail spectrum",
     "question": "impulse response and noise response of Dark Hall (default case), Quartz, Shimmer, Tides and Prism at Decay 3.5 s, Size 50 %",
     "base": BASE,
     "cases": [["quartz", algo("Quartz")], ["shimmer", algo("Shimmer")], ["tides", algo("Tides")], ["prism", algo("Prism")]]},

    {"name": "hybrid-reverb-decay", "plan": "6", "probe": "gap10", "read": ["impulse"], "priority": 1,
     "why": "the Decay control's law: RT60 against the Decay display, from the minimum to beyond what the gap shows",
     "question": "Dark Hall RT60 for Decay 0.1, 0.5, 1, 2, 6 and 12 s (3.5 s is the default case)",
     "base": BASE,
     "cases": [[f"decay-{v:g}", {"Decay": {"display": v}}] for v in (0.1, 0.5, 1, 2, 6, 12)]},

    {"name": "hybrid-reverb-blend", "plan": "3,14", "probe": "gap10", "read": ["impulse", "response.noise_db"], "priority": 1,
     "why": "the Blend law and structure in Serial and Parallel, the engines alone, and the latency at Dry/Wet 0",
     "question": "Routing Convolution and Algorithm alone; Parallel Blend 100/0, 75/25, 25/75, 0/100; Serial Blend 100/0, 50/50, 0/100; Dry/Wet 0",
     "base": BASE | {"Decay": {"display": 1}},
     "cases": [
         ["convolution", {"Routing": {"item": "Convolution"}}],
         ["par-100-0", {"Routing": {"item": "Parallel"}, "Blend": {"norm": 0.0}}],
         ["par-75-25", {"Routing": {"item": "Parallel"}, "Blend": {"norm": 0.25}}],
         ["par-25-75", {"Routing": {"item": "Parallel"}, "Blend": {"norm": 0.75}}],
         ["par-0-100", {"Routing": {"item": "Parallel"}, "Blend": {"norm": 1.0}}],
         ["ser-100-0", {"Routing": {"item": "Serial"}, "Blend": {"norm": 0.0}}],
         ["ser-50-50", {"Routing": {"item": "Serial"}, "Blend": {"norm": 0.5}}],
         ["ser-0-100", {"Routing": {"item": "Serial"}, "Blend": {"norm": 1.0}}],
     ]},

    {"name": "hybrid-reverb-predelay", "plan": "2", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "predelay and algorithm delay in ms and sixteenths (120 BPM), and the predelay feedback ratio and limit",
     "question": "Predelay 100 and 500 ms, 2 and 8 sixteenths, Algo Delay 100 and 500 ms, and Predelay Feedback 50 and 95 % at 100 ms (Decay 0.1 s)",
     "base": BASE | SHORT,
     "cases": [
         ["pd-100ms", {"Predelay": {"display": 0.1}}],
         ["pd-500ms", {"Predelay": {"display": 0.5}}],
         ["sync-2", {"Predelay Sync": {"item": "On"}, "Predelay 16th": 2}],
         ["sync-8", {"Predelay Sync": {"item": "On"}, "Predelay 16th": 8}],
         ["ad-100ms", {"Algo Delay": {"display": 0.1}}],
         ["ad-500ms", {"Algo Delay": {"display": 0.5}}],
         ["fb-50", {"Predelay": {"display": 0.1}, "Predelay FB": {"display": 50}}],
         ["fb-95", {"Predelay": {"display": 0.1}, "Predelay FB": {"display": 95}}],
     ]},

    {"name": "hybrid-reverb-darkhall", "plan": "6", "probe": "gap10", "read": ["impulse", "response.noise_db"], "priority": 2,
     "why": "what Size, Damping, Diffusion, Shape and the two-band decay (Bass Mult at Bass X) do to Dark Hall's decay, density and spectrum",
     "question": "Dark Hall at Size 0 and 100 %, Damping 0 and 100 %, Diffusion 0, Shape 0, Bass Mult 25 and 400 % (all others default)",
     "base": BASE,
     "cases": [
         ["size-0", {"Size": {"display": 0}}],
         ["size-100", {"Size": {"display": 100}}],
         ["damping-0", {"Damping": {"display": 0}}],
         ["damping-100", {"Damping": {"display": 100}}],
         ["diffusion-0", {"Diffusion": {"display": 0}}],
         ["shape-0", {"DH Shape": {"norm": 0.0}}],
         ["bass-25", {"DH BassMult": {"display": 25}}],
         ["bass-400", {"DH BassMult": {"display": 400}}],
     ]},

    {"name": "hybrid-reverb-shimmer", "plan": "7", "probe": "gap10", "read": ["steady tone spectrum", "impulse"], "priority": 2,
     "why": "the pitch the Shimmer feedback adds per repeat, the Shimmer amount law, and the interval between repeats",
     "question": "Shimmer (Decay 2 s) Pitch Shift +7, -12 and 0 semitones (+12 is the default case), Shimmer amount 0 and 100 %",
     "base": BASE | algo("Shimmer", Decay={"display": 2}),
     "cases": [
         ["pitch+7", {"Sh Pitch Shift": {"display": 7}}],
         ["pitch-12", {"Sh Pitch Shift": {"display": -12}}],
         ["pitch0", {"Sh Pitch Shift": {"display": 0}}],
         ["shimmer-0", {"Sh Shimmer": {"display": 0}}],
         ["shimmer-100", {"Sh Shimmer": {"display": 100}}],
     ]},

    {"name": "hybrid-reverb-output", "plan": "12,13", "probe": "gap2", "read": ["stereo", "response.noise_db", "static", "silence"], "priority": 2,
     "why": "Width and Bass Mono on the wet signal, what each Vintage step does (rate and bit-depth reduction, noise), and the dry path at Dry/Wet 0",
     "question": "Width 0 and 200 %, Vintage Subtle, Old, Extreme (steps 1, 2 and 4), Bass Mono on, Dry/Wet 0 and 50 % (Dark Hall, Decay 0.5 s)",
     "base": BASE | {"Decay": {"display": 0.5}},
     "cases": [
         ["width-0", {"Width": {"display": 0}}],
         ["width-200", {"Width": {"display": 200}}],
         ["vintage-1", {"Vintage": 1}],
         ["vintage-2", {"Vintage": 2}],
         ["vintage-4", {"Vintage": 4}],
         ["bass-mono", {"Bass Mono": {"item": "On"}}],
         ["dw-0", {"Dry/Wet": {"display": 0}}],
         ["dw-50", {"Dry/Wet": {"display": 50}}],
     ]},

    {"name": "hybrid-reverb-eq", "plan": "10", "probe": "gap2", "read": ["response.noise_db"], "priority": 3,
     "why": "the wet EQ's band shapes: low cut and shelf slopes, high cut, the two peaks' Q",
     "question": "noise response of the wet path (Decay 0.1 s) with the EQ on and flat (the default case: low cut at 20 Hz, high shelf 0 dB): low cut 1 kHz at 12 and 48 dB, low shelf -12 dB, high cut 2 kHz, peak 1 +12 dB, peak 2 -12 dB at Q 4",
     "base": BASE | SHORT | {"EQ On": {"item": "On"}, "EQ Lo Type": {"item": "Cut"}, "EQ Lo Freq": {"display": 20},
                             "EQ Lo Slope": 1, "EQ Hi Type": {"item": "Shelf"}, "EQ Hi Gain": {"display": 0}},
     "cases": [
         ["locut-1k-12", {"EQ Lo Freq": {"display": 1000}}],
         ["locut-1k-48", {"EQ Lo Freq": {"display": 1000}, "EQ Lo Slope": 5}],
         ["loshelf-1k", {"EQ Lo Type": {"item": "Shelf"}, "EQ Lo Freq": {"display": 1000}, "EQ Lo Gain": {"display": -12}}],
         ["hicut-2k", {"EQ Hi Type": {"item": "Cut"}, "EQ Hi Freq": {"display": 2000}, "EQ Hi Slope": 1}],
         ["peak1", {"EQ Peak 1 Gain": {"display": 12}}],
         ["peak2-q4", {"EQ Peak 2 Gain": {"display": -12}, "EQ Peak 2 Q": {"display": 4}}],
     ]},

    {"name": "hybrid-reverb-freeze", "plan": "9", "probe": "gap10", "read": ["impulse", "silence"], "priority": 3,
     "why": "Freeze set from the first sample: whether the input enters (Freeze In), and whether the loop sustains or decays",
     "question": "Freeze on with Freeze In off and on, against Freeze off (default case)",
     "base": BASE,
     "cases": [
         ["freeze", {"Freeze": {"item": "On"}}],
         ["freeze-in", {"Freeze": {"item": "On"}, "Freeze In": {"item": "On"}}],
     ]},

    # ---- third set: the long-tail probe (gap10) for decays; lanes for
    # Freeze toggled during the render
    {"name": "hybrid-reverb-decay-algos", "plan": "6", "probe": "gap10", "read": ["impulse (.ir.wav: T30 per band)"], "priority": 1,
     "why": "Decay against T60 for the four algorithms besides Dark Hall, and Dark Hall above 12 s (initial slope over the 10 s window)",
     "question": "impulse responses at Decay 1 s and 8 s for Quartz, Shimmer, Tides, Prism; Dark Hall at Decay 20 and 60 s",
     "base": BASE,
     "cases": [[f"{a.lower()}-{d}s", algo(a, Decay={"display": d})] for a in ("Quartz", "Shimmer", "Tides", "Prism") for d in (1, 8)] +
              [[f"darkhall-{d}s", {"Decay": {"display": d}}] for d in (20, 60)]},

    {"name": "hybrid-reverb-algo-controls", "plan": "6", "probe": "gap10", "read": ["impulse (.ir.wav: T30 per band, echo density, spectrum)"], "priority": 2,
     "why": "the other algorithms' own controls, Dark Hall's Bass X, and Prism's crossover",
     "question": "impulse responses (Decay 3.5 s): Quartz Low Damp 0 and 100 %, Distance 0 and 100 %; Prism X Over 400 Hz and 3 kHz with Low Mult at its minimum, High Mult at its minimum; Dark Hall Bass X 150 Hz and 1 kHz with Bass Mult at its maximum; Shimmer at 0 and 100 %",
     "base": BASE,
     "cases": [[f"quartz-lowdamp-{v}", algo("Quartz", **{"Qz Low Damp": {"display": v}})] for v in (0, 100)] +
              [[f"quartz-distance-{v}", algo("Quartz", **{"Qz Distance": {"display": v}})] for v in (0, 100)] +
              [[f"prism-xover-{f}-lowmin", algo("Prism", **{"Pr X Over": {"display": f}, "Pr Low Mult": {"norm": 0}})] for f in (400, 3000)] +
              [["prism-highmin", algo("Prism", **{"Pr High Mult": {"norm": 0}})]] +
              [[f"darkhall-bassx-{f}", {"DH Bass X": {"display": f}, "DH BassMult": {"norm": 1}}] for f in (150, 1000)] +
              [[f"shimmer-{v}", algo("Shimmer", **{"Sh Shimmer": {"display": v}})] for v in (0, 100)]},

    {"name": "hybrid-reverb-tides", "plan": "8", "probe": "gap2", "read": ["noise spectrum over time", "modulation"], "priority": 2,
     "why": "Tides: the movement of the spectrum over time against Tide, Waveform, Rate and Phase",
     "question": "the noise and the steady tone through Tides (Decay 1 s): Tide 100 % at Waveform 0, 50, 100 %; Rate 1/4 and 2; Phase 0 and 180",
     "base": dict(BASE, **algo("Tides", Decay={"display": 1}, **{"Ti Tide": {"display": 100}})),
     "cases": [[f"wave-{w}", {"Ti Waveform": {"display": w}}] for w in (0, 100)] +
              [["rate-q", {"Ti Rate": 16}], ["rate-2", {"Ti Rate": 25}],
               ["phase-0", {"Ti Phase": {"display": 0}}], ["phase-180", {"Ti Phase": {"display": 180}}]]},

    {"name": "hybrid-reverb-freeze-toggle", "plan": "9", "probe": "gap10", "read": ["raw render (level over time, fades)"], "priority": 1,
     "why": "Freeze toggled during the render: the loop's level over time and the fade times, with Freeze In off and on",
     "question": "the impulse's tail with Freeze on at beat 2 (1 s) and off at beat 16 (8 s), Freeze In off and on",
     "base": dict(BASE, **{"Freeze": {"auto": [[0, {"item": "Off"}], [2, {"item": "On"}], [16, {"item": "Off"}]]}}),
     "cases": [["in-off", {}], ["in-on", {"Freeze In": {"item": "On"}}]]},

    {"name": "hybrid-reverb-eq-ranges", "plan": "10, 11", "probe": "gap2", "read": ["response"], "priority": 2,
     "why": "the wet EQ's slopes and Q, and EQ Pre Algo (before or after the algorithm) in each routing",
     "question": "sweep response (Algorithm, Decay 0.1 s): Lo cut at 200 Hz with slopes 6, 24, 96 dB; Peak 1 at 1 kHz +12 dB with its Q at the ends; Hi cut at 2 kHz 36 dB, Pre Algo off and on, in Algorithm and Serial routing",
     "base": dict(BASE, **SHORT, **{"EQ On": {"item": "On"}, "EQ Lo Gain": {"display": 0}, "EQ Hi Gain": {"display": 0},
                                     "EQ Peak 1 Gain": {"display": 0}, "EQ Peak 2 Gain": {"display": 0}}),
     "cases": [[f"locut-{n}", {"EQ Lo Type": {"item": "Cut"}, "EQ Lo Freq": {"display": 200}, "EQ Lo Slope": i}]
               for n, i in (("6db", 0), ("24db", 3), ("96db", 9))] +
              [[f"peak1-q{n}", {"EQ Peak 1 Freq": {"display": 1000}, "EQ Peak 1 Gain": {"display": 12}, "EQ Peak 1 Q": {"norm": q}}]
               for n, q in (("min", 0), ("max", 1))] +
              [[f"hicut-{r.lower()}-pre{p}", {"Routing": {"item": r}, "EQ Hi Type": {"item": "Cut"}, "EQ Hi Freq": {"display": 2000},
                                              "EQ Hi Slope": 4, "EQ Pre Algo": {"item": "On" if p else "Off"}}]
               for r in ("Algorithm", "Serial") for p in (0, 1)]},
]
