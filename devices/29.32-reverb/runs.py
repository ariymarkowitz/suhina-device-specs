# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Reverb behaviour runs for tools/harness/measure.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.32-reverb.md › Measurement plan.

The Reverb already has five runs (README.md in this folder: structure, decay, filters, texture, size)
and most of the plan is done (note › Measured). These runs only take up what those left open and
what one probe render can answer: the Lo Cut's law, the network filters at other frequencies,
Freeze/Flat/Cut set statically from the first sample (plan 9, without automation), Smooth Slow
(plan 10, as far as an export shows it), more Spin pairs, and Diffusion/Scale at a second Size.
The base states are those of make_cases.py, so the setup is the same.

Left out (cannot be measured this way): Smooth's glide times and toggling Freeze during the render
(automation); the decay of the 60 s setting past 60 s (the longest probe has a 30 s gap); CPU cost of
Density; the Predelay's 0.06 to 0.09 ms offset (below what an impulse at 44.1 kHz resolves usefully).
"""

DEVICE = "Reverb"

ON, OFF = 1, 0
# Wet only and time-invariant: what the earlier runs start from.
STATIC = {"Dry/Wet": {"display": 100}, "Chorus On": OFF, "ER Spin On": OFF}
ER_ONLY = {"Diffuse Level": {"norm": 0.0}}
TAIL_ONLY = {"Reflect Level": {"norm": 0.0}}
SHORT = {"Decay Time": {"norm": 0.0}}  # 200 ms
NET = {"Decay Time": {"norm": 0.5}, **TAIL_ONLY, "Diff. Hi On": OFF, "Diff. Lo On": OFF}  # 3.46 s, filters off

LOCUT = {**STATIC, **SHORT, "In Lo Cut On": ON, "In Hi Cut On": OFF, "Input Freq": {"display": 1000},
         "Input Width": {"display": 5.85}}


def shelf(typ, freq, gain=0.4):
    return {"Diff. Hi On": ON, "Diff. Hi Type": {"item": typ}, "Diff. Hi Freq": {"display": freq},
            "HiShelf Gain": {"display": gain}}


SMALL_SMOOTH_NONE = {**STATIC, "Size Smoothing": {"item": "None"}}


def rate_cases():
    """The cases of the runs at other sample rates (note › Measurement plan 14), the same at each
    rate: the bare network as reverb-network-exact, under Smooth None and Fast."""
    smooth = {"none": {"Size Smoothing": {"item": "None"}}, "fast": {"Size Smoothing": {"item": "Fast"}}}
    er = {"Reflect Level": {"display": 0.0}, **ER_ONLY}
    cases = []
    for sm, s in smooth.items():
        # Low's lines, A's and B's fractions as a slope over three Sizes, and the blocks under None
        for z in (1.53, 10.54, 100):
            if (sm, z) != ("none", 100):  # the run's default
                cases.append([f"{sm}-size-{z:g}", {**s, "Room Size": {"display": z}}])
            cases.append([f"{sm}-size-{z:g}-er-only", {**s, "Room Size": {"display": z}, **er}])
        # Mid's and High's allpasses, which split only above Diffusion 0.1 %
        for d in ("Mid", "High"):
            cases.append([f"{d.lower()}-{sm}-diffusion-60-scale-100",
                          {**s, "Density": {"item": d}, "Diffusion": {"display": 60}, "Scale": {"display": 100}}])
            cases.append([f"{d.lower()}-{sm}-er-only", {**s, "Density": {"item": d}, **er}])
        # Stereo's delay of the reflections
        for st in (0, 60):
            cases.append([f"{sm}-stereo-{st:g}-er-only", {**s, "Stereo Image": {"display": st}, **er}])
        # the Shape entry
        for v in (0, 0.25, 0.5, 1):
            cases.append([f"{sm}-decay-0.83s-shape-{v:g}", {**s, "Decay Time": {"norm": 0.25}, "ER Shape": {"display": v}}])
    return cases

RUNS = [
    {"name": "reverb-locut-law", "plan": "3", "probe": "gap2", "read": ["response"], "priority": 2,
     "why": "the Lo Cut's law, which the note calls not understood: corner against Input Freq and Input Width",
     "question": "sweep response of the Lo Cut alone (Hi Cut off, short tail) against Input Width at 1 kHz and Input Freq at Width 5.85",
     "base": LOCUT,
     "cases": [[f"lo-1k-w{w:g}", {"Input Width": {"display": w}}] for w in (0.5, 2, 4.75, 9)]
     + [["lo-300Hz", {"Input Freq": {"display": 300}}], ["lo-2k", {"Input Freq": {"display": 2000}}]]},

    {"name": "reverb-network-freq", "plan": "6", "probe": "gap10", "read": ["impulse"], "priority": 2,
     "why": "the High shelf/Lowpass and Low shelf at other frequencies: shelf midpoint and order, Lowpass corner",
     "question": "decay per octave band (filtered .ir.wav) with the High filter at 250 Hz, 4 kHz, 12 kHz, Lowpass at 250 Hz and 4 kHz, Low shelf at 200 Hz and 2 kHz, gain 0.4",
     "base": {**STATIC, **NET},
     "cases": [["hi-shelf-250", shelf("Shelf", 250)], ["hi-shelf-4k", shelf("Shelf", 4000)],
               ["hi-shelf-12k", shelf("Shelf", 12000)],
               ["hi-lowpass-250", shelf("Lowpass", 250)], ["hi-lowpass-4k", shelf("Lowpass", 4000)],
               ["lo-shelf-200", {"Diff. Lo On": ON, "Diff. Lo Freq": {"display": 200}, "LowShelf Gain": {"display": 0.4}}],
               ["lo-shelf-2k", {"Diff. Lo On": ON, "Diff. Lo Freq": {"display": 2000}, "LowShelf Gain": {"display": 0.4}}]]},

    {"name": "reverb-freeze-static", "plan": "9", "probe": "gap10", "read": ["impulse"], "priority": 2,
     "why": "what Freeze with Cut and Flat does when on from the first sample: does the impulse enter, does the tail sustain, do the shelves drain it",
     "question": "energy of the response to the impulse over 10 s with Freeze on at Cut/Flat on/off, both network filters on, against Freeze off",
     "base": {**STATIC, "Decay Time": {"norm": 0.5}, "Diff. Hi On": ON, "Diff. Lo On": ON, "Freeze On": ON},
     "cases": [["cut-noflat", {"Flat On": OFF}],
               ["nocut-flat", {"Cut On": OFF}],
               ["nocut-noflat", {"Cut On": OFF, "Flat On": OFF}],
               ["freeze-off", {"Freeze On": OFF}]]},

    {"name": "reverb-smooth-slow", "plan": "10", "probe": "gap2", "read": ["impulse"], "priority": 2,
     "why": "whether Size Smoothing Slow also ignores a Size set through the set (only Fast was tested); Size 1.53 and 10.54",
     "question": "early-reflection taps at Size 10.54 and 1.53 with Smooth None, Slow and Fast (the preset)",
     "base": {**STATIC, **ER_ONLY, **SHORT, "Room Size": {"display": 10.54}},
     "cases": [["none-10.54", {"Size Smoothing": {"item": "None"}}],
               ["slow-10.54", {"Size Smoothing": {"item": "Slow"}}],
               ["none-1.53", {"Size Smoothing": {"item": "None"}, "Room Size": {"display": 1.53}}],
               ["slow-1.53", {"Size Smoothing": {"item": "Slow"}, "Room Size": {"display": 1.53}}]]},

    {"name": "reverb-spin-grid", "plan": "4", "probe": "gap2", "read": ["modulation"], "priority": 3,
     "why": "Spin depth in ms against Rate and Amount at more points than the four measured (linearity in each, the 20 % uncertainty)",
     "question": "FM of the 1 kHz tone through the early reflections alone for Spin Amount x Rate pairs",
     "base": {**STATIC, **ER_ONLY, **SHORT, "ER Spin On": ON},
     "cases": [[f"spin-amt{a:g}-{r:g}Hz", {"ER Spin Amount": {"display": a}, "ER Spin Rate": {"display": r}}]
               for a, r in ((17.5, 0.07), (17.5, 0.6), (5, 1.3), (35, 0.15), (55, 1.3))]},

    {"name": "reverb-diffusion-size10", "plan": "7", "probe": "gap2", "read": ["impulse"], "priority": 3,
     "why": "Diffusion and Scale at a larger Size (Smooth None): echo density build-up and comb colouring, to separate them from Size",
     "question": "echo density over 0 to 0.5 s and the spectrum of the response for Diffusion 0.1 and 96 %, Scale 5 and 100 % at Size 10.54",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 10.54}},
     "cases": [["diffusion-0.1", {"Diffusion": {"display": 0.1}}], ["diffusion-96", {"Diffusion": {"display": 96}}],
               ["scale-5", {"Scale": {"display": 5}}], ["scale-100", {"Scale": {"display": 100}}]]},

    # ---- third set: Freeze and Size changed by automation lanes during the
    # render (make_als.py {"auto": ...}). On the gap10 probe the impulse is at 0.5 s (beat 1) and
    # the sweep starts at 10.5 s (beat 21).
    {"name": "reverb-freeze-toggle", "plan": "9", "probe": "gap10", "read": ["raw render (level over time)", "response"], "priority": 1,
     "why": "Freeze pressed after the impulse and released later: the loop's level over time, whether the sweep enters while frozen, Flat and Cut",
     "question": "Freeze on at beat 2 (1 s) and off at beat 40 (20 s), Decay 3.46 s: Flat off and on with Cut off, and Cut on",
     "base": dict(STATIC, **{"Decay Time": {"norm": 0.5},
                             "Freeze On": {"auto": [[0, OFF], [2, ON], [40, OFF]]}}),
     "cases": [["flat-off", {"Flat On": OFF, "Cut On": OFF}], ["flat-on", {"Flat On": ON, "Cut On": OFF}],
               ["cut-on", {"Flat On": OFF, "Cut On": ON}]]},

    {"name": "reverb-smooth-glide", "plan": "10", "probe": "gap2", "read": ["impulse (tap times against time)"], "priority": 1,
     "why": "the Size glide under Smooth None, Slow and Fast: Size jumps from 10 to 100 just before the impulse, so the early taps show where the glide is",
     "question": "early reflection taps of the impulse with Room Size jumping from 10 to 100 at beat 0.9 (45 ms before the impulse), each Size Smoothing",
     "base": dict(STATIC, **SHORT, **{"Room Size": {"auto": [[0, {"display": 10}], [0.9, {"display": 10}], [0.9, {"display": 100}]]}}),
     "cases": [[s.lower(), {"Size Smoothing": {"item": s}}] for s in ("None", "Slow", "Fast")]},
    # ---- network identification: the tail network read from
    # sparse arrivals. Diffusion 0.1 % leaves the allpasses as plain delays, Decay 60 s keeps every
    # pass at nearly full level, and Size 100 spreads the arrivals twice as far apart as the
    # Size 10.54 render did. Shape fades the direct taps at different rates, which tells the input
    # groups apart; Stereo 0 and the other Densities show which lines each side hears and how many.
    {"name": "reverb-network-id", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "the diffusion network's lines, input vectors and mixing matrix, which the Size 10.54 render left open (arrivals overlap there)",
     "question": "impulse response of the bare network (Diffusion 0.1 %, Decay 60 s, filters off, Size 100) for Shape 0 to 1, Stereo 0, each Density, with the reflections alone as reference",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 1.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY},
     "cases": [[f"shape-{v:g}", {"ER Shape": {"display": v}}] for v in (0, 0.25, 0.75, 1)]
     + [["er-only", ER_ONLY],
        ["stereo-0", {"Stereo Image": {"display": 0}}],
        ["diffusion-60", {"Diffusion": {"display": 60}}],
        ["scale-5", {"Diffusion": {"display": 60}, "Scale": {"display": 5}}]]
     + [[f"density-{d.lower()}", {"Density": {"item": d}}] for d in ("Sparse", "Mid", "High")]},
    # Each line's allpass grows with Scale while its delay does not, so at Diffusion 0.1 % every
    # arrival moves with Scale by the allpass lengths along its path: that tells apart lines fed the
    # same input (C1/C2, D1/D2 in the first run). Two more Sizes move the overlaps elsewhere.
    {"name": "reverb-network-scale", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "which line each arrival passed, from how far it moves with Scale; the mixing matrix of the network",
     "question": "impulse response of the bare network (as reverb-network-id) for Scale 5 to 100 %, and at Size 50 and 200 with their reflections alone",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 1.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY},
     "cases": [[f"scale-{v:g}", {"Scale": {"display": v}}] for v in (5, 20, 60, 80, 100)]
     + [c for z in (50, 200) for c in ([f"size-{z}", {"Room Size": {"display": z}}],
                                       [f"size-{z}-er-only", {"Room Size": {"display": z}, **ER_ONLY}])]},
    # A network fitted to the two runs above matches Live to about 280 ms and then loses the fine
    # structure. Two more renders of the base, beside its `default`, show whether Live renders the
    # same tail every time; if not, nothing past that point can be matched sample for sample.
    {"name": "reverb-network-repeat", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "whether the bare network's tail is the same from one render to the next",
     "question": "impulse response of the bare network (as reverb-network-id), rendered three times on three tracks",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 1.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY},
     "cases": [["repeat-1", {}], ["repeat-2", {}]]},
    # The measured network explains Live's right side only to about 0.27 s: there Live hears the
    # first two direct reflections again (13,045 frames in, 11 times the tail's rms) where the
    # network has nothing. Stereo 120 gives each side without the cross-mix. Shape tilts the
    # reflections' levels against the even fade, by +-0.17 dB/ms at Decay 0.2 s (+-9 dB from the
    # first direct reflection to the last), so with the even fade taken out each Shape is another
    # mix of the reflections' own responses, which can be solved for; Scale and Size move the
    # arrivals as in the runs above.
    {"name": "reverb-network-taps", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "the network's paths past 0.27 s, on each side apart and for each direct reflection apart",
     "question": "impulse response of the bare network (as reverb-network-id) with Stereo 120, at Scale 5 and 100 and Size 300, and at Decay 0.2 and 0.83 s for Shape 0, 0.5 and 1",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 1.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY,
              "Stereo Image": {"display": 120}},
     "cases": [[f"scale-{v:g}", {"Scale": {"display": v}}] for v in (5, 100)]
     + [["size-300", {"Room Size": {"display": 300}}]]
     + [[f"decay-{d}-shape-{v:g}", {"Decay Time": {"norm": n}, "ER Shape": {"display": v}}]
        for d, n in (("0.2s", 0.0), ("0.83s", 0.25)) for v in (0, 0.5, 1)]},
    # The return of reverb-network-taps (every direct reflection heard again on the right, A's and
    # G's lengths later) moves with Scale by both lines' allpasses, but at Diffusion 60 % its copies
    # come every G-allpass length, with none at A's own and the return at about one allpass gain:
    # which allpasses it passes, and in what order, is not settled. Stereo 120 keeps the right
    # apart; Scale 100 makes A's allpass 505 frames and G's 144, far apart from the input pairs'
    # 324-frame spacing; three Diffusions give the gain law.
    {"name": "reverb-network-allpass", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "the allpasses on the network's return path, and their gain against Diffusion",
     "question": "impulse response of the bare network (as reverb-network-taps, Stereo 120) at Diffusion 60 % and Scale 40 and 100, and at Diffusion 30 and 96 % with Scale 100",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, "Diffusion": {"display": 60},
              "Decay Time": {"norm": 1.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY,
              "Stereo Image": {"display": 120}},
     "cases": [["scale-100", {"Scale": {"display": 100}}]]
     + [[f"diffusion-{d:g}-scale-100", {"Diffusion": {"display": d}, "Scale": {"display": 100}}] for d in (30, 96)]},
    # Suhina's reverb sums the input to mono before the reflections and the network. Every render
    # above fed both sides the same, so a network that takes its right reflections from the right
    # input and its left ones from the left would look the same. Built with compare/build_set.py
    # and the impulse-left and impulse-right samples, not with a probe: the bare network with
    # Stereo 120, at Scale 40 and 100.
    {"name": "reverb-network-sides", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "whether the reflections and the network take the input in stereo, and from which side the right's return comes",
     "question": "impulse response of the bare network (as reverb-network-taps, Stereo 120) to an impulse on the left only and on the right only, at Scale 40 and 100",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 1.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY,
              "Stereo Image": {"display": 120}},
     "cases": [["scale-100", {"Scale": {"display": 100}}]]},
    # reverb-network-sides showed the input is summed to mono (left-only and right-only renders are
    # bit-identical), so the six input groups can only be told apart by Shape's tilt of the
    # reflections (0.336 dB per ms of a reflection's delay between Shape 0 and 1 at Decay 0.2 s).
    # Four Shapes at three Scales give each group's own response, Scale by Scale, to decode its paths.
    {"name": "reverb-network-groups", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "each input group's own response through the network, from Shape's tilt, at three Scales",
     "question": "impulse response of the bare network (as reverb-network-taps, Stereo 120) at Decay 0.2 s for Shape 0, 0.25, 0.75 and 1 at Scale 5, 40 and 100, and Shape 0.5 at 0.2 s and Shape 0 and 1 at 0.83 s for Scale 5 and 100 (reverb-network-taps has them at 40): seven tilts at every Scale",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 0.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY,
              "Stereo Image": {"display": 120}},
     "cases": [[f"scale-{c:g}-shape-{v:g}", {"Scale": {"display": c}, "ER Shape": {"display": v}}]
               for c in (5, 40, 100) for v in (0, 0.25, 0.75, 1)]
     + [[f"scale-{c:g}-shape-0.5", {"Scale": {"display": c}}] for c in (5, 100)]
     + [[f"scale-{c:g}-decay-0.83s-shape-{v:g}", {"Scale": {"display": c}, "Decay Time": {"norm": 0.25}, "ER Shape": {"display": v}}]
        for c in (5, 100) for v in (0, 1)]},
    # Shape's tilt cannot tell the input groups apart (groups 4 and 5, at 28.4 and 34.2 ms, differ
    # by under 0.5 dB over its whole range). Spin can: it swings each direct reflection's delay on
    # its own LFO by a share of that delay, and the network's input with it, so an impulse every 2 s
    # (compare/build_set.py with the impulse-train sample) catches every reflection at ten
    # different shifts. The reflections alone, with the same Spin, show each shift; Live restarts
    # the LFOs whenever playback starts. Decay 0.2 s, so each response has died before the next.
    # High Cut off: the direct reflections then reach 18 kHz while the filtered ones that follow
    # them stop near 8.6 kHz, so a high-pass leaves the direct ones alone to read the shifts from.
    {"name": "reverb-network-spin", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "each direct reflection's own response through the network, told apart by Spin's shift of it",
     "question": "responses of the bare network (Stereo 120, Diffusion 0.1 %, Decay 0.2 s) to an impulse every 2 s with Spin at 0.3 Hz and Amount 30, at Scale 5, 40 and 100, and the reflections alone",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 0.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY,
              "Stereo Image": {"display": 120}, "ER Spin On": ON, "ER Spin Rate": {"display": 0.3},
              "ER Spin Amount": {"display": 30}, "In Hi Cut On": OFF},
     "cases": [[f"scale-{c:g}", {"Scale": {"display": c}}] for c in (5, 100)]
     + [["er-only", {"Reflect Level": {"display": 0.0}, **ER_ONLY}]]},
    # The same at Spin Rate 0.37 Hz, so the LFOs reach other phases: with reverb-network-spin's
    # default case that is twenty impulses at Scale 40 %, enough to solve each of the ten direct
    # reflections' own responses and still test them on impulses left out.
    {"name": "reverb-network-spin2", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "each direct reflection's own response, not one per input group, from twenty impulses",
     "question": "reverb-network-spin's default and er-only cases with Spin Rate 0.37 Hz",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 0.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY,
              "Stereo Image": {"display": 120}, "ER Spin On": ON, "ER Spin Rate": {"display": 0.37},
              "ER Spin Amount": {"display": 30}, "In Hi Cut On": OFF},
     "cases": [["er-only", {"Reflect Level": {"display": 0.0}, **ER_ONLY}]]},
    # The network's coefficients, read exactly rather than from the peaks of low-passed bumps.
    # With Hi Cut off, Spin and Chorus off and Smooth None every delay settles on whole frames, so
    # at Diffusion 0.1 % each arrival is close to one sample whose value is a product of the
    # network's weights: one line gives its input weight times its output level, two lines the
    # mix entry between them as well. Each line's allpass grows with Scale at its own rate, so six
    # Scales move every path differently and overlapping arrivals can be solved together. The
    # reflections alone at Hi Cut off settle the 4-frame offset between the reflections and the
    # network (reverb-network-spin found it with Spin moving); Shape at Decay 0.83 s tilts each
    # arrival by its source reflection's delay, which tells a filtered reflection from its source.
    {"name": "reverb-network-exact", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "the network's input weights, mix and output levels as exact sample values, at six Scales",
     "question": "impulse response of the bare network (as reverb-network-taps, Stereo 120) with Hi Cut off at Scale 5, 20, 40, 60, 80 and 100 %, the reflections alone, and Shape 0, 0.5 and 1 at Decay 0.83 s",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 1.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY,
              "Stereo Image": {"display": 120}, "In Hi Cut On": OFF},
     "cases": [[f"scale-{c:g}", {"Scale": {"display": c}}] for c in (5, 20, 60, 80, 100)]
     + [["er-only", {"Reflect Level": {"display": 0.0}, **ER_ONLY}]]
     + [[f"decay-0.83s-shape-{v:g}", {"Decay Time": {"norm": 0.25}, "ER Shape": {"display": v}}] for v in (0, 0.5, 1)]},
    # Densities Sparse, Mid and High run networks Suhina has not read: Live's first arrivals come
    # 1,060 (Sparse) and 2,760 frames (Mid, High) after Suhina's, from reverb-network-id's single
    # renders, which have no reflections alone to deconvolve by. The same six Scales as
    # reverb-network-exact for each Density, and each Density's reflections alone.
    {"name": "reverb-network-density", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "the lines, input vectors and mixing matrix of the Sparse, Mid and High networks as exact sample values",
     "question": "impulse response of the bare network (as reverb-network-exact, Hi Cut off) at Density Sparse, Mid and High for Scale 5, 20, 40, 60, 80 and 100 %, and each Density's reflections alone",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 1.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY,
              "Stereo Image": {"display": 120}, "In Hi Cut On": OFF},
     "cases": [c for d in ("Sparse", "Mid", "High") for c in (
                   [[f"{d.lower()}-scale-{v:g}", {"Density": {"item": d}, "Scale": {"display": v}}] for v in (5, 20, 40, 60, 80, 100)]
                   + [[f"{d.lower()}-er-only", {"Density": {"item": d}, "Reflect Level": {"display": 0.0}, **ER_ONLY}]])]},
    # reverb-network-exact read Density Low's network at Size 100 only, and Suhina's tail at Size 1.53
    # and 10.54 comes out 0.3 to 1.6 dB loud. The same bare network at small Sizes, read sample by
    # sample: whether every length (lines, allpasses, entry, family offsets) scales with the size
    # factor, whether the gains do, and (with the High filter on) whether the damping is per pass of
    # a line or per second. Size 0.22 is the smallest, 50 sits between.
    {"name": "reverb-network-small", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "Density Low's network at small Sizes: lengths, gains and the damping's law against Size",
     "question": "impulse response of the bare network (as reverb-network-exact, Hi Cut off) at Size 1.53 and 10.54 for Scale 5, 40 and 100 %, the reflections alone, Decay 0.83 s and the High shelf at 4 kHz; at Size 0.22 and 50 the default and the reflections alone; and the High shelf at Size 100",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 1.53}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 1.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY,
              "Stereo Image": {"display": 120}, "In Hi Cut On": OFF},
     "cases": [c for z in (1.53, 10.54) for c in (
                   [[f"size-{z:g}-scale-{v:g}", {"Room Size": {"display": z}, "Scale": {"display": v}}] for v in (5, 40, 100)]
                   + [[f"size-{z:g}-er-only", {"Room Size": {"display": z}, "Reflect Level": {"display": 0.0}, **ER_ONLY}],
                      [f"size-{z:g}-decay-0.83s", {"Room Size": {"display": z}, "Decay Time": {"norm": 0.25}}],
                      [f"size-{z:g}-hi-shelf-4k", {"Room Size": {"display": z}, **shelf("Shelf", 4000)}]])]
     + [c for z in (0.22, 50) for c in (
                   [f"size-{z:g}", {"Room Size": {"display": z}}],
                   [f"size-{z:g}-er-only", {"Room Size": {"display": z}, "Reflect Level": {"display": 0.0}, **ER_ONLY}])]
     + [["size-100-hi-shelf-4k", {"Room Size": {"display": 100}, **shelf("Shelf", 4000)}]]},
    # In reverb-network-small, A, B, D and F follow one law per line (whole 8-frame blocks, the
    # allpass floored on its own), but C and R miss it at low Scales: C is one or two blocks short at
    # Scale 5 at Size 10.54 and 1.53, R one long at Size 100, Scale 5 and 20. With Diffusion at 30 %
    # each allpass section echoes a pass at -g, 1 - g^2, g(1 - g^2) ... one section length apart, so
    # the sections inside C and R (and how each rounds) show as the spacing of the copies around
    # their first passes. The same Sizes and Scales the misses came from, with Scale 40 and 100 as
    # controls, and Diffusion 60 at Size 100 to check the copies' gains against the setting.
    {"name": "reverb-network-sections", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "the allpass sections inside Density Low's C and R lines, and how each rounds with Size and Scale",
     "question": "impulse response of the bare network (as reverb-network-small) with Diffusion 30 % at Size 100 for Scale 5, 20 and 100, at Size 10.54 and 1.53 for Scale 5, 40 and 100, and with Diffusion 60 % at Size 100 and Scale 100",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, "Diffusion": {"display": 30},
              "Decay Time": {"norm": 1.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY,
              "Stereo Image": {"display": 120}, "In Hi Cut On": OFF},
     "cases": [[f"size-{z:g}-scale-{v:g}", {"Room Size": {"display": z}, "Scale": {"display": v}}]
               for z, scales in ((100, (5, 20, 100)), (10.54, (5, 40, 100)), (1.53, (5, 40, 100))) for v in scales]
     + [["size-100-scale-100-diffusion-60", {"Scale": {"display": 100}, "Diffusion": {"display": 60}}]]},
    # Under Smooth Fast Live's tail at Size 1.53 loses about 1 dB more than under None from its first
    # arrivals, its delays run a few frames short, and its reflections come 4 or 9 to 10 frames
    # early (reverb-impulse set, Fast cases against their reverb-size twins). The bare network of
    # reverb-network-small with Smooth Fast, read sample by sample, shows how Fast reads each line
    # (fractions of a frame, the interpolation and its loss) and each reflection. Scale 5 and 100 at
    # Size 1.53 move the allpasses apart from the delays; Smooth None at Size 1.53 repeats
    # reverb-network-small's size-1.53-scale-40 (it should be bit-identical), and Slow is the
    # other smoothing mode.
    {"name": "reverb-network-fast", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "how Smooth Fast changes Density Low's network and reflections, sample by sample, in small and large rooms",
     "question": "impulse response of the bare network (as reverb-network-small, Hi Cut off, Diffusion 0.1 %, Decay 60 s) with Smooth Fast at Size 1.53, 10.54 and 100 (Scale 40 %), Scale 5 and 100 % at Size 1.53, the reflections alone at each Size, and Size 1.53 with Smooth None and Slow",
     "base": {**STATIC, "Size Smoothing": {"item": "Fast"}, "Room Size": {"display": 1.53}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 1.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY,
              "Stereo Image": {"display": 120}, "In Hi Cut On": OFF},
     "cases": [[f"size-1.53-scale-{v:g}", {"Scale": {"display": v}}] for v in (5, 100)]
     + [c for z in (1.53, 10.54, 100) for c in (
           ([[f"size-{z:g}", {"Room Size": {"display": z}}]] if z != 1.53 else [])
           + [[f"size-{z:g}-er-only", {"Room Size": {"display": z}, "Reflect Level": {"display": 0.0}, **ER_ONLY}]])]
     + [["size-1.53-smooth-none", {"Size Smoothing": {"item": "None"}}],
        ["size-1.53-smooth-slow", {"Size Smoothing": {"item": "Slow"}}]]},
    # Under Smooth Fast Live's lines are fractions of a frame long (A and B read between frames) and
    # keep moving after an impulse (reverb-network-fast): a network fixed at the first passes'
    # lengths matches only the first 0.1 s. An impulse every 0.5 s (compare/samples/
    # impulse-train-fast.wav) reads each line's length and fraction from its first pass at 39
    # times. Decay 0.83 s, so each response is about 40 dB down before the next impulse; None at
    # Size 1.53 and 100 should give the same lengths at every impulse.
    {"name": "reverb-network-fast-train", "plan": "7", "probe": "gap10", "read": ["impulse train (arrivals per impulse)"], "priority": 1,
     "why": "how Smooth Fast's line lengths move over time, from each impulse's first passes",
     "question": "responses of the bare network (as reverb-network-fast, Decay 0.83 s) to an impulse every 0.5 s, with Smooth Fast at Size 1.53, 10.54 and 100, each Size's reflections alone, and Smooth None at Size 1.53 and 100",
     "base": {**STATIC, "Size Smoothing": {"item": "Fast"}, "Room Size": {"display": 1.53}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 0.25}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY,
              "Stereo Image": {"display": 120}, "In Hi Cut On": OFF},
     "cases": [[f"size-{z:g}", {"Room Size": {"display": z}}] for z in (10.54, 100)]
     + [[f"size-{z:g}-er-only", {"Room Size": {"display": z}, "Reflect Level": {"display": 0.0}, **ER_ONLY}] for z in (1.53, 10.54, 100)]
     + [[f"size-{z:g}-smooth-none", {"Room Size": {"display": z}, "Size Smoothing": {"item": "None"}}] for z in (1.53, 100)]},
    # In Live's bare network each line has its own High Shelf, as long as the line, and the input none
    # (reverb-network-small hi-shelf-4k, each line's filter a pass solved as a short FIR). The
    # Low-Pass is not like that: in reverb-filters and reverb-network-freq every line's first pass
    # carries one whole one-pole at the set frequency, and the loop then loses far less, unevenly
    # between the sides. The bare network with the Low-Pass at three frequencies (Size 10.54, so
    # each line's passes stand apart), 1 kHz at Size 1.53 and 100 for how it scales with the
    # lines, and a Low Shelf and a 1 kHz High Shelf to check those are per line too; each Size's
    # reflections alone to deconvolve by.
    {"name": "reverb-network-filters", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "where Density Low's network damping sits (input or lines, which lines) and its response a pass, for the Low-Pass above all",
     "question": "impulse response of the bare network (as reverb-network-small, Hi Cut off, Diffusion 0.1 %, Decay 60 s, Smooth None) at Size 10.54 with the Low-Pass at 250 Hz, 1 kHz and 4 kHz, the Low Shelf at 500 Hz gain 0.2 and the High Shelf at 1 kHz gain 0.2; the Low-Pass at 1 kHz at Size 1.53 and 100; each Size with filters off and its reflections alone",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 10.54}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 1.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY,
              "Stereo Image": {"display": 120}, "In Hi Cut On": OFF},
     "cases": [[f"size-{z:g}-lowpass-{f:g}", {"Room Size": {"display": z}, **shelf("Lowpass", f)}]
               for z, f in ((10.54, 250), (10.54, 1000), (10.54, 4000), (1.53, 1000), (100, 1000))]
     + [["size-10.54-lo-shelf-500-g0.2", {"Diff. Lo On": ON, "Diff. Lo Freq": {"display": 500}, "LowShelf Gain": {"display": 0.2}}],
        ["size-10.54-hi-shelf-1000-g0.2", shelf("Shelf", 1000, 0.2)]]
     + [c for z in (1.53, 10.54, 100) for c in (
           [f"size-{z:g}", {"Room Size": {"display": z}}],
           [f"size-{z:g}-er-only", {"Room Size": {"display": z}, "Reflect Level": {"display": 0.0}, **ER_ONLY}])]},
    # reverb-network-filters read Density Low's damping (a whole one-pole of the Low-Pass a pass in
    # every line, cookbook shelves with a loss proportional to the line's length). Sparse, Mid and
    # High keep Low's law in Suhina and their highs decay 1.5 to 3.6 dB/s too slowly at the default
    # damping (reverb-texture density-*, Decay 1 s), so the same cases at each Density, and the
    # default damping at three Sizes.
    {"name": "reverb-network-density-filters", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "the damping of the Sparse, Mid and High networks: the Low-Pass and shelves a pass, and their law against Size, as Density Low's",
     "question": "impulse response of the bare network (as reverb-network-filters, Hi Cut off, Diffusion 0.1 %, Decay 60 s, Smooth None) at Density Sparse, Mid and High: at Size 10.54 the Low-Pass at 250 Hz, 1 kHz and 4 kHz, the Low Shelf at 500 Hz gain 0.2 and the High Shelf at 1 kHz gain 0.2; the Low-Pass at 1 kHz at Size 1.53 and 100; the High Shelf at 4 kHz at Size 1.53, 10.54 and 100; the default damping at Size 1.53, 10.54 and 100; each Size with filters off and its reflections alone",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 10.54}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 1.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY,
              "Stereo Image": {"display": 120}, "In Hi Cut On": OFF},
     "cases": [c for d in ("Sparse", "Mid", "High") for c in (
                   [[f"{d.lower()}-size-{z:g}-lowpass-{f:g}", {"Density": {"item": d}, "Room Size": {"display": z}, **shelf("Lowpass", f)}]
                    for z, f in ((10.54, 250), (10.54, 1000), (10.54, 4000), (1.53, 1000), (100, 1000))]
                   + [[f"{d.lower()}-size-10.54-lo-shelf-500-g0.2", {"Density": {"item": d}, "Diff. Lo On": ON,
                                                                      "Diff. Lo Freq": {"display": 500}, "LowShelf Gain": {"display": 0.2}}],
                      [f"{d.lower()}-size-10.54-hi-shelf-1000-g0.2", {"Density": {"item": d}, **shelf("Shelf", 1000, 0.2)}]]
                   + [[f"{d.lower()}-size-{z:g}-hi-shelf-4k", {"Density": {"item": d}, "Room Size": {"display": z}, **shelf("Shelf", 4000)}]
                      for z in (1.53, 10.54, 100)]
                   + [[f"{d.lower()}-size-{z:g}-default-damping", {"Density": {"item": d}, "Room Size": {"display": z},
                                                                   "Diff. Hi On": ON, "Diff. Lo On": ON}]
                      for z in (1.53, 10.54, 100)]
                   + [c for z in (1.53, 10.54, 100) for c in (
                         [f"{d.lower()}-size-{z:g}", {"Density": {"item": d}, "Room Size": {"display": z}}],
                         [f"{d.lower()}-size-{z:g}-er-only", {"Density": {"item": d}, "Room Size": {"display": z},
                                                              "Reflect Level": {"display": 0.0}, **ER_ONLY}])])]},
    # With reverb-network-density-filters Mid and High match Live at Decay 60 s with the default damping,
    # yet at the default Decay (reverb-texture density-mid and -high, Size 100) their 8 to 16 kHz
    # decays 1.4 to 1.6 dB/s too slowly. Decay, Diffusion and damping apart, on the bare network.
    {"name": "reverb-network-density-decay", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "what makes the top octave of the Mid and High networks decay faster in Live at a short Decay: the Decay, the Diffusion or the damping",
     "question": "impulse response of the bare network (Size 100, Hi Cut off, Smooth None, Stereo 120, reflections off) at Density Mid and High for the default Decay, 0.83 s, 3.46 s and 60 s, each with Diffusion 0.1 % and the default 60 %, and with the damping off and on (default settings); each Density's reflections alone",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, **TAIL_ONLY,
              "Stereo Image": {"display": 120}, "In Hi Cut On": OFF},
     "cases": [c for d in ("Mid", "High") for c in (
                   [[f"{d.lower()}-decay-{dn}-diffusion-{fn}-damping-{mn}",
                     {"Density": {"item": d}, **dec, **fd, "Diff. Hi On": mv, "Diff. Lo On": mv}]
                    for dn, dec in (("default", {}), ("0.83s", {"Decay Time": {"norm": 0.25}}),
                                    ("3.46s", {"Decay Time": {"norm": 0.5}}), ("60s", {"Decay Time": {"norm": 1.0}}))
                    for fn, fd in (("0.1", {"Diffusion": {"display": 0.1}}), ("60", {}))
                    for mn, mv in (("off", OFF), ("on", ON))]
                   + [[f"{d.lower()}-er-only", {"Density": {"item": d}, "Reflect Level": {"display": 0.0}, **ER_ONLY}]])]},
    # `reverb-decay decay-14.4s` keeps the preset's Smooth Fast, under which Live's network runs a
    # little short (up to 11 frames by 0.25 s against Smooth None), so it cannot be matched sample
    # for sample by a network measured with Smooth None. The same case with Smooth None, its
    # reflections alone to take them out, and the Fast case again as the control.
    {"name": "reverb-decay-none", "plan": "5", "probe": "gap30", "read": ["impulse (.ir.wav)", "impulse.rt60_s"], "priority": 1,
     "why": "the tail at a real decay (14.4 s, the preset's other values) with Smooth None, to compare the measured network against",
     "question": "impulse response of decay-14.4s (as reverb-decay, filters off, Reflect at its minimum) with Smooth None, with its reflections alone, and with Smooth Fast",
     "base": {**SMALL_SMOOTH_NONE, "Decay Time": {"norm": 0.75}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY},
     "cases": [["er-only", ER_ONLY], ["smooth-fast", {"Size Smoothing": {"item": "Fast"}}]]},
    # Solved from the reflections alone, every copy is one tap through a Q 0.5 low-pass, at 11.9 kHz
    # at Decay 60 s, but at 1.2 s Mid's and High's (Hi Cut off) sit at 8.4 and 8.9 kHz while Low's
    # (reverb-size size-100-er, Hi Cut on) sits at 11.25 kHz. Either the corner follows the Density
    # or Hi Cut changes the copies' path (the copy model fits poorly whenever Hi Cut is on). Each
    # Density's reflections alone over Decay with Hi Cut off, and Low and Mid at 1.2 s with Hi Cut on.
    {"name": "reverb-er-decay", "plan": "7", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "the law of the reflections' low-pass against Decay, and whether it depends on the Density or on Hi Cut",
     "question": "impulse response of the reflections alone (Size 100, Hi Cut off, Spin off, Smooth None, Stereo 120, Diffusion 0.1 %) at Density Sparse, Low, Mid and High for Decay 0.2 s, 0.83 s, 1.2 s (default), 3.46 s, 14.4 s and 60 s; and Low and Mid at 1.2 s with Hi Cut on",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, "Diffusion": {"display": 0.1},
              "Stereo Image": {"display": 120}, "In Hi Cut On": OFF, "Reflect Level": {"display": 0.0}, **ER_ONLY},
     "cases": [[f"{d.lower()}-decay-{dn}", {"Density": {"item": d}, **dec}]
               for d in ("Sparse", "Low", "Mid", "High")
               for dn, dec in (("0.2s", {"Decay Time": {"norm": 0.0}}), ("0.83s", {"Decay Time": {"norm": 0.25}}),
                               ("1.2s", {}), ("3.46s", {"Decay Time": {"norm": 0.5}}),
                               ("14.4s", {"Decay Time": {"norm": 0.75}}), ("60s", {"Decay Time": {"norm": 1.0}}))]
              + [[f"{d.lower()}-decay-1.2s-hi-cut", {"Density": {"item": d}, "In Hi Cut On": ON}] for d in ("Low", "Mid")]},
    # Live's reflections come later as Stereo falls from 120, while the tail stays put and Hi Cut adds
    # only its filter's own delay (reflections alone against Stereo 120: 8 frames at Stereo 100 and 32
    # at 0 under Smooth None; 4, 13 and 27 at 100, 60 and 0 under Fast). The 8 frames Decision 24 put
    # on Hi Cut were Stereo 100's. The delay's law over Stereo under each Smooth, whether it moves with
    # Size, Density or Predelay, that Hi Cut leaves it alone, and that the tail does not move.
    {"name": "reverb-er-stereo", "plan": "11", "probe": "gap10", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "the law of the reflections' delay against Stereo under Smooth None and Fast, and what else moves it",
     "question": "impulse response of the reflections alone (Size 100, Hi Cut off, Spin off, Diffusion 0.1 %, Decay 60 s) at Stereo 0 to 120 under Smooth None and Fast, and Slow at three; at Stereo 0, 60 and 120 at Size 10.54, Density Mid and Predelay 50 ms (None); Hi Cut on at Stereo 60; and the bare network at Stereo 0, 60 and 120 (None)",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 1.0}, "In Hi Cut On": OFF, "Reflect Level": {"display": 0.0}, **ER_ONLY},
     "cases": [[f"{sm.lower()}-stereo-{st:g}", {"Size Smoothing": {"item": sm}, "Stereo Image": {"display": st}}]
               for sm in ("None", "Fast")
               for st in (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 105, 110, 115, 119, 120)]
              + [[f"slow-stereo-{st:g}", {"Size Smoothing": {"item": "Slow"}, "Stereo Image": {"display": st}}]
                 for st in (0, 60, 100)]
              + [[f"{name}-stereo-{st:g}", {**extra, "Stereo Image": {"display": st}}]
                 for name, extra in (("size-10.54", {"Room Size": {"display": 10.54}}),
                                     ("mid", {"Density": {"item": "Mid"}}),
                                     ("predelay-50ms", {"Predelay": {"display": 0.05}}))
                 for st in (0, 60, 120)]
              + [["hi-cut-stereo-60", {"In Hi Cut On": ON, "Stereo Image": {"display": 60}}]]
              + [[f"tail-stereo-{st:g}", {**TAIL_ONLY, "Diffuse Level": {"display": 0.0}, "Diff. Hi On": OFF,
                                          "Diff. Lo On": OFF, "Stereo Image": {"display": st}}]
                 for st in (0, 60, 120)]},
    # Suhina's tail hissed in and out at the Chorus rate (reverb-texture chorus-amt2-4Hz on white
    # noise), and Spin a little, while Live's did not; the texture run has them at Low only. The same
    # Chorus and Spin cases at each Density, to listen to and to read the highs' ripple from.
    {"name": "reverb-modulation-density", "plan": "8", "probe": "gap10", "read": ["noise (the highs' level against time)"], "priority": 1,
     "why": "whether the highs of the tail and reflections rise and fall at the Chorus and Spin rates at each Density",
     "question": "the level above 6 and 12 kHz against time of the tail alone (Decay 3.46 s) with Chorus Amount 2 at 1 and 4 Hz, and of the reflections alone with Spin Amount 17.5 at 0.3 Hz and 55 at 1.3 Hz, at Density Sparse, Low, Mid and High",
     "base": STATIC,
     "cases": [[f"{d.lower()}-{name}", {"Density": {"item": d}, **params}]
               for d in ("Sparse", "Low", "Mid", "High")
               for name, params in (
                   *((f"chorus-amt2-{r:g}Hz", {"Chorus On": ON, **TAIL_ONLY, "Decay Time": {"norm": 0.5},
                                               "Chorus Amount": {"display": 2}, "Chorus Rate": {"display": r}})
                     for r in (1, 4)),
                   *((f"spin-amt{a:g}-{r:g}Hz", {"ER Spin On": ON, "Diffuse Level": {"norm": 0.0},
                                                 "ER Spin Amount": {"display": a}, "ER Spin Rate": {"display": r}})
                     for a, r in ((17.5, 0.3), (55, 1.3))))]},
    # Every length so far was read at 44.1 kHz. Converted to 48 kHz a few are round there and only
    # there (Low's A line 2500 samples, two of Mid's and High's allpasses 600 and 700), and A and B
    # are the lines Live reads between frames under Fast. The same bare-network cases at 48 and
    # 96 kHz show whether Live converts its lengths by time, whether A and B are whole samples at
    # 48 kHz, and whether Smooth None's blocks are 8 samples at the session's rate. Both runs go in
    # one set, exported with Live's audio at each rate; only the run whose probe is at the export's
    # rate is read from it (the other's probe is resampled, so its impulse is not one sample).
    {"name": "reverb-rate-48k", "plan": "14", "probe": "gap10-48k", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "the network's lengths, Stereo's delay and the Shape entry at 48 kHz, against their 44.1 kHz reads",
     "question": "impulse response at 48 kHz of the bare network (as reverb-network-exact, Hi Cut off, Diffusion 0.1 %, Decay 60 s) under Smooth None and Fast at Size 1.53, 10.54 and 100, Mid and High at Diffusion 60 % and Scale 100 %, each with its reflections alone; the reflections alone at Stereo 0 and 60; Shape 0, 0.25, 0.5 and 1 at Decay 0.83 s",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 1.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY,
              "Stereo Image": {"display": 120}, "In Hi Cut On": OFF},
     "cases": rate_cases()},
    {"name": "reverb-rate-96k", "plan": "14", "probe": "gap10-96k", "read": ["impulse (.ir.wav arrivals)"], "priority": 1,
     "why": "the network's lengths, Stereo's delay and the Shape entry at 96 kHz, against their 44.1 kHz reads",
     "question": "impulse response at 96 kHz of the bare network (as reverb-network-exact, Hi Cut off, Diffusion 0.1 %, Decay 60 s) under Smooth None and Fast at Size 1.53, 10.54 and 100, Mid and High at Diffusion 60 % and Scale 100 %, each with its reflections alone; the reflections alone at Stereo 0 and 60; Shape 0, 0.25, 0.5 and 1 at Decay 0.83 s",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 100}, "Diffusion": {"display": 0.1},
              "Decay Time": {"norm": 1.0}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY,
              "Stereo Image": {"display": 120}, "In Hi Cut On": OFF},
     "cases": rate_cases()},
]
