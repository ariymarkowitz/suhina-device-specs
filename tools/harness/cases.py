# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Makes a cases file for the probe's Build cases button from a parameter dump.

    python cases.py list dump.json [--device Compressor]
    python cases.py sweep dump.json --device Compressor --param Threshold --points 7 \\
        [--set "Ratio=item:4:1" ...] [--display=-40,-30,-20] -o compressor-threshold.json

`list` prints the devices of a dump, or one device's parameters with range, default and taper.
`sweep` writes one case per value of one parameter (write `--display=-40,...` with the equals
sign when the first value is negative), with the others left at the template's values
or set with --set. Every file starts with a `bypass` case (the device switched off), which renders
the chain without the device, and a `default` case.

Value specs for --set (and in the file): `12.5` (internal value), `norm:0.5` (fraction of the
range), `item:RMS` (a quantized parameter's item), `display:-20` (the value whose display reads
-20 in base units: Hz, s, dB, %).
"""

import argparse
import json
import math
import re
import sys


def load_dump(path):
    with open(path) as f:
        d = json.load(f)
    if not isinstance(d, dict) or not isinstance(d.get("devices"), list):
        raise SystemExit(f"{path}: not a Suhina Probe dump")
    return d


def find_device(dump, name):
    hits = [d for d in dump["devices"]
            if name in (d.get("class_display_name"), d.get("name"), d.get("class_name"), d.get("track"))]
    if not hits:
        known = sorted({d.get("class_display_name", "") for d in dump["devices"]})
        raise SystemExit(f"no device {name!r} in the dump; it has: {', '.join(known)}")
    return hits[0]


def find_param(device, name):
    for p in device["parameters"]:
        if name in (p.get("name"), p.get("original_name")):
            return p
    raise SystemExit(f"{device.get('class_display_name')} has no parameter {name!r}")


def parse_number(text):
    m = re.match(r"^\s*([+-]?(?:\d+(?:\.\d+)?|inf))", str(text).replace("−", "-"), re.I)
    if not m:
        return None
    return float(m.group(1))


def taper(p):
    """Rough taper from the sampled display: linear, logarithmic, stepped or other."""
    if p.get("is_quantized"):
        return "stepped"
    pts = [(v, parse_number(s)) for v, s in p.get("samples", [])]
    pts = [(v, n) for v, n in pts if n is not None and math.isfinite(n)]
    if len(pts) < 5:
        return "unknown"
    vs = [v for v, _ in pts]
    ns = [n for _, n in pts]

    def r2(xs, ys):
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        sxx = sum((x - mx) ** 2 for x in xs)
        syy = sum((y - my) ** 2 for y in ys)
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        return 1.0 if sxx == 0 or syy == 0 else sxy * sxy / (sxx * syy)

    lin = r2(vs, ns)
    log = r2(vs, [math.log(n) for n in ns]) if all(n > 0 for n in ns) else 0.0
    if lin > 0.999:
        return "linear"
    if log > 0.999:
        return "logarithmic"
    return f"other (linear r2 {lin:.3f}, log r2 {log:.3f})"


def parse_spec(text):
    if ":" in text:
        kind, _, rest = text.partition(":")
        if kind == "item":
            return {"item": rest}
        if kind in ("norm", "display", "value"):
            try:
                return {kind: float(rest)}
            except ValueError:
                raise SystemExit(f"bad number in {text!r}")
    try:
        return float(text)
    except ValueError:
        raise SystemExit(f"bad value spec {text!r}: use a number, norm:, item:, display:")


def slug(text):
    s = re.sub(r"[^A-Za-z0-9.+-]+", "-", str(text)).strip("-")
    return s or "x"


def cmd_list(a):
    dump = load_dump(a.dump)
    if not a.device:
        for d in dump["devices"]:
            print(f"{d.get('track', ''):24} {d.get('class_display_name', ''):24} "
                  f"{d.get('class_name', ''):24} {len(d['parameters'])} parameters")
        return
    d = find_device(dump, a.device)
    for p in d["parameters"]:
        samples = p.get("samples") or [[None, ""]]
        rng = f"{samples[0][1]} .. {samples[-1][1]}"
        print(f"{p['name']:28} {rng:34} now {p.get('display', ''):14} {taper(p)}")


def cmd_sweep(a):
    dump = load_dump(a.dump)
    d = find_device(dump, a.device)
    p = find_param(d, a.param)
    fixed = {}
    for s in a.set or []:
        name, eq, spec = s.partition("=")
        if not eq:
            raise SystemExit(f"--set needs Name=value, got {s!r}")
        find_param(d, name.strip())
        fixed[name.strip()] = parse_spec(spec.strip())
    on = next((q["name"] for q in d["parameters"] if q["name"] == "Device On"), None)
    cases = []
    if on:
        cases.append({"id": "bypass", "params": {on: 0}})
    cases.append({"id": "default", "params": dict(fixed)})
    if a.display:
        values = [{"display": float(x)} for x in a.display.split(",")]
        labels = [x.strip() for x in a.display.split(",")]
    elif p.get("is_quantized"):
        items = p.get("value_items") or [s for _, s in p.get("samples", [])]
        values = [{"item": it} for it in items]
        labels = items
    else:
        n = max(2, a.points)
        values = [{"norm": i / (n - 1)} for i in range(n)]
        labels = [f"{100 * i / (n - 1):.0f}pct" for i in range(n)]
    for v, label in zip(values, labels):
        params = dict(fixed)
        params[p["name"]] = v
        cases.append({"id": f"{slug(p['name'])}-{slug(label)}", "params": params})
    out = {"device": d.get("class_display_name") or d.get("name"), "parameter": p["name"], "cases": cases}
    text = json.dumps(out, indent=1)
    if a.output:
        with open(a.output, "w") as f:
            f.write(text + "\n")
        print(f"wrote {a.output}: {len(cases)} cases")
    else:
        print(text)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("dump")
    ls.add_argument("--device")
    sw = sub.add_parser("sweep")
    sw.add_argument("dump")
    sw.add_argument("--device", required=True)
    sw.add_argument("--param", required=True)
    sw.add_argument("--points", type=int, default=7)
    sw.add_argument("--display", help="comma-separated display values instead of even steps")
    sw.add_argument("--set", action="append", help="Name=spec for another parameter, repeatable")
    sw.add_argument("-o", "--output")
    a = ap.parse_args(argv)
    {"list": cmd_list, "sweep": cmd_sweep}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
