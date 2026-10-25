# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Checks the harness on synthetic devices whose behaviour is known exactly.

    tools/.venv/bin/python -m unittest discover -s tools/harness/tests
"""

import contextlib
import gzip
import io
import json
import math
import os
import stat
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import analyse  # noqa: E402
import cases  # noqa: E402
import compare  # noqa: E402
import signals  # noqa: E402
import render_set  # noqa: E402
from wavio import read_wav, write_wav  # noqa: E402

RATE = 48000
AUDIO, MANIFEST = signals.build(RATE, gap=1.0)


def run(device):
    out = device(AUDIO.copy())
    result, extras = analyse.analyse(MANIFEST, AUDIO, out, RATE)
    return result


def gain_at(result, in_db):
    return next(r for r in result["static"] if r["in_db"] == in_db)["left_gain_db"]


def response_at(result, hz, kind="sweep_db", ch=0):
    c = result["response"]["centres_hz"]
    i = min(range(len(c)), key=lambda k: abs(c[k] - hz))
    return result["response"][kind][ch][i]


# ------------------------------------------------------------------ synthetic devices

def gain(db):
    return lambda x: x * 10 ** (db / 20)


def taps(ms, levels):
    """Dry plus echoes at multiples of `ms` with the given linear levels."""
    def dev(x):
        d = int(RATE * ms / 1000)
        out = x.copy()
        for k, lv in enumerate(levels, start=1):
            out[d * k:] += lv * x[:len(x) - d * k]
        return out
    return dev


def one_pole_lowpass(fc):
    a = math.exp(-2 * math.pi * fc / RATE)

    def dev(x):
        # y[n] = (1 - a) x[n] + a y[n-1], done with a recursive filter in blocks via cumulative trick
        y = np.zeros_like(x)
        for ch in range(x.shape[1]):
            acc = 0.0
            col = x[:, ch]
            out = y[:, ch]
            b = 1 - a
            for n in range(len(col)):
                acc = b * col[n] + a * acc
                out[n] = acc
        return y
    return dev


def hard_clip(db):
    lim = 10 ** (db / 20)
    return lambda x: np.clip(x, -lim, lim)


def compressor(threshold_db, ratio, attack_ms, release_ms):
    ka = math.exp(-1 / (RATE * attack_ms / 1000))
    kr = math.exp(-1 / (RATE * release_ms / 1000))

    def dev(x):
        # peak level per sample, static curve in dB, gain smoothed in dB with attack/release
        level = np.maximum(np.abs(x).max(axis=1), 1e-9)
        # a peak detector on a sine: hold the cycle's peak with a 1 ms window
        win = int(RATE / 1000)
        padded = np.concatenate([np.zeros(win), level])
        from numpy.lib.stride_tricks import sliding_window_view
        peak = sliding_window_view(padded, win + 1).max(axis=1)[:len(level)]
        ldb = 20 * np.log10(np.maximum(peak, 1e-9))
        target = np.where(ldb > threshold_db, (threshold_db + (ldb - threshold_db) / ratio) - ldb, 0.0)
        g = np.zeros_like(target)
        state = 0.0
        for n in range(len(target)):
            k = ka if target[n] < state else kr
            state = k * state + (1 - k) * target[n]
            g[n] = state
        return x * (10 ** (g / 20))[:, None]
    return dev


def tremolo(rate_hz, depth_db):
    def dev(x):
        t = np.arange(len(x)) / RATE
        g = 10 ** ((-depth_db / 2 + depth_db / 2 * np.sin(2 * np.pi * rate_hz * t)) / 20)
        return x * g[:, None]
    return dev


def vibrato(rate_hz, depth_ms):
    def dev(x):
        n = np.arange(len(x))
        delay = (depth_ms / 1000 * RATE) * (1 + np.sin(2 * np.pi * rate_hz * n / RATE)) / 2 + 2
        pos = n - delay
        out = np.zeros_like(x)
        for ch in range(x.shape[1]):
            out[:, ch] = np.interp(pos, n, x[:, ch], left=0.0)
        return out
    return dev


def swap_channels(x):
    return x[:, ::-1].copy()


# ------------------------------------------------------------------ tests

class Signals(unittest.TestCase):
    def test_manifest_matches_audio(self):
        self.assertEqual(MANIFEST["length"], len(AUDIO))
        names = [s["name"] for s in MANIFEST["segments"]]
        self.assertEqual(names, ["impulse", "sweep", "staircase", "bursts", "steady", "noise", "left", "right", "silence"])
        for s in MANIFEST["segments"]:
            self.assertLessEqual(s["start"] + s["length"], len(AUDIO))
        self.assertLessEqual(np.max(np.abs(AUDIO)), 1.0)

    def test_wav_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.wav")
            write_wav(p, RATE, AUDIO[:1000])
            r, back = read_wav(p)
            self.assertEqual(r, RATE)
            np.testing.assert_allclose(back, AUDIO[:1000], atol=1e-7)

    def test_reads_24_bit_pcm(self):
        import struct
        vals = [0, 1, -1, 4194304, -8388608]
        frames = b"".join(struct.pack("<i", v)[:3] for v in vals)
        fmt = struct.pack("<HHIIHH", 1, 1, 44100, 44100 * 3, 3, 24)
        data = b"RIFF" + struct.pack("<I", 4 + 8 + 16 + 8 + len(frames)) + b"WAVE" + b"fmt " + \
            struct.pack("<I", 16) + fmt + b"data" + struct.pack("<I", len(frames)) + frames
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.wav")
            with open(p, "wb") as f:
                f.write(data)
            r, x = read_wav(p)
        self.assertEqual(r, 44100)
        np.testing.assert_allclose(x[:, 0], [v / 8388608 for v in vals])

    def test_rejects_garbage(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.wav")
            with open(p, "wb") as f:
                f.write(b"not a wav at all")
            with self.assertRaises(ValueError):
                read_wav(p)


class ExtendedProbe(unittest.TestCase):
    """The extended probe (signals.py --kind ext) and what analyse.py reads from it."""

    @classmethod
    def setUpClass(cls):
        cls.audio, cls.manifest = signals.build_ext(rate=RATE, gap=0.5)
        cls.probe = cls.audio

    def analyse(self, fn):
        out = fn(self.audio.copy())
        return analyse.analyse(self.manifest, self.probe, out, RATE)

    def test_manifest_matches_audio(self):
        self.assertEqual(self.manifest["kind"], "ext")
        self.assertEqual(self.manifest["segments"][0]["name"], "impulse")
        for s in self.manifest["segments"]:
            self.assertLessEqual(s["start"] + s["length"], len(self.audio))
        self.assertLessEqual(np.max(np.abs(self.audio)), 1.0)

    def test_identity(self):
        r, extras = self.analyse(lambda x: x)
        self.assertNotIn("static", r)
        e = r["ext"]
        self.assertAlmostEqual(e["stair100"][10]["left_gain_db"], 0.0, places=2)
        for k in ("tone10k", "tone15k", "tone3k", "tone50", "saw"):
            self.assertAlmostEqual(e[k]["gain_db"][0], 0.0, places=3, msg=k)
        self.assertAlmostEqual(e["shortbursts"][0]["peak_gain_db"][0], 0.0, places=2)
        self.assertAlmostEqual(e["mid"]["side_db"], -240.0)
        self.assertAlmostEqual(e["side"]["mid_db"], -240.0)
        self.assertAlmostEqual(e["lrsplit"]["gain_db"][1], 0.0, places=3)
        self.assertAlmostEqual(e["dcstep"]["end"], 0.3, places=4)
        self.assertAlmostEqual(e["ramp"][40]["down_left_gain_db"], 0.0, places=1)
        self.assertIn("ramp", extras["ext_envelope"])

    def test_gain_and_swap(self):
        r, _ = self.analyse(lambda x: 0.5 * x[:, ::-1])
        e = r["ext"]
        self.assertAlmostEqual(e["tone3k"]["gain_db"][0], -6.02, places=1)
        self.assertAlmostEqual(e["lrsplit"]["level_db"][0], -18 - 6.02, places=1)
        self.assertAlmostEqual(e["side"]["side_db"], -6.02, places=1)

    def test_dc_blocker(self):
        """A one-pole high-pass's step response, written over the DC step."""
        tau = 0.03
        seg = next(x for x in self.manifest["segments"] if x["name"] == "dcstep")

        def hp(x):
            n = seg["length"]
            x[seg["start"]:seg["start"] + n] = (0.3 * np.exp(-np.arange(n) / RATE / tau))[:, None]
            return x
        r, _ = self.analyse(hp)
        self.assertAlmostEqual(r["ext"]["dcstep"]["tau_ms"], 1000 * tau, delta=0.1)


class Analysis(unittest.TestCase):
    def test_identity(self):
        r = run(lambda x: x)
        self.assertAlmostEqual(gain_at(r, -12.0), 0.0, places=2)
        for hz in (50, 1000, 10000):
            self.assertAlmostEqual(response_at(r, hz), 0.0, delta=0.2)
            self.assertAlmostEqual(response_at(r, hz, "noise_db"), 0.0, delta=0.2)
        self.assertEqual([round(t["time_ms"], 3) for t in r["impulse"]["taps"]], [0.0])
        self.assertAlmostEqual(r["impulse"]["peak_db"], 0.0, places=3)
        self.assertIsNone(r["dynamics"]["attack"]["t63_ms"])
        self.assertAlmostEqual(r["stereo"]["left_to_left_db"], 0.0, places=2)
        self.assertLess(r["stereo"]["left_to_right_db"], -100)
        self.assertLess(r["modulation"]["left"]["am"]["depth_db"], 0.1)
        self.assertLess(r["modulation"]["left"]["fm"]["depth_cents"], 0.5)
        self.assertLess(r["silence"]["rms_db"][0], -200)

    def test_gain(self):
        r = run(gain(-6))
        self.assertAlmostEqual(gain_at(r, -30.0), -6.0, places=2)
        self.assertAlmostEqual(response_at(r, 1000), -6.0, delta=0.2)

    def test_delay_taps(self):
        r = run(taps(100, [0.5, 0.25]))
        t = r["impulse"]["taps"]
        self.assertEqual([round(x["time_ms"]) for x in t], [0, 100, 200])
        self.assertAlmostEqual(t[1]["level_db"], -6.02, places=1)
        self.assertAlmostEqual(t[2]["level_db"], -12.04, places=1)

    def test_lowpass(self):
        r = run(one_pole_lowpass(1000))
        self.assertAlmostEqual(response_at(r, 100), 0.0, delta=0.3)
        self.assertAlmostEqual(response_at(r, 1000), -3.0, delta=0.6)
        self.assertAlmostEqual(response_at(r, 10000), -20.0, delta=1.5)
        self.assertAlmostEqual(response_at(r, 1000, "noise_db"), -3.0, delta=0.6)

    def test_hard_clip(self):
        r = run(hard_clip(-12))
        self.assertAlmostEqual(gain_at(r, -30.0), 0.0, places=2)
        st = next(x for x in r["static"] if x["in_db"] == 0.0)
        self.assertGreater(st["left_thd_pct"], 10)
        self.assertLess(st["left_out_db"], -9)
        quiet = next(x for x in r["static"] if x["in_db"] == -30.0)
        self.assertLess(quiet["left_thd_pct"], 0.1)

    def test_compressor(self):
        r = run(compressor(-20, 4, 10, 100))
        self.assertAlmostEqual(gain_at(r, -30.0), 0.0, delta=0.1)
        self.assertAlmostEqual(gain_at(r, 0.0), -15.0, delta=0.3)
        self.assertAlmostEqual(gain_at(r, -12.0), -6.0, delta=0.3)
        att = r["dynamics"]["attack"]
        rel = r["dynamics"]["release"]
        self.assertAlmostEqual(att["to_db"] - att["from_db"], -10.5, delta=0.5)
        self.assertAlmostEqual(att["t63_ms"], 10, delta=2.5)
        self.assertAlmostEqual(rel["t63_ms"], 100, delta=10)

    def test_tremolo(self):
        r = run(tremolo(4.0, 6.0))
        am = r["modulation"]["left"]["am"]
        self.assertAlmostEqual(am["rate_hz"], 4.0, delta=0.1)
        self.assertAlmostEqual(am["depth_db"], 6.0, delta=0.5)
        self.assertGreater(r["modulation"]["envelope_correlation"], 0.99)

    def test_vibrato(self):
        r = run(vibrato(2.0, 2.0))
        fm = r["modulation"]["left"]["fm"]
        self.assertAlmostEqual(fm["rate_hz"], 2.0, delta=0.1)
        # peak frequency deviation of a sine-modulated delay: 2*pi*f_mod*(depth/2) * f / f, in cents
        dev = 2 * math.pi * 2.0 * (0.002 / 2)
        cents = 1200 * math.log2(1 + dev)
        self.assertAlmostEqual(fm["depth_cents"], cents, delta=cents * 0.15)

    def test_swapped_channels(self):
        r = run(swap_channels)
        self.assertAlmostEqual(r["stereo"]["left_to_right_db"], 0.0, places=2)
        self.assertLess(r["stereo"]["left_to_left_db"], -100)

    def test_xcorr_alignment_finds_latency(self):
        def late(x):
            out = np.zeros_like(x)
            out[123:] = x[:-123]
            return out
        out = late(AUDIO.copy())
        res, _ = analyse.analyse(MANIFEST, AUDIO, out, RATE, align="xcorr")
        self.assertEqual(res["offset_samples"], 123)
        self.assertEqual([round(t["time_ms"], 3) for t in res["impulse"]["taps"]], [0.0])

    def test_reverb_decay(self):
        rng = np.random.default_rng(3)
        rt = 0.5
        n = int(0.9 * RATE)
        tail = rng.standard_normal(n) * np.exp(-6.91 * np.arange(n) / (rt * RATE)) * 0.05

        def reverb(x):
            out = x.copy()
            for ch in range(2):
                out[:, ch] += np.convolve(x[:, ch], tail)[:len(x)]
            return out
        r = run(reverb)
        self.assertAlmostEqual(r["impulse"]["rt60_s"], rt, delta=0.08)

    def test_short_or_silent_render_does_not_crash(self):
        short = AUDIO[:1000].copy()
        res, _ = analyse.analyse(MANIFEST, AUDIO, short, RATE)
        self.assertEqual(res["impulse"]["taps"], [])
        res, _ = analyse.analyse(MANIFEST, AUDIO, np.zeros((len(AUDIO), 1)), RATE)
        self.assertIsNone(res["impulse"]["rt60_s"])

    def test_wrong_rate_is_an_error(self):
        with self.assertRaises(ValueError):
            analyse.analyse(MANIFEST, AUDIO, AUDIO, 44100)

    def test_cli_writes_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            write_wav(os.path.join(d, "probe.wav"), RATE, AUDIO)
            with open(os.path.join(d, "probe.json"), "w") as f:
                json.dump(MANIFEST, f)
            write_wav(os.path.join(d, "half.wav"), RATE, AUDIO * 0.5)
            with contextlib.redirect_stdout(io.StringIO()):
                code = analyse.main([os.path.join(d, "probe.json"), os.path.join(d, "half.wav"), "-o", os.path.join(d, "out")])
            self.assertEqual(code, 0)
            for ext in (".json", ".response.csv", ".static.csv", ".envelope.csv", ".ir.wav"):
                self.assertTrue(os.path.exists(os.path.join(d, "out", "half" + ext)), ext)


class Compare(unittest.TestCase):
    def check(self, dev_a, dev_b):
        rep = compare.Report(0.5, 0.1, 0.5)
        compare.compare(run(dev_a), run(dev_b), rep)
        return rep

    def test_same_device_matches(self):
        self.assertFalse(self.check(gain(-6), gain(-6)).fail)

    def test_gain_difference_is_found(self):
        rep = self.check(gain(-6), gain(-5))
        self.assertTrue(rep.fail)
        self.assertTrue(any(r[0].startswith("static gain") and r[4] == "DIFF" for r in rep.rows))

    def test_release_difference_is_found(self):
        rep = self.check(compressor(-20, 4, 10, 100), compressor(-20, 4, 10, 200))
        self.assertTrue(any(r[0] == "release t63_ms" and r[4] == "DIFF" for r in rep.rows))
        self.assertFalse(any(r[0] == "attack t63_ms" and r[4] == "DIFF" for r in rep.rows))

    def test_pairs_by_case_id(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = os.path.join(d, "a"), os.path.join(d, "b")
            os.makedirs(a)
            os.makedirs(b)
            for p in (os.path.join(a, "My Set 3-thr-12.json"), os.path.join(b, "thr-12.json"),
                      os.path.join(a, "default.json"), os.path.join(b, "default.json")):
                open(p, "w").close()
            got = compare.pairs(a, b, ["thr-12", "default"])
            self.assertEqual(sorted(k for k, _, _ in got), ["default", "thr-12"])


class Cases(unittest.TestCase):
    DUMP = {"devices": [{"track": "Probe", "name": "Compressor", "class_name": "Compressor2",
                         "class_display_name": "Compressor", "parameters": [
                             {"name": "Device On", "is_quantized": True, "value_items": ["off", "on"],
                              "samples": [[0, "off"], [1, "on"]]},
                             {"name": "Threshold", "is_quantized": False, "min": 0, "max": 1,
                              "samples": [[i / 4, f"{-40 + 10 * i} dB"] for i in range(5)]},
                             {"name": "Model", "is_quantized": True, "value_items": ["Peak", "RMS", "Expand"],
                              "samples": [[0, "Peak"], [1, "RMS"], [2, "Expand"]]}]}]}

    def sweep(self, *args):
        with tempfile.TemporaryDirectory() as d:
            dump = os.path.join(d, "dump.json")
            out = os.path.join(d, "cases.json")
            with open(dump, "w") as f:
                json.dump(self.DUMP, f)
            with contextlib.redirect_stdout(io.StringIO()):
                cases.main(["sweep", dump, "--device", "Compressor", "-o", out] + list(args))
            with open(out) as f:
                return json.load(f)

    def test_continuous_sweep(self):
        c = self.sweep("--param", "Threshold", "--points", "3", "--set", "Model=item:RMS")
        self.assertEqual(c["device"], "Compressor")
        self.assertEqual([x["id"] for x in c["cases"]], ["bypass", "default", "Threshold-0pct", "Threshold-50pct", "Threshold-100pct"])
        self.assertEqual(c["cases"][0]["params"], {"Device On": 0})
        self.assertEqual(c["cases"][3]["params"], {"Model": {"item": "RMS"}, "Threshold": {"norm": 0.5}})

    def test_quantized_and_display_sweeps(self):
        c = self.sweep("--param", "Model")
        self.assertEqual([x["params"]["Model"] for x in c["cases"][2:]], [{"item": "Peak"}, {"item": "RMS"}, {"item": "Expand"}])
        c = self.sweep("--param", "Threshold", "--display=-30,-20")
        self.assertEqual(c["cases"][2]["params"]["Threshold"], {"display": -30.0})

    def test_unknown_parameter_is_an_error(self):
        with self.assertRaises(SystemExit):
            self.sweep("--param", "Knee")

    def test_taper(self):
        p = self.DUMP["devices"][0]["parameters"]
        self.assertEqual(cases.taper(p[1]), "linear")
        self.assertEqual(cases.taper(p[2]), "stepped")
        logp = {"samples": [[i / 8, f"{20 * 1000 ** (i / 8):.1f} Hz"] for i in range(9)]}
        self.assertEqual(cases.taper(logp), "logarithmic")


SET_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Ableton MajorVersion="5" MinorVersion="12.0_12402" Creator="Ableton Live 12.4.6"><LiveSet><Tracks>
<AudioTrack Id="1"><Name><EffectiveName Value="Probe"/></Name><DeviceChain><Mixer><Speaker><Manual Value="true"/></Speaker></Mixer></DeviceChain></AudioTrack>
<AudioTrack Id="2"><Name><EffectiveName Value="thr-12"/></Name><DeviceChain><Mixer><Speaker><Manual Value="true"/></Speaker></Mixer></DeviceChain></AudioTrack>
<AudioTrack Id="3"><Name><EffectiveName Value="thr 6/7"/></Name><DeviceChain><Mixer/></DeviceChain></AudioTrack>
</Tracks></LiveSet></Ableton>"""


class RenderSet(unittest.TestCase):
    def test_solo_copy_switches_other_tracks_off(self):
        root = render_set.ET.fromstring(SET_XML.split("\n", 1)[1])
        copy = render_set.solo_copy(root, 1)
        on = [t.find("DeviceChain/Mixer/Speaker/Manual").get("Value") for t in render_set.tracks(copy)]
        self.assertEqual(on, ["false", "true", "false"])
        # the original is untouched
        self.assertEqual(root.find("LiveSet/Tracks/AudioTrack/DeviceChain/Mixer/Speaker/Manual").get("Value"), "true")

    def test_renders_each_track_with_the_cli(self):
        with tempfile.TemporaryDirectory() as d:
            als = os.path.join(d, "cases.als")
            with open(als, "wb") as f:
                f.write(gzip.compress(SET_XML.encode()))
            # a stand-in renderer that records the solo state it was given
            fake = os.path.join(d, "fake-cli")
            with open(fake, "w") as f:
                f.write("#!" + sys.executable + "\n"
                        "import sys, gzip, re\n"
                        "src = gzip.open(sys.argv[2]).read().decode()\n"
                        "vals = re.findall(r'Speaker>\\s*<Manual Value=\"(\\w+)\"', src)\n"
                        "open(sys.argv[4], 'w').write(','.join(vals))\n")
            os.chmod(fake, os.stat(fake).st_mode | stat.S_IEXEC)
            out = os.path.join(d, "out")
            with contextlib.redirect_stdout(io.StringIO()):
                code = render_set.main([als, "-o", out, "--command", f"'{fake}' render {{set}} -o {{out}}"])
            self.assertEqual(code, 0)
            self.assertEqual(sorted(os.listdir(out)), ["Probe.wav", "thr-12.wav", "thr_6_7.wav"])
            with open(os.path.join(out, "thr-12.wav")) as f:
                self.assertEqual(f.read(), "false,true,false")
            self.assertEqual([f for f in os.listdir(d) if f.startswith(".render-set")], [])

    def test_unknown_track_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            als = os.path.join(d, "cases.als")
            with open(als, "w") as f:
                f.write(SET_XML)
            err = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                code = render_set.main([als, "-o", os.path.join(d, "o"), "--command", "/bin/true {set} {out}", "--only", "nope"])
            self.assertEqual(code, 1)
            self.assertIn("no tracks named nope", err.getvalue())

    def test_command_needs_the_set_and_the_output(self):
        for command in ("render {set}", "render {out}", ""):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                render_set.main(["cases.als", "--command", command])

    def test_a_renderer_that_cannot_start_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            als = os.path.join(d, "cases.als")
            with open(als, "w") as f:
                f.write(SET_XML)
            err = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                code = render_set.main([als, "-o", os.path.join(d, "o"), "--command",
                                        os.path.join(d, "missing") + " {set} {out}", "--only", "Probe"])
            self.assertEqual(code, 1)
            self.assertIn("the renderer failed", err.getvalue())
            self.assertEqual([f for f in os.listdir(d) if f.startswith(".render-set")], [])


if __name__ == "__main__":
    unittest.main()
