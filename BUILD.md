# BUILD: Reel Editor

## Intent

A package a non technical small business owner can use without help: one link, pasted into Claude
Code, and it walks them through the whole thing. In the owner's words: "put together a skill
package ... just to edit his reels for social media. Just captions, basic editing, fixing up the
studio audio on it to make him sound better and any sort of colour grading he might need. Allow him
to customise it ... set up, downloading whatever it needs to be able to edit on his computer ...
say that the video is in iCloud and you can fetch it off iCloud ... really self explanatory in each
step."

**The one sentence that decides whether it worked:** "I just want to be able to send him this link.
He pastes it into Claude Code and it walks him through the process."

## Plan

1. `README.md`: the one line to paste, what it does, what it needs, how to ask for edits.
2. `CLAUDE.md` (and `AGENTS.md`): a friendly one step at a time onboarding. Explains each install
   before doing it, confirms each success, never takes passwords in chat.
3. `scripts/setup.sh`: idempotent. Homebrew (the user installs it, it needs their password), then
   ffmpeg, whisper-cpp, tesseract, icloudpd from Homebrew; Pillow in a private Python venv; the
   whisper `small.en` model (about 470 MB, SHA-256 checked); DeepFilterNet 0.5.6 (about 30 MB,
   SHA-256 checked per chip). All under `~/.reel-editor` except Homebrew's.
4. iCloud: `docs/ICLOUD.md` plus `scripts/icloud-signin.sh` (typed by the user in their own
   Terminal) and `scripts/icloud-fetch.sh`. AirDrop or the Inbox folder as the fallback.
5. Skill `.claude/skills/edit-reel/`: cuts by sound, mirror check by OCR, 9:16 crop, measured gentle
   grade with before/after sheet, studio sound chain, captions drawn with Pillow inside phone safe
   zones, loudness near -14 LUFS, checks and a report.
6. `config.default.json` plus the user's own `config.json`, changed through plain words
   (`docs/STYLE.md`).

HyperFrames was considered and left out: captions, grade and sound need only ffmpeg and Pillow,
and Homebrew's ffmpeg has no subtitle or text filters, so captions are drawn as images instead.

### Numbers

- Set up: about 15 to 20 minutes, one 470 MB download, about 3 GB of disk.
- A 35 second clip edits in about 45 seconds, a 73 second clip in about 80 seconds, on an M series
  Mac.
- Cost: nothing. No paid APIs and no cloud services other than the user's own iCloud.

## Non goals

- Windows or Linux (Mac only, stated honestly).
- Motion graphics, B roll, music, auto posting, thumbnails.
- Removing sentences or retakes by itself (it only cuts dead air and long pauses; the user can ask
  for specific ranges to be dropped).
- Making the sound "perfect" without ears: it is tuned by measurement, the user decides.
- Reading or storing any password or 6 digit code.

## Changes to the plan

- icloudpd is installed from Homebrew, not pip: the pip build is a bundled binary that crashed on
  the newest Python.
- Captions are drawn with Pillow and overlaid, because the Homebrew ffmpeg has no libass.

## Verified

On an Apple silicon Mac, on four real phone clips (35 to 73 seconds, 4K portrait):

- Fresh set up into an empty folder: every step ran, models verified by checksum, ended `ALL SET`;
  `--check` mode changes nothing.
- Cuts by sound: leading dead air trimmed (about 1 s in the samples), long pauses shortened,
  trailing dead air trimmed. Final files measured with `silencedetect`: no quiet at the start or
  end beyond the allowed margin, no long pauses left.
- Mirror check: a front camera clip with a TV in frame was detected as mirrored by OCR (real words
  read only when flipped) and flipped; clips with no readable text were left alone and reported
  `unknown`.
- Grade: stays inside fixed limits, before/after sheet written, exposure left alone when already
  in range.
- Sound: loudness -14.3 to -14.7 LUFS, true peak about -4.4 dB on every file.
- Captions: re transcribing the final file matched the caption words 0.91 to 1.0; line and word
  styles, uppercase, custom font and a spelling replacement all worked; all inside the safe zone.
- Logo, end card, zoom and the `--latest` Inbox path worked.
- HDR (HLG) colour mapping chain runs on a synthetic clip.
- iCloud failure path: with no sign in, the fetch stops with `ICLOUD_FETCH_FAILED` and a clear
  message instead of hanging.
- `skill-audit`: SKILL.md 158 lines, description under the limit, one level deep, OK.

Not verified: a live iCloud sign in (needs a real Apple ID and a code), an Intel Mac, a Mac with no
Homebrew, Windows.

## Publishing

Published as a public repository on 12 Nov 2026 ("Public is fine"). No client or business names appear in
the repository.
