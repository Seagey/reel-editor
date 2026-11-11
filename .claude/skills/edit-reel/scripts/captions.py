"""Burned in captions drawn with Pillow (no special ffmpeg build needed).

Phone safe zones for a 1080x1920 reel: Instagram, Facebook and TikTok put buttons and the caption
text over the top ~250 px, the bottom ~400 px and the right ~120 px. Captions stay inside:
  x from 90 to 960, y from 250 to 1520.
Highlighted word: the fill colour changes and the dark outline stays. No coloured boxes behind
words, because a box behind outlined text goes soft and blurry on a face.
"""
import sys, re, os, json
from pathlib import Path
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import hex_rgb, HOME_DIR
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
SAFE = {"left": 90, "right": 960, "top": 250, "bottom": 1520}
POS = {"upper": 0.30, "middle": 0.50, "lower": 0.66}
FONT_DIRS = [str(HOME_DIR / "fonts"), "/System/Library/Fonts", "/System/Library/Fonts/Supplemental", "/Library/Fonts",
             str(Path.home() / "Library/Fonts")]


def find_font(name, size):
    """name can be a font family ('Arial Black', 'Impact') or a path to a .ttf/.otf/.ttc file."""
    if os.path.isfile(os.path.expanduser(name)):
        return ImageFont.truetype(os.path.expanduser(name), size)
    want = name.lower().replace(" ", "")
    best = None
    for d in FONT_DIRS:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith((".ttf", ".otf", ".ttc")):
                continue
            stem = f.rsplit(".", 1)[0].lower().replace(" ", "").replace("-", "")
            if stem == want or stem == want + "bold" or stem == want + "regular":
                best = best or os.path.join(d, f)
                if stem == want:
                    return ImageFont.truetype(os.path.join(d, f), size)
    if best:
        return ImageFont.truetype(best, size)
    for d in FONT_DIRS:  # looser: family name appears in the file name
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if want in f.lower().replace(" ", "").replace("-", "") and f.lower().endswith((".ttf", ".otf")):
                    return ImageFont.truetype(os.path.join(d, f), size)
    print(f"   (font '{name}' not found, using Arial Black)", file=sys.stderr)
    return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Black.ttf", size)


def clean_words(words, cfg, onset=None, duration=None):
    reps = {k.lower(): v for k, v in cfg.get("replacements", {}).items()}
    out = []
    for w in words:
        if duration and w["t0"] >= duration - 0.05:
            continue  # speech to text sometimes invents words past the end
        if onset is not None and w["t1"] <= onset:
            continue
        t = w["text"]
        base = re.sub(r"[^\w']", "", t).lower()
        if base in reps:
            t = t.replace(re.sub(r"[^\w']", "", t), reps[base]) if re.sub(r"[^\w']", "", t) else reps[base]
        out.append({"t0": w["t0"], "t1": w["t1"], "text": t})
    if onset is not None and out:
        out[0]["t0"] = max(out[0]["t0"], onset - 0.05)
    cc = cfg["captions"]
    for w in out:
        w["raw"] = w["text"]
        t = w["text"] if cc["show_punctuation"] else re.sub(r"[.,;:!?\"“”]+", "", w["text"])
        w["text"] = t.upper() if cc["uppercase"] else t
    return [w for w in out if w["text"]]


def group_cards(words, font, max_width, max_lines=2, max_words=6):
    cards, cur = [], []
    def fits(ws):
        lines, line = 1, ""
        for w in ws:
            trial = (line + " " + w["text"]).strip()
            if font.getlength(trial) <= max_width:
                line = trial
            else:
                lines += 1; line = w["text"]
        return lines <= max_lines
    for i, w in enumerate(words):
        if cur and (not fits(cur + [w]) or len(cur) >= max_words or re.search(r"[.?!]$", cur[-1]["raw"])
                    or w["t0"] - cur[-1]["t1"] > 0.6):
            cards.append(cur); cur = []
        cur.append(w)
    if cur:
        cards.append(cur)
    return cards


def layout(card, font, max_width):
    lines, line = [], []
    for w in card:
        trial = " ".join(x["text"] for x in line + [w])
        if line and font.getlength(trial) > max_width:
            lines.append(line); line = [w]
        else:
            line.append(w)
    lines.append(line)
    return lines


def render_state(card, active, font, cc, y_top_pad, size, mode):
    """Transparent image for one card with word index `active` highlighted."""
    ow = cc["outline_width"]
    max_w = SAFE["right"] - SAFE["left"]
    lines = layout(card, font, max_w)
    lh = int(size * 1.18)
    img = Image.new("RGBA", (W, lh * len(lines) + ow * 2 + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    base, hi, out = hex_rgb(cc["color"]), hex_rgb(cc["highlight_color"]), hex_rgb(cc["outline_color"])
    idx = 0
    for li, line in enumerate(lines):
        text = " ".join(x["text"] for x in line)
        x = (SAFE["left"] + SAFE["right"]) / 2 - font.getlength(text) / 2
        y = ow + 4 + li * lh
        space = font.getlength(" ")
        for w in line:
            col = hi if idx == active else base
            if mode == "word":
                col = hi if cc.get("word_pop_highlight", False) else base
            d.text((x, y), w["text"], font=font, fill=col + (255,), stroke_width=ow, stroke_fill=out + (255,))
            x += font.getlength(w["text"]) + space
            idx += 1
    return img


def build(words, cfg, out_dir, total_dur, fps=30):
    """Writes PNG states plus a concat list. Returns (list_path, y_position, report)."""
    cc = cfg["captions"]
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    size = int(cc["size"] * (1.25 if cc["style"] == "word" else 1.0))
    font = find_font(cc["font"], size)
    max_w = SAFE["right"] - SAFE["left"]
    if cc["style"] == "word":
        cards = [[w] for w in words]
    else:
        cards = group_cards(words, font, max_w)
    lh = int(size * 1.18)
    max_lines = max(len(layout(c, font, max_w)) for c in cards) if cards else 1
    band_h = lh * max_lines + cc["outline_width"] * 2 + 8
    cy = int(H * POS.get(cc["position"], 0.66))
    y = max(SAFE["top"], min(SAFE["bottom"] - band_h, cy - band_h // 2))
    blank = Image.new("RGBA", (W, band_h), (0, 0, 0, 0)); blank.save(out_dir / "blank.png")
    entries, t = [], 0.0
    n = 0
    def add(path, dur):
        if dur > 0.001:
            entries.append((str(path), dur))
    for ci, card in enumerate(cards):
        start = card[0]["t0"]
        nxt = cards[ci + 1][0]["t0"] if ci + 1 < len(cards) else total_dur
        add(out_dir / "blank.png", start - t); t = max(t, start)
        for wi, w in enumerate(card):
            w_start = max(t, w["t0"])
            w_end = card[wi + 1]["t0"] if wi + 1 < len(card) else min(max(w["t1"] + 0.25, w_start + 0.3), nxt)
            if w_end <= w_start:
                w_end = w_start + 0.05
            im = render_state(card, wi, font, cc, 0, size, cc["style"])
            canvas = Image.new("RGBA", (W, band_h), (0, 0, 0, 0)); canvas.alpha_composite(im, (0, 0))
            p = out_dir / f"c{n:04d}.png"; canvas.save(p); n += 1
            add(p, w_end - w_start); t = w_end
    add(out_dir / "blank.png", total_dur - t)
    lst = out_dir / "captions.txt"
    with open(lst, "w") as f:
        for p, dur in entries:
            f.write(f"file '{p}'\nduration {dur:.4f}\n")
        f.write(f"file '{entries[-1][0]}'\n")
    rep = {"cards": len(cards), "words": len(words), "y": y, "band_height": band_h,
           "bottom_edge": y + band_h, "inside_safe_zone": SAFE["top"] <= y and y + band_h <= SAFE["bottom"]}
    return lst, y, rep
