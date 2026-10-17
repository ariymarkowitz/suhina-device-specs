# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Reads the open Live Set's devices through the AbletonMCP Remote Script and checks a set
written by make_als.py against it.

    python live_check.py read [-o read.json]
    python live_check.py verify measure.cases.json [--read read.json] [-o measure.verified.json]

The Remote Script (https://github.com/ahujasid/ableton-mcp, MIT) runs inside Live as a control
surface and answers JSON commands on 127.0.0.1:9877. Only the Remote Script is needed: this
talks to its socket directly, without the project's MCP server. Install it with
`uvx --from ableton-mcp ableton-mcp-install-script`, then in Live's Settings › Link, Tempo &
MIDI choose AbletonMCP as a Control Surface (Input and Output None). Open the set in Live
(`open -a "Ableton Live 12 Trial" set.als`) before reading.

`read` writes every track's devices with each parameter's API value and display text.
`verify` checks each track of a make_als.py set: the device is there, each case parameter has
the API value the case asked for, and every other parameter still has the dump's default (a
wrongly mapped element shows up there). With -o it writes the cases file again with what Live
shows (`live`: value and display), which is the record to analyse against.
"""

import argparse
import json
import socket
import sys

import make_als

HOST, PORT = "127.0.0.1", 9877


class Live:
    def __init__(self, host=HOST, port=PORT, timeout=30.0):
        try:
            self.sock = socket.create_connection((host, port), timeout=timeout)
        except OSError as e:
            raise SystemExit(f"cannot reach the AbletonMCP Remote Script on {host}:{port} ({e}); "
                             "is Live open with AbletonMCP chosen as a Control Surface?")

    def call(self, kind, **params):
        self.sock.sendall(json.dumps({"type": kind, "params": params}).encode("utf-8"))
        buf = b""
        while True:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise SystemExit(f"{kind}: the Remote Script closed the connection")
            buf += chunk
            try:
                reply = json.loads(buf.decode("utf-8"))
                break
            except (ValueError, UnicodeDecodeError):
                continue
        if reply.get("status") != "success":
            raise RuntimeError(f"{kind}: {reply.get('message', reply)}")
        return reply.get("result", {})


def read_set(live):
    info = live.call("get_session_info")
    out = {"tempo": info.get("tempo"), "tracks": []}
    for i in range(int(info["track_count"])):
        t = live.call("get_track_info", track_index=i)
        track = {"index": i, "name": t.get("name"), "devices": []}
        for d in t.get("devices", []):
            r = live.call("get_device_parameters", track_index=i, device_index=d["index"])
            dev = r.get("device", r)
            track["devices"].append({
                "index": d["index"],
                "name": dev.get("name", d.get("name")),
                "class_name": dev.get("class_name", d.get("class_name")),
                "parameters": [{k: p.get(k) for k in ("name", "value", "min", "max", "is_quantized", "value_string")}
                               for p in dev.get("parameters", [])],
            })
        out["tracks"].append(track)
    return out


def cmd_read(a):
    data = read_set(Live())
    text = json.dumps(data, indent=1)
    if a.output:
        with open(a.output, "w") as f:
            f.write(text + "\n")
        print(f"wrote {a.output}: {len(data['tracks'])} tracks")
    else:
        print(text)


def close(p, want, tol):
    if want is None:
        return True
    if p.get("is_quantized"):
        return round(p["value"]) == round(want)
    return abs(p["value"] - want) <= tol * max(1e-12, (p["max"] - p["min"]))


def cmd_verify(a):
    spec = make_als.load_json(a.cases)
    data = make_als.load_json(a.read) if a.read else read_set(Live())
    dump = make_als.load_json(a.dump)
    live = {t["name"]: t for t in data["tracks"]}
    problems = []
    for rec in spec["cases"]:
        t = live.get(rec["id"])
        devs = [d for d in (t or {}).get("devices", []) if d["class_name"] == rec["device"]]
        if not devs:
            problems.append(f"{rec['id']}: {'no such track' if t is None else 'no ' + rec['device']}")
            continue
        ps = devs[0]["parameters"]
        now = dict(zip(make_als.keyed([p["name"] for p in ps]), ps))
        defaults = make_als.dump_params(make_als.dump_device(dump, rec["device"]))
        for name, p in now.items():
            want = rec["params"][name]["value"] if name in rec["params"] else (defaults.get(name) or {}).get("value")
            tol = max(a.tol, rec["params"].get(name, {}).get("tol", 0.0))
            if not close(p, want, tol):
                what = "case value" if name in rec["params"] else "default"
                problems.append(f"{rec['id']}: {name} is {p['value']} ({p.get('value_string')}), {what} {want}")
            if name in rec["params"]:
                rec["params"][name]["live"] = {"value": p["value"], "display": p.get("value_string")}
        for name in rec["params"]:
            if name not in now:
                problems.append(f"{rec['id']}: Live has no parameter {name}")
    for line in problems:
        print(line)
    print(f"{len(spec['cases'])} tracks checked, {len(problems)} problems")
    if a.output:
        with open(a.output, "w") as f:
            json.dump(spec, f, indent=1)
        print(f"wrote {a.output}")
    return 1 if problems else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("read")
    r.add_argument("-o", "--output")
    v = sub.add_parser("verify")
    v.add_argument("cases", help="the .cases.json make_als.py wrote beside the set")
    v.add_argument("--read", help="a saved `read` instead of asking Live")
    v.add_argument("--dump", default=make_als.DEFAULTS["dump"])
    v.add_argument("--tol", type=float, default=0.002, help="allowed error as a fraction of the range")
    v.add_argument("-o", "--output")
    a = ap.parse_args(argv)
    return {"read": cmd_read, "verify": cmd_verify}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
