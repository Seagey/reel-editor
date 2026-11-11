"""Studio sound: noise removal, voice EQ, de-esser, compressor, limiter, loudness to -14 LUFS.

This is the 'B' chain: the approved studio voice chain plus presence (3.3 kHz), a touch of air
(5.5 kHz shelf), a lighter de-esser pass and a limiter. Tuned by measurement, so your ears decide:
if it sounds harsh or thin, say so and the strength gets turned down.
"""
import json, sys, tempfile, shutil
from pathlib import Path
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import run, need, DEEP_FILTER


def chain(m):
    """m scales every EQ boost: 1.0 standard, 0.5 light."""
    g = lambda x: round(x * m, 2)
    return (
        "highpass=f=85,"
        f"equalizer=f=130:t=q:w=1:g={g(2)},equalizer=f=300:t=q:w=1.2:g={-g(3.5)},"
        f"equalizer=f=3500:t=q:w=1:g={g(3)},equalizer=f=9000:t=h:w=2000:g={g(1.5)},"
        "deesser=i=0.4,"
        "acompressor=threshold=-22dB:ratio=3:attack=6:release=90:makeup=4,"
        "agate=threshold=0.008:ratio=2:attack=5:release=150,"
        f"equalizer=f=3300:t=q:w=1:g={g(1.8)},highshelf=f=5500:g={g(1.2)},"
        "deesser=i=0.25,alimiter=limit=0.9"
    )


def process(in_wav, out_wav, strength="standard", target=-14.0):
    """in_wav: 48 kHz wav. Returns loudness measurements."""
    need("ffmpeg")
    tmp = Path(tempfile.mkdtemp(prefix="reel-audio-"))
    src = Path(in_wav)
    if strength in ("standard", "light"):
        if not DEEP_FILTER.exists():
            sys.exit("Voice clean up tool missing. Run scripts/setup.sh first.")
        cmd = [DEEP_FILTER, "-D", "-o", tmp]
        if strength == "light":
            cmd += ["-a", "14"]
        run(cmd + [src])
        src = tmp / src.name
    m = {"standard": 1.0, "light": 0.5, "off": 0.0}[strength]
    ch = chain(m) if strength != "off" else "highpass=f=70"
    ln = f"loudnorm=I={target}:TP=-1.5:LRA=7"
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-af", f"{ch},{ln}:print_format=json", "-f", "null", "-"])
    txt = r.stderr
    meas = json.loads(txt[txt.rindex("{"):txt.rindex("}") + 1])
    lin = (f"measured_I={meas['input_i']}:measured_TP={meas['input_tp']}:measured_LRA={meas['input_lra']}:"
           f"measured_thresh={meas['input_thresh']}:offset={meas['target_offset']}:linear=true")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", f"{ch},{ln}:{lin},aresample=48000", "-c:a", "pcm_s16le", out_wav])
    shutil.rmtree(tmp, ignore_errors=True)
    return meas
