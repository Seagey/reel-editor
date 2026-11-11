#!/bin/bash
# Downloads your most recent videos from iCloud Photos into the Inbox folder.
#   scripts/icloud-fetch.sh <apple id email> [how many recent items to look at, default 30]
# Needs scripts/icloud-signin.sh to have been done in the last two months or so.
HOME_DIR="${REEL_EDITOR_HOME:-$HOME/.reel-editor}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
for b in /opt/homebrew/bin /usr/local/bin; do [ -d "$b" ] && PATH="$PATH:$b"; done
BIN="$(command -v icloudpd)"
APPLE_ID="${1:-}"; N="${2:-30}"
[ -n "$APPLE_ID" ] || { echo "Usage: icloud-fetch.sh <apple id email> [count]"; exit 1; }
[ -n "$BIN" ] || { echo "Set up has not been run yet."; exit 1; }
INBOX="$REPO/Inbox"; mkdir -p "$INBOX"
# When Claude runs this there is no keyboard, so if the sign in has expired it stops with a message
# instead of hanging. When you run it yourself in Terminal it can still ask you.
IN=/dev/stdin; [ -t 0 ] || IN=/dev/null
"$BIN" --username "$APPLE_ID" --cookie-directory "$HOME_DIR/icloud" --directory "$INBOX" \
  --recent "$N" --skip-photos --folder-structure none --mfa-provider console < "$IN" 2>&1 | tail -25
code=${PIPESTATUS[0]}
if [ "$code" -ne 0 ]; then
  echo
  echo "ICLOUD_FETCH_FAILED: the iCloud sign in has probably expired or was never done. Run scripts/icloud-signin.sh in Terminal."
  exit "$code"
fi
echo "ICLOUD_FETCH_OK"
