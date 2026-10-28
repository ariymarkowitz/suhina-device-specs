"""Builds a Live Set that plays a sample through a device's cases, for the side-by-side comparison.

    python compare/build_set.py DEVICE SAMPLE [--run RUN ...] [--rate 44100]

DEVICE is a folder of devices/ or part of its name (`compressor`), SAMPLE a WAV in samples/ (name
or path). The cases are those of the device's runs (devices/<device>/cases/), with the sample in
place of each run's probe; runs that need a side-chain key or MIDI are left out. Writes
sets/<device>-<sample>/ with the set (`set.als`), its cases file and an empty export/ folder, and
prints the export settings (EXPORT.md). Build the set only: nothing in it is made by hand.
"""
import argparse
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = os.path.join(ROOT, "tools", ".venv", "bin", "python")
BPM = 120


def device_folder(name):
    hits = sorted(d for d in glob.glob(os.path.join(ROOT, "devices", "*")) if name in os.path.basename(d))
    exact = [d for d in hits if os.path.basename(d) == name or os.path.basename(d).split("-", 1)[-1] == name]
    hits = exact or hits
    if len(hits) != 1:
        sys.exit(f"{name!r} matches {[os.path.basename(h) for h in hits] or 'no device'}")
    return hits[0]


def needs_other_tracks(spec):
    return any(isinstance(v, str) and (v.startswith("key:") or v.startswith("midi"))
               for c in spec["cases"] for v in c.get("params", {}).values()) or \
        any(k.startswith("midi") for c in spec["cases"] for k in c.get("params", {}))


def sample_path(s):
    p = s if os.path.exists(s) else os.path.join(HERE, "samples", s if s.endswith(".wav") else s + ".wav")
    if not os.path.exists(p):
        sys.exit(f"no sample {s!r}; run compare/make_samples.py or give a WAV at 44.1 kHz")
    return os.path.abspath(p)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("device")
    ap.add_argument("sample")
    ap.add_argument("--run", action="append", help="only these runs (the cases file's name)")
    a = ap.parse_args()

    folder = device_folder(a.device)
    slug = os.path.basename(folder).split("-", 1)[1]
    sample = sample_path(a.sample)
    name = f"{slug}-{os.path.splitext(os.path.basename(sample))[0]}"
    out = os.path.join(HERE, "sets", name)
    os.makedirs(os.path.join(out, "export"), exist_ok=True)
    os.makedirs(os.path.join(out, "cases"), exist_ok=True)

    cases = []
    for path in sorted(glob.glob(os.path.join(folder, "cases", "*.json"))):
        run = os.path.splitext(os.path.basename(path))[0]
        if a.run and run not in a.run:
            continue
        with open(path) as f:
            spec = json.load(f)
        if needs_other_tracks(spec):
            print(f"skipping {run}: it needs a key or MIDI track", file=sys.stderr)
            continue
        spec.pop("probe", None)
        dest = os.path.join(out, "cases", run + ".json")
        with open(dest, "w") as f:
            json.dump(spec, f, indent=1)
        cases.append(dest)
    if not cases:
        sys.exit("no runs to build")

    # one stereo-rate check: the set is 44.1 kHz and a sample at another rate would play at the wrong pitch
    sys.path.insert(0, os.path.join(ROOT, "tools", "harness"))
    from wavio import read_wav
    rate, audio = read_wav(sample)
    if rate != 44100:
        sys.exit(f"{sample} is {rate} Hz; the sets are 44.1 kHz")
    seconds = len(audio) / rate
    bars = seconds / (4 * 60 / BPM)

    als = os.path.join(out, "set.als")
    subprocess.run([PY, os.path.join(ROOT, "tools", "harness", "make_als.py"), "build", *cases,
                    "-o", als, "--probe", sample, "--share"], check=True, cwd=ROOT)
    with open(os.path.join(out, "info.json"), "w") as f:
        json.dump({"device": slug, "sample": os.path.basename(sample), "export_name": name,
                   "seconds": seconds, "bars": bars, "sample_rate": rate}, f, indent=1)

    print(f"""
Set: {os.path.relpath(als, ROOT)}   ({len(cases)} runs)

  {os.path.relpath(PY, ROOT)} tools/harness/live_check.py open {os.path.relpath(als, ROOT)}

Then File > Export Audio/Video:
  Rendered Track   All Individual Tracks
  Start / Length   1.1.1, {bars:g} bars ({seconds:g} s at {BPM} BPM)
  File type        WAV, 32-bit, {rate} Hz, Normalize off, Create Analysis File off
  Folder           {os.path.relpath(os.path.join(out, 'export'), ROOT)}/
  Export name      {name}
Then:
  {os.path.relpath(PY, ROOT)} compare/render_suhina.py {name}
  {os.path.relpath(PY, ROOT)} compare/make_page.py {name} --serve
""")


if __name__ == "__main__":
    main()
