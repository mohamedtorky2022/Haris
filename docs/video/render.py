"""Renders the Haris explainer videos, one per language.

Needs ffmpeg and Playwright's Chromium. The voice clips come from build_voice.sh (macOS).
    python3 docs/video/render.py ar            # one language
    python3 docs/video/render.py all           # all four
    python3 docs/video/render.py ar --stills 3.0,20.5   # only draw frames at these seconds
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "out"
FPS, LEAD, GAP, TAIL = 30, 0.8, 0.45, 2.6
RATE = 16000


def pcm(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(RATE), "-f", "s16le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768


def prepare(src: Path, dst: Path, tempo: float) -> Path:
    """A clean copy of one voice clip: slightly faster if asked, low rumble removed."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", f"atempo={tempo},highpass=f=70",
                    "-ar", "44100", str(dst)], check=True)
    return dst


def timeline(lang: str, spec: dict) -> dict:
    t, lines, track = LEAD, [], []
    for i, line in enumerate(spec["lines"], 1):
        clip = prepare(HERE / "voice" / lang / f"{i:02d}.m4a", OUT / "clips" / lang / f"{i:02d}.wav", spec.get("tempo", 1.0))
        audio = pcm(clip)
        dur = len(audio) / RATE
        lines.append({**line, "t0": round(t, 3), "t1": round(t + dur, 3), "clip": str(clip)})
        track.append((t, audio))
        t += dur + (GAP if i < len(spec["lines"]) else 0)
    total = t + TAIL
    full = np.zeros(int(total * RATE) + RATE, dtype=np.float32)
    for start, audio in track:
        s = int(start * RATE)
        full[s:s + len(audio)] += audio
    # mouth opening per video frame: loudness, smoothed and scaled to 0..1
    hop = RATE // FPS
    frames = int(total * FPS) + 1
    rms = np.array([np.sqrt(np.mean(full[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(frames)])
    ref = np.percentile(rms[rms > 1e-3], 90) if (rms > 1e-3).any() else 1
    env = np.clip(rms / ref, 0, 1)
    env = np.convolve(env, [0.25, 0.5, 0.25], mode="same")
    env[env < 0.06] = 0
    return {"lines": lines, "total": round(total, 3), "env": [round(float(x), 3) for x in env]}


def page_data(lang: str, spec: dict, tl: dict) -> dict:
    locale = json.loads((ROOT / "backend" / "haris" / "locales" / f"{lang}.json").read_text())
    ui = {**spec["ui"], "risk": locale["risk_labels"]["high"]}
    return {"lang": lang, "dir": spec["dir"], "font": spec["font"], "ui": ui,
            "lines": [{k: l[k] for k in ("scene", "show", "t0", "t1")} for l in tl["lines"]],
            "total": tl["total"], "env": tl["env"]}


def open_page(p, data):
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto((HERE / "haris-video.html").as_uri())
    page.evaluate("d => init(d)", data)
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(300)
    return browser, page


def stills(lang: str, times: list[float]) -> None:
    spec = json.loads((HERE / "scripts.json").read_text())[lang]
    data = page_data(lang, spec, timeline(lang, spec))
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser, page = open_page(p, data)
        for t in times:
            page.evaluate(f"render({t})")
            page.screenshot(path=str(OUT / f"still-{lang}-{t:05.1f}.jpg"), type="jpeg", quality=90)
        browser.close()


def render(lang: str) -> Path:
    spec = json.loads((HERE / "scripts.json").read_text())[lang]
    tl = timeline(lang, spec)
    data = page_data(lang, spec, tl)
    OUT.mkdir(exist_ok=True)
    video_tmp, final = OUT / f"_video-{lang}.mp4", OUT / f"Haris-{lang}.mp4"
    tmp = OUT / f"_tmp-{lang}.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg",
                            "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                            "-r", str(FPS), str(video_tmp)], stdin=subprocess.PIPE)
    frames = int(tl["total"] * FPS)
    with sync_playwright() as p:
        browser, page = open_page(p, data)
        for f in range(frames):
            page.evaluate(f"render({f / FPS})")
            enc.stdin.write(page.screenshot(type="jpeg", quality=92))
            if f % 300 == 0:
                print(f"{lang}: {f}/{frames}", flush=True)
        browser.close()
    enc.stdin.close()
    assert enc.wait() == 0
    # the voice: every clip placed at its start time
    inputs, filters = [], []
    for i, l in enumerate(tl["lines"]):
        inputs += ["-i", l["clip"]]
        ms = int(l["t0"] * 1000)
        filters.append(f"[{i + 1}:a]adelay={ms}|{ms}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(tl["lines"])))
    filters.append(f"{mix}amix=inputs={len(tl['lines'])}:normalize=0,loudnorm=I=-16:TP=-1.5,apad[aout]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video_tmp), *inputs, "-filter_complex", ";".join(filters),
                    "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-ac", "2",
                    "-shortest", "-movflags", "+faststart", str(tmp)], check=True)
    tmp.rename(final)
    video_tmp.unlink()
    return final


if __name__ == "__main__":
    langs = ["ar", "en", "ur", "hi"] if sys.argv[1] == "all" else [sys.argv[1]]
    if "--stills" in sys.argv:
        times = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")]
        for lang in langs:
            stills(lang, times)
    else:
        for lang in langs:
            print(render(lang))
