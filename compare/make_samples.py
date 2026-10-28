"""Makes the samples in samples/: an impulse and white noise to compare a device with.

    python compare/make_samples.py

Each is stereo, 44.1 kHz (the sample rate of the sets), 32-bit float and 10 s long, peaking at
-3 dBFS. `impulse` is one sample on both sides at 0.5 s, then silence for a device's tail;
`white-noise` is 5 s of independent white noise on each side with 50 ms fades, then 5 s of
silence, seeded so it is the same when made again.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "harness"))
from wavio import write_wav

RATE = 44100
LENGTH = 10.0
HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(1)
N = int(RATE * LENGTH)
NOISE = int(RATE * 5.0)


def impulse():
    out = np.zeros(N)
    out[int(0.5 * RATE)] = 1.0
    return out, out


def white():
    i = np.arange(NOISE)
    fade = np.minimum(1, i / (0.05 * RATE)) * np.minimum(1, (NOISE - i) / (0.05 * RATE))
    return rng.standard_normal(NOISE) * fade, rng.standard_normal(NOISE) * fade


SAMPLES = {"impulse": impulse, "white-noise": white}


def main():
    os.makedirs(os.path.join(HERE, "samples"), exist_ok=True)
    for name, make in SAMPLES.items():
        left, right = make()
        data = np.zeros((N, 2))
        data[:len(left), 0], data[:len(right), 1] = left, right
        data *= 10 ** (-3 / 20) / np.abs(data).max()
        write_wav(os.path.join(HERE, "samples", name + ".wav"), RATE, data)
        print(name)


if __name__ == "__main__":
    main()
