#!/bin/bash
# Reel editor setup. Safe to run again: it only installs what is missing.
#   scripts/setup.sh          install anything missing
#   scripts/setup.sh --check  only report what is installed, change nothing
# Everything it downloads for itself goes into ~/.reel-editor (override with REEL_EDITOR_HOME).
set -u
HOME_DIR="${REEL_EDITOR_HOME:-$HOME/.reel-editor}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
CHECK=0; [ "${1:-}" = "--check" ] && CHECK=1
MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin"
MODEL_SHA="c6138d6d58ecc8322097e0f987c32f1be8bb0a18532a3f88f734d1bbf9c41e5d"
DF_VER="0.5.6"
DF_SHA_ARM="4601e7f4e4c03e59a4c5b5000216ef3add3e808799cfccd95e14e83ea4611081"
DF_SHA_X86="d3be84003acb7c23e738ad7f70a158ec779a8d233a82e7fa3e717d112eb5b50f"

say() { printf '\n== %s\n' "$*"; }
ok()  { printf '   OK   %s\n' "$*"; }
miss(){ printf '   MISSING  %s\n' "$*"; }

say "Step 1 of 7: checking this computer"
if [ "$(uname)" != "Darwin" ]; then
  echo "   This reel editor only works on a Mac for now."; exit 2
fi
ARCH="$(uname -m)"; ok "Mac ($ARCH), macOS $(sw_vers -productVersion)"
FREE_GB=$(df -g "$HOME" | awk 'NR==2{print $4}')
[ "${FREE_GB:-0}" -lt 3 ] && echo "   WARNING: only ${FREE_GB} GB free. The set up needs about 3 GB, and each reel needs a few hundred MB while it is being made."

say "Step 2 of 7: Homebrew (the Mac app installer everything else uses)"
for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do [ -x "$b" ] && eval "$($b shellenv)"; done
if command -v brew >/dev/null 2>&1; then ok "Homebrew $(brew --version | head -1)"; else
  miss "Homebrew"
  echo "   Homebrew has to be installed by you, in your own Terminal, because it asks for your Mac password."
  echo "   Never type that password into a chat. See README, section 'If Homebrew is missing'."
  exit 10
fi

say "Step 3 of 7: video, speech, text and iCloud tools from Homebrew"
need=()
for f in ffmpeg whisper-cpp tesseract icloudpd; do
  if brew list --formula "$f" >/dev/null 2>&1; then ok "$f"; else miss "$f"; need+=("$f"); fi
done
if python3 -c 'import sys;sys.exit(0 if sys.version_info>=(3,9) else 1)' 2>/dev/null; then ok "python3 $(python3 -V | cut -d' ' -f2)"; else miss "python3 (3.9 or newer)"; need+=(python); fi
if [ ${#need[@]} -gt 0 ] && [ $CHECK -eq 0 ]; then brew install "${need[@]}" || { echo "   brew install failed"; exit 3; }; fi
if ! ffmpeg -hide_banner -filters 2>/dev/null | grep -q " loudnorm "; then echo "   ffmpeg is missing audio filters we need"; fi

say "Step 4 of 7: Python helper in a private folder ($HOME_DIR/venv)"
if [ ! -x "$HOME_DIR/venv/bin/python" ]; then
  miss "private python environment"
  if [ $CHECK -eq 0 ]; then mkdir -p "$HOME_DIR"; python3 -m venv "$HOME_DIR/venv" || exit 4; fi
fi
if [ -x "$HOME_DIR/venv/bin/python" ]; then
  PIPS=""
  "$HOME_DIR/venv/bin/python" -c 'import PIL' 2>/dev/null || PIPS="$PIPS Pillow"
  if [ -n "$PIPS" ]; then
    miss "python packages:$PIPS"
    [ $CHECK -eq 0 ] && { "$HOME_DIR/venv/bin/pip" install --quiet --upgrade pip $PIPS || exit 4; }
  else ok "Pillow (draws the captions)"; fi
fi

say "Step 5 of 7: the speech to text model (about 470 MB, one time)"
MODEL="$HOME_DIR/models/ggml-small.en.bin"
if [ -f "$MODEL" ] && [ "$(shasum -a 256 "$MODEL" | cut -d' ' -f1)" = "$MODEL_SHA" ]; then ok "ggml-small.en.bin"; else
  miss "ggml-small.en.bin"
  if [ $CHECK -eq 0 ]; then
    mkdir -p "$HOME_DIR/models"
    curl -L --fail -C - -o "$MODEL.part" "$MODEL_URL" || { echo "   download failed, run this again"; exit 5; }
    [ "$(shasum -a 256 "$MODEL.part" | cut -d' ' -f1)" = "$MODEL_SHA" ] || { echo "   the model file did not verify, deleting it"; rm -f "$MODEL.part"; exit 5; }
    mv "$MODEL.part" "$MODEL"; ok "ggml-small.en.bin downloaded and verified"
  fi
fi

say "Step 6 of 7: the voice clean up tool (DeepFilterNet, about 30 MB, one time)"
DF="$HOME_DIR/bin/deep-filter"
if [ "$ARCH" = "arm64" ]; then DFA=aarch64; DFS=$DF_SHA_ARM; else DFA=x86_64; DFS=$DF_SHA_X86; fi
if [ -x "$DF" ] && [ "$(shasum -a 256 "$DF" | cut -d' ' -f1)" = "$DFS" ]; then ok "deep-filter $DF_VER"; else
  miss "deep-filter"
  if [ $CHECK -eq 0 ]; then
    mkdir -p "$HOME_DIR/bin"
    curl -L --fail -o "$DF.part" "https://github.com/Rikorose/DeepFilterNet/releases/download/v$DF_VER/deep-filter-$DF_VER-$DFA-apple-darwin" || { echo "   download failed, run this again"; exit 6; }
    [ "$(shasum -a 256 "$DF.part" | cut -d' ' -f1)" = "$DFS" ] || { echo "   file did not verify, deleting it"; rm -f "$DF.part"; exit 6; }
    chmod +x "$DF.part"; mv "$DF.part" "$DF"; ok "deep-filter downloaded and verified"
  fi
fi

say "Step 7 of 7: your folders and settings"
[ $CHECK -eq 0 ] && mkdir -p "$REPO/Inbox" "$REPO/Edited"
[ -d "$REPO/Inbox" ] && ok "Inbox and Edited folders in $REPO"
if [ ! -f "$REPO/config.json" ] && [ $CHECK -eq 0 ]; then cp "$REPO/config.default.json" "$REPO/config.json"; ok "created your settings file (config.json)"; fi

echo
OK=1
command -v ffmpeg >/dev/null && command -v whisper-cli >/dev/null && command -v tesseract >/dev/null && command -v icloudpd >/dev/null || OK=0
[ -x "$HOME_DIR/venv/bin/python" ] && [ -f "$MODEL" ] && [ -x "$DF" ] || OK=0
if [ $OK -eq 1 ]; then echo "ALL SET. Everything the reel editor needs is installed."; else echo "NOT READY: something above says MISSING."; [ $CHECK -eq 1 ] && echo "Run scripts/setup.sh to install it."; exit 1; fi
