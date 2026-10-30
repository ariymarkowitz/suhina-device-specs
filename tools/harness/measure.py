# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Measures Live's devices: builds a Live Set from a device's runs, and analyses the renders.

    python measure.py list                              # devices, their runs, and what is already measured
    python measure.py check [DEVICE ...]                # every run's values against the dump and the map
    python measure.py build [DEVICE ...] [--run RUN ...]   # cases files and the set, in work/sets/<name>/
    python measure.py analyse [DEVICE ...] [--run RUN ...] [--export DIR] [--trim]
    python measure.py summary [DEVICE ...] [--run RUN ...]   # key figures per case

DEVICE is a folder of `devices/` or any part of its name (`29.01-amp`, `29.01`, `amp`); none
means every audio effect. A set holds the runs of the devices named, so measuring one device is
`build amp`, and everything is `build`.

**Runs.** Each device folder (`devices/29.NN-name/`) holds a `runs.py` with `DEVICE` (its display
name) and `RUNS`, a list of dicts:

    {"name": "compressor-ratio",          # unique over all devices; starts with the device's slug
     "plan": "2",                         # the step(s) of the note's Measurement plan it answers
     "question": "slope above the threshold for Ratio 2 to inf, hard knee, Peak",
     "read": ["static"],                  # which parts of analyse.py's result answer it
     "probe": "gap2",                     # a probe of probes.py (default gap2)
     "base": {"Model": {"item": "Peak"}}, # every case, and the run's `default`, has these
     "cases": [["ratio-2", {"Ratio": {"display": 2}}], ...]}

Value specs are make_als.py's (`{"norm": x}`, `{"display": x}` in base units, `{"item": "Peak"}`,
a bare API value, `{"stored": x}`), and its stored elements (`"@Input_RoutingMode": 0`),
automation lanes (`{"auto": [[beat, spec], ...]}`) and key tracks (`"key:key-duck"`). Every run
gets a `bypass` case (Device On off) and a `default` case (the base alone) in front of its own.
`check` works out every value against the dump and the map, as `build` would, so a wrong name or
an impossible value shows before Live is involved.

**Build.** `build` writes each run's cases file into its device's `cases/` (`<run>.json`), then
one set from all of them in `work/sets/<name>/<name>.als` (`<name>` is the device's slug for one
device, `batch` for several, or `--name`), ordered by probe so each probe's tracks are together,
with `make_als.py build --share`: every run's `bypass` of a device, and any case another run
already has, plays on one track, and is rendered and analysed once. It makes the probes it needs
in `probes/`, and prints the commands to open and check the set in Live and the export
settings (`tools/README.md` › 2, step 5).

**Export.** Open the set (`live_check.py open`), check it (`live_check.py verify`), then export
into `work/sets/<name>/export/`: either each probe's tracks on their own, under the name `<name>`
for the main probe (`gap2`) and `<name>-<probe>` for the others (select that group's tracks,
Rendered Track Selected Tracks Only, the probe's length), or every track at once under `<name>`
at the longest probe's length, and `analyse --trim` cuts each render back to its own probe's
length.

**Analyse.** For each probe group, the bypass renders give the export's offset against the probe
(Live has exported a whole set 40 ms early); every track of the group is analysed with that offset.
The measurements go to the device's `results/<track>.json` (the data a device is built from), the
CSV views and impulse responses to its `extras/`, and the render is then filed in its
`renders/<track>.wav` (`--no-file` leaves it; analysing again finds renders there). The renders
and extras are not in the repository.
"""

import argparse
import copy
import glob
import importlib.util
import json
import math
import os
import sys
from collections import Counter

import als
import analyse
import make_als
import probes
from wavio import read_wav, write_wav

ROOT = make_als.ROOT
DEVICES = os.path.join(ROOT, "devices")
SETS = os.path.join(ROOT, "work", "sets")
MAIN_PROBE = "gap2"


def device_folders(selectors=None, audio_only=True):
    """Device folder names matching the selectors (the whole name or any part of it); none means
    every audio effect (`29.*`), or every device with `audio_only` false."""
    every = sorted(d for d in os.listdir(DEVICES) if os.path.exists(os.path.join(DEVICES, d, "runs.py")))
    if not selectors:
        return [d for d in every if d.startswith("29.")] if audio_only else every
    out = []
    for sel in selectors:
        exact = [d for d in every if d == sel]
        hits = exact or [d for d in every if sel in d]
        if len(hits) != 1:
            raise SystemExit(f"{sel!r} matches {', '.join(hits) if hits else 'no device'}; "
                             f"the devices are {', '.join(every)}")
        out.append(hits[0])
    return out


def load_runs(paths=None):
    """{run name: (run dict, device display name, device folder)} from the runs.py files."""
    if not paths:
        paths = [os.path.join(DEVICES, d, "runs.py") for d in device_folders()]
    out = {}
    for path in paths:
        spec = importlib.util.spec_from_file_location(f"runs_{len(out)}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for r in mod.RUNS:
            if r["name"] in out:
                raise SystemExit(f"{path}: run {r['name']} is also in {out[r['name']][2]}")
            out[r["name"]] = (r, mod.DEVICE, os.path.dirname(os.path.abspath(path)))
    return out


def run_cases(r):
    """The run's cases, with `bypass` and `default` in front."""
    base = dict(r.get("base") or {})
    out = [{"id": "bypass", "params": {"Device On": 0}}, {"id": "default", "params": dict(base)}]
    for cid, params in r["cases"]:
        p = dict(base)
        p.update(params)
        out.append({"id": cid, "params": p})
    ids = [c["id"] for c in out]
    dup = [i for i, n in Counter(ids).items() if n > 1]
    if dup:
        raise ValueError(f"duplicate case ids {dup}")
    return out


def check_run(r, device, dump, amap, devices_root):
    """Problems with a run's values, worked out as make_als.py build would."""
    problems = []
    try:
        cs = run_cases(r)
    except ValueError as e:
        return [str(e)]
    dd = make_als.dump_device(dump, device)
    cls = dd["class_name"]
    if cls not in amap:
        return [f"{cls} is not in the map"]
    dparams = make_als.dump_params(dd)
    mparams = amap[cls]["params"]
    dev = make_als.source_device(devices_root, dd)
    for c in cs:
        for name, vspec in c["params"].items():
            if make_als.is_element(name):
                if isinstance(vspec, str) and vspec.startswith("key:"):
                    if vspec[4:] not in probes.PROBES and not os.path.exists(os.path.join(ROOT, vspec[4:])):
                        problems.append(f"{c['id']}: {name}: key {vspec[4:]} not found")
                    vspec = "AudioIn/Track.0/PostFxOut"
                elif isinstance(vspec, dict) and "midi" in vspec:
                    import midi_set
                    try:
                        midi_set.norm_clip(vspec["midi"])
                    except (ValueError, KeyError) as e:
                        problems.append(f"{c['id']}: {name}: {e}")
                    vspec = "MidiIn/Track.0/TrackOut"
                try:
                    make_als.set_element(copy.deepcopy(dev), name, vspec)
                except ValueError as e:
                    problems.append(f"{c['id']}: {e}")
                continue
            item, dp = mparams.get(name), dparams.get(name)
            if dp is None:
                problems.append(f"{c['id']}: no parameter {name!r}")
                continue
            if item is None:
                problems.append(f"{c['id']}: {name} is not in the map")
                continue
            try:
                rng = als.controller_range(als.parameter(dev, item["element"]))
                if make_als.is_auto(vspec):
                    make_als.auto_points(item, dp, vspec, rng)
                else:
                    make_als.stored_value(item, dp, vspec, rng)
            except ValueError as e:
                problems.append(f"{c['id']}: {name}: {e}")
    for k in ("name", "question", "cases"):
        if not r.get(k):
            problems.append(f"no {k}")
    if probe_of(r) not in probes.PROBES:
        problems.append(f"no probe {probe_of(r)!r}")
    return problems


def cmd_check(a):
    runs = load_runs([os.path.join(DEVICES, d, "runs.py") for d in device_folders(a.devices)])
    dump = make_als.load_json(make_als.DEFAULTS["dump"])
    amap = make_als.load_json(make_als.DEFAULTS["map"])["devices"]
    devices_root = als.read_set(make_als.DEFAULTS["devices"])
    bad = 0
    tracks = 0
    for name, (r, device, folder) in runs.items():
        ps = check_run(r, device, dump, amap, devices_root)
        n = len(r["cases"]) + 2
        tracks += n
        print(f"{'FAIL' if ps else 'ok  '} {name:44} {device:24} {n:3} cases")
        for p in ps:
            print(f"       {p}")
        bad += bool(ps)
    print(f"{len(runs)} runs, {tracks} cases, {bad} with problems")
    return 1 if bad else 0


def selection(a):
    """(set name, [run names], runs) for the command line's devices and --run."""
    folders = device_folders(a.devices)
    runs = load_runs([os.path.join(DEVICES, d, "runs.py") for d in folders])
    names = list(runs)
    if a.run:
        missing = [n for n in a.run if n not in runs]
        if missing:
            raise SystemExit(f"no run {', '.join(missing)} in {', '.join(folders)}")
        names = list(a.run)
    if a.name:
        name = a.name
    elif len(folders) == 1:
        name = folders[0].split("-", 1)[1]
    else:
        name = "batch"
    return name, names, runs


def probe_of(r):
    return r.get("probe", MAIN_PROBE)


def set_dir(name):
    return os.path.join(SETS, name)


def set_path(name):
    return os.path.join(set_dir(name), name + ".als")


def cases_path(name):
    return os.path.join(set_dir(name), name + ".cases.json")


def export_name(name, probe_key):
    return name if probe_key == MAIN_PROBE else f"{name}-{probe_key}"


def plan(name, names, runs):
    """Writes each run's cases file and the set from them; returns make_als.py build's status."""
    groups = []
    for n in names:
        if probe_of(runs[n][0]) not in groups:
            groups.append(probe_of(runs[n][0]))
    files = []
    for n in sorted(names, key=lambda n: groups.index(probe_of(runs[n][0]))):
        r, device, folder = runs[n]
        spec = {"device": device, "parameter": n, "question": r["question"], "plan": r.get("plan"),
                "read": r.get("read"), "probe": probe_of(r), "cases": run_cases(r)}
        path = os.path.join(folder, "cases", n + ".json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(json.dumps(spec, indent=1) + "\n")
        files.append(path)
    os.makedirs(set_dir(name), exist_ok=True)
    return make_als.main(["build", *files, "-o", set_path(name), "--share", "--probe", groups[0]])


def bars(manifest):
    """The probe's length in bars of 4/4 at the manifest's tempo, rounded up."""
    return math.ceil(manifest["length"] / manifest["rate"] * manifest["tempo"] / 240)


def cmd_build(a):
    name, names, runs = selection(a)
    status = plan(name, names, runs)
    if status:
        return status
    spec = make_als.load_json(cases_path(name))
    keys = []
    for c in spec["cases"]:
        k = os.path.splitext(os.path.basename(c["probe"]))[0]
        if k not in keys:
            keys.append(k)
    tracks = len({c["track"] for c in spec["cases"]})
    export = os.path.join(set_dir(name), "export")
    live = os.path.join("tools", "harness", "live_check.py")
    print(f"\n{len(names)} runs, {len(spec['cases'])} cases on {tracks} tracks: {os.path.relpath(set_path(name), ROOT)}")
    print("\nNext, in Live (tools/README.md > 2, step 5):")
    print(f"  python {live} open {os.path.relpath(set_path(name), ROOT)}")
    print(f"  python {live} verify {os.path.relpath(cases_path(name), ROOT)} -o "
          f"{os.path.relpath(os.path.join(set_dir(name), name + '.verified.json'), ROOT)}")
    print("  File > Export Audio/Video: All Individual Tracks, WAV, 32-bit, Normalize off, into")
    print(f"  {os.path.relpath(export, ROOT)}/, from 1.1.1, for the length below, under the name below:")
    for k in keys:
        m = make_als.load_json(os.path.splitext(make_als.probe_path(k))[0] + ".json")
        print(f"    {export_name(name, k):24} {bars(m)} bars ({m['length'] / m['rate']:.0f} s)"
              + ("  (with only this probe's tracks selected)" if len(keys) > 1 else ""))
    if len(keys) > 1:
        print(f"  or all tracks at once under '{name}' at the longest length, then analyse with --trim")
    print(f"Then: python tools/harness/measure.py analyse {' '.join(a.devices)}"
          + (f" --name {a.name}" if a.name else ""))
    return 0


def file_name(track):
    """A track's name as Live writes it in an export's file name ("/" becomes "_"); the
    analysis files use it too."""
    return track.replace("/", "_")


def cmd_analyse(a):
    name, names, runs = selection(a)
    if not os.path.exists(cases_path(name)):
        status = plan(name, names, runs)
        if status:
            return status
    spec = make_als.load_json(cases_path(name))
    folder_of = {n: runs[n][2] for n in names}
    export = a.export or os.path.join(set_dir(name), "export")
    groups = {}
    for c in spec["cases"]:
        if c["run"] in folder_of:
            groups.setdefault(os.path.splitext(os.path.basename(c["probe"]))[0], []).append(c)
    failed = 0
    for key, cs in groups.items():
        probe_wav = make_als.probe_path(key)
        manifest = make_als.load_json(os.path.splitext(probe_wav)[0] + ".json")
        prate, probe = read_wav(probe_wav)
        ename = export_name(name, key)

        def wav(c):
            """The render of a case's track: in the export, or filed under its device."""
            track = file_name(c["track"])
            filed = os.path.join(folder_of[c["run"]], "renders")
            for p in (os.path.join(export, f"{ename} {track}.wav"), os.path.join(export, f"{name} {track}.wav"),
                      os.path.join(filed, f"{track}.wav")):
                if os.path.exists(p):
                    return p
            # a shared track is named after the first run that had it, which differs between sets
            if c["case"] in ("bypass", "default"):
                found = glob.glob(os.path.join(glob.escape(filed), f"* {c['case']}.wav"))
                if len(found) == 1:
                    return found[0]
            return os.path.join(export, f"{ename} {track}.wav")

        # the export's offset, from every bypass render of the group
        offsets = {}
        for c in cs:
            if c["case"] == "bypass" and c["track"] == c["id"] and os.path.exists(wav(c)):
                rate, audio = read_wav(wav(c))
                offsets[c["track"]] = analyse.find_latency(probe, audio[:len(probe)], rate)
        if not offsets:
            raise SystemExit(f"no bypass render of {key} in {export} (looked for '{ename} <track>.wav')")
        offset, votes = Counter(offsets.values()).most_common(1)[0]
        odd = {t: o for t, o in offsets.items() if o != offset}
        print(f"{key}: export '{ename}', offset {offset} samples from {votes} of {len(offsets)} bypass renders"
              + (f"; disagreeing: {odd}" if odd else ""))
        done = set()
        for c in cs:
            if c["track"] != c["id"] or c["track"] in done:
                continue  # a shared track is analysed once, under the case that has it
            done.add(c["track"])
            path = wav(c)
            if not os.path.exists(path):
                print(f"missing {path}", file=sys.stderr)
                failed += 1
                continue
            folder = folder_of[c["run"]]
            rate, audio = read_wav(path)
            if a.trim and len(audio) > len(probe):
                # rendered past its probe's end (one export at the longest probe's length): cut to size
                audio = audio[:len(probe)]
                write_wav(path, rate, audio)
            try:
                result, extras = analyse.analyse(manifest, probe, audio, rate, str(offset))
            except (ValueError, KeyError) as e:
                print(f"{path}: {e}", file=sys.stderr)
                failed += 1
                continue
            filed = os.path.join(folder, "renders", file_name(c["track"]) + ".wav")
            result["source"] = os.path.relpath(path if a.no_file else filed, ROOT)
            for d in ("results", "extras"):
                os.makedirs(os.path.join(folder, d), exist_ok=True)
            analyse.write_outputs(os.path.join(folder, "results", file_name(c["track"])), result, extras, rate,
                                  extras_base=os.path.join(folder, "extras", file_name(c["track"])))
            if not a.no_file and os.path.abspath(path) != os.path.abspath(filed):
                os.makedirs(os.path.dirname(filed), exist_ok=True)
                os.replace(path, filed)
        print(f"{key}: {len(done)} renders analysed")
    return 1 if failed else 0


OCTAVES = [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]


def nearest(centres, f):
    return min(range(len(centres)), key=lambda i: abs(math.log(centres[i] / f)))


def fmt(x, nd=2):
    return "-" if x is None else f"{x:.{nd}f}"


def summarise(res, read):
    """A few lines of the figures `read` names, from one analysis result."""
    lines = []
    read = read or ["impulse", "response", "static", "dynamics", "modulation", "stereo", "silence"]
    want = " ".join(read)
    if "impulse" in want or "ir" in want or "taps" in want:
        im = res["impulse"]
        taps = ", ".join(f"{t['time_ms']:.2f}ms {t['level_db']:.1f}dB" for t in im["taps"][:8])
        lines.append(f"impulse peak {fmt(im['peak_db'])} dB, rt60 {fmt(im['rt60_s'], 3)} s; taps {taps}")
    if "response" in want or "sweep" in want or "noise" in want:
        r = res["response"]
        idx = [nearest(r["centres_hz"], f) for f in OCTAVES]
        for label, k in (("sweep", "sweep_db"), ("noise", "noise_db")):
            if k.split("_")[0] in want or "response" in want:
                for ch, vals in zip("LR", r[k]):
                    lines.append(f"{label} {ch}: " + " ".join(f"{OCTAVES[j]:g}:{fmt(vals[i], 1)}"
                                                         for j, i in enumerate(idx)))
    if "static" in want:
        rows = res["static"]
        lines.append("static in->gain(L) thd%: " + " ".join(
            f"{r['in_db']:.0f}:{fmt(r['left_gain_db'])}/{fmt(r.get('left_thd_pct'), 1)}" for r in rows[::2]))
    if "dynamics" in want:
        d = res["dynamics"]
        lines.append(f"attack {fmt(d['attack']['from_db'])}->{fmt(d['attack']['to_db'])} dB t63 {d['attack']['t63_ms']} "
                     f"t90 {d['attack']['t90_ms']} ms; release {fmt(d['release']['from_db'])}->"
                     f"{fmt(d['release']['to_db'])} dB t63 {d['release']['t63_ms']} t90 {d['release']['t90_ms']} ms")
    if "modulation" in want:
        m = res["modulation"]
        for ch in ("left", "right"):
            x = m.get(ch) or {}
            am, fm = x.get("am") or {}, x.get("fm") or {}
            lines.append(f"mod {ch}: level {fmt(x.get('level_db'))} dB, AM {fmt(am.get('depth_db'))} dB at "
                         f"{fmt(am.get('rate_hz'), 3)} Hz, FM {fmt(fm.get('depth_cents'))} c at "
                         f"{fmt(fm.get('rate_hz'), 3)} Hz, mean {fmt(fm.get('mean_cents'))} c")
        if m.get("envelope_correlation") is not None:
            lines.append(f"mod L/R envelope correlation {fmt(m['envelope_correlation'])}")
    if "stereo" in want:
        st = res["stereo"]
        lines.append("stereo " + " ".join(f"{k.replace('_db', '')} {fmt(v, 1)}" for k, v in st.items()))
    if "silence" in want:
        lines.append(f"silence rms {res['silence']['rms_db']} peak {res['silence']['peak_db']} dB")
    return lines


def cmd_summary(a):
    name, names, runs = selection(a)
    if not os.path.exists(cases_path(name)):
        plan(name, names, runs)
    spec = make_als.load_json(cases_path(name))
    track_run = {c["id"]: c["run"] for c in spec["cases"] if c["track"] == c["id"]}
    for n in names:
        r = runs[n][0]
        print(f"## {n} ({runs[n][1]}; plan {r.get('plan')}): {r['question']}")
        for c in spec["cases"]:
            if c["run"] != n:
                continue
            path = os.path.join(runs[track_run[c["track"]]][2], "results", file_name(c["track"]) + ".json")
            if not os.path.exists(path):
                print(f"  {c['case']}: no result")
                continue
            print(f"  {c['case']}:")
            for line in summarise(make_als.load_json(path), a.read or r.get("read")):
                print(f"    {line}")
    return 0


def cmd_list(a):
    for d in device_folders(a.devices, audio_only=False):
        folder = os.path.join(DEVICES, d)
        runs = load_runs([os.path.join(folder, "runs.py")])
        results = os.path.join(folder, "results")
        have = len([f for f in os.listdir(results) if f.endswith(".json")]) if os.path.isdir(results) else 0
        print(f"{d:34} {len(runs):3} runs, {have:4} results")
        if a.devices:
            for n, (r, _, _) in runs.items():
                print(f"    {n:44} {len(r['cases']) + 2:3} cases  {r['question']}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, run=True):
        p.add_argument("devices", nargs="*", metavar="DEVICE", help="default: every audio effect")
        if run:
            p.add_argument("--run", nargs="*", help="only these runs")
            p.add_argument("--name", help="the set's name (default: the device's slug, or batch)")

    common(sub.add_parser("check"), run=False)
    common(sub.add_parser("list"), run=False)
    common(sub.add_parser("build"))
    n = sub.add_parser("analyse")
    common(n)
    n.add_argument("--export", help="the folder Live exported into (default: work/sets/<name>/export)")
    n.add_argument("--trim", action="store_true",
                   help="cut each render to its probe's length in place (after one export of every track "
                        "at the longest probe's length)")
    n.add_argument("--no-file", action="store_true", help="leave the renders where they are")
    m = sub.add_parser("summary")
    common(m)
    m.add_argument("--read", nargs="*", help="parts to show instead of each run's `read`")
    a = ap.parse_args(argv)
    return {"check": cmd_check, "list": cmd_list, "build": cmd_build, "analyse": cmd_analyse,
            "summary": cmd_summary}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
