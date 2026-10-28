# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Checks measure.py: runs files, their checks, and the device selectors.

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
import measure  # noqa: E402
import make_als  # noqa: E402

D = make_als.DEFAULTS
HAVE_DATA = all(os.path.exists(p) for p in (D["dump"], D["devices"], D["template"], D["map"]))

RUNS = '''
DEVICE = "Compressor"
RUNS = [
    {"name": "t-ratio", "question": "q", "base": {"Knee": 0},
     "cases": [["r2", {"Ratio": {"display": 2}}], ["r4", {"Ratio": {"display": 4}}]]},
    {"name": "t-bad", "question": "q",
     "cases": [["x", {"Ratio": {"display": 2000}}], ["y", {"Nope": 1}], ["z", {"Model": {"item": "Loud"}}]]},
]
'''


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*args)


class Runs(unittest.TestCase):
    def test_cases_get_bypass_and_default(self):
        cs = measure.run_cases({"base": {"Knee": 0}, "cases": [["a", {"Ratio": 1}]]})
        self.assertEqual([c["id"] for c in cs], ["bypass", "default", "a"])
        self.assertEqual(cs[0]["params"], {"Device On": 0})
        self.assertEqual(cs[1]["params"], {"Knee": 0})
        self.assertEqual(cs[2]["params"], {"Knee": 0, "Ratio": 1})
        with self.assertRaises(ValueError):
            measure.run_cases({"cases": [["default", {}]]})

    @unittest.skipUnless(HAVE_DATA, "needs reference/ and devices/")
    def test_check_finds_bad_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "runs.py")
            with open(path, "w") as f:
                f.write(RUNS)
            runs = measure.load_runs([path])
            dump = make_als.load_json(D["dump"])
            amap = make_als.load_json(D["map"])["devices"]
            root = als.read_set(D["devices"])
            r, dev, _ = runs["t-ratio"]
            self.assertEqual(measure.check_run(r, dev, dump, amap, root), [])
            r, dev, _ = runs["t-bad"]
            probs = measure.check_run(r, dev, dump, amap, root)
            self.assertEqual(len(probs), 3, probs)
            self.assertIn("no parameter 'Nope'", probs[1])
            self.assertIn("Loud", probs[2])

    @unittest.skipUnless(HAVE_DATA, "needs reference/ and devices/")
    def test_summary_lines(self):
        res = make_als.load_json(os.path.join(make_als.ROOT, "devices", "29.09-compressor", "results",
                                              "compressor-threshold default.json"))
        lines = measure.summarise(res, ["static", "impulse"])
        self.assertTrue(lines[0].startswith("impulse peak"))
        self.assertTrue(lines[1].startswith("static in->gain"))


class Selectors(unittest.TestCase):
    @unittest.skipUnless(os.path.isdir(measure.DEVICES), "needs devices/")
    def test_device_folders(self):
        every = measure.device_folders()
        self.assertTrue(all(d.startswith("29.") for d in every))
        self.assertIn("29.01-amp", every)
        self.assertEqual(measure.device_folders(["amp"]), ["29.01-amp"])
        self.assertEqual(measure.device_folders(["29.09"]), ["29.09-compressor"])
        self.assertEqual(measure.device_folders(["29.09-compressor"]), ["29.09-compressor"])
        with self.assertRaises(SystemExit):
            measure.device_folders(["reverb"])  # Hybrid Reverb and Reverb
        with self.assertRaises(SystemExit):
            measure.device_folders(["nothing-like-this"])

    def test_export_names_and_bars(self):
        self.assertEqual(measure.export_name("amp", "gap2"), "amp")
        self.assertEqual(measure.export_name("amp", "ext"), "amp-ext")
        self.assertEqual(measure.bars({"length": 2061676, "rate": 44100, "tempo": 120.0}), 24)
        self.assertEqual(measure.file_name("a/b c"), "a_b c")

    @unittest.skipUnless(os.path.isdir(measure.DEVICES), "needs devices/")
    def test_every_run_names_a_known_probe(self):
        import probes
        for name, (r, _, _) in measure.load_runs().items():
            self.assertIn(measure.probe_of(r), probes.PROBES, name)


if __name__ == "__main__":
    unittest.main()
