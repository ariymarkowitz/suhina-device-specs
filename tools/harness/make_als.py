# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Writes a Live Set with one track per test case, without Build cases or any clicking in Live.

    python make_als.py calibrate --device Compressor -o calib.als
    python live_check.py read -o calib.read.json            # with calib.als open in Live
    python make_als.py map calib.calibration.json calib.read.json
    python make_als.py build cases.json [cases.json ...] -o measure.als [--probe probe-gap10/probe.wav]
    python live_check.py verify measure.cases.json          # with measure.als open in Live

A set holds each parameter as a stored value in its own units, under an element name that
often differs from the parameter's API name and in a different order (Compressor's Output is
`Gain`, EQ Eight's Adaptive Q comes last). So a device is first calibrated:

- `calibrate` writes a set with a `ref` track per device (its factory default) and one track per
  parameter element with only that element's stored value changed.
- Open it in Live and read every track's parameters through the AbletonMCP Remote Script
  (`live_check.py read`).
- `map` compares each track with its `ref`: the one API parameter that moved is the element's.
  From the stored and API values at the default and the changed value, and the dump's display
  text, it picks how an API value becomes a stored value (the same number; the display's number
  in Hz, s, ms, % / 100 or dB as linear gain; an index), and writes it to the map file
  (`measurements/als-map-12.4.6.json`).

`build` then writes any number of cases files (cases.py's format) into one set: a copy of the
template track per case, named `<run> <case id>` (run = the cases file's name), holding a fresh
copy of the device with the case's values. Beside the set it writes `<set>.cases.json`: every
track's device and the API value and stored value it should have. `live_check.py verify` checks
those against Live, which is the test that the set means what it should.

Value specs are cases.py's (`norm`, `value` or a plain number, `item`, `display`) plus
`{"stored": x}`, which writes x as it is. A `display` value in base units (Hz, s, dB, %) is
converted exactly; a `norm` or `value` goes through the dump's sampled display curve
(65 points), so it lands within the display's rounding (three figures) of the target.
"""

import argparse
import copy
import json
import math
import os
import re
import sys

import als
from wavio import read_wav

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DEFAULTS = {
    "dump": os.path.join(ROOT, "measurements", "dump-12.4.6.json"),
    "devices": os.path.join(ROOT, "measurements", "populate-12.4.6.als"),
    "template": os.path.join(ROOT, "measurements", "29.09-compressor", "compressor-threshold.als"),
    "track": None,
    "map": os.path.join(ROOT, "measurements", "als-map-12.4.6.json"),
    "probe": os.path.join(ROOT, "measurements", "probe.wav"),
}

# How an API value becomes a stored value, for continuous parameters, by the display's number
# in base units (Hz, s, dB, %, or the bare number). "same" uses the API value itself.
CONVERSIONS = {
    "base": lambda n: n,
    "ms": lambda n: n * 1000.0,
    "percent": lambda n: n / 100.0,
    "gain": lambda n: 10.0 ** (n / 20.0),
}
PREFERENCE = ["same", "base", "ms", "percent", "gain"]


# ---------------------------------------------------------------- display text

def parse_display(text):
    """(number in base units, unit, half of the last shown digit in base units), or None.
    Base units: Hz (from kHz), s (from ms), and the shown unit otherwise."""
    s = str(text).replace("−", "-").strip()
    m = re.match(r"^([+-]?)\s*inf\b\s*(.*)$", s, re.I)
    if m:
        return (-math.inf if m.group(1) == "-" else math.inf), m.group(2).strip(), 0.0
    m = re.match(r"^([+-]?\d+(?:\.(\d+))?)\s*(.*)$", s)
    if not m:
        return None
    n = float(m.group(1))
    half = 0.5 * 10.0 ** -(len(m.group(2)) if m.group(2) else 0)
    unit = m.group(3).strip()
    scale = {"khz": (1000.0, "Hz"), "ms": (0.001, "s")}.get(unit.lower())
    if scale:
        return n * scale[0], scale[1], half * scale[0]
    return n, unit, half


def keyed(names):
    """Unique keys for a device's parameter names: a repeated name gets ' #2', ' #3'."""
    seen = {}
    out = []
    for n in names:
        seen[n] = seen.get(n, 0) + 1
        out.append(n if seen[n] == 1 else f"{n} #{seen[n]}")
    return out


# ---------------------------------------------------------------- loading

def load_json(path):
    with open(path) as f:
        return json.load(f)


def dump_device(dump, name):
    """The dump's entry for a device by class or display name, preferring the fresh copy that
    Populate put on a track named after it."""
    hits = [d for d in dump["devices"] if name in (d.get("class_name"), d.get("class_display_name"))]
    if not hits:
        raise SystemExit(f"no device {name!r} in the dump")
    fresh = [d for d in hits if d.get("track") == d.get("class_display_name")]
    return (fresh or hits)[0]


def dump_params(device):
    return dict(zip(keyed([p["name"] for p in device["parameters"]]), device["parameters"]))


def source_device(devices_root, dump_dev):
    """A fresh copy of the device's element, from the track Populate named after it."""
    try:
        track = als.find_track(devices_root, dump_dev["class_display_name"])
        for d in als.devices_holder(track):
            if d.tag == dump_dev["class_name"]:
                return d
    except KeyError:
        pass
    return als.find_device(devices_root, dump_dev["class_name"])


def start_set(a):
    root = als.read_set(a.template)
    template = als.find_track(root, a.track) if a.track else als.clip_track(root)
    rate, audio = read_wav(a.probe)
    tempo = float(root.find("LiveSet/MainTrack/DeviceChain/Mixer/Tempo/Manual").get("Value"))
    als.point_clip_at(template, a.probe, os.path.dirname(os.path.abspath(a.output)),
                      frames=len(audio), rate=rate, tempo=tempo)
    if not a.keep_returns:
        als.remove_returns(root)
    als.clear_tracks(root)
    return root, template


def write_out(root, ids, path):
    ids.close()
    als.write_set(root, path)


# ---------------------------------------------------------------- calibrate

def changed_value(param):
    """A stored value clearly different from the element's default and inside its range."""
    text = als.manual(param)
    kind = als.stored_kind(text)
    if kind == "bool":
        return "false" if text == "true" else "true"
    v = float(text)
    rng = als.controller_range(param)
    if rng is None:
        return als.format_stored(v + 1 if kind == "int" else (v * 1.5 if v else 0.5), kind)
    lo, hi = rng
    integral = all(float(x).is_integer() for x in (lo, hi, v))
    if integral and hi - lo <= 64:
        return als.format_stored(v + 1 if v + 1 <= hi else v - 1, kind)
    if hi > 1e30:
        return als.format_stored(v * 2 if v > 0 else lo + 1, "float")
    if lo > 0 and hi / lo >= 20:
        picks = [lo * (hi / lo) ** f for f in (0.3, 0.7)]
        far = max(picks, key=lambda p: abs(math.log(p / v)) if v > 0 else p)
    else:
        picks = [lo + (hi - lo) * f for f in (0.3, 0.7)]
        far = max(picks, key=lambda p: abs(p - v))
    return als.format_stored(far, "float")


def cmd_calibrate(a):
    dump = load_json(a.dump)
    devices_root = als.read_set(a.devices)
    root, template = start_set(a)
    ids = als.Ids(root)
    record = {"set": os.path.basename(a.output), "tracks": []}
    for name in a.device:
        dd = dump_device(dump, name)
        dev = source_device(devices_root, dd)
        cls = dd["class_name"]
        als.add_track(root, template, f"ref {cls}", [dev], ids)
        record["tracks"].append({"name": f"ref {cls}", "device": cls, "element": None})
        for path, param in als.parameters(dev):
            d = copy.deepcopy(dev)
            p = als.parameter(d, path)
            new = changed_value(p)
            als.set_manual(p, new)
            tname = f"cal {cls} {path}"
            als.add_track(root, template, tname, [d], ids)
            record["tracks"].append({"name": tname, "device": cls, "element": path,
                                     "default": als.manual(param), "stored": new})
    write_out(root, ids, a.output)
    side = os.path.splitext(a.output)[0] + ".calibration.json"
    with open(side, "w") as f:
        json.dump(record, f, indent=1)
    print(f"wrote {a.output} ({len(record['tracks'])} tracks) and {side}")


# ---------------------------------------------------------------- map

def consistent(conv, pairs):
    """Whether a conversion fits every (api value, display text, stored value) pair."""
    used = 0
    for v, disp, s in pairs:
        if conv == "same":
            if abs(v - s) > 1e-5 * max(1.0, abs(s)):
                return False
            used += 1
            continue
        d = disp if isinstance(disp, tuple) else parse_display(disp)
        if d is None:
            return False
        n, _, half = d
        if math.isinf(n):
            continue
        f = CONVERSIONS[conv]
        lo, hi = sorted((f(n - half), f(n + half)))
        slack = 1e-6 * abs(s) + 1e-9
        if not lo - slack <= s <= hi + slack:
            return False
        used += 1
    return used > 0


def log_taper(dp):
    """Whether the display (in base units) follows the API value more closely in log than
    linearly: decides how to interpolate between the dump's samples. Never for dB."""
    pts = []
    for v, text in dp.get("samples", []):
        d = parse_display(text)
        if d is None or not math.isfinite(d[0]):
            continue
        if d[1] == "dB":
            return False
        pts.append((v, d[0]))
    if len(pts) < 3 or any(n <= 0 for _, n in pts):
        return False

    def r2(xs, ys):
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        sxx = sum((x - mx) ** 2 for x in xs)
        syy = sum((y - my) ** 2 for y in ys)
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        return 1.0 if sxx == 0 or syy == 0 else sxy * sxy / (sxx * syy)

    vs = [v for v, _ in pts]
    return r2(vs, [math.log(n) for _, n in pts]) > r2(vs, [n for _, n in pts])


def display_is_value(dp):
    """Whether the display's number is the API value itself (Output in dB, Knee)."""
    seen = 0
    for v, text in dp.get("samples", []):
        d = parse_display(text)
        if d is None or not math.isfinite(d[0]):
            continue
        if abs(d[0] - v) > d[2] + 1e-9:
            return False
        seen += 1
    return seen >= 2


def display_at(dp, v):
    """What the control shows at API value v, from the dump, as parse_display gives it: exact at
    the loaded value and at the samples, interpolated between them with a wider margin (the
    Remote Script does not report display text in Live 12.4.6)."""
    if dp is None:
        return None
    if abs(dp["value"] - v) < 1e-7:
        return parse_display(dp["display"])
    pts = [(sv, parse_display(t)) for sv, t in dp.get("samples", [])]
    pts = [(sv, d) for sv, d in pts if d is not None]
    for sv, d in pts:
        if abs(sv - v) < 1e-7:
            return d
    for (v0, d0), (v1, d1) in zip(pts, pts[1:]):
        if v0 <= v <= v1 and math.isfinite(d0[0]) and math.isfinite(d1[0]):
            t = (v - v0) / (v1 - v0)
            if d0[0] > 0 and d1[0] > 0 and log_taper(dp):
                n = math.exp(math.log(d0[0]) + t * math.log(d1[0] / d0[0]))
            else:
                n = d0[0] + t * (d1[0] - d0[0])
            return n, d0[1], max(d0[2], d1[2], 0.25 * abs(d1[0] - d0[0]), 0.01 * abs(n))
    return None


def choose_conversion(qparam, kind, pairs, endpoints):
    """The conversion for one parameter, or None when nothing fits."""
    if qparam:
        if kind == "bool":
            ok = all((s != 0) == (v != 0) for v, _, s in pairs)
            return {"convert": "bool"} if ok else None
        offsets = {round(s - v, 6) for v, _, s in pairs}
        return {"convert": "offset", "offset": offsets.pop()} if len(offsets) == 1 else None
    fits = [c for c in PREFERENCE if consistent(c, pairs)]
    if not fits:
        return None
    best = [c for c in fits if consistent(c, pairs + endpoints)] or fits
    return {"convert": best[0]}


def cmd_map(a):
    cal = load_json(a.calibration)
    read = load_json(a.read)
    dump = load_json(a.dump)
    devices_root = als.read_set(a.devices)
    live = {t["name"]: t for t in read["tracks"]}
    out = load_json(a.map) if os.path.exists(a.map) else {"live_version": read.get("live_version"), "devices": {}}
    by_dev = {}
    for t in cal["tracks"]:
        by_dev.setdefault(t["device"], []).append(t)
    for cls, rows in by_dev.items():
        dd = dump_device(dump, cls)
        dev = source_device(devices_root, dd)
        dparams = dump_params(dd)
        ref = live.get(f"ref {cls}")
        if ref is None or not ref["devices"]:
            print(f"{cls}: no ref track in {a.read}", file=sys.stderr)
            continue

        def values(track):
            ps = track["devices"][0]["parameters"]
            return dict(zip(keyed([p["name"] for p in ps]), ps))

        refv = values(ref)
        entry = {"display_name": dd["class_display_name"], "params": {}, "unmatched_elements": {}}
        for row in rows:
            if row["element"] is None:
                continue
            t = live.get(row["name"])
            if t is None or not t["devices"]:
                entry["unmatched_elements"][row["element"]] = "track or device missing in Live"
                continue
            now = values(t)
            moved = [k for k in refv if k in now and abs(now[k]["value"] - refv[k]["value"]) > 1e-9]
            if len(moved) != 1:
                entry["unmatched_elements"][row["element"]] = (
                    "no API parameter moved" if not moved else "several moved: " + ", ".join(moved))
                continue
            key = moved[0]
            param = als.parameter(dev, row["element"])
            dp = dparams.get(key)
            pairs = [(x[key]["value"], x[key].get("value_string") or display_at(dp, x[key]["value"]),
                      als.parse_stored(stored))
                     for x, stored in ((refv, row["default"]), (now, row["stored"]))]
            endpoints = []
            rng = als.controller_range(param)
            if rng and dp and dp.get("samples"):
                endpoints = [(dp["samples"][0][0], dp["samples"][0][1], rng[0]),
                             (dp["samples"][-1][0], dp["samples"][-1][1], rng[1])]
            quantized = bool(refv[key].get("is_quantized"))
            # "1" can be a float element's value: only a quantized parameter's element holds an index
            kind = "bool" if row["default"] in ("true", "false") else ("int" if quantized else "float")
            conv = choose_conversion(quantized, kind, pairs, endpoints)
            item = {"element": row["element"], "kind": kind, "points": [[v, s] for v, _, s in pairs]}
            if conv is None:
                item["convert"] = None
                print(f"{cls} {key} ({row['element']}): no conversion fits {pairs}", file=sys.stderr)
            else:
                item.update(conv)
            if key in entry["params"]:
                print(f"{cls} {key}: matched both {entry['params'][key]['element']} and {row['element']}",
                      file=sys.stderr)
            entry["params"][key] = item
        entry["unmatched_params"] = [k for k in refv if k not in entry["params"]]
        out["devices"][cls] = entry
        print(f"{cls}: {len(entry['params'])} parameters mapped, "
              f"{len(entry['unmatched_params'])} without an element, "
              f"{len(entry['unmatched_elements'])} elements without a parameter")
    with open(a.map, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"wrote {a.map}")


# ---------------------------------------------------------------- build

def api_value(dp, spec):
    """The API value a value spec means, or raises ValueError."""
    lo, hi = dp["min"], dp["max"]
    if isinstance(spec, (int, float)):
        v = float(spec)
    elif "value" in spec:
        v = float(spec["value"])
    elif "norm" in spec:
        v = lo + (hi - lo) * float(spec["norm"])
    elif "item" in spec:
        items = dp.get("value_items") or []
        if spec["item"] not in items:
            raise ValueError(f"no item {spec['item']!r} (has {', '.join(items)})")
        v = lo + items.index(spec["item"])
    elif "display" in spec:
        v = value_for_display(dp, float(spec["display"]))
    else:
        raise ValueError(f"bad value spec {spec!r}")
    if not lo - 1e-9 <= v <= hi + 1e-9:
        raise ValueError(f"value {v} outside {lo} .. {hi}")
    return round(v) if dp.get("is_quantized") else v


def interpolate_stored(dp, conv, rng, v):
    """The stored value at API value v: the display number interpolated between the dump's
    samples (in log for a logarithmic taper, never for dB) and converted. A sample showing
    -inf or inf stands for the end of the element's controller range."""
    f = CONVERSIONS[conv]
    pts = []
    for sv, text in dp.get("samples", []):
        d = parse_display(text)
        if d is None:
            continue
        n = d[0]
        if math.isinf(n):
            if rng is None:
                continue
            pts.append((sv, None, rng[0] if n < 0 else rng[1]))
        else:
            pts.append((sv, n, f(n)))
    log = log_taper(dp)
    for (v0, n0, s0), (v1, n1, s1) in zip(pts, pts[1:]):
        if not v0 <= v <= v1:
            continue
        t = 0.0 if v1 == v0 else (v - v0) / (v1 - v0)
        if n0 is not None and n1 is not None:
            if log and n0 > 0 and n1 > 0:
                return f(math.exp(math.log(n0) + t * (math.log(n1) - math.log(n0))))
            return f(n0 + t * (n1 - n0))
        if s0 > 0 and s1 > 0:
            return math.exp(math.log(s0) + t * (math.log(s1) - math.log(s0)))
        return s0 + t * (s1 - s0)
    return None


def curve(dp):
    """[(api value, display number in base units)] from the dump's samples, finite ones only."""
    pts = []
    for v, text in dp.get("samples", []):
        d = parse_display(text)
        if d is not None and math.isfinite(d[0]):
            pts.append((v, d[0]))
    return pts


def value_for_display(dp, n):
    """The API value whose display reads n (base units), from the sampled curve."""
    if display_is_value(dp):
        return n
    pts = curve(dp)
    log = log_taper(dp)
    for (v0, n0), (v1, n1) in zip(pts, pts[1:]):
        if min(n0, n1) <= n <= max(n0, n1):
            if n1 == n0:
                return v0
            if log and min(n0, n1, n) > 0:
                return v0 + math.log(n / n0) / math.log(n1 / n0) * (v1 - v0)
            return v0 + (n - n0) / (n1 - n0) * (v1 - v0)
    raise ValueError(f"display {n} outside the control's range")


def stored_value(item, dp, spec, rng=None):
    """(API value or None, stored text) for a value spec, through the map entry `item`; `rng` is
    the element's controller range, for display ends that read -inf or inf."""
    kind = item["kind"]
    if isinstance(spec, dict) and "stored" in spec:
        return None, als.format_stored(float(spec["stored"]), kind)
    conv = item.get("convert")
    if conv is None:
        raise ValueError("the map has no conversion for this parameter; use {\"stored\": x}")
    v = api_value(dp, spec)
    if conv == "bool":
        return v, als.format_stored(v != 0, "bool")
    if conv == "offset":
        return v, als.format_stored(v + item["offset"], kind)
    if conv == "same":
        return v, als.format_stored(v, kind)
    if isinstance(spec, dict) and "display" in spec:
        n = float(spec["display"])
    else:
        x = interpolate_stored(dp, conv, rng, v)
        if x is None:
            raise ValueError(f"no display near value {v}; use display: or stored:")
        return v, als.format_stored(x, kind)
    return v, als.format_stored(CONVERSIONS[conv](n), kind)


def cmd_build(a):
    dump = load_json(a.dump)
    devices_root = als.read_set(a.devices)
    amap = load_json(a.map)["devices"]
    root, template = start_set(a)
    ids = als.Ids(root)
    out = {"set": os.path.basename(a.output), "generated_by": "make_als.py", "cases": []}
    problems = 0
    for path in a.cases:
        spec = load_json(path)
        run = os.path.splitext(os.path.basename(path))[0]
        dd = dump_device(dump, spec["device"])
        cls = dd["class_name"]
        if cls not in amap:
            raise SystemExit(f"{path}: {cls} is not in the map yet; calibrate it first")
        dparams = dump_params(dd)
        mparams = amap[cls]["params"]
        fresh = source_device(devices_root, dd)
        for case in spec["cases"]:
            dev = copy.deepcopy(fresh)
            rec = {"id": f"{run} {case['id']}", "run": run, "case": case["id"], "device": cls,
                   "params": {}, "errors": []}
            for name, vspec in (case.get("params") or {}).items():
                item, dp = mparams.get(name), dparams.get(name)
                if item is None or dp is None:
                    rec["errors"].append(f"{name}: not in the map" if dp else f"no parameter {name}")
                    continue
                el = als.parameter(dev, item["element"])
                try:
                    v, text = stored_value(item, dp, vspec, als.controller_range(el))
                except ValueError as e:
                    rec["errors"].append(f"{name}: {e}")
                    continue
                als.set_manual(el, text)
                rec["params"][name] = {"value": v, "element": item["element"], "stored": text}
                if isinstance(vspec, dict) and "display" in vspec and dp.get("samples"):
                    # the API value is only known to within the samples the display was read at
                    rec["params"][name]["tol"] = 1.0 / (len(dp["samples"]) - 1)
            problems += len(rec["errors"])
            als.add_track(root, template, rec["id"], [dev], ids)
            out["cases"].append(rec)
    write_out(root, ids, a.output)
    side = os.path.splitext(a.output)[0] + ".cases.json"
    with open(side, "w") as f:
        json.dump(out, f, indent=1)
    print(f"wrote {a.output} ({len(out['cases'])} tracks) and {side}"
          + (f"; {problems} problems (see the errors in {side})" if problems else ""))
    for rec in out["cases"]:
        for e in rec["errors"]:
            print(f"  {rec['id']}: {e}", file=sys.stderr)
    return 1 if problems else 0


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, template=True):
        p.add_argument("--dump", default=DEFAULTS["dump"])
        p.add_argument("--devices", default=DEFAULTS["devices"],
                       help="a set with a fresh copy of each device (Populate's)")
        if template:
            p.add_argument("--template", default=DEFAULTS["template"],
                           help="a set with an audio track holding the probe clip, Warp off")
            p.add_argument("--track", default=DEFAULTS["track"],
                           help="that track's name (default: the first audio track with a clip)")
            p.add_argument("--keep-returns", action="store_true")
            p.add_argument("--probe", default=DEFAULTS["probe"],
                           help="the probe WAV the clip plays, at the set's sample rate (its length sets the clip's)")
            p.add_argument("-o", "--output", required=True)

    c = sub.add_parser("calibrate")
    common(c)
    c.add_argument("--device", action="append", required=True, help="class or display name, repeatable")
    m = sub.add_parser("map")
    common(m, template=False)
    m.add_argument("calibration")
    m.add_argument("read")
    m.add_argument("--map", default=DEFAULTS["map"])
    b = sub.add_parser("build")
    common(b)
    b.add_argument("cases", nargs="+")
    b.add_argument("--map", default=DEFAULTS["map"])
    a = ap.parse_args(argv)
    return {"calibrate": cmd_calibrate, "map": cmd_map, "build": cmd_build}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
