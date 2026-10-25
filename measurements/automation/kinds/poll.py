# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Reads what Live's automation gives other kinds of parameter (integer, frequency, choice, toggle).

The set (kinds.als, from the three cases files here with `make_als.py build`) holds one track per
lane. With the set open in Live and playback stopped, this moves the playhead to each beat on a
grid, waits for Live to apply the lanes, and records every track's automated parameter as the
Remote Script reports it (the API value, not a render). Nothing in the set is changed.

    tools/.venv/bin/python measurements/automation/kinds/poll.py [--step 0.125] [--end 34]
        writes live/kinds.poll.json: {track name: {"param": name, "beats": [...], "values": [...]}}

Playing the set and polling would give the same values with the timing of the socket in them;
setting the playhead gives exact beats.
"""

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools", "harness"))
import live_check  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", type=float, default=0.125)
    ap.add_argument("--end", type=float, default=34.0)
    ap.add_argument("--settle", type=float, default=0.05, help="seconds to wait after moving the playhead")
    ap.add_argument("-o", "--output", default=os.path.join(HERE, "live", "kinds.poll.json"))
    a = ap.parse_args()

    live = live_check.Live()
    if live.call("get_session_info")["is_playing"]:
        sys.exit("stop playback first")
    n = live.call("get_session_info")["track_count"]
    out = {}
    for ti in range(n):
        d = live.call("get_device_parameters", track_index=ti, device_index=0)["device"]
        name = live.call("get_track_info", track_index=ti)["name"]
        (param,) = d["automated_parameters"]
        out[name] = {"track": ti, "param": param, "beats": [], "values": []}
    steps = int(round(a.end / a.step)) + 1
    for k in range(steps):
        beat = k * a.step
        live.call("set_current_song_time", time=beat)
        time.sleep(a.settle)
        for name, rec in out.items():
            d = live.call("get_device_parameters", track_index=rec["track"], device_index=0)["device"]
            rec["values"].append(next(p["value"] for p in d["parameters"] if p["name"] == rec["param"]))
            rec["beats"].append(beat)
    os.makedirs(os.path.dirname(a.output), exist_ok=True)
    with open(a.output, "w") as f:
        json.dump(out, f)
    print(f"wrote {a.output}: {len(out)} lanes at {steps} beats")


if __name__ == "__main__":
    main()
