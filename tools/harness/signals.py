# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Builds the probe: one stereo WAV holding every test signal in turn, and a manifest that says
where each one starts, so a single render per setting measures everything.

    python signals.py -o probe.wav [--rate 48000] [--gap 2] [--tempo 120]

writes probe.wav and probe.json. Segments, each followed by `gap` seconds of silence for the
device's tail (use --gap 10 or more for reverbs and long delays):

  impulse    one sample at -6 dBFS: impulse response, delay taps, decay time
  sweep      exponential sine sweep 20 Hz - 20 kHz at -12 dBFS: frequency response
  staircase  1 kHz sine from -60 to 0 dBFS in 3 dB steps: static gain curve, distortion per level
  bursts     1 kHz sine, -30 dBFS, then -6 dBFS, then -30 dBFS: attack and release
  steady     1 kHz sine at -12 dBFS for 8 s: modulation rate and depth (amplitude and pitch)
  noise      white noise at -18 dBFS RMS: averaged response of time-varying devices
  left/right 1 kHz sine at -12 dBFS in one channel only: stereo matrix
  silence    nothing: what the device adds on its own (noise, crackle)

`--kind ext` writes the extended probe instead (build_ext; use --gap 1): the impulse, then a
100 Hz staircase, sines at 10 and 15 kHz (aliasing), 3 kHz and 50 Hz, 1 kHz bursts of 1 to 300 ms,
bursts over a -30 dBFS bed (release after a click, 100 ms and 3 s), 60 + 200 Hz + 2 kHz, a loud
left and a quieter right channel, mid-only and side-only noise, a DC step, 1, 5 and 20 Hz sines,
a 10 dB/s level ramp up and down, a 200 to 400 Hz glide, a 150 Hz saw, an impulse train,
silence, and 60 Hz bursts over a bed.
"""

import argparse
import json
import math
import os

import numpy as np

from wavio import write_wav

FADE = 0.005


def db(x):
    return 10.0 ** (x / 20.0)


def fade(sig, rate):
    n = min(int(FADE * rate), len(sig) // 2)
    if n > 0:
        ramp = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n))
        sig[:n] *= ramp
        sig[-n:] *= ramp[::-1]
    return sig


def sine(freq, seconds, rate, level_db, phase=0.0):
    t = np.arange(int(round(seconds * rate))) / rate
    return db(level_db) * np.sin(2 * np.pi * freq * t + phase)


def log_sweep(f0, f1, seconds, rate, level_db):
    n = int(round(seconds * rate))
    t = np.arange(n) / rate
    k = np.log(f1 / f0)
    return db(level_db) * np.sin(2 * np.pi * f0 * seconds / k * (np.exp(t * k / seconds) - 1))


def staircase(freq, lo_db, hi_db, step_db, step_s, rate):
    levels = np.arange(lo_db, hi_db + step_db / 2, step_db)
    n_step = int(round(step_s * rate))
    t = np.arange(n_step * len(levels)) / rate
    env = np.repeat(db(levels), n_step)
    return env * np.sin(2 * np.pi * freq * t), [float(x) for x in levels]


def build(rate=48000, gap=2.0, tempo=120.0, seed=1):
    rng = np.random.default_rng(seed)
    segments = []
    parts = []
    pos = 0

    def add(name, left, right=None, **info):
        nonlocal pos
        right = left if right is None else right
        seg = np.stack([left, right], axis=1)
        segments.append(dict(name=name, start=pos, length=len(seg), **info))
        parts.append(seg)
        pos += len(seg)
        silence = np.zeros((int(round(gap * rate)), 2))
        parts.append(silence)
        pos += len(silence)

    # lead-in so lookahead devices start settled
    lead = np.zeros((int(0.5 * rate), 2))
    parts.append(lead)
    pos += len(lead)

    imp = np.zeros(1)
    imp[0] = db(-6)
    add("impulse", imp, level_db=-6.0)

    add("sweep", fade(log_sweep(20.0, 20000.0, 4.0, rate, -12.0), rate), f0=20.0, f1=20000.0, level_db=-12.0)

    stair, levels = staircase(1000.0, -60.0, 0.0, 3.0, 0.25, rate)
    add("staircase", fade(stair, rate), freq=1000.0, levels_db=levels, step_length=int(round(0.25 * rate)))

    phase = int(round(1.0 * rate))
    t = np.arange(3 * phase) / rate
    env = np.concatenate([np.full(phase, db(-30)), np.full(phase, db(-6)), np.full(phase, db(-30))])
    add("bursts", fade(env * np.sin(2 * np.pi * 1000.0 * t), rate), freq=1000.0, low_db=-30.0, high_db=-6.0,
        phase_length=phase)

    add("steady", fade(sine(1000.0, 8.0, rate, -12.0), rate), freq=1000.0, level_db=-12.0)

    noise = rng.standard_normal(int(4.0 * rate))
    noise *= db(-18) / np.sqrt(np.mean(noise ** 2))
    noise_r = rng.standard_normal(len(noise))
    noise_r *= db(-18) / np.sqrt(np.mean(noise_r ** 2))
    add("noise", fade(noise, rate), fade(noise_r, rate), level_db=-18.0, seed=seed)

    s = fade(sine(1000.0, 1.0, rate, -12.0), rate)
    add("left", s, np.zeros_like(s), freq=1000.0, level_db=-12.0)
    add("right", np.zeros_like(s), s, freq=1000.0, level_db=-12.0)

    add("silence", np.zeros(int(2.0 * rate)))

    audio = np.concatenate(parts)
    manifest = dict(suhina_probe_signal=1, rate=rate, channels=2, length=len(audio), gap=gap,
                    tempo=tempo, segments=segments)
    return audio, manifest


def bursts_at(freq, level_db, starts_s, lengths_s, total_s, rate, bed_db=None):
    """A sine of `freq` that is at `level_db` during each burst and at `bed_db` (or silent)
    elsewhere. Bursts start and end on whole cycles, so the steps fall on zero crossings."""
    n = int(round(total_s * rate))
    env = np.full(n, 0.0 if bed_db is None else db(bed_db))
    for s, length in zip(starts_s, lengths_s):
        a = int(round(s * rate))
        env[a:a + int(round(length * rate))] = db(level_db)
    return env * np.sin(2 * np.pi * freq * np.arange(n) / rate)


def build_ext(rate=48000, gap=1.0, tempo=120.0, seed=2):
    """The extended probe: the signals the first probe lacks, for the gaps its renders left open
    (low-frequency curves, aliasing, detector and release tests, stereo link and mid/side, DC,
    level hysteresis, pitch). It starts with the same impulse, so renders align the same way."""
    rng = np.random.default_rng(seed)
    segments, parts = [], []
    pos = 0

    def add(name, left, right=None, **info):
        nonlocal pos
        right = left if right is None else right
        seg = np.stack([left, right], axis=1)
        segments.append(dict(name=name, start=pos, length=len(seg), **info))
        parts.append(seg)
        pos += len(seg)
        parts.append(np.zeros((int(round(gap * rate)), 2)))
        pos += len(parts[-1])

    parts.append(np.zeros((int(0.5 * rate), 2)))
    pos += len(parts[-1])

    imp = np.zeros(1)
    imp[0] = db(-6)
    add("impulse", imp, level_db=-6.0)

    stair, levels = staircase(100.0, -60.0, 0.0, 3.0, 0.25, rate)
    add("stair100", fade(stair, rate), freq=100.0, levels_db=levels, step_length=int(round(0.25 * rate)))

    for f, lvl in ((10000.0, -6.0), (15000.0, -6.0), (3000.0, -12.0), (50.0, -6.0)):
        add(f"tone{f / 1000:g}k" if f >= 1000 else f"tone{f:g}", fade(sine(f, 1.0 if f >= 1000 else 2.0, rate, lvl), rate),
            freq=f, level_db=lvl)

    lengths = [0.001, 0.005, 0.01, 0.03, 0.1, 0.3]
    starts, t = [], 0.1
    for length in lengths:
        starts.append(t)
        t += length + 0.7
    add("shortbursts", bursts_at(1000.0, -6.0, starts, lengths, t, rate), freq=1000.0, level_db=-6.0,
        burst_starts_s=starts, burst_lengths_s=lengths)

    starts, lengths = [0.5, 2.0, 4.0], [0.001, 0.1, 3.0]
    add("bedbursts", fade(bursts_at(1000.0, -6.0, starts, lengths, 10.0, rate, bed_db=-30.0), rate),
        freq=1000.0, level_db=-6.0, bed_db=-30.0, burst_starts_s=starts, burst_lengths_s=lengths)

    tones = (60.0, 200.0, 2000.0)
    add("threetone", fade(sum(sine(f, 4.0, rate, -18.0) for f in tones), rate), freqs=list(tones), level_db=-18.0)

    add("lrsplit", fade(sine(1000.0, 2.0, rate, -6.0), rate), fade(sine(1000.0, 2.0, rate, -18.0), rate),
        freq=1000.0, left_db=-6.0, right_db=-18.0)

    noise = rng.standard_normal(int(2.0 * rate))
    noise = fade(noise * db(-18) / np.sqrt(np.mean(noise ** 2)), rate)
    add("mid", noise, noise, level_db=-18.0, seed=seed)
    add("side", noise, -noise, level_db=-18.0, seed=seed)

    add("dcstep", np.full(int(1.0 * rate), 0.3), level=0.3)

    lows = [(1.0, 2.0), (5.0, 1.0), (20.0, 1.0)]
    add("lowsines", np.concatenate([fade(sine(f, s, rate, -6.0), rate) for f, s in lows]),
        freqs=[f for f, _ in lows], lengths_s=[s for _, s in lows], level_db=-6.0)

    n = int(6.0 * rate)
    ramp_db = np.concatenate([np.linspace(-60.0, 0.0, n, endpoint=False), np.linspace(0.0, -60.0, n)])
    add("ramp", db(ramp_db) * np.sin(2 * np.pi * 1000.0 * np.arange(2 * n) / rate), freq=1000.0,
        from_db=-60.0, to_db=0.0, rate_db_per_s=10.0)

    secs, f0, f1 = 4.0, 200.0, 400.0
    t = np.arange(int(secs * rate)) / rate
    k = math.log(f1 / f0)
    add("glide", fade(db(-12) * np.sin(2 * np.pi * f0 * secs / k * (np.exp(t * k / secs) - 1)), rate),
        f0=f0, f1=f1, level_db=-12.0)

    f = 150.0
    t = np.arange(int(2.0 * rate)) / rate
    saw = sum(np.sin(2 * np.pi * f * h * t) / h for h in range(1, int(rate / 2 / f)))
    add("saw", fade(saw / np.max(np.abs(saw)) * db(-12), rate), freq=f, peak_db=-12.0)

    train = np.zeros(int(2.0 * rate))
    train[::int(0.1 * rate)] = db(-6)
    add("impulsetrain", train, period_s=0.1, level_db=-6.0)

    add("silence", np.zeros(int(2.0 * rate)))

    # added after the first renders, at the end so the segments above keep their places
    starts, lengths = [0.5, 2.0], [0.1, 1.0]
    add("bursts60", fade(bursts_at(60.0, -6.0, starts, lengths, 4.0, rate, bed_db=-30.0), rate),
        freq=60.0, level_db=-6.0, bed_db=-30.0, burst_starts_s=starts, burst_lengths_s=lengths)

    audio = np.concatenate(parts)
    manifest = dict(suhina_probe_signal=1, kind="ext", rate=rate, channels=2, length=len(audio), gap=gap,
                    tempo=tempo, segments=segments)
    return audio, manifest


def build_fifth(rate=48000, gap=1.0, tempo=120.0):
    """The fifth probe: three signals the others lack. A sine at a quarter of the sample rate
    at phases 0 and 45 degrees (the second has sample peaks 3 dB under its reconstructed peak), 20 Hz
    and 5 kHz staircases, and a sequence of band-limited saws (and one sine) with silences between
    them, for a pitch tracker's rest value: what it does outside its limits and after what history.
    It starts with the same impulse, so renders align the same way."""
    segments, parts = [], []
    pos = 0

    def add(name, left, right=None, **info):
        nonlocal pos
        right = left if right is None else right
        seg = np.stack([left, right], axis=1)
        segments.append(dict(name=name, start=pos, length=len(seg), **info))
        parts.append(seg)
        pos += len(seg)
        parts.append(np.zeros((int(round(gap * rate)), 2)))
        pos += len(parts[-1])

    parts.append(np.zeros((int(0.5 * rate), 2)))
    pos += len(parts[-1])

    imp = np.zeros(1)
    imp[0] = db(-6)
    add("impulse", imp, level_db=-6.0)

    f4 = rate / 4.0
    for deg in (0, 45):
        add(f"fs4_p{deg}", fade(sine(f4, 1.0, rate, -6.0, math.radians(deg)), rate),
            freq=f4, phase_deg=deg, level_db=-6.0)

    for f, step_s in ((20.0, 0.5), (5000.0, 0.25)):
        stair, levels = staircase(f, -54.0, -6.0, 3.0, step_s, rate)
        add(f"stair{f / 1000:g}k" if f >= 1000 else f"stair{f:g}", fade(stair, rate), freq=f,
            levels_db=levels, step_length=int(round(step_s * rate)))

    # (frequency in Hz, "saw" | "sine"; None is silence), one second each
    seq = [(220, "saw"), (None, ""), (1760, "saw"), (None, ""), (330, "saw"), (1760, "saw"), (None, ""),
           (1760, "saw"), (None, ""), (40, "saw"), (None, ""), (110, "saw"), (40, "saw"), (None, ""),
           (3000, "sine"), (None, ""), (150, "saw"), (3000, "sine")]
    pieces, items = [], []
    for k, (f, wave) in enumerate(seq):
        n = int(round(1.0 * rate))
        t = np.arange(n) / rate
        if f is None:
            x = np.zeros(n)
        elif wave == "saw":
            x = sum(np.sin(2 * np.pi * f * h * t) / h for h in range(1, int(rate / 2 / f)))
            x = fade(x / np.max(np.abs(x)) * db(-12), rate)
        else:
            x = fade(sine(f, 1.0, rate, -12.0), rate)
        pieces.append(x)
        items.append(dict(start_s=float(k), freq=f, wave=wave or "silence"))
    add("vocseq", np.concatenate(pieces), items=items, level_db=-12.0)

    add("silence", np.zeros(int(2.0 * rate)))

    audio = np.concatenate(parts)
    manifest = dict(suhina_probe_signal=1, kind="fifth", rate=rate, channels=2, length=len(audio), gap=gap,
                    tempo=tempo, segments=segments)
    return audio, manifest


def build_key(kind, rate=48000, gap=2.0, tempo=120.0, seed=3):
    """A side-chain key (or vocoder carrier) the length of the main probe, timed against it:

      key-duck   silence under the impulse, staircase, bursts and stereo segments; the probe's
                 own sweep and noise under its sweep and noise (so a side-chain EQ heard through
                 Listen reads as a response); under the steady tone, 1 kHz bursts of 0.5 s every
                 second at -36, -30, -24, -18, -12, -6 and 0 dBFS (gain reduction against key
                 level, and attack and release from the key)
      key-saw    a 110 Hz band-limited saw at -12 dBFS throughout (a harmonic carrier)
      key-noise  white noise at -18 dBFS RMS throughout, another seed than the probe's"""
    audio, manifest = build(rate, gap, tempo)
    n = len(audio)
    segs = {x["name"]: x for x in manifest["segments"]}
    key = np.zeros((n, 2))
    info = []
    if kind == "key-duck":
        for name in ("sweep", "noise"):
            x = segs[name]
            key[x["start"]:x["start"] + x["length"]] = audio[x["start"]:x["start"] + x["length"]]
            info.append(dict(name=name, start=x["start"], length=x["length"], same_as_probe=True))
        x = segs["steady"]
        levels = [-36.0, -30.0, -24.0, -18.0, -12.0, -6.0, 0.0]
        starts = [0.25 + i for i in range(len(levels))]
        b = np.zeros(int(round(8.0 * rate)))
        t = np.arange(len(b)) / rate
        for a, lvl in zip(starts, levels):
            i0, i1 = int(round(a * rate)), int(round((a + 0.5) * rate))
            b[i0:i1] = db(lvl)
        b = b * np.sin(2 * np.pi * 1000.0 * t)
        key[x["start"]:x["start"] + len(b)] = b[:, None]
        info.append(dict(name="keybursts", start=x["start"], length=len(b), freq=1000.0,
                         burst_starts_s=starts, burst_length_s=0.5, levels_db=levels))
    elif kind == "key-saw":
        f = 110.0
        t = np.arange(n) / rate
        saw = sum(np.sin(2 * np.pi * f * h * t) / h for h in range(1, int(rate / 2 / f)))
        key[:] = fade(saw / np.max(np.abs(saw)) * db(-12), rate)[:, None]
        info.append(dict(name="saw", start=0, length=n, freq=f, peak_db=-12.0))
    elif kind == "key-noise":
        rng = np.random.default_rng(seed)
        w = rng.standard_normal(n)
        key[:] = fade(w * db(-18) / np.sqrt(np.mean(w ** 2)), rate)[:, None]
        info.append(dict(name="noise", start=0, length=n, level_db=-18.0, seed=seed))
    else:
        raise ValueError(f"no key {kind!r}")
    return key, dict(suhina_probe_signal=1, kind=kind, rate=rate, channels=2, length=n, gap=gap,
                     tempo=tempo, segments=info, timed_against="the main probe (build)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output", default="probe.wav")
    ap.add_argument("--kind", choices=("main", "ext", "fifth", "key-duck", "key-saw", "key-noise"), default="main",
                    help="the main probe, the extended one (build_ext) with the signals it lacks, or a "
                         "side-chain key timed against the main probe (build_key); the fifth probe (build_fifth) "
                         "has the quarter-sample-rate tones, 20 Hz and 5 kHz staircases and the saw sequence")
    ap.add_argument("--rate", type=int, default=48000)
    ap.add_argument("--gap", type=float, default=2.0, help="seconds of silence after each signal")
    ap.add_argument("--tempo", type=float, default=120.0, help="the set's tempo, recorded in the manifest")
    a = ap.parse_args()
    if not 8000 <= a.rate <= 384000:
        ap.error("--rate must be 8000 to 384000")
    if not 0.1 <= a.gap <= 120:
        ap.error("--gap must be 0.1 to 120 seconds")
    if a.kind.startswith("key-"):
        audio, manifest = build_key(a.kind, a.rate, a.gap, a.tempo)
    else:
        audio, manifest = {"ext": build_ext, "fifth": build_fifth}.get(a.kind, build)(a.rate, a.gap, a.tempo)
    write_wav(a.output, a.rate, audio)
    with open(os.path.splitext(a.output)[0] + ".json", "w") as f:
        json.dump(manifest, f, indent=1)
    print(f"wrote {a.output}: {len(audio) / a.rate:.1f} s at {a.rate} Hz, {len(manifest['segments'])} signals")


if __name__ == "__main__":
    main()
