# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Measures how Live 12.4.6 plays automation, from the sets in sets/ and their renders in export/.

Each run is a set whose first track automates one parameter with straight segments, curved
segments and jumps (two points at one beat), and the render of that track: a 261.6 Hz sine from
Operator. For each run this script

- reads the automation points (beat, stored value, curve controls) from the set;
- measures the level (or, for Operator's Fine, the frequency) of the render every 2 ms;
- predicts every segment three ways: moving evenly in the parameter's position (knob or fader
  travel, 0 to 1), in dB, and in the stored value, each bent by the cubic Bezier the point
  stores, and reports how far each prediction is from the render;
- fits the ramp at each jump on the raw samples: its length, where it is centred and whether it
  moves evenly in position, dB or gain.

Usage (numpy only, like the rest of the harness):

    tools/.venv/bin/python automation/analyse.py [run ...]

It writes live/<run>.json and live/<run>.envelope.csv, and live/fader-taper.csv from the track
volume run. The renders are not in the repository (export/ is ignored); see README.md here.
"""

import gzip
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools" / "harness"))
from wavio import read_wav  # noqa: E402

TONE = 261.6256  # Operator's C3 at 440 Hz tuning
BLOCK_S = 0.002
GUARD_BEATS = 0.04  # left out around each point: smoothing and the 2 ms blocks

# kind: which position the parameter's lane uses. jumps: beat of each jump.
RUNS = {
    "utility-gain-curves": {"kind": "utility", "jumps": []},
    "utility-gain-jump13": {"kind": "utility", "jumps": [28]},
    "utility-gain-jump62": {"kind": "utility", "jumps": [28]},
    "utility-gain-jump62-88k": {"kind": "utility", "jumps": [28]},
    "track-volume": {"kind": "fader", "jumps": [30], "table_from": (3, 6)},
    "operator-volume-88k": {"kind": "fader", "jumps": [28]},
    "operator-fine": {"kind": "fine", "jumps": [2, 3]},
    # Curve shapes: split curves and hand-dragged ones (curve_drag.py reads the handles).
    "utility-gain-splits": {"kind": "utility", "jumps": []},
    "curve-drag": {"kind": "utility", "jumps": []},
    "curve-drag-lopsided": {"kind": "utility", "jumps": []},
}


# --- the set ---------------------------------------------------------------------------------

def read_set(path):
    """The first automation envelope's points (beat, value, curve or None) and the tempo."""
    root = ET.fromstring(gzip.decompress(path.read_bytes()))
    envelope = root.find(".//AutomationEnvelope")
    points = []
    for event in envelope.find("Automation/Events"):
        beat = float(event.get("Time"))
        if beat < 0:
            continue  # the value before the song starts
        curve = None
        if event.get("CurveControl1X") is not None:
            curve = tuple(float(event.get(k)) for k in
                          ("CurveControl1X", "CurveControl1Y", "CurveControl2X", "CurveControl2Y"))
        points.append((beat, float(event.get("Value")), curve))
    tempo = float(root.find(".//Tempo/Manual").get("Value"))
    return points, tempo


def segments(points):
    """(start beat, end beat, start value, end value, curve) for each segment, jumps left out.
    A point's curve controls shape the segment that starts at it."""
    return [(a[0], b[0], a[1], b[1], a[2]) for a, b in zip(points, points[1:]) if b[0] > a[0]]


# --- the curve -------------------------------------------------------------------------------

def bezier(x, curve):
    """The share of the way (0 to 1) at the share of the time `x`, for a cubic Bezier from (0, 0)
    to (1, 1) with control points (x1, y1) and (x2, y2); a straight line for None."""
    x = np.asarray(x, float)
    if curve is None:
        return x
    x1, y1, x2, y2 = curve
    s = np.linspace(0, 1, 20001)
    bx = 3 * s * (1 - s) ** 2 * x1 + 3 * s * s * (1 - s) * x2 + s ** 3
    by = 3 * s * (1 - s) ** 2 * y1 + 3 * s * s * (1 - s) * y2 + s ** 3
    return np.interp(x, bx, by)


# --- positions -------------------------------------------------------------------------------

UTILITY_SLOPE = 35.0  # dB per unit of the knob's -1 ... 1 range above the knee
UTILITY_KNEE = -0.5   # -17.5 dB
# Below the knee the gain is a power of (1 + k), with the power that keeps the slope continuous.
UTILITY_POWER = UTILITY_SLOPE * (1 + UTILITY_KNEE) * np.log(10) / 20


def utility_db(position):
    """Utility's Gain in dB at knob position 0 ... 1 (the API's -1 ... 1 is 2 p - 1)."""
    k = 2 * np.asarray(position, float) - 1
    above = UTILITY_SLOPE * k
    with np.errstate(divide="ignore"):
        below = UTILITY_SLOPE * UTILITY_KNEE + 20 * UTILITY_POWER * np.log10(
            np.clip(1 + k, 0, None) / (1 + UTILITY_KNEE))
    return np.where(k >= UTILITY_KNEE, above, below)


class Taper:
    """A position (0 ... 1) to dB mapping, from a table, monotone."""

    def __init__(self, position, db):
        self.position = np.asarray(position, float)
        self.db = np.maximum.accumulate(np.asarray(db, float))

    def to_db(self, p):
        return np.interp(p, self.position, self.db)

    def to_position(self, db):
        return np.interp(db, self.db, self.position)


def utility_taper():
    p = np.linspace(0, 1, 200001)
    d = utility_db(p)
    d[0] = -400.0  # -inf, for interpolation
    return Taper(p, d)


def db_of(gain):
    return 20 * np.log10(np.maximum(gain, 1e-20))


# --- the render ------------------------------------------------------------------------------

def analytic(x):
    """The analytic signal (x plus i times its Hilbert transform), by FFT."""
    n = len(x)
    spectrum = np.fft.fft(x)
    h = np.zeros(n)
    h[0] = 1
    if n % 2 == 0:
        h[n // 2] = 1
        h[1:n // 2] = 2
    else:
        h[1:(n + 1) // 2] = 2
    return np.fft.ifft(spectrum * h)


def blocks(values, rate):
    k = int(round(rate * BLOCK_S))
    n = len(values) // k
    return values[:n * k].reshape(n, k).mean(axis=1), (np.arange(n) + 0.5) * k / rate


def level_db(audio, rate):
    amp, t = blocks(np.abs(analytic(audio[:, 0])), rate)
    return t, db_of(amp)


def frequency(audio, rate):
    phase = np.unwrap(np.angle(analytic(audio[:, 0])))
    f, t = blocks(np.diff(phase) * rate / (2 * np.pi), rate)
    return t, f


# --- segment predictions ---------------------------------------------------------------------

def predict(segs, beats, space, taper=None, fine=False):
    """The predicted value (dB, or Hz for Fine without a reference) at `beats` (NaN near points)."""
    out = np.full(len(beats), np.nan)
    for b0, b1, v0, v1, curve in segs:
        m = (beats > b0 + GUARD_BEATS) & (beats < b1 - GUARD_BEATS)
        y = bezier((beats[m] - b0) / (b1 - b0), curve)
        if fine:
            if space == "position":
                out[m] = TONE * (1 + (v0 + (v1 - v0) * y) / 1000)
            else:  # evenly in pitch
                a, b = np.log(1 + v0 / 1000), np.log(1 + v1 / 1000)
                out[m] = TONE * np.exp(a + (b - a) * y)
        elif space == "position":
            p0, p1 = taper.to_position(db_of(v0)), taper.to_position(db_of(v1))
            out[m] = taper.to_db(p0 + (p1 - p0) * y)
        elif space == "dB":
            a, b = max(db_of(v0), -70.0), max(db_of(v1), -70.0)
            out[m] = a + (b - a) * y
        else:
            out[m] = db_of(v0 + (v1 - v0) * y)
    return out


def compare(segs, beats, measured, space, taper, fine=False, reference=None, tempo=120.0):
    """Residuals of one prediction; the reference level (or frequency scale) is fitted."""
    pred = predict(segs, beats, space, taper, fine)
    ok = np.isfinite(pred) & np.isfinite(measured) & (measured > -120 if not fine else True)
    if fine:
        # Fit a small time offset and the tone's frequency (Operator's Fine scale may differ
        # slightly from 1 + Fine/1000), then report the error in cents.
        best = None
        for shift in np.arange(-0.012, 0.0121, 0.0005):
            p = predict(segs, beats - shift, space, taper, fine)
            ok = np.isfinite(p)
            scale = np.exp(np.median(np.log(measured[ok] / p[ok])))
            cents = 1200 * np.log2(p[ok] * scale / measured[ok])
            rms = float(np.sqrt(np.mean(cents ** 2)))
            if best is None or rms < best[0]:
                best = (rms, shift, scale, cents)
        rms, shift, scale, cents = best
        return {"rms_cents": round(rms, 2), "max_cents": round(float(np.abs(cents).max()), 2),
                "time_offset_ms": round(shift * 60 / tempo * 1000, 2), "base_hz": round(TONE * scale, 3)}
    ref = reference if reference is not None else float(np.median(measured[ok] - pred[ok]))
    r = pred[ok] + ref - measured[ok]
    per = []
    for b0, b1, v0, v1, curve in segs:
        m = (beats[ok] > b0) & (beats[ok] < b1)
        if m.any():
            per.append({"from": b0, "to": b1, "curve": curve is not None,
                        "rms_db": round(float(np.sqrt(np.mean(r[m] ** 2))), 3),
                        "max_db": round(float(np.abs(r[m]).max()), 3)})
    return {"reference_dbfs": round(ref, 3), "rms_db": round(float(np.sqrt(np.mean(r ** 2))), 3),
            "max_db": round(float(np.abs(r).max()), 3), "segments": per}


def fader_table(beats, measured, segs, start, end):
    """The fader's taper from a straight segment that runs from the lane's bottom (start) to its
    top (end): position = share of the time."""
    m = (beats > start + 0.01) & (beats < end - 0.01)
    p = (beats[m] - start) / (end - start)
    top = next(v1 for b0, b1, v0, v1, c in segs if b0 == start and b1 == end)
    # 0 dB: the render's level where the automation sits at gain 1 (the song's last point).
    last = segs[-1]
    zero = float(np.median(measured[(beats > last[1] - 0.1) & (beats < last[1] - 0.02)]))
    d = measured[m] - zero
    p = np.concatenate([[0.0], p, [1.0]])
    d = np.concatenate([[-70.0], d, [db_of(top)]])
    return Taper(p, d), zero


# --- ramps at jumps --------------------------------------------------------------------------

SHAPES = {
    "smootherstep": lambda u: u ** 3 * (u * (6 * u - 15) + 10),
    "raised cosine": lambda u: 0.5 - 0.5 * np.cos(np.pi * u),
    "smoothstep": lambda u: u * u * (3 - 2 * u),
    "linear": lambda u: u,
}


def ramp_fit(audio, rate, beat, tempo, before, after, taper, shapes=SHAPES, spaces=("position", "dB", "gain")):
    """Fits gain(t) = g0 + (g1 - g0) w(shape((t - t0) / L)) around a jump on the raw samples, the
    tone's amplitude and phase on each side free, plus a slow trend. Returns the best L and t0
    for each space and shape."""
    centre = int(round(beat * 60 / tempo * rate))
    half = int(0.03 * rate)
    x = audio[centre - half:centre + half, 0]
    n = np.arange(-half, half)
    w = 2 * np.pi * TONE / rate
    sin, cos, trend = np.sin(w * n), np.cos(w * n), n / half
    g0, g1 = before, after

    def weight(u, space):
        if space == "gain":
            return u
        if space == "dB":
            r = g1 / g0
            return (r ** u - 1) / (r - 1)
        p0, p1 = taper.to_position(db_of(g0)), taper.to_position(db_of(g1))
        return (10 ** (taper.to_db(p0 + (p1 - p0) * u) / 20) - g0) / (g1 - g0)

    def residual(n0, length, shape, space):
        v = weight(shape(np.clip((n - n0) / length, 0, 1)), space)
        cols = []
        for g in (1 - v, v, (1 - v) * trend, v * trend):
            cols += [g * sin, g * cos]
        a = np.column_stack(cols)
        coef = np.linalg.lstsq(a, x, rcond=None)[0]
        return float(np.sqrt(np.mean((x - a @ coef) ** 2)))

    def search(shape, space):
        # Coarse (every 0.25 ms), then every 2 samples around the best, then every sample.
        best = None
        for step, span_l, span_n in ((rate // 4000, None, None), (2, 24, 24), (1, 4, 4)):
            if best is None:
                lengths = range(int(0.0005 * rate), int(0.015 * rate), step)
                starts = range(-int(0.015 * rate), int(0.004 * rate), step)
            else:
                _, L0, s0 = best
                lengths = range(max(2, L0 - span_l), L0 + span_l + 1, step)
                starts = range(s0 - span_n, s0 + span_n + 1, step)
            best = min((residual(n0, L, shape, space), L, n0) for L in lengths for n0 in starts)
        r, L, n0 = best
        return {"residual": r, "samples": L, "ms": round(L / rate * 1000, 2),
                "centre_samples": round(n0 + L / 2, 1)}

    out = {"signal_rms": float(np.sqrt(np.mean(x[half + int(0.01 * rate):] ** 2)))}
    for space in spaces:
        for name, shape in shapes.items():
            out[f"{space}, {name}"] = search(shape, space)
    return out


# --- runs ------------------------------------------------------------------------------------

def run(name, spec, taper_cache):
    points, tempo = read_set(HERE / "sets" / f"{name}.als")
    rate, audio = read_wav(HERE / "export" / f"{name}.wav")
    segs = segments(points)
    result = {"run": name, "rate": rate, "tempo": tempo,
              "points": [[b, v, c] for b, v, c in points]}
    if spec["kind"] == "fine":
        t, f = frequency(audio, rate)
        beats = t * tempo / 60
        np.savetxt(HERE / "live" / f"{name}.envelope.csv", np.column_stack([beats, f]),
                   delimiter=",", header="beat,hz", fmt="%.5f")
        result["even in Fine"] = compare(segs, beats, f, "position", None, fine=True, tempo=tempo)
        result["even in pitch"] = compare(segs, beats, f, "pitch", None, fine=True, tempo=tempo)
        # Jumps: share of the step reached 0.5 ms and 1 ms after the beat, at 0.25 ms resolution.
        phase = np.unwrap(np.angle(analytic(audio[:, 0])))
        inst = np.diff(phase) * rate / (2 * np.pi)
        k = int(rate * 0.00025)
        result["jumps"] = []
        for jb in spec["jumps"]:
            pre = [v for b, v, c in points if b == jb]
            c = int(round(jb * 60 / tempo * rate))
            lo, hi = TONE * (1 + pre[0] / 1000), TONE * (1 + pre[-1] / 1000)
            sm = np.convolve(inst[c - rate // 100:c + rate // 50], np.ones(k) / k, mode="same")
            share = (sm - lo) / (hi - lo)
            at = lambda ms: round(float(share[rate // 100 + int(ms * rate / 1000)]), 3)
            result["jumps"].append({"beat": jb, "share at -1 ms": at(-1), "at 0": at(0),
                                    "at +0.5 ms": at(0.5), "at +1 ms": at(1), "at +3 ms": at(3)})
        return result

    t, d = level_db(audio, rate)
    beats = t * tempo / 60
    np.savetxt(HERE / "live" / f"{name}.envelope.csv", np.column_stack([beats, d]),
               delimiter=",", header="beat,dbfs", fmt="%.5f")
    if spec["kind"] == "utility":
        taper = utility_taper()
    elif "table_from" in spec:
        taper, zero = fader_table(beats, d, segs, *spec["table_from"])
        taper_cache["fader"] = taper
        np.savetxt(HERE / "live" / "fader-taper.csv",
                   np.column_stack([taper.position[::25], taper.db[::25]]),
                   delimiter=",", header="position,db", fmt="%.5f")
        # Predict the other segments only: the table's own sweep would fit itself.
        segs = [s for s in segs if (s[0], s[1]) != spec["table_from"]]
        result["fader table"] = {"from": spec["table_from"], "zero_db_dbfs": round(zero, 3),
                                 "position of 0 dB": round(float(taper.to_position(0)), 4)}
    else:
        taper = taper_cache.get("fader") or Taper(*np.loadtxt(HERE / "live" / "fader-taper.csv",
                                                              delimiter=",", unpack=True))
    for space, label in (("position", "even in position"), ("dB", "even in dB"),
                         ("gain", "even in gain")):
        result[label] = compare(segs, beats, d, space, taper)
    result["jumps"] = []
    for jb in spec["jumps"]:
        values = [v for b, v, c in points if b == jb]
        fit = ramp_fit(audio, rate, jb, tempo, values[0], values[-1], taper)
        best = min((v["residual"], k) for k, v in fit.items() if isinstance(v, dict))
        result["jumps"].append({"beat": jb, "from_db": round(db_of(values[0]), 2),
                                "to_db": round(db_of(values[-1]), 2), "best": best[1], **fit})
    return result


def main(argv):
    names = argv or list(RUNS)
    (HERE / "live").mkdir(exist_ok=True)
    cache = {}
    for name in sorted(names, key=lambda n: n != "track-volume"):
        result = run(name, RUNS[name], cache)
        (HERE / "live" / f"{name}.json").write_text(json.dumps(result, indent=1) + "\n")
        summary = {k: v for k, v in result.items() if k.startswith("even")}
        print(name, json.dumps({k: (v.get("rms_db"), v.get("max_db")) if "rms_db" in v else
                                (v["rms_cents"], v["max_cents"]) for k, v in summary.items()}))
        for j in result.get("jumps", []):
            if "best" in j:
                b = j[j["best"]]
                print(f"   jump at {j['beat']}: best {j['best']}: {b['samples']} samples = {b['ms']} ms, "
                      f"centre {b['centre_samples']:+}")
            else:
                print("   jump", j)


if __name__ == "__main__":
    main(sys.argv[1:])
