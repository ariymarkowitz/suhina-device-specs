# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Scale behaviour runs for tools/harness/midi_set.py (see its docstring for the format).
Plan steps refer to live-12/midi-effects/30.07-scale.md › Measurement plan.

The grid is written as the twelve Map parameters (Map n = the row the column of pitch class
n above Base points to, -1 none, 12 the top C). A preset (Scale Name) is written as its
InternalScale index with the Maps left at the identity: whether Live recomputes the Maps from
it on loading shows in `verify` (Map n differs from the default) and in the recording.

Not taken: the LED and the effective Base / Scale Name display (step 8, view only), a clip's
scale changed during playback (step 8: one clip per track), per-note expression and CCs
(step 10: the set builder writes neither)."""

DEVICE = "Scale"

ALL = {"length": 64, "notes": [[p, p / 2, 0.25, 100] for p in range(128)]}
CHROMATIC = [[60 + i, i / 2, 0.25, 100] for i in range(13)]
SCALE_NAMES = ["Major", "Minor", "Dorian", "Mixolydian", "Lydian", "Phrygian", "Locrian",
               "Whole Tone", "Half-whole Dim.", "Whole-half Dim.", "Minor Blues",
               "Minor Pentatonic", "Major Pentatonic", "Harmonic Minor", "Harmonic Major",
               "Dorian #4", "Phrygian Dominant", "Melodic Minor", "Lydian Augmented",
               "Lydian Dominant", "Super Locrian", "8-Tone Spanish", "Bhairav",
               "Hungarian Minor", "Hirajoshi", "In-Sen", "Iwato", "Kumoi", "Pelog Selisir",
               "Pelog Tembung", "Messiaen 3", "Messiaen 4", "Messiaen 5", "Messiaen 6",
               "Messiaen 7"]


def maps(**cols):
    """Map parameters from column=row pairs, e.g. maps(m0=2)."""
    return {f"Map {k[1:]}": v for k, v in cols.items()}


def slug(name):
    return name.lower().replace(" ", "-").replace(".", "").replace("#", "s")


def chromatic(scale):
    return {"length": 7, "notes": CHROMATIC, "scale": scale}


RUNS = [
    {"name": "scale-grid", "plan": "1, 3, 4",
     "question": "User grid at Base C on every pitch: C -> D, C -> top C (Map 12), C -> none (Map -1), and the descending diagonal (the default case is the identity)",
     "clip": ALL, "base": {},
     "cases": [["c-to-d", maps(m0=2)], ["c-to-top", maps(m0=12)], ["c-none", maps(m0=-1)],
               ["diagonal", {f"Map {i}": 11 - i for i in range(12)}]]},

    {"name": "scale-base", "plan": "2",
     "question": "the C -> D grid (column 0 to row 2) at Base D and F#: do the squares move with Base, and which octave anchors the grid",
     "clip": ALL, "base": maps(m0=2),
     "cases": [["base-d", {"Base": 2}], ["base-fs", {"Base": 6}], ["identity-base-d", dict(maps(m0=0), Base=2)]]},

    {"name": "scale-presets", "plan": "5",
     "question": "each Scale Name at Base C (and Major and Minor Pentatonic at Base D): output pitch class for every input, and whether the Maps follow the preset",
     "clip": ALL, "base": {},
     "cases": [[slug(n), {"InternalScale": {"item": n}}] for n in SCALE_NAMES] +
              [["major-base-d", {"InternalScale": {"item": "Major"}, "Base": 2}],
               ["minor-pentatonic-base-d", {"InternalScale": {"item": "Minor Pentatonic"}, "Base": 2}]]},

    {"name": "scale-fold", "plan": "6",
     "question": "Fold with C -> A, C# -> B, D -> G#; Fold on and off (default off); C -> F# and C -> G (6 and 7 above) with Fold on; Transpose +7 with Fold on",
     "clip": ALL, "base": maps(m0=9, m1=11, m2=8),
     "cases": [["fold", {"Fold": {"item": "On"}}],
               ["c-to-fs", dict(maps(m0=6, m1=1, m2=2))], ["c-to-fs-fold", dict(maps(m0=6, m1=1, m2=2), Fold={"item": "On"})],
               ["c-to-g", dict(maps(m0=7, m1=1, m2=2))], ["c-to-g-fold", dict(maps(m0=7, m1=1, m2=2), Fold={"item": "On"})],
               ["fold-transpose+7", {"Fold": {"item": "On"}, "Transpose": 7}]]},

    {"name": "scale-window", "plan": "7",
     "question": "Transpose -36, -1, +1, +7, +36 on the identity; Lowest C2 Range 36 (the manual's example) at Transpose 0 and +7; Range 1, 12, 127 at Lowest 100; window before or after the grid (C -> top C with the window starting at C#3)",
     "clip": ALL, "base": {},
     "cases": [[f"transpose{t:+d}", {"Transpose": t}] for t in (-36, -1, 1, 7, 36)] +
              [["c2-36", {"Lowest": 48, "Range": 36}], ["c2-36-transpose+7", {"Lowest": 48, "Range": 36, "Transpose": 7}]] +
              [[f"lowest100-range{r}", {"Lowest": 100, "Range": r}] for r in (1, 12, 127)] +
              [["window-after-grid", dict(maps(m0=12), Lowest=61, Range=12)]]},

    {"name": "scale-current", "plan": "8; common C4",
     "question": "Use Current Scale on C3..C4 chromatic with the clip's scale C major, D minor, A minor pentatonic and none; Fold with D minor",
     "clip": chromatic(["C", "Major"]), "base": {"Use Current Scale": {"item": "On"}},
     "cases": [["d-minor", {}, {"clip": chromatic(["D", "Minor"])}],
               ["a-minor-pentatonic", {}, {"clip": chromatic(["A", "Minor Pentatonic"])}],
               ["no-scale", {}, {"clip": chromatic(None)}],
               ["d-minor-fold", {"Fold": {"item": "On"}}, {"clip": chromatic(["D", "Minor"])}]]},

    {"name": "scale-noteoff", "plan": "9",
     "question": "C3, C#3, E3 together for a bar then in an overlapping staircase, with C# -> C (two inputs onto one output); a held C3 while Transpose steps 0 -> +5 and Base 0 -> 2 at beat 2",
     "clip": {"length": 12, "notes": [[60, 0, 4, 100], [61, 0, 4, 100], [64, 0, 4, 100],
                                      [60, 5, 2, 100], [61, 6, 2, 100], [64, 7, 2, 100]]},
     "base": maps(m1=0),
     "cases": [["transpose-step", maps(m1=1), {"automation": {"Transpose": [[0, 0], [2, 5]]},
                                                "clip": {"length": 6, "notes": [[60, 0, 4, 100]]}}],
               ["base-step", dict(maps(m1=1), **maps(m0=2)), {"automation": {"Base": [[0, 0], [2, 2]]},
                                                               "clip": {"length": 6, "notes": [[60, 0, 4, 100]]}}]]},
]
