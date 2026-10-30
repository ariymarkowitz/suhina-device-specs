"""Renders a built comparison set through Suhina, one WAV per track, into sets/<name>/suhina/.

    python compare/render_suhina.py NAME [--cli path/to/suhina-cli] [--only track,track]

NAME is the folder in sets/ build_set.py made. The renderer is suhina-cli of the suhina-daw
checkout beside this repository (release build) unless --cli says otherwise. Uses
tools/harness/render_set.py, so each track is rendered alone.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = os.path.join(ROOT, "tools", ".venv", "bin", "python")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("--cli", default=os.path.join(ROOT, "..", "suhina-daw", "target", "release", "suhina-cli"))
    ap.add_argument("--only")
    a = ap.parse_args()
    folder = os.path.join(HERE, "sets", a.name)
    if not os.path.exists(os.path.join(folder, "set.als")):
        sys.exit(f"no set {a.name}; run compare/build_set.py first")
    if not os.path.exists(a.cli):
        sys.exit(f"{a.cli} not found; build it (cargo build --release -p suhina-cli in suhina-daw) or pass --cli")
    cmd = [PY, os.path.join(ROOT, "tools", "harness", "render_set.py"), os.path.join(folder, "set.als"),
           "-o", os.path.join(folder, "suhina"), "--rate", "44100",
           "--command", f"{os.path.abspath(a.cli)} render {{set}} -o {{out}} --sample-rate {{rate}}"]
    if a.only:
        cmd += ["--only", a.only]
    sys.exit(subprocess.run(cmd).returncode)


if __name__ == "__main__":
    main()
