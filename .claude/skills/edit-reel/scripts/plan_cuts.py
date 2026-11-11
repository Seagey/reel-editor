"""Plans where to cut, by SOUND. Never by caption times.

Whisper word times at the very start of a clip can sit inside silence, so they are only used to
tell real speech from noise. The cut points come from the loudness of the audio itself.

  python3 plan_cuts.py <video> [--tightness gentle|normal|tight] [--drop 12.0-15.5,40-41]

Prints JSON: keep segments (source seconds) and a plain list of what was cut and why.
"""
import json, sys, argparse
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import pcm16k, envelope_db, speech_threshold, transcribe, load_config

# lead pad, tail pad, longest pause kept as is, length a long pause is shortened to
TIGHT = {"gentle": (0.30, 0.45, 1.10, 0.50), "normal": (0.15, 0.30, 0.70, 0.30), "tight": (0.10, 0.20, 0.45, 0.18)}
FR = 0.01  # seconds per envelope frame
SEAM_QUIET_SEARCH = 0.05


def speech_runs(env, thr):
    """Runs of voiced frames, with tiny gaps (under 120 ms, normal between syllables) bridged."""
    runs, cur = [], None
    for i, v in enumerate(env):
        if v >= thr:
            if cur and i - cur[1] <= 12:
                cur[1] = i
            elif cur:
                runs.append(cur); cur = [i, i]
            else:
                cur = [i, i]
    if cur:
        runs.append(cur)
    return [(a * FR, (b + 1) * FR) for a, b in runs]


def quietest(env, t, lo, hi):
    """Quietest 10 ms moment near t, kept inside [lo, hi]."""
    a, b = int(max(lo, t - SEAM_QUIET_SEARCH) / FR), int(min(hi, t + SEAM_QUIET_SEARCH) / FR)
    if b <= a:
        return max(lo, min(hi, t))
    best = min(range(a, b + 1), key=lambda i: env[min(i, len(env) - 1)])
    return best * FR


def subtract(segs, drops):
    out = []
    for s, e in segs:
        pieces = [(s, e)]
        for ds, de in drops:
            nxt = []
            for ps, pe in pieces:
                if de <= ps or ds >= pe:
                    nxt.append((ps, pe))
                else:
                    if ds > ps: nxt.append((ps, ds))
                    if de < pe: nxt.append((de, pe))
            pieces = nxt
        out += pieces
    return [(s, e) for s, e in out if e - s > 0.15]


def plan(video, tightness="normal", drops=(), words=None, vocabulary=()):
    pcm = pcm16k(video)
    env = envelope_db(pcm)
    dur = len(env) * FR
    thr, floor, top = speech_threshold(env)
    if words is None:
        words = transcribe(video, vocabulary)
    runs = speech_runs(env, thr)
    # a run is speech if a transcribed word overlaps it, or it is long (laughing, a sound he made on purpose)
    def is_speech(r):
        return (r[1] - r[0]) > 0.5 or any(w["t1"] > r[0] - 0.25 and w["t0"] < r[1] + 0.25 for w in words)
    runs = [r for r in runs if is_speech(r)]
    if not runs:
        return {"error": "no speech found", "dur": dur}
    lead, tail, max_pause, keep_pause = TIGHT[tightness]
    cuts, keep = [], []
    start = quietest(env, runs[0][0] - lead, 0, runs[0][0] - 0.03)
    end = quietest(env, runs[-1][1] + tail, runs[-1][1] + 0.03, dur)
    if start > 0.05:
        cuts.append({"from": 0, "to": round(start, 2), "why": "dead air before you start talking"})
    if end < dur - 0.05:
        cuts.append({"from": round(end, 2), "to": round(dur, 2), "why": "dead air after you finish"})
    pos = start
    for (a0, a1), (b0, b1) in zip(runs, runs[1:]):
        gap = b0 - a1
        if gap > max_pause:
            c0 = quietest(env, a1 + keep_pause / 2, a1 + 0.02, b0 - 0.05)
            c1 = quietest(env, b0 - keep_pause / 2, c0 + 0.05, b0 - 0.02)
            if c1 - c0 > 0.12:
                keep.append((pos, c0)); pos = c1
                cuts.append({"from": round(c0, 2), "to": round(c1, 2), "why": f"long pause ({gap:.1f}s) shortened"})
    keep.append((pos, end))
    if drops:
        keep = subtract(keep, drops)
        for d in drops:
            cuts.append({"from": d[0], "to": d[1], "why": "removed on request"})
    return {"keep": [(round(s, 3), round(e, 3)) for s, e in keep], "cuts": sorted(cuts, key=lambda c: c["from"]),
            "source_seconds": round(dur, 2), "kept_seconds": round(sum(e - s for s, e in keep), 2),
            "threshold_db": round(thr, 1), "noise_floor_db": round(floor, 1), "words": words}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--tightness"); ap.add_argument("--drop", default="")
    a = ap.parse_args()
    cfg = load_config()
    drops = [tuple(map(float, x.split("-"))) for x in a.drop.split(",") if x]
    res = plan(a.video, a.tightness or cfg["cuts"]["tightness"], drops, vocabulary=cfg["vocabulary"])
    print(json.dumps(res, indent=1))
