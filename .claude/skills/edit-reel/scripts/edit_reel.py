"""Edits one phone video into a finished 1080x1920 reel.

  python3 edit_reel.py <video> [--tightness gentle|normal|tight] [--drop 12-15.5,40-41] [--keep-work]
  python3 edit_reel.py --latest N        (the newest N videos in the Inbox folder, one reel each)

All choices (captions, colour, sound, cuts) come from config.json. Writes the reel to the Edited
folder, plus a checks folder with a contact sheet, a before/after colour sheet and a report.
"""
import argparse, json, shutil, sys, time
from pathlib import Path
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import *
import plan_cuts, mirror_check, grade, audio, captions
from PIL import Image

VIDEO_EXT = (".mov", ".mp4", ".m4v")


def latest_videos(inbox, n):
    vids = [p for p in inbox.iterdir() if p.suffix.lower() in VIDEO_EXT and not p.name.startswith(".")]
    return sorted(vids, key=lambda p: p.stat().st_mtime, reverse=True)[:n]


def hdr_chain(info):
    # iPhone HDR (HLG) clips look flat on normal screens. This maps the colours to standard video.
    return "colorspace=all=bt709:iall=bt2020:fast=1,format=yuv420p" if info["hdr"] else ""


def edit_one(src, cfg, tightness=None, drops=(), keep_work=False):
    t_start = time.time()
    src = Path(src).expanduser().resolve()
    name = src.stem
    edited = folder(cfg, "edited"); edited.mkdir(parents=True, exist_ok=True)
    checks = edited / "checks" / name
    work = edited / ".work" / name
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    report = {"source": src.name}
    log = lambda m: print(f"[{name}] {m}", flush=True)

    info = probe(src)
    if not info["has_audio"]:
        sys.exit(f"{src.name} has no sound, so there is nothing to caption.")
    report["source_info"] = {k: info[k] for k in ("w", "h", "duration", "fps", "hdr")}

    # 1. cuts, planned by sound
    log("finding the dead air and long pauses (by sound)")
    plan = plan_cuts.plan(src, tightness or cfg["cuts"]["tightness"], drops, vocabulary=cfg["vocabulary"])
    if "error" in plan:
        sys.exit(f"{src.name}: {plan['error']}")
    keep = plan["keep"]
    report["cuts"] = plan["cuts"]
    report["seconds"] = {"before": plan["source_seconds"], "after": plan["kept_seconds"]}

    # 2. mirrored front camera?
    fr = cfg["framing"]
    flip = False
    if fr["mirror_fix"] == "always":
        flip = True; report["mirror"] = {"decision": "flip", "why": "set to always"}
    elif fr["mirror_fix"] == "auto":
        log("checking whether the picture is mirrored (reading text in frame)")
        m = mirror_check.check(src)
        flip = m["decision"] == "flip"; report["mirror"] = m
    else:
        report["mirror"] = {"decision": "keep", "why": "turned off"}

    # 3. colour grade chosen from measured frames
    pre = hdr_chain(info)
    mid = [(keep[0][0] + keep[-1][1]) * f for f in (0.15, 0.45, 0.8)]
    grade_chain = ""
    if cfg["grade"]["enabled"]:
        log("measuring the colour and choosing a gentle grade")
        grade_chain, g = grade.make(src, mid, pre, cfg, checks)
        report["grade"] = g

    # 4. cut + crop + grade in one pass
    W_, H_ = info["w"], info["h"]
    zoom = max(1.0, float(fr["zoom"]))
    cw = min(W_, H_ * 9 / 16) / zoom
    ch = cw * 16 / 9
    if ch > H_:
        ch = H_ / zoom; cw = ch * 9 / 16
    cx = int((W_ - cw) * fr["centre_x"]) // 2 * 2
    cy = int((H_ - ch) * 0.35) // 2 * 2
    segs_v, segs_a = [], []
    for i, (s, e) in enumerate(keep):
        d = e - s
        segs_v.append(f"[0:v]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS[v{i}]")
        segs_a.append(f"[0:a:0]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,"
                      f"afade=t=in:d=0.015,afade=t=out:st={max(d - 0.015, 0):.3f}:d=0.015[a{i}]")
    n = len(keep)
    concat_in = "".join(f"[v{i}][a{i}]" for i in range(n))
    vf = [x for x in (pre, "hflip" if flip else "", f"crop={int(cw) // 2 * 2}:{int(ch) // 2 * 2}:{cx}:{cy}",
                      "scale=1080:1920:flags=lanczos", grade_chain, "fps=30", "format=yuv420p") if x]
    fc = ";".join(segs_v + segs_a + [f"{concat_in}concat=n={n}:v=1:a=1[cv][ca]", f"[cv]{','.join(vf)}[vout]"])
    cut_mp4, cut_wav = work / "cut.mp4", work / "cut.wav"
    log("cutting, cropping to 9:16 and grading")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc,
         "-map", "[vout]", "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p", cut_mp4,
         "-map", "[ca]", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", cut_wav])
    dur = probe(cut_mp4)["duration"]

    # 5. studio sound
    log(f"studio sound ({cfg['audio']['strength']})")
    studio = work / "studio.wav"
    meas = audio.process(cut_wav, studio, cfg["audio"]["strength"], cfg["audio"]["target_lufs"])
    report["audio_in"] = {"loudness_lufs": meas["input_i"], "peak_db": meas["input_tp"]}

    # 6. captions from the cleaned sound (more accurate than the raw)
    final_in = cut_mp4
    cap_list, y, cap_rep = None, 0, None
    onset = None
    if cfg["captions"]["enabled"]:
        log("transcribing for captions")
        pcm = pcm16k(studio)
        env = envelope_db(pcm); thr, _, _ = speech_threshold(env)
        onset = next((i * 0.01 for i, v in enumerate(env) if v >= thr), 0.0)
        words = captions.clean_words(transcribe(studio, cfg["vocabulary"]), cfg, onset, dur)
        (checks).mkdir(parents=True, exist_ok=True)
        (checks / "captions-words.txt").write_text(" ".join(w["text"] for w in words) + "\n")
        cap_list, y, cap_rep = captions.build(words, cfg, work / "cap", dur)
        report["captions"] = cap_rep

    # 7. final encode: captions + logo on top, studio audio underneath
    out = edited / f"{name}-edited.mp4"
    inputs = ["-i", cut_mp4, "-i", studio]
    fg, last, idx = [], "[0:v]", 2
    if cap_list:
        inputs += ["-f", "concat", "-safe", "0", "-i", cap_list]
        fg.append(f"[{idx}:v]fps=30,format=rgba[cap]"); fg.append(f"{last}[cap]overlay=0:{y}:eof_action=pass[ov{idx}]")
        last = f"[ov{idx}]"; idx += 1
    logo = cfg["logo"]
    if logo["enabled"] and logo["path"] and Path(logo["path"]).expanduser().exists():
        s = int(logo["size"]); right = "right" in logo["corner"]; top = "top" in logo["corner"]
        x = f"W-w-100" if right else "90"; yy = "270" if top else "H-h-420"
        inputs += ["-i", Path(logo["path"]).expanduser()]
        fg.append(f"[{idx}:v]scale={s}:-1,format=rgba[logo]"); fg.append(f"{last}[logo]overlay={x}:{yy}[ov{idx}]")
        last = f"[ov{idx}]"; idx += 1
    maps = ["-filter_complex", ";".join(fg), "-map", last.strip() if fg else "0:v", "-map", "1:a"] if fg else ["-map", "0:v", "-map", "1:a"]
    log("final encode")
    run(["ffmpeg", "-v", "error", "-y", *inputs, *maps, "-t", f"{dur:.3f}", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
         "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", out])
    # 8. checks (on the reel itself, before any end card is added)
    log("checking the result")
    report["checks"] = verify(out, cfg, checks, cap_list is not None)
    if cfg["end_card"]["enabled"]:
        out = add_end_card(out, cfg, work)
    report["output"] = str(out)
    report["took_seconds"] = round(time.time() - t_start)
    (checks / "report.json").write_text(json.dumps(report, indent=1, default=str))
    if not keep_work:
        shutil.rmtree(work, ignore_errors=True)
        shutil.rmtree(edited / ".work", ignore_errors=True) if not any((edited / ".work").iterdir()) else None
    return report


def add_end_card(out, cfg, work):
    from PIL import ImageDraw
    ec = cfg["end_card"]
    img = Image.new("RGB", (1080, 1920), hex_rgb(ec["background"]))
    d = ImageDraw.Draw(img)
    y = 760
    lg = cfg["logo"]
    if ec["use_logo"] and lg["path"] and Path(lg["path"]).expanduser().exists():
        l = Image.open(Path(lg["path"]).expanduser()).convert("RGBA")
        l.thumbnail((420, 420)); img.paste(l, ((1080 - l.width) // 2, y - l.height - 40), l)
    font = captions.find_font(cfg["captions"]["font"], 72)
    lines = ec["text"].split("\n")
    for i, t in enumerate(lines):
        d.text((540, y + i * 90), t, font=font, fill=hex_rgb(ec["color"]), anchor="mm")
    png = work / "end.png"; img.save(png)
    card = work / "end.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-t", str(ec["seconds"]), "-i", png,
         "-f", "lavfi", "-t", str(ec["seconds"]), "-i", "anullsrc=r=48000:cl=stereo", "-c:v", "libx264", "-crf", "18",
         "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
         "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", card])
    lst = work / "join.txt"
    lst.write_text(f"file '{out}'\nfile '{card}'\n")
    joined = out.with_name(out.stem + "-tmp.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", joined])
    joined.replace(out)
    return out


def verify(out, cfg, checks, had_captions):
    """Loudness, dead air at start and end (by sound), a contact sheet, and a re-transcription."""
    checks.mkdir(parents=True, exist_ok=True)
    res = {}
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"])
    tail = r.stderr[r.stderr.rindex("Summary:"):]
    import re
    res["loudness_lufs"] = float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail).group(1))
    res["true_peak_db"] = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail).group(1))
    d = probe(out)["duration"]
    sd = run(["ffmpeg", "-hide_banner", "-nostats", "-i", out, "-af", "silencedetect=noise=-35dB:d=0.3", "-f", "null", "-"]).stderr
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", sd)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", sd)]
    first_voice = ends[0] if starts and starts[0] <= 0.05 and ends else 0.0
    last_voice = starts[-1] if starts and len(starts) > len(ends) else d
    res["seconds_of_quiet_at_start"] = round(first_voice, 2)
    res["seconds_of_quiet_at_end"] = round(d - last_voice, 2)
    res["long_pauses_left"] = len([1 for s, e in zip(starts, ends) if e - s > 1.2 and s > 0.05])
    res["duration"] = round(d, 2)
    # contact sheet: 8 frames
    cols = 8; tw, th = 216, 384
    sheet = Image.new("RGB", (tw * cols, th), (20, 20, 20))
    for i in range(cols):
        t = d * (i + 0.5) / cols
        f = checks / f"_f{i}.png"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", out, "-frames:v", "1", "-vf", f"scale={tw}:{th}", f])
        sheet.paste(Image.open(f), (i * tw, 0)); f.unlink()
    sheet.save(checks / "contact-sheet.jpg", quality=85)
    # a full size frame through the caption area, for reading the caption words at 100%
    if had_captions:
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{d * 0.4:.2f}", "-i", out, "-frames:v", "1", checks / "caption-frame.png"])
        words = transcribe(out, cfg["vocabulary"])
        res["heard_in_final"] = " ".join(w["text"] for w in words)
        cw = (checks / "captions-words.txt").read_text().strip().lower()
        norm = lambda s: re.sub(r"[^a-z0-9' ]", "", s.lower()).split()
        a, b = norm(cw), norm(res["heard_in_final"])
        import difflib
        res["caption_vs_sound_match"] = round(difflib.SequenceMatcher(None, a, b).ratio(), 2)
    res["start_ok"] = res["seconds_of_quiet_at_start"] <= 0.45
    res["end_ok"] = res["seconds_of_quiet_at_end"] <= 0.75
    res["loudness_ok"] = abs(res["loudness_lufs"] - cfg["audio"]["target_lufs"]) <= 1.0 and res["true_peak_db"] <= -1.0
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", nargs="*")
    ap.add_argument("--latest", type=int)
    ap.add_argument("--tightness"); ap.add_argument("--drop", default="")
    ap.add_argument("--keep-work", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    for t in ("ffmpeg", "ffprobe", "whisper-cli"):
        need(t)
    vids = [Path(v) for v in a.video]
    if a.latest:
        inbox = folder(cfg, "inbox")
        vids += latest_videos(inbox, a.latest) if inbox.exists() else []
    if not vids:
        sys.exit("No video given and none found in the Inbox folder.")
    drops = [tuple(map(float, x.split("-"))) for x in a.drop.split(",") if x]
    for v in vids:
        rep = edit_one(v, cfg, a.tightness, drops, a.keep_work)
        c = rep["checks"]
        print(f"\nDONE: {rep['output']}")
        print(json.dumps({k: c[k] for k in ("loudness_lufs", "true_peak_db", "seconds_of_quiet_at_start",
                                            "seconds_of_quiet_at_end", "start_ok", "end_ok", "loudness_ok")}))


if __name__ == "__main__":
    main()
