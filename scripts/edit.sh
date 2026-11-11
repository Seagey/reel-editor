#!/bin/bash
# Runs the reel editor with its private Python.  scripts/edit.sh <video file>   or   scripts/edit.sh --latest 3
HOME_DIR="${REEL_EDITOR_HOME:-$HOME/.reel-editor}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PY="$HOME_DIR/venv/bin/python"
[ -x "$PY" ] || { echo "Set up has not been run yet (scripts/setup.sh)."; exit 1; }
exec "$PY" "$REPO/.claude/skills/edit-reel/scripts/edit_reel.py" "$@"
