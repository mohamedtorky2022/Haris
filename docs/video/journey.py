"""The Haris journey video: the poster, then a resident, a visitor and a child, the authority's screen,
community warnings, privacy, how it works, and what comes next.

Haris narrates each line (voice.py records it), captions appear beside him, he points at each step,
and hopeful music (composed here in code, so there is no licence to clear) plays under his voice.
    python3 docs/video/journey.py ar               # one language
    python3 docs/video/journey.py all              # ar, en
    python3 docs/video/journey.py ar --stills 3,20 # only draw frames at these seconds
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from playwright.sync_api import sync_playwright
from scipy.signal import butter, fftconvolve, sosfilt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "out"
FPS, LEAD, SR = 30, 0.5, 44100


# --- Music -------------------------------------------------------------------
# Hopeful and steady, and quiet enough to sit under the narration: a warm pad, a plucked
# arpeggio in eighth notes, a soft pulse (kick and shaker), a bass and a bell-like melody,
# at 84 beats a minute in C major (Am - F - C - G), ending on a held C chord.

BPM = 84
BEAT = 60 / BPM
BAR = 4 * BEAT
PROGRESSION = [  # one chord a bar: notes for the pad and the arpeggio, and the bass root
    ("Am", [57, 60, 64, 67], 45), ("F", [53, 57, 60, 64], 41),
    ("C", [48, 55, 60, 64], 36), ("G", [55, 59, 62, 67], 43),
    ("Am", [57, 60, 64, 69], 45), ("F", [53, 57, 60, 65], 41),
    ("C", [52, 55, 60, 64], 36), ("Gsus", [55, 60, 62, 67], 43),
]
FINAL = ("C", [48, 55, 60, 64, 67], 36)
# a bell melody over 8 bars: (bar, beat, midi, beats)
MELODY = [(0, 0, 76, 1.5), (0, 1.5, 74, 0.5), (0, 2, 72, 2), (1, 0, 72, 1), (1, 1, 69, 3),
          (2, 0, 67, 1.5), (2, 1.5, 72, 0.5), (2, 2, 76, 2), (3, 0, 74, 4),
          (4, 0, 76, 1.5), (4, 1.5, 79, 0.5), (4, 2, 76, 2), (5, 0, 77, 1), (5, 1, 72, 3),
          (6, 0, 72, 1.5), (6, 1.5, 74, 0.5), (6, 2, 76, 2), (7, 0, 74, 4)]


def hz(m: float) -> float:
    return 440 * 2 ** ((m - 69) / 12)


def env(n: int, attack: float, release: float) -> np.ndarray:
    e = np.ones(n)
    a, r = min(n, int(attack * SR)), min(n, int(release * SR))
    if a:
        e[:a] = np.linspace(0, 1, a)
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def music(total: float) -> np.ndarray:
    n = int(total * SR) + 6 * SR
    left, right = np.zeros(n), np.zeros(n)
    rng = np.random.default_rng(11)

    def add(sig, start, pan=0.0, gain=1.0):
        s = int(start * SR)
        if s >= n:
            return
        e = min(n, s + len(sig))
        left[s:e] += sig[: e - s] * gain * (1 - pan) / 2
        right[s:e] += sig[: e - s] * gain * (1 + pan) / 2

    bars = int(np.ceil(total / BAR))
    lp = butter(2, 1400, "low", fs=SR, output="sos")
    plp = butter(2, 3200, "low", fs=SR, output="sos")
    hp = butter(2, 6500, "high", fs=SR, output="sos")
    # one-shot sounds
    tk = np.arange(int(0.35 * SR)) / SR
    kick = np.sin(2 * np.pi * np.cumsum(45 + 70 * np.exp(-tk * 30)) / SR) * np.exp(-tk * 9)
    shaker = sosfilt(hp, rng.standard_normal(int(0.09 * SR))) * np.exp(-np.arange(int(0.09 * SR)) / SR * 45)
    for b in range(bars):
        last = b >= bars - 2
        if last and b == bars - 1:
            continue
        name, notes, root = FINAL if last else PROGRESSION[b % len(PROGRESSION)]
        start = b * BAR
        length = int((BAR + 1.5) * SR) if not last else int((2 * BAR + 2.5) * SR)
        t = np.arange(length) / SR
        # pad: soft, slightly detuned, with a slow swell
        for m in notes:
            for det, pan in ((-5, -0.6), (5, 0.6)):
                f = hz(m - 12) * 2 ** (det / 1200)
                tone = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) + 0.1 * np.sin(6 * np.pi * f * t)
                add(sosfilt(lp, tone) * env(length, 1.2, 1.6), start, pan, 0.024)
        if last:
            continue
        # plucked arpeggio in eighth notes, from bar 1
        if b >= 1:
            pattern = [0, 1, 2, 3, 2, 1, 2, 3] if b % 2 == 0 else [0, 2, 1, 3, 2, 3, 1, 2]
            for k, idx in enumerate(pattern):
                m = notes[idx] + 12
                ln = int(0.9 * SR)
                ta = np.arange(ln) / SR
                f = hz(m)
                pl = sum(np.sin(2 * np.pi * f * h * ta) / h ** 1.3 for h in range(1, 6))
                pl = sosfilt(plp, pl) * np.exp(-ta * 5.5) * np.clip(ta / 0.003, 0, 1)
                add(pl, start + k * BEAT / 2, 0.35 if k % 2 else -0.35, 0.040 if k % 2 else 0.050)
        # bass and pulse from bar 4
        if b >= 4:
            for k, beats in ((0, 1.5), (1.5, 0.5), (2, 2)):
                bl = int(beats * BEAT * SR)
                tb = np.arange(bl) / SR
                bass = (np.sin(2 * np.pi * hz(root) * tb) + 0.2 * np.sin(4 * np.pi * hz(root) * tb)) * env(bl, 0.02, 0.15)
                add(bass, start + k * BEAT, 0, 0.085)
            for k in range(4):
                add(kick, start + k * BEAT, 0, 0.11 if k % 2 == 0 else 0.07)
            for k in range(8):
                add(shaker, start + k * BEAT / 2 + 0.01, 0.4, 0.020 if k % 2 else 0.011)
    # bell melody: every other 8-bar phrase, from bar 8
    for phrase in range(8, bars - 4, 16):
        for bar, beat, m, beats in MELODY:
            s = (phrase + bar) * BAR + beat * BEAT
            if s > (bars - 3) * BAR:
                break
            ln = int((beats * BEAT + 1.2) * SR)
            tm = np.arange(ln) / SR
            f = hz(m)
            bell = (np.sin(2 * np.pi * f * tm) + 0.4 * np.sin(2 * np.pi * 2.0 * f * tm) * np.exp(-tm * 3)
                    + 0.15 * np.sin(2 * np.pi * 3.0 * f * tm) * np.exp(-tm * 6))
            add(bell * np.exp(-tm * 1.8) * np.clip(tm / 0.004, 0, 1), s, -0.15, 0.040)

    # a soft room
    ir_t = np.arange(int(2.2 * SR)) / SR
    irs = [rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.55) for _ in range(2)]
    wet = [fftconvolve(ch, ir)[:n] for ch, ir in zip((left, right), irs)]
    mix = np.stack([left + 0.018 * wet[0], right + 0.018 * wet[1]], axis=1)
    fade = np.ones(n)
    fi, fo = int(1.5 * SR), int(4.0 * SR)
    fade[:fi] = np.linspace(0, 1, fi)
    end = int(total * SR)
    fade[end - fo:end] = np.linspace(1, 0, fo)
    fade[end:] = 0
    mix *= fade[:, None]
    return (mix / np.max(np.abs(mix)) * 0.8)[:end]


def write_music(total: float, path: Path, voice=None) -> Path:
    mix = music(total)
    if voice is not None:  # the music steps back while Haris speaks
        talk = np.convolve(np.abs(voice) > 0.01, np.ones(int(0.6 * SR)) / (0.6 * SR), mode="same")
        duck = 1 - 0.65 * np.clip(talk * 4, 0, 1)
        mix = mix * duck[: len(mix), None] * 0.8
        n = min(len(mix), len(voice))
        mix[:n] += voice[:n, None] * 0.9
        mix /= max(1.0, np.max(np.abs(mix)) / 0.95)
    pcm = (mix * 32767).astype("<i2")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-", str(path)],
                   input=pcm.tobytes(), check=True)
    return path


# --- Video -------------------------------------------------------------------


def data(lang: str) -> dict:
    journey = json.loads((HERE / "journey.json").read_text())
    scenes = journey["scenes"]
    total = LEAD + sum(s["dur"] for s in scenes)
    shared = {k: journey[k] for k in ("ru", "alerts", "refs")}
    ui = journey[lang]
    timing = OUT / f"voice-{lang}" / "timing.json"
    if timing.exists():  # narrated: scenes last as long as their lines, captions start with them
        tm = json.loads(timing.read_text())
        for s in scenes:
            s["dur"] = tm["scenes"][s["k"]]
        for k, caps in tm["captions"].items():
            ui["captions"][k] = [[at, ui["captions"][k][i][1]] for at, i in caps]
        total = LEAD + sum(s["dur"] for s in scenes)
        voice = voice_track(lang, total)
        speech = [[c["t"], c["len"]] for c in tm["clips"]]
        return {"lang": lang, "ui": ui, "shared": shared, "scenes": scenes, "lead": LEAD, "total": total,
                "lips": lips(voice), "speech": speech}
    return {"lang": lang, "ui": ui, "shared": shared, "scenes": scenes, "lead": LEAD, "total": total,
            "lips": [], "speech": []}


def lips(voice) -> list:
    """How far Haris's mouth is open in each frame (0-1), from the loudness of the narration."""
    hop = SR // FPS
    n = len(voice) // hop
    rms = np.sqrt(np.mean(voice[: n * hop].reshape(n, hop) ** 2, axis=1))
    ref = np.percentile(rms[rms > 1e-4], 95) if np.any(rms > 1e-4) else 1
    level = np.clip((rms / ref - 0.12) / 0.88, 0, 1)
    smooth = np.convolve(level, [0.25, 0.5, 0.25], mode="same")
    return [round(float(v), 2) for v in smooth]


def voice_track(lang: str, total: float):
    """The narration as one mono track, or None when the language has no recorded voice."""
    timing = OUT / f"voice-{lang}" / "timing.json"
    if not timing.exists():
        return None
    track = np.zeros(int(total * SR) + SR)
    for c in json.loads(timing.read_text())["clips"]:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(OUT / f"voice-{lang}" / c["file"]), "-f", "s16le",
                              "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
        clip = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768
        s = int(c["t"] * SR)
        track[s:s + len(clip)] += clip[: len(track) - s]
    return track[: int(total * SR)]


def open_page(p, d):
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto((HERE / "journey.html").as_uri())
    page.evaluate("d => init(d)", d)
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(300)
    return browser, page


def stills(lang: str, times: list[float]) -> None:
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser, page = open_page(p, data(lang))
        for t in times:
            page.evaluate(f"render({t})")
            page.screenshot(path=str(OUT / f"jstill-{lang}-{t:05.1f}.jpg"), type="jpeg", quality=90)
        browser.close()


def render(lang: str, track: Path) -> Path:
    d = data(lang)
    OUT.mkdir(exist_ok=True)
    video, tmp, final = OUT / f"_jvideo-{lang}.mp4", OUT / f"_jtmp-{lang}.mp4", OUT / f"Haris-journey-{lang}.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg",
                            "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                            str(video)], stdin=subprocess.PIPE)
    frames = int(d["total"] * FPS)
    with sync_playwright() as p:
        browser, page = open_page(p, d)
        for f in range(frames):
            page.evaluate(f"render({f / FPS})")
            enc.stdin.write(page.screenshot(type="jpeg", quality=92))
            if f % 300 == 0:
                print(f"{lang}: {f}/{frames}", flush=True)
        browser.close()
    enc.stdin.close()
    assert enc.wait() == 0
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(track), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5", "-c:a", "aac", "-b:a", "160k", "-shortest",
                    "-movflags", "+faststart", str(tmp)], check=True)
    tmp.rename(final)
    video.unlink()
    return final


if __name__ == "__main__":
    langs = ["ar", "en"] if sys.argv[1] == "all" else [sys.argv[1]]
    if "--stills" in sys.argv:
        times = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")]
        for lang in langs:
            stills(lang, times)
    else:
        for lang in langs:
            d = data(lang)
            track = write_music(d["total"], OUT / f"music-{lang}.wav", voice_track(lang, d["total"]))
            print(render(lang, track))
