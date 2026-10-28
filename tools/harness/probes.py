# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""The probe signals the runs use, by name, kept in `probes/` (a missing one is made on first use).

    python probes.py            # make every probe that is missing
    python probes.py gap10 ext  # make these

Every probe is made at 44.1 kHz and 120 BPM by signals.py (the noise is seeded, so a remade
probe is the one the original measurements used). A run names its probe with `"probe": "<name>"`
(default `gap2`); a side-chain key is `"key:<name>"`.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DIR = os.path.join(ROOT, "probes")
RATE = 44100

# name -> signals.py arguments: the main probe with 2, 10 and 30 s of silence after each signal
# (the long gaps are for reverbs), the extended and fifth probes, and the side-chain keys.
PROBES = {
    "gap2": ["--gap", "2"],
    "gap10": ["--gap", "10"],
    "gap30": ["--gap", "30"],
    "ext": ["--kind", "ext", "--gap", "1"],
    "fifth": ["--kind", "fifth", "--gap", "1"],
    "key-duck": ["--kind", "key-duck", "--gap", "2"],
    "key-saw": ["--kind", "key-saw", "--gap", "2"],
    "key-noise": ["--kind", "key-noise", "--gap", "2"],
}


def path(name):
    """The probe's WAV, made if it is not there yet. Its manifest is beside it, as `<name>.json`."""
    if name not in PROBES:
        raise KeyError(f"no probe {name!r}; the probes are {', '.join(PROBES)}")
    wav = os.path.join(DIR, name + ".wav")
    if not (os.path.exists(wav) and os.path.exists(os.path.join(DIR, name + ".json"))):
        os.makedirs(DIR, exist_ok=True)
        subprocess.run([sys.executable, os.path.join(HERE, "signals.py"), "-o", wav, "--rate", str(RATE),
                        *PROBES[name]], check=True, stdout=subprocess.DEVNULL)
    return wav


if __name__ == "__main__":
    for n in sys.argv[1:] or PROBES:
        print(path(n))
