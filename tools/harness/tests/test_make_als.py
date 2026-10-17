# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Checks make_als.py and als.py against the sets Live 12.4.6 saved (measurements/).

    tools/.venv/bin/python -m unittest discover -s tools/harness/tests
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import als  # noqa: E402
import live_check  # noqa: E402
import make_als  # noqa: E402

D = make_als.DEFAULTS
COMPRESSOR_RUN = os.path.join(make_als.ROOT, "measurements", "29.09-compressor")
HAVE_DATA = all(os.path.exists(p) for p in (D["dump"], D["devices"], D["template"]))

# The Compressor's map as calibration in Live 12.4.6 gives it, for the parameters used here.
COMPRESSOR_MAP = {"devices": {"Compressor2": {"display_name": "Compressor", "params": {
    "Device On": {"element": "On", "kind": "bool", "convert": "bool"},
    "Threshold": {"element": "Threshold", "kind": "float", "convert": "gain"},
    "Ratio": {"element": "Ratio", "kind": "float", "convert": "base"},
    "Attack": {"element": "Attack", "kind": "float", "convert": "ms"},
    "Model": {"element": "Model", "kind": "int", "convert": "offset", "offset": 0},
}}}}


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*args)


class Display(unittest.TestCase):
    def test_units_and_rounding(self):
        self.assertEqual(make_als.parse_display("1.00 kHz"), (1000.0, "Hz", 5.0))
        n, unit, half = make_als.parse_display("30.0 ms")
        self.assertAlmostEqual(n, 0.03)
        self.assertEqual(unit, "s")
        self.assertAlmostEqual(half, 0.00005)
        self.assertEqual(make_als.parse_display("-inf dB")[0], float("-inf"))
        self.assertEqual(make_als.parse_display("4.00 : 1")[:2], (4.0, ": 1"))
        self.assertIsNone(make_als.parse_display("Off"))

    def test_repeated_names_get_numbers(self):
        self.assertEqual(make_als.keyed(["A", "B", "A"]), ["A", "B", "A #2"])


class Conversion(unittest.TestCase):
    """Pairs of (API value, display, stored value) read from the dump and the saved sets."""

    def pick(self, quantized, kind, pairs, endpoints=()):
        c = make_als.choose_conversion(quantized, kind, pairs, list(endpoints))
        return c and c["convert"]

    def test_continuous(self):
        self.assertEqual(self.pick(False, "float", [(0.85, "0.00 dB", 1.0), (0.25, "-28.8 dB", 0.03630783)]), "gain")
        self.assertEqual(self.pick(False, "float", [(0.4, "1.00 ms", 1.0), (0.5, "3.16 ms", 3.16227766)]), "ms")
        self.assertEqual(self.pick(False, "float", [(0.75, "4.00 : 1", 4.0), (0.875, "8.00 : 1", 8.0)]), "base")
        self.assertEqual(self.pick(False, "float", [(1.15, "1 : 1.15", 1.15), (1.7, "1 : 1.70", 1.7)]), "same")
        self.assertEqual(self.pick(False, "float", [(0.5263, "50 %", 0.5), (0.0, "0.0 %", 0.0)]), "percent")
        self.assertEqual(self.pick(False, "float", [(0.5954, "375 ms", 0.3749999404)]), "base")

    def test_endpoints_break_ties(self):
        # Dry/Wet at 1 fits both; the changed value and the ends agree on either, so the first wins
        self.assertEqual(self.pick(False, "float", [(1.0, "100 %", 1.0), (0.0, "0.0 %", 0.0)]), "same")

    def test_quantized(self):
        self.assertEqual(self.pick(True, "bool", [(1, "On", 1.0), (0, "Off", 0.0)]), "bool")
        self.assertEqual(make_als.choose_conversion(True, "int", [(1, "RMS", 1.0), (2, "Expand", 2.0)], []),
                         {"convert": "offset", "offset": 0.0})
        self.assertEqual(make_als.choose_conversion(True, "bool", [(1, "Log", 1.0), (0, "Lin", 0.0)], []),
                         {"convert": "bool"})

    def test_nothing_fits(self):
        self.assertIsNone(self.pick(False, "float", [(0.3, "12.0 Hz", 99.0), (0.6, "40.0 Hz", 3.0)]))


@unittest.skipUnless(HAVE_DATA, "needs measurements/ from Live 12.4.6")
class FromLiveSets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dump = make_als.load_json(D["dump"])

    def test_threshold_matches_what_live_stored(self):
        """The Compressor run was built through the API at Threshold 0, 25, 50, 75 and 100 %;
        Live saved the stored values, which the conversion must give back."""
        dp = make_als.dump_params(make_als.dump_device(self.dump, "Compressor"))["Threshold"]
        item = COMPRESSOR_MAP["devices"]["Compressor2"]["params"]["Threshold"]
        root = als.read_set(os.path.join(COMPRESSOR_RUN, "compressor-threshold.als"))
        seen = 0
        for t in als.tracks(root, ("AudioTrack",)):
            name = t.find("Name/EffectiveName").get("Value")
            devs = [d for d in als.devices_holder(t) if d.tag == "Compressor2"]
            if not name.startswith("Threshold-") or not devs:
                continue
            el = als.parameter(devs[0], "Threshold")
            norm = int(name.split("-")[1][:-3]) / 100
            _, mine = make_als.stored_value(item, dp, {"norm": norm}, als.controller_range(el))
            self.assertAlmostEqual(float(mine) / float(als.manual(el)), 1.0, places=5, msg=name)
            seen += 1
        self.assertEqual(seen, 5)

    def test_tapers(self):
        dps = make_als.dump_params(make_als.dump_device(self.dump, "Compressor"))
        # Attack's display rounds to 0.01 ms at the bottom, which spoils a strict log fit
        self.assertTrue(make_als.log_taper(dps["Attack"]))
        self.assertTrue(make_als.log_taper(dps["Release"]))  # shown in ms, then s
        self.assertFalse(make_als.log_taper(dps["Threshold"]))  # dB
        self.assertTrue(make_als.display_is_value(dps["Output"]))
        self.assertFalse(make_als.display_is_value(dps["Threshold"]))
        self.assertEqual(make_als.value_for_display(dps["Output"], -6.0), -6.0)
        # Live reads 0.200 for 0.1 ms; the dump only pins it to one sample step
        self.assertAlmostEqual(make_als.value_for_display(dps["Attack"], 0.0001), 0.2, delta=1 / 64)

    def test_display_specs_are_exact(self):
        dps = make_als.dump_params(make_als.dump_device(self.dump, "Compressor"))
        p = COMPRESSOR_MAP["devices"]["Compressor2"]["params"]
        self.assertEqual(make_als.stored_value(p["Threshold"], dps["Threshold"], {"display": -20})[1], "0.1")
        self.assertEqual(make_als.stored_value(p["Attack"], dps["Attack"], {"display": 0.01})[1], "10")
        self.assertEqual(make_als.stored_value(p["Model"], dps["Model"], {"item": "Peak"})[1], "0")
        self.assertEqual(make_als.stored_value(p["Device On"], dps["Device On"], 0)[1], "false")

    def check_set(self, path):
        root = als.read_set(path)
        ids = als.global_ids(root)
        self.assertEqual(len(ids), len(set(ids)), "global ids repeat")
        self.assertGreater(int(root.find("LiveSet/NextPointeeId").get("Value")), max(ids))
        ts = als.tracks(root)
        self.assertEqual(len({t.get("Id") for t in ts}), len(ts), "track ids repeat")
        self.assertFalse([t for t in ts if t.tag == "ReturnTrack"])
        self.assertFalse(list(root.iter("TrackSendHolder")))
        return root, ts

    def test_calibrate(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "calib.als")
            quiet(make_als.main, ["calibrate", "--device", "Compressor", "-o", out])
            root, ts = self.check_set(out)
            rec = make_als.load_json(os.path.join(tmp, "calib.calibration.json"))
            self.assertEqual([als.track_name(t) for t in ts], [r["name"] for r in rec["tracks"]])
            self.assertEqual(len(ts), 1 + 25)
            for t, r in zip(ts, rec["tracks"]):
                (dev,) = list(als.devices_holder(t))
                self.assertEqual(dev.tag, "Compressor2")
                if r["element"]:
                    self.assertEqual(als.manual(als.parameter(dev, r["element"])), r["stored"])
                    self.assertNotEqual(r["stored"], r["default"])

    def test_map_from_a_simulated_readback(self):
        """A readback where each calibration track moved the parameter the map says."""
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "calib.als")
            quiet(make_als.main, ["calibrate", "--device", "Compressor", "-o", out])
            rec = make_als.load_json(os.path.join(tmp, "calib.calibration.json"))
            dd = make_als.dump_device(self.dump, "Compressor")
            base = [{"name": p["name"], "value": p["value"], "min": p["min"], "max": p["max"],
                     "is_quantized": p["is_quantized"], "value_string": p["display"]} for p in dd["parameters"]]
            moves = {"Threshold": ("Threshold", 0.125, "-44.6 dB"), "Attack": ("Attack", 0.75, "56.2 ms"),
                     "On": ("Device On", 0, "Off"), "Model": ("Model", 2, "Expand")}
            tracks = []
            for r in rec["tracks"]:
                ps = json.loads(json.dumps(base))
                if r["element"] in moves:
                    name, v, s = moves[r["element"]]
                    p = next(p for p in ps if p["name"] == name)
                    p["value"], p["value_string"] = v, s
                    r["stored"] = {"Threshold": "0.005888", "Attack": "56.2", "On": "false", "Model": "2"}[r["element"]]
                tracks.append({"name": r["name"], "devices": [{"class_name": "Compressor2", "parameters": ps}]})
            cal = os.path.join(tmp, "cal.json")
            with open(cal, "w") as f:
                json.dump(rec, f)
            read = os.path.join(tmp, "read.json")
            with open(read, "w") as f:
                json.dump({"tracks": tracks}, f)
            amap = os.path.join(tmp, "map.json")
            quiet(make_als.main, ["map", cal, read, "--map", amap])
            got = make_als.load_json(amap)["devices"]["Compressor2"]
            self.assertEqual(got["params"]["Threshold"]["convert"], "gain")
            self.assertEqual(got["params"]["Attack"]["convert"], "ms")
            self.assertEqual(got["params"]["Device On"]["convert"], "bool")
            self.assertEqual(got["params"]["Model"], {"element": "Model", "kind": "int", "convert": "offset",
                                                      "offset": 0.0, "points": [[1, 1.0], [2, 2.0]]})
            self.assertEqual(got["unmatched_elements"]["LegacyModel"], "no API parameter moved")

    def test_build_and_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            amap = os.path.join(tmp, "map.json")
            with open(amap, "w") as f:
                json.dump(COMPRESSOR_MAP, f)
            out = os.path.join(tmp, "measure.als")
            src = os.path.join(COMPRESSOR_RUN, "compressor-threshold.json")
            self.assertEqual(quiet(make_als.main, ["build", src, "--map", amap, "-o", out]), 0)
            root, ts = self.check_set(out)
            spec = make_als.load_json(os.path.join(tmp, "measure.cases.json"))
            names = [als.track_name(t) for t in ts]
            self.assertEqual(names[:3], ["compressor-threshold bypass", "compressor-threshold default",
                                         "compressor-threshold Threshold-0pct"])
            self.assertEqual(names, [c["id"] for c in spec["cases"]])
            (dev,) = list(als.devices_holder(ts[0]))
            self.assertEqual(als.manual(als.parameter(dev, "On")), "false")
            (dev,) = list(als.devices_holder(ts[4]))
            self.assertAlmostEqual(float(als.manual(als.parameter(dev, "Threshold"))), 0.1995263, places=5)

            # verify against a readback that matches, then one with a wrong value
            dd = make_als.dump_device(self.dump, "Compressor")
            tracks = []
            for c in spec["cases"]:
                ps = [{"name": p["name"], "value": c["params"].get(p["name"], {}).get("value", p["value"]),
                       "min": p["min"], "max": p["max"], "is_quantized": p["is_quantized"],
                       "value_string": ""} for p in dd["parameters"]]
                tracks.append({"name": c["id"], "devices": [{"class_name": "Compressor2", "parameters": ps}]})
            read = os.path.join(tmp, "read.json")
            with open(read, "w") as f:
                json.dump({"tracks": tracks}, f)
            cases = os.path.join(tmp, "measure.cases.json")
            self.assertEqual(quiet(live_check.main, ["verify", cases, "--read", read]), 0)
            tracks[3]["devices"][0]["parameters"][1]["value"] = 0.3
            with open(read, "w") as f:
                json.dump({"tracks": tracks}, f)
            self.assertEqual(quiet(live_check.main, ["verify", cases, "--read", read]), 1)

    def test_unmapped_parameter_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            amap = os.path.join(tmp, "map.json")
            with open(amap, "w") as f:
                json.dump(COMPRESSOR_MAP, f)
            src = os.path.join(tmp, "knee.json")
            with open(src, "w") as f:
                json.dump({"device": "Compressor", "cases": [{"id": "k", "params": {"Knee": 3}}]}, f)
            out = os.path.join(tmp, "k.als")
            self.assertEqual(quiet(make_als.main, ["build", src, "--map", amap, "-o", out]), 1)
            spec = make_als.load_json(os.path.join(tmp, "k.cases.json"))
            self.assertEqual(spec["cases"][0]["errors"], ["Knee: not in the map"])


if __name__ == "__main__":
    unittest.main()
