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
    # `reverb-decay decay-14.4s` keeps the preset's Smooth Fast, under which Live's network runs a
    # little short (up to 11 frames by 0.25 s against Smooth None), so it cannot be matched sample
    # for sample by a network measured with Smooth None. The same case with Smooth None, its
    # reflections alone to take them out, and the Fast case again as the control.
    {"name": "reverb-decay-none", "plan": "5", "probe": "gap30", "read": ["impulse (.ir.wav)", "impulse.rt60_s"], "priority": 1,
     "why": "the tail at a real decay (14.4 s, the preset's other values) with Smooth None, to compare the measured network against",
     "question": "impulse response of decay-14.4s (as reverb-decay, filters off, Reflect at its minimum) with Smooth None, with its reflections alone, and with Smooth Fast",
     "base": {**SMALL_SMOOTH_NONE, "Decay Time": {"norm": 0.75}, "Diff. Hi On": OFF, "Diff. Lo On": OFF, **TAIL_ONLY},
     "cases": [["er-only", ER_ONLY], ["smooth-fast", {"Size Smoothing": {"item": "Fast"}}]]},
]
