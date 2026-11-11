"""Is the picture mirrored (front camera)? Proved with text OCR, never by eye.

  python3 mirror_check.py <video> [--times 3,8,15]

Reads on-screen text (signs, TV screens, shirts, posters) in a few frames, normal and flipped,
and says which way round real words appear. Prints JSON {decision: flip|keep|unknown, ...}.
"""
import json, sys, subprocess, tempfile, shutil, re
from pathlib import Path
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import probe, run
from PIL import Image, ImageOps


def score(img_path):
    r = subprocess.run(["tesseract", str(img_path), "stdout", "--psm", "11", "tsv"], capture_output=True, text=True)
    words = []
    for line in r.stdout.splitlines()[1:]:
        p = line.split("\t")
        if len(p) >= 12 and re.fullmatch(r"[A-Za-z]{3,}", p[11].strip()) and float(p[10]) >= 70:
            words.append(p[11].strip())
    return len(words), words


def check(video, times=None):
    if not shutil.which("tesseract"):
        return {"decision": "unknown", "why": "tesseract is not installed"}
    d = probe(video)["duration"]
    times = times or [d * f for f in (0.1, 0.3, 0.5, 0.7, 0.9)]
    tmp = Path(tempfile.mkdtemp(prefix="reel-mirror-"))
    n_norm = n_flip = 0
    ex_norm, ex_flip = [], []
    for i, t in enumerate(times):
        f = tmp / f"f{i}.png"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", "-vf", "scale=1080:-2", f])
        a, wa = score(f)
        g = tmp / f"g{i}.png"
        ImageOps.mirror(Image.open(f)).save(g)
        b, wb = score(g)
        n_norm += a; n_flip += b; ex_norm += wa[:4]; ex_flip += wb[:4]
    shutil.rmtree(tmp, ignore_errors=True)
    if max(n_norm, n_flip) < 2:
        decision, why = "unknown", "no readable text in frame, so nothing to prove it either way (look at a frame yourself)"
    elif n_flip >= 2 and n_flip > 1.5 * n_norm:
        decision, why = "flip", "real words read correctly only when flipped"
    else:
        decision, why = "keep", "real words read correctly as filmed"
    return {"decision": decision, "why": why, "words_as_filmed": n_norm, "words_flipped": n_flip,
            "examples_as_filmed": ex_norm[:6], "examples_flipped": ex_flip[:6]}


if __name__ == "__main__":
    times = None
    if "--times" in sys.argv:
        times = [float(x) for x in sys.argv[sys.argv.index("--times") + 1].split(",")]
    print(json.dumps(check(sys.argv[1], times), indent=1))
