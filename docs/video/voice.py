"""Arabic narration for the journey video, recorded with the macOS voice Majed.

    python3 docs/video/voice.py lines ar     # writes out/voice-ar/lines.json (what to record)
    # on a Mac: python3 docs/video/voice.py record ar   (needs `say` and the Majed voice)
    python3 docs/video/voice.py timing ar    # measures the clips and writes out/voice-ar/timing.json

journey.py then lengthens any scene whose narration runs longer than the scene, starts each
caption with its line, and mixes the voice over the music.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VOICE, RATE, GAP, TAIL = "Majed", 240, 0.3, 0.8


def lines(lang: str) -> list[dict]:
    j = json.loads((HERE / "journey.json").read_text())
    ui = j[lang]
    out = []
    for sc in j["scenes"]:
        items = [("caption", i, at, text) for i, (at, text) in enumerate(ui["captions"].get(sc["k"], []))]
        if sc["k"] in ui.get("narration_extra", {}):
            items = [("extra", i, at, text) for i, (at, text) in enumerate(ui["narration_extra"][sc["k"]])]
        for kind, i, at, text in items:
            say = text
            for a, b in ui.get("say", {}).items():
                say = say.replace(a, b)
            out.append({"id": f"{len(out) + 1:02d}", "scene": sc["k"], "kind": kind, "i": i, "at": at, "say": say.strip().lstrip(".، ")})
    return out


def folder(lang: str) -> Path:
    return HERE / "out" / f"voice-{lang}"


def record(lang: str) -> None:
    d = folder(lang)
    d.mkdir(parents=True, exist_ok=True)
    for ln in json.loads((d / "lines.json").read_text()):
        subprocess.run(["say", "-v", VOICE, "-r", str(RATE), "-o", str(d / f"{ln['id']}.aiff"), ln["say"]], check=True)
        print(ln["id"], ln["say"][:40])


def trim(src: Path) -> Path:
    """Cut the silence the voice leaves before and after each line."""
    dst = src.parent / (src.name.split(".")[0] + ".wav")
    af = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", af, "-ar", "44100", "-ac", "1", str(dst)], check=True)
    return dst


def split(lang: str) -> None:
    """Cut long recordings (hamdan1.*, hamdan2.* … as listed in chunks.json) into one clip per line.

    Each recording holds several lines read in order. The cut between two lines is the silence
    nearest the point where the next line should begin, judged by the share of letters before it.
    """
    d = folder(lang)
    lns = {ln["id"]: ln for ln in json.loads((d / "lines.json").read_text())}
    for n, ids in enumerate(json.loads((d / "chunks.json").read_text()), 1):
        src = next(p for p in d.glob(f"hamdan{n}.*") if p.suffix != ".txt")
        total = duration(src)
        log = subprocess.run(["ffmpeg", "-i", str(src), "-af", "silencedetect=noise=-40dB:d=0.25", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
        starts = [float(x.split("silence_start: ")[1].split()[0]) for x in log.splitlines() if "silence_start" in x]
        ends = [float(x.split("silence_end: ")[1].split()[0]) for x in log.splitlines() if "silence_end" in x]
        gaps = [(s, e) for s, e in zip(starts, ends) if e - s >= 0.25]
        chars = [len(lns[i]["say"]) for i in ids]
        cuts, used = [], set()
        for k in range(1, len(ids)):
            want = total * sum(chars[:k]) / sum(chars)
            best = min((g for g in gaps if g not in used), key=lambda g: abs((g[0] + g[1]) / 2 - want))
            used.add(best)
            cuts.append((best[0] + best[1]) / 2)
        cuts = sorted(cuts)
        bounds = [0.0] + cuts + [total]
        for i, a, b in zip(ids, bounds, bounds[1:]):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-ss", f"{a:.3f}", "-to", f"{b:.3f}",
                            "-ar", "44100", "-ac", "1", str(d / f"{i}.src.wav")], check=True)
            print(i, f"{a:6.2f}-{b:6.2f}", lns[i]["say"][:30])


def duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout)


def timing(lang: str) -> None:
    d = folder(lang)
    j = json.loads((HERE / "journey.json").read_text())
    lns = json.loads((d / "lines.json").read_text())
    by_scene: dict[str, list] = {}
    for ln in lns:
        src = d / f"{ln['id']}.src.wav"
        if not src.exists():
            src = d / f"{ln['id']}.aiff"
        ln["len"] = round(duration(trim(src)), 3)
        by_scene.setdefault(ln["scene"], []).append(ln)
    scenes, captions, clips = {}, {}, []
    start = 0.5  # LEAD in journey.py
    for sc in j["scenes"]:
        t_end = 0.0
        caps = []
        for ln in by_scene.get(sc["k"], []):
            at = max(ln["at"], t_end + GAP if t_end else ln["at"])
            t_end = at + ln["len"]
            clips.append({"file": f"{ln['id']}.wav", "t": round(start + at, 3), "len": ln["len"]})
            if ln["kind"] == "caption":
                caps.append([round(at, 2), ln["i"]])
        dur = max(sc["dur"], round(t_end + TAIL, 2))
        scenes[sc["k"]] = dur
        if caps:
            captions[sc["k"]] = caps
        start += dur
    (d / "timing.json").write_text(json.dumps({"scenes": scenes, "captions": captions, "clips": clips}, indent=1))
    print(f"total {start:.1f}s")


if __name__ == "__main__":
    cmd, lang = sys.argv[1], sys.argv[2]
    if cmd == "lines":
        folder(lang).mkdir(parents=True, exist_ok=True)
        (folder(lang) / "lines.json").write_text(json.dumps(lines(lang), ensure_ascii=False, indent=1))
        print(len(lines(lang)), "lines")
    elif cmd == "record":
        record(lang)
    elif cmd == "split":
        split(lang)
    elif cmd == "timing":
        timing(lang)
