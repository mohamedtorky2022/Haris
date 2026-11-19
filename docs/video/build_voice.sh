#!/bin/bash
# Records Haris's lines with the macOS system voices (the same voices the browser uses).
# Run on a Mac from the repo root:  bash docs/video/build_voice.sh
set -euo pipefail
cd "$(dirname "$0")"
/usr/bin/python3 - <<'PY'
import json, os, subprocess
S = json.load(open("scripts.json"))
installed = subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout
def best(voice):  # prefer the clearer Premium or Enhanced download of the same voice when installed
    for kind in ("Premium", "Enhanced"):
        if f"{voice} ({kind})" in installed:
            return f"{voice} ({kind})"
    return voice
for lang, spec in S.items():
    voice = best(spec["voice"])
    print(lang, "->", voice)
    os.makedirs(f"voice/{lang}", exist_ok=True)
    for i, line in enumerate(spec["lines"], 1):
        out = f"voice/{lang}/{i:02d}.m4a"
        text = line.get("say", line["show"])
        subprocess.run(["say", "-v", voice, "-r", str(spec["rate"]), "-o", out,
                        "--file-format=m4af", "--data-format=alac", text], check=True)
        print(out)
PY
