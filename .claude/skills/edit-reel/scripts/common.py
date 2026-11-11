"""Shared helpers for the reel editor: paths, settings, running tools."""
import json, os, shutil, subprocess, sys, array, math
from pathlib import Path

HOME_DIR = Path(os.environ.get("REEL_EDITOR_HOME", Path.home() / ".reel-editor"))
REPO = Path(__file__).resolve().parents[4]
SCRIPTS = Path(__file__).resolve().parent
for p in ("/opt/homebrew/bin", "/usr/local/bin"):
    if p not in os.environ["PATH"].split(":"):
        os.environ["PATH"] += ":" + p

MODEL = HOME_DIR / "models" / "ggml-small.en.bin"
DEEP_FILTER = HOME_DIR / "bin" / "deep-filter"


def deep_merge(base, over):
    out = dict(base)
    for k, v in over.items():
        out[k] = deep_merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def load_config():
    cfg = json.loads((REPO / "config.default.json").read_text())
    user = REPO / "config.json"
    if user.exists():
        cfg = deep_merge(cfg, json.loads(user.read_text()))
    return cfg


def folder(cfg, key):
    p = Path(cfg["folders"][key]).expanduser()
    return p if p.is_absolute() else REPO / p


def need(tool):
    path = shutil.which(tool)
    if not path:
        sys.exit(f"'{tool}' is not installed. Run scripts/setup.sh first.")
    return path


def run(cmd, check=True, quiet=True):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if check and r.returncode != 0:
        tail = (r.stderr or "")[-1500:]
        sys.exit(f"Command failed: {' '.join(str(c) for c in cmd[:3])} ...\n{tail}")
    return r


def probe(path):
    """Display size (after phone rotation), duration, fps, HDR flag, has audio."""
    r = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path])
    d = json.loads(r.stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list", []):
        if "rotation" in sd:
            rot = int(sd["rotation"])
    if abs(rot) in (90, 270):
        w, h = h, w
    num, den = (v.get("r_frame_rate", "30/1").split("/") + ["1"])[:2]
    fps = float(num) / float(den or 1)
    trc = v.get("color_transfer", "")
    return {
        "w": w, "h": h, "duration": float(d["format"]["duration"]), "fps": fps,
        "hdr": trc in ("arib-std-b67", "smpte2084"), "trc": trc,
        "has_audio": any(s["codec_type"] == "audio" for s in d["streams"]),
    }


def pcm16k(path, start=None, end=None):
    """Mono 16 kHz samples of an audio or video file as an array of int16."""
    cmd = ["ffmpeg", "-v", "error"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}"]
    if end is not None:
        cmd += ["-to", f"{end:.3f}"]
    cmd += ["-i", str(path), "-map", "0:a:0", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        sys.exit("Could not read the audio: " + r.stderr.decode()[-500:])
    a = array.array("h")
    a.frombytes(r.stdout[: len(r.stdout) // 2 * 2])
    return a


def envelope_db(pcm, step=160):
    """Loudness every 10 ms in dBFS."""
    out = []
    for i in range(0, len(pcm) - step + 1, step):
        seg = pcm[i:i + step]
        rms = math.sqrt(sum(x * x for x in seg) / step)
        out.append(20 * math.log10(rms / 32768 + 1e-9))
    return out


def speech_threshold(env):
    s = sorted(env)
    floor = s[int(len(s) * 0.10)]
    top = s[int(len(s) * 0.90)]
    return floor + min(20, max(8, 0.35 * (top - floor))), floor, top


def transcribe(audio, vocabulary=()):
    """Word by word transcript with times, using whisper.cpp. Returns [{t0,t1,text}]."""
    import tempfile
    need("whisper-cli")
    if not MODEL.exists():
        sys.exit("Speech model missing. Run scripts/setup.sh first.")
    tmp = Path(tempfile.mkdtemp(prefix="reel-tr-"))
    wav = tmp / "in.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", audio, "-map", "0:a:0", "-ac", "1", "-ar", "16000", wav])
    cmd = ["whisper-cli", "-m", MODEL, "-f", wav, "-oj", "-of", tmp / "out", "-ml", "1", "-sow", "-np", "-nt"]
    if vocabulary:
        cmd += ["--prompt", "Words that may come up: " + ", ".join(vocabulary) + "."]
    run(cmd)
    data = json.loads((tmp / "out.json").read_text())
    words = []
    for seg in data["transcription"]:
        t = seg["text"].strip()
        if not t or (t.startswith("[") and t.endswith("]")) or (t.startswith("(") and t.endswith(")")):
            continue
        words.append({"t0": seg["offsets"]["from"] / 1000, "t1": seg["offsets"]["to"] / 1000, "text": t})
    shutil.rmtree(tmp, ignore_errors=True)
    return words


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
