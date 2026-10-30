# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Measures renders of the probe signal.

    python analyse.py probe.json render.wav [more.wav ...] -o results/ [--align none|xcorr|<samples>]

For each render writes results/<name>.json with the measurements below, and beside it
<name>.response.csv, <name>.static.csv, <name>.envelope.csv and <name>.ir.wav.

  latency      offset of the render against the probe (only with --align; Live's export is
               delay-compensated, so the default is none)
  impulse      the strongest taps (time, level), the decay time (RT60 from the Schroeder curve)
  response     magnitude in dB at 1/6-octave centres from the sweep, and from the noise (cross-spectrum,
               which averages out time-varying devices); per channel
  static       per staircase step: output level, gain, THD and the first harmonics
  dynamics     attack and release: time for the gain to move 63 % and 90 % of the way after the
               level steps up and down
  modulation   amplitude modulation (rate, depth) and pitch modulation (rate, depth in cents) of
               the steady sine, and the correlation of the two channels' envelopes
  stereo       the 2x2 matrix of levels (dB) from left-only and right-only input
  silence      what comes out with no input (RMS, peak)
"""

import argparse
import csv
import json
import math
import os
import sys

import numpy as np

from wavio import read_wav, write_wav

EPS = 1e-12


def to_db(x):
    return 20.0 * math.log10(max(float(x), EPS))


def rms(x):
    return float(np.sqrt(np.mean(np.square(x)))) if len(x) else 0.0


def segment(audio, seg, offset=0, extra=0):
    a = seg["start"] + offset
    b = a + seg["length"] + extra
    out = np.zeros((seg["length"] + extra, audio.shape[1]))
    lo, hi = max(a, 0), min(b, len(audio))
    if hi > lo:
        out[lo - a:hi - a] = audio[lo:hi]
    return out


def band_centres(lo=20.0, hi=20000.0, per_octave=6):
    n = int(math.floor(math.log2(hi / lo) * per_octave)) + 1
    return [lo * 2 ** (i / per_octave) for i in range(n)]


def band_db(freqs, power, centres, per_octave=6):
    """Average of `power` over each band around the centres; dB (10 log10)."""
    half = 2 ** (1 / (2 * per_octave))
    out = []
    for c in centres:
        m = (freqs >= c / half) & (freqs < c * half)
        out.append(10 * math.log10(max(float(np.mean(power[m])), EPS)) if m.any() else None)
    return out


# ------------------------------------------------------------------ alignment

def find_latency(probe, render, rate, max_s=1.0):
    x = probe.mean(axis=1)
    y = render.mean(axis=1)
    n = 1 << int(math.ceil(math.log2(len(x) + len(y))))
    xc = np.fft.irfft(np.fft.rfft(y, n) * np.conj(np.fft.rfft(x, n)), n)
    lim = int(max_s * rate)
    window = np.concatenate([xc[-lim:], xc[:lim + 1]])
    return int(np.argmax(np.abs(window))) - lim


# ------------------------------------------------------------------ measurements

def impulse(seg_out, seg, rate):
    amp = 10 ** (seg["level_db"] / 20)
    ir = seg_out / amp
    mono = np.abs(ir).max(axis=1)
    peak = float(mono.max()) if len(mono) else 0.0
    res = {"peak_db": to_db(peak), "taps": [], "rt60_s": None}
    if peak < 1e-9:
        return res, ir
    floor = peak * 10 ** (-40 / 20)
    sep = max(1, int(0.001 * rate))
    cand = np.where((mono[1:-1] >= mono[:-2]) & (mono[1:-1] >= mono[2:]) & (mono[1:-1] >= floor))[0] + 1
    if mono[0] >= floor:
        cand = np.concatenate([[0], cand])
    chosen = []
    for i in cand[np.argsort(-mono[cand])]:
        if all(abs(i - j) >= sep for j in chosen):
            chosen.append(int(i))
        if len(chosen) >= 16:
            break
    for i in sorted(chosen):
        res["taps"].append({"time_ms": 1000 * i / rate, "level_db": to_db(mono[i]),
                            "left": float(ir[i, 0]), "right": float(ir[i, -1])})
    energy = np.sum(np.square(ir), axis=1)
    edc = np.cumsum(energy[::-1])[::-1]
    edc_db = 10 * np.log10(np.maximum(edc / max(edc[0], EPS), EPS))
    for lo, hi in ((-5, -35), (-5, -25), (-5, -15)):
        i0 = np.argmax(edc_db <= lo)
        i1 = np.argmax(edc_db <= hi)
        if edc_db[i0] <= lo and edc_db[i1] <= hi and i1 > i0 + 2:
            t = np.arange(i0, i1) / rate
            slope = np.polyfit(t, edc_db[i0:i1], 1)[0]
            if slope < 0:
                res["rt60_s"] = float(-60 / slope)
                res["rt60_from"] = f"{lo} to {hi} dB"
            break
    return res, ir


def response_sweep(inp, out, rate, centres):
    n = 1 << int(math.ceil(math.log2(len(inp))))
    X = np.fft.rfft(inp, n)
    f = np.fft.rfftfreq(n, 1 / rate)
    res = []
    px = np.abs(X) ** 2
    for ch in range(out.shape[1]):
        Y = np.fft.rfft(out[:, ch], n)
        h2 = np.abs(Y) ** 2 / np.maximum(px, EPS)
        # weight by input power so bands the sweep barely covers do not dominate
        res.append(weighted_band_db(f, h2, px, centres))
    return res


def weighted_band_db(freqs, h2, weight, centres, per_octave=6):
    half = 2 ** (1 / (2 * per_octave))
    out = []
    for c in centres:
        m = (freqs >= c / half) & (freqs < c * half)
        w = weight[m]
        if not m.any() or w.sum() <= EPS:
            out.append(None)
            continue
        out.append(10 * math.log10(max(float(np.sum(h2[m] * w) / np.sum(w)), EPS)))
    return out


def response_noise(inp, out, rate, centres, nfft=8192):
    win = np.hanning(nfft)
    hop = nfft // 2
    f = np.fft.rfftfreq(nfft, 1 / rate)
    res = []
    for ch in range(out.shape[1]):
        sxx = np.zeros(len(f))
        sxy = np.zeros(len(f), dtype=complex)
        x_ch = inp[:, min(ch, inp.shape[1] - 1)]
        for s in range(0, len(x_ch) - nfft + 1, hop):
            X = np.fft.rfft(x_ch[s:s + nfft] * win)
            Y = np.fft.rfft(out[s:s + nfft, ch] * win)
            sxx += np.abs(X) ** 2
            sxy += Y * np.conj(X)
        h2 = np.abs(sxy) ** 2 / np.maximum(sxx, EPS) ** 2
        res.append(band_db(f, h2, centres))
    return res


def harmonics(x, freq, rate, count=10):
    n = len(x)
    if n < 16 or rms(x) < 1e-9:
        return None
    w = np.hanning(n)
    spec = np.abs(np.fft.rfft(x * w))
    bin_hz = rate / n
    levels = []
    for k in range(1, count + 1):
        fk = freq * k
        if fk >= rate / 2:
            break
        b = int(round(fk / bin_hz))
        lo, hi = max(b - 3, 0), min(b + 4, len(spec))
        levels.append(float(np.sqrt(np.sum(spec[lo:hi] ** 2))))
    if not levels or levels[0] <= EPS:
        return None
    thd = math.sqrt(sum(h * h for h in levels[1:])) / levels[0]
    return {"thd_pct": 100 * thd, "harmonics_db": [to_db(h / levels[0]) for h in levels[1:6]]}


def static_curve(out, seg, rate):
    n = seg["step_length"]
    rows = []
    for i, lvl in enumerate(seg["levels_db"]):
        a = i * n + n // 2
        b = (i + 1) * n - int(0.01 * rate)
        part = out[a:b]
        row = {"in_db": lvl}
        for ch, name in enumerate(["left", "right"][:out.shape[1]]):
            level = to_db(rms(part[:, ch]) * math.sqrt(2))  # sine peak level, comparable to in_db
            row[f"{name}_out_db"] = level
            row[f"{name}_gain_db"] = level - lvl
            h = harmonics(part[:, ch], seg["freq"], rate)
            row[f"{name}_thd_pct"] = h["thd_pct"] if h else None
            if h and ch == 0:
                row["harmonics_db"] = h["harmonics_db"]
        rows.append(row)
    return rows


def envelope(x, rate, hop_s=0.0005, win_s=0.002):
    hop = max(1, int(hop_s * rate))
    win = max(hop, int(win_s * rate))
    sq = np.concatenate([[0.0], np.cumsum(np.square(x))])
    starts = np.arange(0, len(x) - win, hop)
    e = np.sqrt((sq[starts + win] - sq[starts]) / win)
    return (starts + win / 2) / rate, e


def settle_times(t, gain_db, t_step, before, after, guard):
    """Times after t_step for the gain to cover 63 % and 90 % of the change. Envelope windows that
    straddle the step (within `guard` of it) mix both levels and are skipped, so times shorter than
    `guard` (one cycle of the test tone) read as `guard`."""
    g0 = float(np.median(gain_db[(t > t_step - before) & (t < t_step - 0.01)]))
    g1 = float(np.median(gain_db[(t > t_step + after * 0.8) & (t < t_step + after - 0.01)]))
    res = {"from_db": g0, "to_db": g1, "t63_ms": None, "t90_ms": None}
    change = g1 - g0
    if abs(change) < 0.5:
        return res
    m = t >= t_step + guard
    tt, gg = t[m], gain_db[m]
    for frac, key in ((0.63, "t63_ms"), (0.9, "t90_ms")):
        target = g0 + frac * change
        hit = np.where((gg - target) * np.sign(change) >= 0)[0]
        if len(hit):
            res[key] = 1000 * float(tt[hit[0]] - t_step)
    return res


def dynamics(out, seg, rate):
    phase = seg["phase_length"] / rate
    lin = np.concatenate([np.full(seg["phase_length"], 10 ** (seg["low_db"] / 20)),
                          np.full(seg["phase_length"], 10 ** (seg["high_db"] / 20)),
                          np.full(seg["phase_length"], 10 ** (seg["low_db"] / 20))])
    mono = out.mean(axis=1)
    cycle = 1.0 / seg["freq"]
    t, e = envelope(mono, rate, hop_s=0.00025, win_s=cycle)
    ref = lin[np.minimum((t * rate).astype(int), len(lin) - 1)] / math.sqrt(2)
    gain = 20 * np.log10(np.maximum(e, EPS) / ref)
    guard = cycle / 2
    return {"attack": settle_times(t, gain, phase, phase, phase, guard),
            "release": settle_times(t, gain, 2 * phase, phase, phase, guard),
            "resolution_ms": 1000 * cycle}, (t, gain)


def dominant_rate(sig, step, lo=0.05, hi=50.0):
    s = sig - np.mean(sig)
    if np.max(np.abs(s)) < 1e-9 or len(s) < 8:
        return None
    n = 1 << int(math.ceil(math.log2(len(s) * 4)))
    spec = np.abs(np.fft.rfft(s * np.hanning(len(s)), n))
    f = np.fft.rfftfreq(n, step)
    m = (f >= lo) & (f <= hi)
    if not m.any():
        return None
    return float(f[m][np.argmax(spec[m])])


def modulation(out, seg, rate):
    trim = int(0.5 * rate)
    part = out[trim:len(out) - trim]
    res = {}
    envs = []
    for ch, name in enumerate(["left", "right"][:out.shape[1]]):
        x = part[:, ch]
        t, e = envelope(x, rate, hop_s=0.002, win_s=0.004)
        envs.append(e)
        edb = 20 * np.log10(np.maximum(e, EPS))
        am = {"depth_db": float(np.percentile(edb, 99) - np.percentile(edb, 1)),
              "rate_hz": dominant_rate(edb, 0.002)}
        # instantaneous frequency from rising zero crossings
        fm = {"depth_cents": None, "rate_hz": None}
        s = np.signbit(x)
        zc = np.where(s[:-1] & ~s[1:])[0]
        if len(zc) > 20:
            frac = x[zc] / np.where(x[zc] - x[zc + 1] == 0, EPS, x[zc] - x[zc + 1])
            times = (zc + frac) / rate
            periods = np.diff(times)
            ok = periods > 0
            inst = 1 / periods[ok]
            cents = 1200 * np.log2(inst / seg["freq"])
            fm["depth_cents"] = float((np.percentile(cents, 99) - np.percentile(cents, 1)) / 2)
            fm["mean_cents"] = float(np.median(cents))
            if fm["depth_cents"] > 1:
                grid = np.arange(times[1], times[-1], 0.002)
                fm["rate_hz"] = dominant_rate(np.interp(grid, times[1:][ok], cents), 0.002)
        res[name] = {"am": am, "fm": fm, "level_db": to_db(rms(x) * math.sqrt(2))}
    if len(envs) == 2 and np.std(envs[0]) > 1e-9 and np.std(envs[1]) > 1e-9:
        res["envelope_correlation"] = float(np.corrcoef(envs[0], envs[1])[0, 1])
    return res


def stereo(out_l, out_r, seg, rate):
    trim = int(0.1 * rate)
    def lvl(x):
        return to_db(rms(x[trim:len(x) - trim]) * math.sqrt(2)) - seg["level_db"]
    return {"left_to_left_db": lvl(out_l[:, 0]), "left_to_right_db": lvl(out_l[:, -1]),
            "right_to_left_db": lvl(out_r[:, 0]), "right_to_right_db": lvl(out_r[:, -1])}


def silence(out):
    return {"rms_db": [to_db(rms(out[:, c])) for c in range(out.shape[1])],
            "peak_db": [to_db(np.max(np.abs(out[:, c])) if len(out) else 0) for c in range(out.shape[1])]}


# ------------------------------------------------------------------ the extended probe

def peaks(x, rate, count=8, floor_db=-120.0):
    """The strongest spectral lines of x: [(Hz, dB re a full-scale sine)], Hann window."""
    n = len(x)
    if n < 64 or rms(x) < 1e-12:
        return []
    w = np.hanning(n)
    spec = np.abs(np.fft.rfft(x * w)) * 2 / np.sum(w)
    f = np.fft.rfftfreq(n, 1 / rate)
    loc = np.where((spec[1:-1] > spec[:-2]) & (spec[1:-1] >= spec[2:]))[0] + 1
    loc = loc[np.argsort(-spec[loc])][:count]
    return [[round(float(f[i]), 2), round(to_db(spec[i]), 2)] for i in sorted(loc) if to_db(spec[i]) > floor_db]


def tone_gain(x, freq, rate):
    """Level (dB re a full-scale sine) and phase of x at freq, by projection on whole cycles."""
    cycles = int(len(x) * freq / rate)
    n = int(round(cycles * rate / freq)) if cycles else len(x)
    t = np.arange(n) / rate
    c = 2 * np.mean(x[:n] * np.cos(2 * np.pi * freq * t))
    s_ = 2 * np.mean(x[:n] * np.sin(2 * np.pi * freq * t))
    return to_db(math.hypot(c, s_)), math.degrees(math.atan2(c, s_))


def chan_db(x):
    return [to_db(rms(x[:, c])) for c in range(x.shape[1])]


def ext_measures(manifest, probe, render, rate, offset):
    """Generic readings of the extended probe's segments; the device notes do the rest from the
    renders. Levels are dB re a full-scale sine unless they say RMS."""
    segs = {s["name"]: s for s in manifest["segments"]}
    gap = int(manifest["gap"] * rate)
    res, env = {}, {}
    inner = int(0.05 * rate)

    def out(name, extra=0):
        return segment(render, segs[name], offset, extra)

    def inp(name, extra=0):
        return segment(probe, segs[name], 0, extra)

    if "stair100" in segs:
        res["stair100"] = static_curve(out("stair100"), segs["stair100"], rate)

    for name in ("tone10k", "tone15k", "tone3k", "tone50", "saw"):
        if name not in segs:
            continue
        s = segs[name]
        x = out(name)[inner:-inner]
        d = {"rms_db": chan_db(x)}
        d["level_db"] = [tone_gain(x[:, c], s["freq"], rate)[0] for c in range(x.shape[1])]
        ref = tone_gain(inp(name)[inner:-inner][:, 0], s["freq"], rate)[0]
        d["gain_db"] = [v - ref for v in d["level_db"]]
        d["peaks"] = [peaks(x[:, c], rate, 12) for c in range(x.shape[1])]
        h = harmonics(x[:, 0], s["freq"], rate)
        d["thd_pct"] = h["thd_pct"] if h else None
        res[name] = d

    if "shortbursts" in segs:
        s = segs["shortbursts"]
        x = out("shortbursts")
        rows = []
        for a, length in zip(s["burst_starts_s"], s["burst_lengths_s"]):
            i0, i1 = int(round(a * rate)), int(round((a + length) * rate))
            part = x[i0:i1]
            tail = x[i1:i1 + int(0.5 * rate)]
            peak = [to_db(np.max(np.abs(part[:, c]))) for c in range(x.shape[1])]
            rows.append({"length_ms": 1000 * length, "peak_db": peak,
                         "peak_gain_db": [p - s["level_db"] for p in peak],
                         "rms_gain_db": [to_db(rms(part[:, c]) * math.sqrt(2)) - s["level_db"] for c in range(x.shape[1])],
                         "tail_peak_db": [to_db(np.max(np.abs(tail[:, c]))) for c in range(x.shape[1])]})
        res["shortbursts"] = rows

    for name in ("bedbursts", "ramp", "shortbursts", "bursts60"):
        if name not in segs:
            continue
        s = segs[name]
        x, ix = out(name), inp(name)
        cyc = 1.0 / s["freq"]
        t, ei = envelope(ix[:, 0], rate, hop_s=0.0005, win_s=cyc)
        _, el = envelope(x[:, 0], rate, hop_s=0.0005, win_s=cyc)
        _, er = envelope(x[:, -1], rate, hop_s=0.0005, win_s=cyc)
        k = math.sqrt(2)
        env[name] = (t, 20 * np.log10(np.maximum(ei * k, EPS)), 20 * np.log10(np.maximum(el * k, EPS)),
                     20 * np.log10(np.maximum(er * k, EPS)))

    if "ramp" in segs:
        t, ind, l, r = env["ramp"]
        half = len(t) // 2
        rows = []
        for lvl in range(-60, 1, 1):
            row = {"in_db": lvl}
            for part, key in ((slice(0, half), "up"), (slice(half, len(t)), "down")):
                m = np.abs(ind[part] - lvl) < 0.25
                row[f"{key}_left_gain_db"] = float(np.median(l[part][m] - ind[part][m])) if m.any() else None
                row[f"{key}_right_gain_db"] = float(np.median(r[part][m] - ind[part][m])) if m.any() else None
            rows.append(row)
        res["ramp"] = rows

    if "threetone" in segs:
        s = segs["threetone"]
        x = out("threetone")[inner:-inner]
        res["threetone"] = {"gain_db": {str(int(f)): [tone_gain(x[:, c], f, rate)[0] - s["level_db"]
                                                       for c in range(x.shape[1])] for f in s["freqs"]},
                            "peaks": [peaks(x[:, c], rate, 12) for c in range(x.shape[1])]}

    if "lrsplit" in segs:
        s = segs["lrsplit"]
        x = out("lrsplit")[inner:-inner]
        lv = [tone_gain(x[:, c], s["freq"], rate)[0] for c in range(x.shape[1])]
        res["lrsplit"] = {"level_db": lv, "gain_db": [lv[0] - s["left_db"], lv[-1] - s["right_db"]]}

    for name in ("mid", "side"):
        if name not in segs:
            continue
        x = out(name)[inner:-inner]
        ix = inp(name)[inner:-inner]
        ref = rms(ix[:, 0])
        m, sd = (x[:, 0] + x[:, -1]) / 2, (x[:, 0] - x[:, -1]) / 2
        res[name] = {"mid_db": to_db(rms(m) / ref), "side_db": to_db(rms(sd) / ref),
                     "left_db": to_db(rms(x[:, 0]) / ref), "right_db": to_db(rms(x[:, -1]) / ref)}

    if "dcstep" in segs:
        s = segs["dcstep"]
        x = out("dcstep", gap)
        n = segs["dcstep"]["length"]
        mono = x[:, 0]
        head = mono[:max(1, int(0.002 * rate))]
        i0 = int(np.argmax(np.abs(head)))
        first = float(head[i0])
        d = {"start": first, "end": float(np.mean(mono[n - int(0.1 * rate):n])),
             "after_end_min": float(np.min(mono[n:n + int(0.5 * rate)])) if len(mono) > n else None,
             "tau_ms": None}
        if abs(first) > 1e-4:
            below = np.where(mono[i0:n] * np.sign(first) <= abs(first) / math.e)[0]
            if len(below):
                d["tau_ms"] = 1000 * float(below[0]) / rate
        res["dcstep"] = d

    if "lowsines" in segs:
        s = segs["lowsines"]
        x = out("lowsines")
        rows, pos = [], 0
        for f, secs in zip(s["freqs"], s["lengths_s"]):
            n = int(round(secs * rate))
            part = x[pos:pos + n]
            q = n // 4
            rows.append({"freq": f, "gain_db": [tone_gain(part[q:n - q, c], f, rate)[0] - s["level_db"]
                                                for c in range(x.shape[1])]})
            pos += n
        res["lowsines"] = rows

    if "glide" in segs:
        x = out("glide")[inner:-inner]
        res["glide"] = {"rms_db": chan_db(x)}

    if "impulsetrain" in segs:
        s = segs["impulsetrain"]
        x = out("impulsetrain", gap)
        res["impulsetrain"] = {"rms_db": chan_db(x)}

    return res, env


# ------------------------------------------------------------------ driver

def analyse(manifest, probe, render, rate, align="none"):
    if rate != manifest["rate"]:
        raise ValueError(f"render is {rate} Hz but the probe is {manifest['rate']} Hz")
    if render.shape[1] == 1:
        render = np.repeat(render, 2, axis=1)
    if align == "xcorr":
        offset = find_latency(probe, render, rate)
    elif align == "none":
        offset = 0
    else:
        offset = int(align)
    segs = {s["name"]: s for s in manifest["segments"]}
    gap = int(manifest["gap"] * rate)
    centres = band_centres()
    result = {"rate": rate, "offset_samples": offset, "length_s": len(render) / rate}
    extras = {}

    s = segs["impulse"]
    result["impulse"], extras["ir"] = impulse(segment(render, s, offset, gap), s, rate)

    if "sweep" in segs and "noise" in segs:
        s = segs["sweep"]
        out = segment(render, s, offset, gap)
        inp = segment(probe, s, 0, gap)[:, 0]
        sweep = response_sweep(inp, out, rate, centres)
        s = segs["noise"]
        noise = response_noise(segment(probe, s), segment(render, s, offset), rate, centres)
        result["response"] = {"centres_hz": centres, "sweep_db": sweep, "noise_db": noise}

    if "staircase" in segs:
        s = segs["staircase"]
        result["static"] = static_curve(segment(render, s, offset), s, rate)

    if "bursts" in segs:
        s = segs["bursts"]
        result["dynamics"], extras["envelope"] = dynamics(segment(render, s, offset), s, rate)

    if "steady" in segs:
        s = segs["steady"]
        result["modulation"] = modulation(segment(render, s, offset), s, rate)

    if "left" in segs and "right" in segs:
        result["stereo"] = stereo(segment(render, segs["left"], offset), segment(render, segs["right"], offset),
                                  segs["left"], rate)
    result["silence"] = silence(segment(render, segs["silence"], offset))

    if manifest.get("kind") == "ext":
        result["ext"], extras["ext_envelope"] = ext_measures(manifest, probe, render, rate, offset)
    return result, extras


def write_outputs(base, result, extras, rate, extras_base=None):
    """Writes `<base>.json`; the CSV views and the impulse response go beside it, or to `extras_base`."""
    ebase = extras_base or base
    with open(base + ".json", "w") as f:
        json.dump(result, f, indent=1)
    r = result.get("response")
    if r:
        with open(ebase + ".response.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["freq_hz", "sweep_left_db", "sweep_right_db", "noise_left_db", "noise_right_db"])
            for i, c in enumerate(r["centres_hz"]):
                w.writerow([f"{c:.1f}"] + [("" if v[i] is None else f"{v[i]:.3f}") for v in r["sweep_db"] + r["noise_db"]])
    if result.get("static"):
        with open(ebase + ".static.csv", "w", newline="") as f:
            w = csv.writer(f)
            keys = ["in_db", "left_out_db", "right_out_db", "left_gain_db", "right_gain_db", "left_thd_pct", "right_thd_pct"]
            w.writerow(keys)
            for row in result["static"]:
                w.writerow(["" if row.get(k) is None else f"{row[k]:.3f}" for k in keys])
    if "envelope" in extras:
        t, g = extras["envelope"]
        with open(ebase + ".envelope.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["time_s", "gain_db"])
            for a, b in zip(t, g):
                w.writerow([f"{a:.5f}", f"{b:.3f}"])
    if "ext_envelope" in extras:
        with open(ebase + ".ext-envelope.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["segment", "time_s", "in_db", "left_db", "right_db"])
            for name, (t, ind, l, r) in extras["ext_envelope"].items():
                for row in zip(t, ind, l, r):
                    w.writerow([name, f"{row[0]:.5f}"] + [f"{x:.3f}" for x in row[1:]])
    write_wav(ebase + ".ir.wav", rate, extras["ir"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest", help="probe.json from signals.py")
    ap.add_argument("renders", nargs="+")
    ap.add_argument("-o", "--out", default="results")
    ap.add_argument("--align", default="none", help="none (default), xcorr, or an offset in samples")
    a = ap.parse_args(argv)
    if a.align not in ("none", "xcorr"):
        try:
            int(a.align)
        except ValueError:
            ap.error("--align must be none, xcorr or a whole number of samples")
    with open(a.manifest) as f:
        manifest = json.load(f)
    probe_path = os.path.splitext(a.manifest)[0] + ".wav"
    prate, probe = read_wav(probe_path)
    os.makedirs(a.out, exist_ok=True)
    failed = 0
    for path in a.renders:
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            rate, audio = read_wav(path)
            result, extras = analyse(manifest, probe, audio, rate, a.align)
        except (ValueError, KeyError) as e:
            print(f"{path}: {e}", file=sys.stderr)
            failed += 1
            continue
        result["source"] = os.path.abspath(path)
        write_outputs(os.path.join(a.out, name), result, extras, rate)
        line = f"{name}: peak {result['impulse']['peak_db']:.1f} dB, taps {len(result['impulse']['taps'])}"
        if "static" in result:
            d = result["dynamics"]
            line += (f", 1 kHz gain {result['static'][-8]['left_gain_db']:.2f} dB, "
                     f"attack t63 {d['attack']['t63_ms']}, release t63 {d['release']['t63_ms']}")
        print(line)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
