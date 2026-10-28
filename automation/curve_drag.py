# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""How Live 12 splits a bent automation segment and how dragging a curve moves its handles.

Three sets, all automating Utility's Gain on the Operator track (see README.md here):

- utility-gain-splits: bars 1-4 are bent segments; bars 5-8 are the same segments, each split by a
  point placed on it; bar 9 is split segments reshaped by hand.
- curve-drag: 4 copies of 14 starting curves (CURVES below), each copy dragged by hand by a
  different amount, one drag per segment.
- curve-drag-lopsided: 4 copies of 12 lopsided S curves and curves that cross the diagonal
  (LOPSIDED below); copies 1-3 one drag each, copy 4 two drags in the same direction.

The drag plan, per segment (Alt/Option-drag the curve, never the points): copy 1 a little one
way, copy 2 a lot the same way, copy 3 a lot the other way, copy 4 the same way as copy 2 (in the
lopsided set as two drags, letting go while the curve is an S). Save the set and Bounce the
Operator track (Arrangement, the whole song) for analyse.py.

Usage (numpy only):

    tools/.venv/bin/python automation/curve_drag.py make <set> <out-dir>
        writes the two starting sets (curve-drag.start.als, curve-drag-lopsided.start.als) from a
        set like sets/utility-gain-splits.als, to drag again in Live
    tools/.venv/bin/python automation/curve_drag.py analyse
        checks the splits and replays every drag through the rule in automation.md; writes
        live/utility-gain-splits.splits.json, live/curve-drag.drags.json and
        live/curve-drag-lopsided.drags.json

The handle coordinates (the rule itself is written up in live-12/automation.md › Dragging a curve):
each handle lies on a path (0, 1) -> (p, p) -> (1, 0); F is 0, 1 and 2 at those three points.
"""

import gzip
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
UTILITY_GAIN = "22587"  # the PointeeId of Utility's Gain in these sets
STEP = 1 / 64           # one step of a drag, in F
TOL = 1e-4

# --- handle coordinates ----------------------------------------------------------------------


def handle(p, F):
    """The handle at F on the path (0, 1) -> (p, p) -> (1, 0)."""
    if F <= 1:
        return (F * p, 1 - F * (1 - p))
    g = F - 1
    return (p + g * (1 - p), p * (1 - g))


def coord(h):
    """(p, F) of a handle; p is None on the diagonal (any p) and in the corners (0,1) and (1,0)."""
    x, y = h
    if (abs(x) < 1e-9 and abs(y - 1) < 1e-9):
        return None, 0.0
    if (abs(x - 1) < 1e-9 and abs(y) < 1e-9):
        return None, 2.0
    if abs(x - y) < 1e-9:
        return x, 1.0                                   # on the diagonal: its own point
    if y > x:                                           # above the diagonal: the leg from (0, 1)
        if abs(y - 1) < 1e-9:
            return 1.0, x                               # top edge
        if abs(x) < 1e-9:
            return 0.0, 1 - y                           # left edge
        q = x / (x + 1 - y)
        return q, x / q
    if abs(x - 1) < 1e-9:
        return 1.0, 2 - y                               # right edge
    if abs(y) < 1e-9:
        return 0.0, 1 + x                               # bottom edge
    q = y / (y + 1 - x)                                 # below: the leg to (1, 0)
    return q, 1 + (x - q) / (1 - q)


def vcurve(p1, F1, p2, F2):
    return tuple(round(v, 6) for v in handle(p1, F1) + handle(p2, F2))


# --- the drag rule ---------------------------------------------------------------------------


def start_paths(curve):
    """p and F of both handles at the start of a drag. A straight segment, or one whose handles
    are both on the diagonal or both in corners, starts on Live's own family (p = 1/4, 3/4)."""
    if curve is None:
        return [0.25, 0.75], [1.0, 1.0]
    (p1, F1), (p2, F2) = coord(curve[:2]), coord(curve[2:])
    straight = F1 == 1 and F2 == 1
    if straight or (p1 is None and p2 is None):
        return [0.25, 0.75], [F1, F2]
    # One handle in a corner: no data says which path it takes; Live's family is the guess.
    return [0.25 if p1 is None else p1, 0.75 if p2 is None else p2], [F1, F2]


def side(F):
    return (F > 1 + 1e-9) - (F < 1 - 1e-9)


def drag(p, F, steps):
    """F after one drag of `steps` (signed; + is the later direction). The mode is chosen at the
    start: both handles on one side of the diagonal (or both on it) move together, otherwise
    apart (the handle with the larger F follows the drag, the other goes the opposite way). A
    handle that would pass 0 or 2 stops there; a step that no handle can take in full is not
    taken."""
    F = list(F)
    same = side(F[0]) == side(F[1])
    if same:
        sign = [1, 1]
    else:
        sign = [1, -1] if F[0] >= F[1] else [-1, 1]
    d = STEP if steps > 0 else -STEP
    for _ in range(abs(steps)):
        new = [F[i] + sign[i] * d for i in range(2)]
        if not any(0 <= v <= 2 for v in new):
            break
        F = [min(2.0, max(0.0, v)) for v in new]
    return F, "same" if same else "opposite"


def close(curve, p, F):
    c = handle(p[0], F[0]) + handle(p[1], F[1])
    return all(abs(a - b) < TOL for a, b in zip(c, curve))


def fit(start, got, drags):
    """The shortest drag (fewest steps in all) that turns `start` into `got` under the rule, or
    None. A drag that ended against a clamp fits any longer drag too; `clamped` says so."""
    p, F0 = start_paths(start)
    if drags == 1:
        for n in sorted(range(-130, 131), key=abs):
            F, mode = drag(p, F0, n)
            if close(got, p, F):
                clamped = close(got, p, drag(p, F0, n + (1 if n >= 0 else -1))[0])
                return {"steps": [n], "modes": [mode], "clamped": clamped}
        return None
    # copy 4 of the lopsided set: two drags the same way
    for total in range(2, 261):
        for k in range(1, total):
            for sign in (1, -1):
                F1, m1 = drag(p, F0, sign * k)
                F, m2 = drag(p, F1, sign * (total - k))
                if close(got, p, F):
                    longer = drag(p, F1, sign * (total - k + 1))[0]
                    return {"steps": [sign * k, sign * (total - k)], "modes": [m1, m2],
                            "clamped": close(got, p, longer)}
    return None


# --- the starting curves ---------------------------------------------------------------------

CURVES = [
    ("straight", None),
    ("Live's family, early, a = 1/8", (0.125, 0.625, 0.375, 0.875)),
    ("Live's family, late, y1 = 1/8", (0.625, 0.125, 0.875, 0.375)),
    ("extreme early", (0.0, 1.0, 0.0, 1.0)),
    ("extreme late", (1.0, 0.0, 1.0, 0.0)),
    ("top edge (0.2, 1) (0.6, 1)", (0.2, 1.0, 0.6, 1.0)),
    ("S (0.6, 0) (0.4, 1)", (0.6, 0.0, 0.4, 1.0)),
    ("crossed, bottom edge", (0.36, 0.0, 0.24, 0.0)),
    ("uneven, mild", (0.1, 0.3, 0.5, 0.9)),
    ("half of a split curve", (0.17034, 0.49556, 0.42509, 0.80242)),
    ("reverse S", (0.1, 0.7, 0.9, 0.3)),
    ("both handles at the centre", (0.5, 0.5, 0.5, 0.5)),
    ("family, early, a = 1/8, other direction", (0.125, 0.625, 0.375, 0.875)),
    ("S, other direction", (0.6, 0.0, 0.4, 1.0)),
]

LOPSIDED = [
    ("lopsided S: p 1/4 3/4, F 0.4 1.3", vcurve(0.25, 0.4, 0.75, 1.3)),
    ("lopsided S: p 1/4 3/4, F 1.7 0.8", vcurve(0.25, 1.7, 0.75, 0.8)),
    ("lopsided S: p 1/4 3/4, F 0.3 1.5", vcurve(0.25, 0.3, 0.75, 1.5)),
    ("opposite sides, not point-symmetric: p 1/8 5/6, F 0.5 1.5", vcurve(0.125, 0.5, 5 / 6, 1.5)),
    ("lopsided S on the edges: p 0 1, F 1.7 0.2", vcurve(0.0, 1.7, 1.0, 0.2)),
    ("lopsided S: p 0.3 0.6, F 0.6 1.4", vcurve(0.3, 0.6, 0.6, 1.4)),
    ("point-symmetric S: p 1/8 7/8, F 0.5 1.5", vcurve(0.125, 0.5, 0.875, 1.5)),
    ("near crossing: p 1/4 3/4, F 0.9 0.6", vcurve(0.25, 0.9, 0.75, 0.6)),
    ("near crossing: p 1/8 5/6, F 1.2 1.5", vcurve(0.125, 1.2, 5 / 6, 1.5)),
    ("near crossing: p 0.2 0.7, F 0.95 0.3", vcurve(0.2, 0.95, 0.7, 0.3)),
    ("top edge near the corner: p 1 1, F 0.8 0.3", vcurve(1.0, 0.8, 1.0, 0.3)),
    ("one handle on the diagonal: (0.3, 0.3), p 3/4 F 0.5", (0.3, 0.3) + vcurve(0.25, 0, 0.75, 0.5)[2:]),
]

SETS = {"curve-drag": CURVES, "curve-drag-lopsided": LOPSIDED}
LOW, HIGH = 1.0, 3.98107171  # 0 dB and +12 dB
SEG = 4.0                    # a bar per segment
COPIES = 4


def layout(curves):
    """Each segment's copy, place, start beat and starting curve. Segments alternate rising and
    falling from 0 dB; each copy ends with a flat bar."""
    period = (len(curves) + 1) * SEG
    out = []
    for k in range(COPIES):
        for j, (label, c) in enumerate(curves):
            out.append({"copy": k + 1, "segment": j + 1, "label": label,
                        "start": k * period + j * SEG, "rising": j % 2 == 0, "curve": c})
    return out, period


# --- sets ------------------------------------------------------------------------------------


def envelope_points(path):
    root = ET.fromstring(gzip.decompress(Path(path).read_bytes()))
    env = next(e for e in root.iter("AutomationEnvelope")
               if e.find("EnvelopeTarget/PointeeId").get("Value") == UTILITY_GAIN)
    pts = []
    for e in env.iter("FloatEvent"):
        t = float(e.get("Time"))
        if t < 0:
            continue
        c = None
        if e.get("CurveControl1X") is not None:
            c = tuple(float(e.get(k)) for k in
                      ("CurveControl1X", "CurveControl1Y", "CurveControl2X", "CurveControl2Y"))
        pts.append((t, float(e.get("Value")), c))
    return pts


def make(src, out_dir):
    """The starting sets, from a set with the Operator track and Utility (utility-gain-splits)."""
    xml0 = gzip.decompress(Path(src).read_bytes()).decode("utf-8")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, curves in SETS.items():
        segs, period = layout(curves)
        total = COPIES * period
        ev, n = ['<FloatEvent Id="0" Time="-63072000" Value="1" />'], 1
        for s in segs:
            v = LOW if s["rising"] else HIGH
            e = f'<FloatEvent Id="{n}" Time="{s["start"]:g}" Value="{v:.8g}"'
            if s["curve"]:
                e += (' CurveControl1X="{:.17g}" CurveControl1Y="{:.17g}" CurveControl2X="{:.17g}"'
                      ' CurveControl2Y="{:.17g}"').format(*s["curve"])
            ev.append(e + " />")
            n += 1
            if s["segment"] == len(curves):  # the end of the copy, flat for a bar
                end_v = HIGH if s["rising"] else LOW
                ev.append(f'<FloatEvent Id="{n}" Time="{s["start"] + SEG:g}" Value="{end_v:.8g}" />')
                n += 1
        xml = xml0
        m = re.search(r'(<PointeeId Value="%s" />.*?<Events>)(.*?)(\n(\t*)</Events>)' % UTILITY_GAIN,
                      xml, re.S)
        indent = m.group(4) + "\t"
        xml = xml[:m.start(2)] + "".join("\n" + indent + e for e in ev) + xml[m.end(2):]
        clip = re.search(r'<MidiClip Id="0" Time="0">.*?</MidiClip>', xml, re.S)
        c = clip.group(0)
        for tag in ("CurrentEnd", "LoopEnd", "RightTime", "OtherTime"):
            c = re.sub(rf'<{tag} Value="[^"]*" />', f'<{tag} Value="{total:g}" />', c, count=1)
        c = c.replace('<LoopOn Value="true" />', '<LoopOn Value="false" />', 1)
        c = re.sub(r'(<MidiNoteEvent Time="0" Duration=")[^"]*"', rf'\g<1>{total:g}"', c)
        c = c.replace('<Disabled Value="true" />', '<Disabled Value="false" />', 1)
        xml = xml[:clip.start()] + c + xml[clip.end():]
        # The old bounce leaves the bounce track, so the next Bounce is the only clip there.
        xml = re.sub(r'\n\t*<AudioClip Id="0" Time="0">.*?</AudioClip>', "", xml, count=1, flags=re.S)
        (out_dir / f"{name}.start.als").write_bytes(gzip.compress(xml.encode("utf-8")))
        print(f"{name}.start.als: {len(ev)} points, {total:g} beats")


# --- analyses --------------------------------------------------------------------------------


def bezier_at(c, t):
    x1, y1, x2, y2 = c
    b = lambda p1, p2: 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3
    return b(x1, x2), b(y1, y2)


def split_bezier(c, t):
    """de Casteljau at t: the two halves' controls, each in its own unit box, and the point."""
    P = [(0, 0), (c[0], c[1]), (c[2], c[3]), (1, 1)]
    lerp = lambda a, b: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    a, b, cc = lerp(P[0], P[1]), lerp(P[1], P[2]), lerp(P[2], P[3])
    d, e = lerp(a, b), lerp(b, cc)
    f = lerp(d, e)
    left = (a[0] / f[0], a[1] / f[1], d[0] / f[0], d[1] / f[1])
    right = ((e[0] - f[0]) / (1 - f[0]), (e[1] - f[1]) / (1 - f[1]),
             (cc[0] - f[0]) / (1 - f[0]), (cc[1] - f[1]) / (1 - f[1]))
    return left, right, f


def utility_position(gain):
    """Utility's knob position (0 to 1) for gains from -17.5 dB up, where it is even in dB."""
    import math
    return (1 + 20 * math.log10(gain) / 35) / 2


def splits():
    pts = envelope_points(HERE / "sets" / "utility-gain-splits.als")
    whole = [(a, b) for a, b in zip(pts, pts[1:]) if b[0] > a[0] and b[0] <= 16]
    i = max(k for k, p in enumerate(pts) if p[0] == 16)
    out = []
    for A, B in whole:
        a, m, b = pts[i], pts[i + 1], pts[i + 2]
        i += 2
        c = A[2]
        x = (m[0] - a[0]) / (b[0] - a[0])
        lo, hi = 0.0, 1.0
        for _ in range(100):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if bezier_at(c, mid)[0] < x else (lo, mid)
        t = (lo + hi) / 2
        left, right, f = split_bezier(c, t)
        pa, pb, pm = utility_position(a[1]), utility_position(b[1]), utility_position(m[1])
        err = max(max(abs(u - v) for u, v in zip(left, a[2])),
                  max(abs(u - v) for u, v in zip(right, m[2])),
                  abs((pm - pa) / (pb - pa) - f[1]))
        out.append({"whole": [A[0], B[0]], "curve": c, "split_at": m[0], "share_of_time": round(x, 6),
                    "t": round(t, 6), "left": a[2], "right": m[2], "max_error": err})
        print(f"  {a[0]:g}-{b[0]:g} split at {m[0]:.4f} (x {x:.4f}, t {t:.4f}): "
              f"largest difference from de Casteljau {err:.1e}")
    return out


def drags(name):
    pts = {round(t, 6): c for t, v, c in envelope_points(HERE / "sets" / f"{name}.als")}
    segs, _ = layout(SETS[name])
    out, bad = [], 0
    for s in segs:
        got = pts[round(s["start"], 6)]
        n = 2 if name == "curve-drag-lopsided" and s["copy"] == 4 else 1
        p, F = start_paths(s["curve"])
        r = fit(s["curve"], got, n)
        row = {**s, "got": got, "start_p": p, "start_F": F,
               "got_F": [coord(got[:2])[1], coord(got[2:])[1]], "fit": r}
        out.append(row)
        if r is None:
            bad += 1
            print(f"  NO FIT copy {s['copy']} segment {s['segment']} ({s['label']}): {got}")
    print(f"  {len(segs) - bad} of {len(segs)} segments follow the rule")
    # The direction: with each segment's copies dragged the same way (copies 1, 2 and 4) or the
    # other way (copy 3), + must mean the same mouse direction for every mode.
    if name == "curve-drag-lopsided":
        for j in range(1, len(SETS[name]) + 1):
            rows = [o for o in out if o["segment"] == j and o["fit"]]
            signs = [(o["copy"], [x > 0 for x in o["fit"]["steps"]]) for o in rows]
            first = {c: s[0] for c, s in signs}
            ok = first.get(1) == first.get(2) == first.get(4) != first.get(3)
            if not ok:
                print(f"  segment {j}: drag directions do not follow the plan: {signs}")
    return out


def analyse():
    (HERE / "live").mkdir(exist_ok=True)
    print("utility-gain-splits")
    (HERE / "live" / "utility-gain-splits.splits.json").write_text(json.dumps(splits(), indent=1) + "\n")
    for name in SETS:
        print(name)
        (HERE / "live" / f"{name}.drags.json").write_text(json.dumps(drags(name), indent=1) + "\n")


if __name__ == "__main__":
    if sys.argv[1:2] == ["make"]:
        make(sys.argv[2], sys.argv[3])
    elif sys.argv[1:2] == ["analyse"]:
        analyse()
    else:
        print(__doc__)
