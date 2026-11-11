#!/bin/bash
# Signs in to iCloud so reels can be fetched. Run this yourself in Terminal (not through a chat):
# it asks for your Apple ID password and the 6 digit code Apple sends to your phone.
# Nothing you type here is shown to or stored by Claude. The sign in lasts about two months.
HOME_DIR="${REEL_EDITOR_HOME:-$HOME/.reel-editor}"
for b in /opt/homebrew/bin /usr/local/bin; do [ -d "$b" ] && PATH="$PATH:$b"; done
BIN="$(command -v icloudpd)"
[ -n "$BIN" ] || { echo "Set up has not been run yet. Ask Claude to run the set up first."; exit 1; }
APPLE_ID="${1:-}"
if [ -z "$APPLE_ID" ]; then read -r -p "Your Apple ID email: " APPLE_ID; fi
mkdir -p "$HOME_DIR/icloud"
echo
echo "Next, Terminal asks for your Apple ID password (you will not see it as you type), then a 6 digit code."
echo "If it asks whether to save the password in your Mac keychain, type y and press Return. That keeps it on your Mac only."
echo
"$BIN" --username "$APPLE_ID" --cookie-directory "$HOME_DIR/icloud" --auth-only --mfa-provider console
code=$?
echo
if [ $code -eq 0 ]; then
  echo "SIGNED IN. You can close this window and go back to Claude."
else
  echo "That did not work (see the message above). Common reasons:"
  echo "  1. 'Access iCloud Data on the Web' is off in your iPhone settings"
  echo "  2. Advanced Data Protection is on (it blocks this)"
  echo "  3. The password or code was typed wrong"
  echo "Tell Claude which message you got and it will walk you through the fix."
fi
exit $code
