"""Gentle, measured colour grade with a before and after check. Never an 'overdone look'."""
import math, sys, tempfile, shutil
from pathlib import Path
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import run
from PIL import Image, ImageStat

LIMITS = {"gamma": (0.88, 1.22), "contrast": (0.96, 1.10), "sat": (0.92, 1.12)}
LOOKS = {"natural": (0, 0, 0), "punchy": (0.04, 0.06, 0), "soft": (-0.03, -0.05, 0), "warm": (0, 0.02, 0.3)}
FACE_LUMA_OK = (0.40, 0.56)  # inside this band the exposure is left alone


def clamp(v, key):
    lo, hi = LIMITS[key]
    return max(lo, min(hi, v))


def sample(video, times, pre, out_dir, grade_chain=None, width=360):
    paths = []
    for i, t in enumerate(times):
        p = Path(out_dir) / (f"g{i}.png" if grade_chain else f"o{i}.png")
        vf = ",".join(x for x in (pre, f"scale={width}:-2", grade_chain) if x)
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", "-vf", vf, p])
        paths.append(p)
    return paths


def measure(paths):
    mean_c, p1, p99, sat, clip, crush = [], [], [], [], [], []
    for p in paths:
        im = Image.open(p).convert("RGB")
        w, h = im.size
        luma = im.convert("L")
        centre = luma.crop((int(w * .25), int(h * .2), int(w * .75), int(h * .7)))
        mean_c.append(ImageStat.Stat(centre).mean[0] / 255)
        hist = luma.histogram(); tot = sum(hist)
        def pct(q):
            c = 0
            for i, v in enumerate(hist):
                c += v
                if c >= q * tot: return i / 255
        p1.append(pct(.01)); p99.append(pct(.99))
        clip.append(sum(hist[250:]) / tot); crush.append(sum(hist[:6]) / tot)
        hsv = im.convert("HSV"); hs = hsv.split()
        sats = [s for s, v in zip(hs[1].getdata(), hs[2].getdata()) if 38 < v < 220]
        sat.append(sum(sats) / len(sats) / 255 if sats else 0.3)
    av = lambda x: sum(x) / len(x)
    return {"face_luma": av(mean_c), "spread": av(p99) - av(p1), "sat": av(sat), "clip": av(clip), "crush": av(crush)}


def recommend(m, cfg):
    g = cfg["grade"]
    look = LOOKS.get(g.get("look", "natural"), LOOKS["natural"])
    fl = max(m["face_luma"], 0.05)
    gamma = math.log(fl) / math.log(max(FACE_LUMA_OK[0], min(FACE_LUMA_OK[1], fl)))
    contrast = 1 + (min(0.10, (0.80 - m["spread"]) * 0.4) if m["spread"] < 0.80 else 0)
    sat = 1.10 if m["sat"] < 0.28 else (0.95 if m["sat"] > 0.50 else 1.03)
    s = g["strength"] / 0.7
    gamma = clamp(1 + (gamma - 1) * s, "gamma")
    contrast = clamp(1 + (contrast - 1) * s + look[0], "contrast")
    sat = clamp(1 + (sat - 1) * s + look[1], "sat")
    warmth = max(-1, min(1, g.get("warmth", 0) + look[2]))
    return {"gamma": round(gamma, 3), "contrast": round(contrast, 3), "sat": round(sat, 3), "warmth": round(warmth, 2)}


def chain(r):
    f = f"eq=gamma={r['gamma']}:contrast={r['contrast']}:saturation={r['sat']}"
    if abs(r["warmth"]) > 0.01:
        f += f",colorbalance=rm={0.06 * r['warmth']:.3f}:bm={-0.06 * r['warmth']:.3f}"
    return f


def make(video, times, pre, cfg, check_dir):
    """Returns (filter chain or None, report dict). Writes before/after sheet into check_dir."""
    tmp = Path(tempfile.mkdtemp(prefix="reel-grade-"))
    before = sample(video, times, pre, tmp)
    mb = measure(before)
    rec = recommend(mb, cfg)
    for attempt in range(3):
        after = sample(video, times, pre, tmp, chain(rec))
        ma = measure(after)
        if ma["clip"] > max(0.03, mb["clip"] + 0.012) or ma["crush"] > max(0.08, mb["crush"] + 0.02):
            rec["gamma"] = round(1 + (rec["gamma"] - 1) / 2, 3)
            rec["contrast"] = round(1 + (rec["contrast"] - 1) / 2, 3)
            rec["backed_off"] = True
            continue
        break
    # side by side sheet: original left, graded right, for each sample
    tiles = [(Image.open(a), Image.open(b)) for a, b in zip(before, after)][:3]
    w, h = tiles[0][0].size
    sheet = Image.new("RGB", (w * 2 * len(tiles) + 12 * (len(tiles) - 1), h), (30, 30, 30))
    x = 0
    for a, b in tiles:
        sheet.paste(a, (x, 0)); sheet.paste(b, (x + w, 0)); x += 2 * w + 12
    check_dir = Path(check_dir); check_dir.mkdir(parents=True, exist_ok=True)
    sheet.save(check_dir / "colour-before-after.jpg", quality=88)
    shutil.rmtree(tmp, ignore_errors=True)
    rep = {"applied": rec, "before": {k: round(v, 3) for k, v in mb.items()}, "after": {k: round(v, 3) for k, v in ma.items()}}
    return chain(rec), rep
