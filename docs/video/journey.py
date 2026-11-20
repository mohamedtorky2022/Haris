"""The Haris journey video: from scanning the poster to the official warning.

Haris does not speak: captions appear beside him, he points at each step, and
formal music (composed here in code, so there is no licence to clear) plays.
    python3 docs/video/journey.py ar               # one language
    python3 docs/video/journey.py all              # ar, en, ur, hi
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
NATIVE = {"ar": "العربية", "en": "English", "ur": "اردو", "hi": "हिन्दी"}


# --- Music -------------------------------------------------------------------

BPM = 72
BEAT = 60 / BPM
BAR = 4 * BEAT
CHORD = {"D": (62, "maj"), "Bm": (59, "min"), "G": (55, "maj"), "A": (57, "maj"), "F#m": (54, "min")}
# The piece is built from 4-bar blocks: an intro, then phrases A B C D (repeating B C D for a
# longer video), then a 2-bar cadence, so it always ends on its last chord with the video.
BLOCKS = {  # chords, and melody as (bar in block, beat, midi note, beats)
    "intro": (["D", "Bm", "G", "A"], []),
    "A": (["D", "Bm", "G", "A"], [(0, 0, 66, 2), (0, 2, 69, 2), (1, 0, 66, 2), (1, 2, 62, 2), (2, 0, 67, 2), (2, 2, 71, 2), (3, 0, 69, 4)]),
    "B": (["D", "F#m", "G", "A"], [(0, 0, 74, 2), (0, 2, 73, 1), (0, 3, 71, 1), (1, 0, 69, 4), (2, 0, 71, 2), (2, 2, 74, 2), (3, 0, 73, 2), (3, 2, 76, 2)]),
    "C": (["Bm", "G", "D", "A"], [(0, 0, 74, 2), (0, 2, 78, 2), (1, 0, 74, 4), (2, 0, 69, 2), (2, 2, 74, 2), (3, 0, 73, 4)]),
    "D": (["D", "Bm", "G", "A"], [(0, 0, 78, 2), (0, 2, 76, 1), (0, 3, 74, 1), (1, 0, 74, 2), (1, 2, 71, 2), (2, 0, 71, 2), (2, 2, 74, 2), (3, 0, 76, 4)]),
    "end": (["A", "D"], [(0, 0, 73, 2), (0, 2, 76, 2), (1, 0, 74, 4)]),
}


def plan(body_blocks: int) -> list[str]:
    order = ["A", "B", "C", "D"] + ["B", "C", "D"] * 4
    return ["intro"] + order[:body_blocks] + ["end"]


def bars_for(body_blocks: int) -> int:
    return 4 + 4 * body_blocks + 2


def schedule(body_blocks: int):
    """Chords per bar, melody notes with absolute bars, and the bars where a block starts."""
    chords, melody, starts = [], [], []
    for name in plan(body_blocks):
        start = len(chords)
        starts.append((start, name))
        names, notes = BLOCKS[name]
        chords += names
        melody += [(start + b, beat, m, n) for b, beat, m, n in notes]
    return chords, melody, starts


def hz(m: float) -> float:
    return 440 * 2 ** ((m - 69) / 12)


def env(n: int, attack: float, release: float) -> np.ndarray:
    e = np.ones(n)
    a, r = int(attack * SR), int(release * SR)
    e[:a] = np.linspace(0, 1, a) if a else 1
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def saw(f: float, n: int, harmonics: int = 14, detune: float = 0.0) -> np.ndarray:
    t = np.arange(n) / SR
    f = f * 2 ** (detune / 1200)
    out = np.zeros(n)
    for k in range(1, harmonics + 1):
        if f * k > 9000:
            break
        out += np.sin(2 * np.pi * f * k * t + k) / k
    return out


def chord_notes(name: str) -> list[int]:
    root, q = CHORD[name]
    third = 3 if q == "min" else 4
    return [root, root + third, root + 7, root + 12]


def music(total: float, body_blocks: int) -> np.ndarray:
    progression, melody, block_starts = schedule(body_blocks)
    last = len(progression) - 1
    n = int(total * SR) + SR
    left, right = np.zeros(n), np.zeros(n)

    def add(sig, start, pan=0.0, gain=1.0):
        s = int(start * SR)
        e = min(n, s + len(sig))
        left[s:e] += sig[: e - s] * gain * (1 - pan) / 2
        right[s:e] += sig[: e - s] * gain * (1 + pan) / 2

    lp = butter(2, 2200, "low", fs=SR, output="sos")
    loud = {start for start, name in block_starts if name in ("C", "D")}
    bell_bars = set()
    for start, name in block_starts:
        if name in ("C", "D") and start >= 12:
            bell_bars.update(range(start, start + 4))
    bell_bars.add(last - 1)
    timpani_bars = {start for start, name in block_starts if name != "end"}
    for b, name in enumerate(progression):
        start = b * BAR
        length = int((BAR + 0.9) * SR)
        # strings pad: detuned saws, soft
        for m in chord_notes(name):
            for det, pan in ((-7, -0.6), (6, 0.6), (0, 0)):
                tone = saw(hz(m), length, detune=det)
                add(sosfilt(lp, tone) * env(length, 0.7, 0.9), start, pan, 0.045 if b < 4 else 0.055)
        # bass from bar 4
        if b >= 4:
            t = np.arange(int(BAR * SR)) / SR
            f = hz(CHORD[name][0] - 24 if CHORD[name][0] >= 57 else CHORD[name][0] - 12)
            bass = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * env(len(t), 0.05, 0.4)
            add(bass, start, 0, 0.16)
        # bells: an arpeggio of eighth notes in the later phrases
        if b in bell_bars:
            notes = chord_notes(name)
            for i in range(8):
                m = notes[i % 4] + 12
                t = np.arange(int(0.9 * SR)) / SR
                bell = (np.sin(2 * np.pi * hz(m) * t) + 0.25 * np.sin(2 * np.pi * hz(m) * 2.76 * t)) * np.exp(-t * 5)
                add(bell, start + i * BEAT / 2, 0.3 if i % 2 else -0.3, 0.05)
        # timpani on the strong bars, and a roll into the last chord
        if b in timpani_bars:
            add(timpani(hz(38)), start, 0, 0.5)
    roll_start = (last - 1) * BAR + 2 * BEAT
    for i in range(16):
        add(timpani(hz(45)) * (0.25 + 0.04 * i), roll_start + i * (2 * BEAT / 16), 0, 0.35)
    add(timpani(hz(38)) * 1.2, last * BAR, 0, 0.6)

    # horn melody
    hlp = butter(2, 1800, "low", fs=SR, output="sos")
    for bar, beat, m, beats in melody:
        length = int((beats * BEAT + 0.35) * SR)
        if bar == last:
            length = int((4 * BEAT + 2.0) * SR)
        t = np.arange(length) / SR
        vib = 1 + 0.004 * np.sin(2 * np.pi * 5 * t) * np.clip((t - 0.3) * 3, 0, 1)
        f = hz(m)
        tone = sum(np.sin(2 * np.pi * f * k * np.cumsum(vib) / SR) / k ** 1.3 for k in range(1, 9))
        horn = sosfilt(hlp, tone) * env(length, 0.08, 0.3) * (0.85 + 0.15 * np.exp(-t * 3))
        add(horn, bar * BAR + beat * BEAT, 0.15, 0.13 if bar >= 12 else 0.10)

    # a hall: short decaying noise as the impulse response
    rng = np.random.default_rng(7)
    ir_t = np.arange(int(2.4 * SR)) / SR
    irs = [rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.55) for _ in range(2)]
    wet = [fftconvolve(ch, ir)[:n] for ch, ir in zip((left, right), irs)]
    mix = np.stack([left + 0.022 * wet[0], right + 0.022 * wet[1]], axis=1)
    fade = np.ones(n)
    fi, fo = int(1.2 * SR), int(2.5 * SR)
    fade[:fi] = np.linspace(0, 1, fi)
    end = int(total * SR)
    fade[end - fo:end] = np.linspace(1, 0, fo)
    fade[end:] = 0
    mix *= fade[:, None]
    return (mix / np.max(np.abs(mix)) * 0.8)[:end]


def timpani(f: float) -> np.ndarray:
    t = np.arange(int(1.6 * SR)) / SR
    pitch = f * (1 + 0.15 * np.exp(-t * 12))
    tone = np.sin(2 * np.pi * np.cumsum(pitch) / SR) * np.exp(-t * 2.6)
    noise = np.random.default_rng(1).standard_normal(len(t)) * np.exp(-t * 30) * 0.3
    return tone + sosfilt(butter(2, 600, "low", fs=SR, output="sos"), noise)


def write_music(total: float, body_blocks: int, path: Path) -> Path:
    pcm = (music(total, body_blocks) * 32767).astype("<i2")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-", str(path)],
                   input=pcm.tobytes(), check=True)
    return path


# --- Video -------------------------------------------------------------------

SLOW = 1.55  # how much slower than the first cut, so every line on screen can be read


def fit(base: float, slow: float = SLOW) -> tuple[float, int]:
    """The reading factor closest to `slow` that makes the video end with a whole music block."""
    blocks = max(4, round(((base * slow + LEAD) / BAR - 6) / 4))
    return (bars_for(blocks) * BAR - LEAD) / base, blocks


def data(lang: str) -> dict:
    journey = json.loads((HERE / "journey.json").read_text())
    slow, blocks = fit(sum(journey["durations"]))
    spec = json.loads((HERE / "scripts.json").read_text())[lang]
    locale = json.loads((ROOT / "backend" / "haris" / "locales" / f"{lang}.json").read_text())
    ui = {**spec["ui"], **journey[lang], "wa": locale["whatsapp"], "risk": locale["risk_labels"]["high"], "native": NATIVE[lang]}
    durations = [round(d * slow, 4) for d in journey["durations"]]
    total = LEAD + sum(durations)
    return {"lang": lang, "dir": spec["dir"], "font": spec["font"], "ui": ui, "lead": LEAD, "slow": slow,
            "blocks": blocks, "durations": durations, "scenes": journey["scenes"], "total": total}


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
                    "-c:v", "copy", "-af", "loudnorm=I=-18:TP=-1.5", "-c:a", "aac", "-b:a", "160k", "-shortest",
                    "-movflags", "+faststart", str(tmp)], check=True)
    tmp.rename(final)
    video.unlink()
    return final


if __name__ == "__main__":
    langs = ["ar", "en", "ur", "hi"] if sys.argv[1] == "all" else [sys.argv[1]]
    if "--stills" in sys.argv:
        times = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")]
        for lang in langs:
            stills(lang, times)
    else:
        d0 = data(langs[0])
        track = write_music(d0["total"], d0["blocks"], OUT / "music.wav")
        for lang in langs:
            print(render(lang, track))
