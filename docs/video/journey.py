"""The Haris journey video: the poster, then a resident, a visitor and a child, the authority's screen,
community warnings, privacy, how it works, and what comes next.

Haris does not speak: captions appear beside him, he points at each step, and calm music
(composed here in code, so there is no licence to clear) plays.
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
# Calm and unobtrusive, so the viewer can read: a soft pad, a slow piano-like arpeggio,
# a quiet bass and a sparse melody, at 60 beats a minute, ending on a held chord.

BPM = 60
BEAT = 60 / BPM
BAR = 4 * BEAT
PROGRESSION = [  # one chord a bar: notes for the pad, the arpeggio and the bass root
    ("Dmaj7", [50, 54, 57, 61], 38), ("Bm7", [47, 50, 54, 57], 35),
    ("Gmaj7", [43, 47, 50, 54], 31), ("A6", [45, 49, 52, 54], 33),
    ("Dmaj7", [50, 54, 57, 61], 38), ("F#m7", [42, 45, 49, 52], 30),
    ("Gmaj7", [43, 47, 50, 54], 31), ("Asus", [45, 50, 52, 57], 33),
]
FINAL = ("D", [50, 54, 57, 62], 38)
# a quiet melody over 8 bars: (bar, beat, midi, beats)
MELODY = [(0, 0, 69, 3), (1, 0, 66, 2), (1, 2, 69, 2), (2, 0, 71, 3), (3, 0, 69, 4),
          (4, 0, 73, 3), (5, 0, 69, 2), (5, 2, 66, 2), (6, 0, 67, 3), (7, 0, 69, 4)]


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
    n = int(total * SR) + 4 * SR
    left, right = np.zeros(n), np.zeros(n)

    def add(sig, start, pan=0.0, gain=1.0):
        s = int(start * SR)
        if s >= n:
            return
        e = min(n, s + len(sig))
        left[s:e] += sig[: e - s] * gain * (1 - pan) / 2
        right[s:e] += sig[: e - s] * gain * (1 + pan) / 2

    bars = int(np.ceil(total / BAR))
    lp = butter(2, 1600, "low", fs=SR, output="sos")
    for b in range(bars):
        last = b >= bars - 2
        name, notes, root = FINAL if last else PROGRESSION[b % len(PROGRESSION)]
        start = b * BAR
        length = int((BAR + 1.8) * SR) if not last else int((2 * BAR + 2) * SR)
        if last and b == bars - 1:
            continue
        t = np.arange(length) / SR
        # pad: soft sines with a slow swell, slightly detuned left and right
        for m in notes:
            for det, pan in ((-4, -0.5), (4, 0.5)):
                f = hz(m) * 2 ** (det / 1200)
                tone = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t) + 0.08 * np.sin(6 * np.pi * f * t)
                add(sosfilt(lp, tone) * env(length, 1.6, 2.0), start, pan, 0.030)
        # bass from bar 2
        if b >= 2:
            bl = int((BAR + 0.6) * SR) if not last else length
            tb = np.arange(bl) / SR
            bass = np.sin(2 * np.pi * hz(root) * tb) * env(bl, 0.3, 1.2)
            add(bass, start, 0, 0.10)
        # piano-like arpeggio, one note a beat, from bar 2 until the last chord
        if 2 <= b and not last:
            order = [0, 1, 2, 3] if b % 2 == 0 else [3, 2, 1, 2]
            for i in range(4):
                m = notes[order[i]] + 12
                ta = np.arange(int(2.4 * SR)) / SR
                key = (np.sin(2 * np.pi * hz(m) * ta) + 0.35 * np.sin(4 * np.pi * hz(m) * ta) + 0.1 * np.sin(6 * np.pi * hz(m) * ta))
                key *= np.exp(-ta * 1.6) * np.clip(ta / 0.006, 0, 1)
                add(key, start + i * BEAT, 0.25 if i % 2 else -0.25, 0.055)
    # the melody: a soft flute-like line every other 8-bar phrase, from bar 10
    flp = butter(2, 2400, "low", fs=SR, output="sos")
    for phrase in range(10, bars - 4, 16):
        for bar, beat, m, beats in MELODY:
            s = (phrase + bar) * BAR + beat * BEAT
            if s > (bars - 3) * BAR:
                break
            ln = int((beats * BEAT + 0.6) * SR)
            tm = np.arange(ln) / SR
            vib = 1 + 0.003 * np.sin(2 * np.pi * 4.5 * tm) * np.clip(tm - 0.4, 0, 1)
            ph = 2 * np.pi * hz(m) * np.cumsum(vib) / SR
            tone = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.05 * np.sin(3 * ph)
            add(sosfilt(flp, tone) * env(ln, 0.25, 0.6), s, 0.1, 0.045)

    # a soft hall
    rng = np.random.default_rng(7)
    ir_t = np.arange(int(3.0 * SR)) / SR
    irs = [rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.8) for _ in range(2)]
    wet = [fftconvolve(ch, ir)[:n] for ch, ir in zip((left, right), irs)]
    mix = np.stack([left + 0.02 * wet[0], right + 0.02 * wet[1]], axis=1)
    fade = np.ones(n)
    fi, fo = int(2.5 * SR), int(4.0 * SR)
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
