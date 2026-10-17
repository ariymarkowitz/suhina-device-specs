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
"""

import argparse
import json
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output", default="probe.wav")
    ap.add_argument("--rate", type=int, default=48000)
    ap.add_argument("--gap", type=float, default=2.0, help="seconds of silence after each signal")
    ap.add_argument("--tempo", type=float, default=120.0, help="the set's tempo, recorded in the manifest")
    a = ap.parse_args()
    if not 8000 <= a.rate <= 384000:
        ap.error("--rate must be 8000 to 384000")
    if not 0.1 <= a.gap <= 120:
        ap.error("--gap must be 0.1 to 120 seconds")
    audio, manifest = build(a.rate, a.gap, a.tempo)
    write_wav(a.output, a.rate, audio)
    with open(os.path.splitext(a.output)[0] + ".json", "w") as f:
        json.dump(manifest, f, indent=1)
    print(f"wrote {a.output}: {len(audio) / a.rate:.1f} s at {a.rate} Hz, {len(manifest['segments'])} signals")


if __name__ == "__main__":
    main()
