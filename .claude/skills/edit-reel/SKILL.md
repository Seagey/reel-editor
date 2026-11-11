---
name: edit-reel
description: Edits phone videos into finished vertical reels (1080x1920 MP4). Trims dead air and long pauses by sound, fixes a mirrored front camera, cleans up the voice to studio sound, applies a gentle colour grade, burns in readable captions inside the phone safe zones, and sets loudness to about -14 LUFS. Use when the person says "edit my latest video", "edit this reel", "fetch my newest videos from iCloud and edit them", "make the captions yellow", "less colour", "cut it tighter", or asks to change any reel setting.
---

# Edit a reel

Everything runs on the person's own Mac. No paid services. The one script that does the work is
`scripts/edit.sh` in the repo root, which calls `scripts/edit_reel.py` beside this file.

The person is not technical. Talk in plain Australian English, short sentences, no jargon. Say what
you are about to do before you do it, then say what happened. Never use em or en dashes.

## Contents

- Quick path
- Getting the video
- What one edit does
- Settings the person can ask to change
- Before you hand it over: the checks
- Reading the result back to them
- Things that go wrong
- Hard rules

## Quick path

1. Check the set up is done: `scripts/setup.sh --check`. If it says NOT READY, follow `CLAUDE.md`
   (the onboarding), do not improvise installs.
2. Get the video (see below), then run:
   - one named file: `scripts/edit.sh "<path to video>"`
   - the newest N in the Inbox folder: `scripts/edit.sh --latest 3`
3. Run the checks below, look at the pictures, read the captions, then report.

A 30 to 60 second clip takes about one to two minutes on an Apple chip Mac, longer on an older one.

## Getting the video

In this order, stopping at the first that works:

1. **A file they name or drag in.** Use it where it is. Never move or delete their original.
2. **The Inbox folder.** Anything they AirDropped or dropped into `Inbox/` (in the repo folder).
3. **iCloud Photos.** Only if iCloud was set up (`docs/ICLOUD.md`). Their Apple ID email is in
   `config.json` under `icloud_apple_id`. Run `scripts/icloud-fetch.sh <apple id> 30`.
   - It prints `ICLOUD_FETCH_OK` when it worked. The newest videos land in `Inbox/`.
   - It prints `ICLOUD_FETCH_FAILED` when the sign in has expired (it lasts about two months) or
     was never done. Do not try to fix it yourself: tell them, and walk them through
     `docs/ICLOUD.md` step "Signing in again". They type the password and the 6 digit code into
     their own Terminal, never into the chat.
   - "Newest" means the most recently filmed. Videos just filmed can take a few minutes to reach
     iCloud, so if the one they mean is missing, tell them and offer to try again in a minute.
   - Before editing, list the newest videos with their lengths
     (`ffprobe` the duration) and confirm which one they mean if there is any doubt.
4. **Nothing works.** Offer the fallback: AirDrop the video to their Mac, or drag it into the
   Inbox folder.

## What one edit does

In order:

1. **Cuts, by sound.** Finds where the voice really starts and ends from the loudness of the audio,
   not from caption times (speech to text times at the very start of a clip can sit inside the
   silence and hide dead air). Trims the quiet at the start and end, and shortens long pauses.
   Cuts are placed at the quietest moment nearby and each seam has a 15 ms fade, so no word is
   clipped. Sentences are kept whole; nothing is removed that was not dead air.
2. **Mirror check.** Front camera clips are often mirrored. Reads any text in frame (signs,
   screens, shirts) normal and flipped with OCR and flips the video only if real words read
   correctly flipped. Never judged by eye. If there is no readable text it leaves the video
   alone and says so in the report.
3. **Crop to 9:16** and scale to 1080x1920 (landscape clips are cropped to the middle).
4. **Colour.** Measures a few frames and applies a small exposure, contrast and saturation
   correction, capped so it can never look overdone, with a before/after sheet. HDR iPhone clips
   are mapped to standard colour first.
5. **Studio sound.** Noise removal, voice EQ, de-esser, compressor, limiter, then loudness to
   -14 LUFS. This was tuned by measurement. Ears decide: if it sounds harsh, thin or over
   processed, drop `audio.strength` to `light`.
6. **Captions.** Transcribes the cleaned sound, then draws captions with Pillow. Inside phone safe
   zones (x 90 to 960, y 250 to 1520 on a 1080x1920 frame) so buttons and the app's own text do
   not cover them. The active word changes colour. The outline stays dark. No coloured boxes behind
   words, because they go soft over a face.
7. **Outputs.** `Edited/<name>-edited.mp4` and, in `Edited/checks/<name>/`: `contact-sheet.jpg`,
   `colour-before-after.jpg`, `caption-frame.png`, `captions-words.txt`, `report.json`.

## Settings the person can ask to change

All in `config.json` in the repo root (created from `config.default.json`, which is never edited).
The person never touches the file. They say it in plain words and you change it, run the edit
again, and show them. Full word to setting table: `docs/STYLE.md`.

Examples:

- "Make the captions yellow" sets `captions.highlight_color` (the active word) or `captions.color`
  (all words). Ask which if unclear.
- "Bigger captions" raises `captions.size` by about 12 (default 78). Keep the result inside the
  safe zone: the script reports `inside_safe_zone`.
- "Move the captions up" sets `captions.position` to `middle` or `upper`.
- "One word at a time" sets `captions.style` to `word`. "Lines" sets it back to `line`.
- "No captions" sets `captions.enabled` to false.
- "Less colour" lowers `grade.strength` by 0.2. "No colour grading" sets `grade.enabled` false.
- "Cut it tighter" sets `cuts.tightness` to `tight`. "Leave more breathing room": `gentle`.
- "Sounds too processed": `audio.strength` to `light`.
- "Closer on my face": `framing.zoom` 1.15 (max sensible 1.4).
- Name spelled wrong in captions: add it to `vocabulary` (helps the listener get it right) and,
  if it still comes out wrong, to `replacements` as `{"heard": "Right Spelling"}`.

After a change, re-run the edit on the same video and show the new result. Use `Edited/` files;
re-running replaces the old edit of the same name.

## Before you hand it over: the checks

The script prints a summary and writes `report.json`. You still have to look.

1. **Numbers.** `loudness_ok`, `start_ok`, `end_ok` should all be true. Quiet at the start should be
   0.45 s or less and at the end 0.75 s or less. If not, say so and re-run with `--tightness tight`.
2. **Look at the pictures** with the Read tool: `contact-sheet.jpg` (is the face in frame, does
   the picture look natural, are captions inside the screen), `colour-before-after.jpg` (left is
   the original, right is the grade: skin natural, not orange or grey, whites not clipped, blacks
   not crushed) and `caption-frame.png` (read every word at full size, can you read each one
   against the background).
3. **Read the captions.** Open `captions-words.txt`. Speech to text mishears names and local
   words (for example a brand name). Fix with `vocabulary` and `replacements`, then re-run. Check
   `caption_vs_sound_match` in the report: below 0.9 means something is off, investigate.
4. **Mirror.** Look at `report.json` `mirror`. If `decision` is `unknown` and there is text in
   frame (a sign, a screen), look at a frame and check the text reads correctly. If it is
   backwards, set `framing.mirror_fix` to `always` and re-run.
5. **Dead air by sound.** The script runs `silencedetect` on the final mix. Do not trust caption times
   for this.

You cannot listen. Say so honestly: the sound was tuned and measured, but their ears decide.

## Reading the result back to them

Short, plain, in this shape:

- Where the file is, and how to open it (Finder, `Edited` folder inside the reel editor folder).
- What was cut ("took 1.1 seconds of quiet off the start, shortened two long pauses, 36 seconds
  down to 33").
- Whether the picture was flipped and why.
- What the sound now measures ("about -14, the usual level for Instagram and TikTok").
- Captions: font, colours, any word you changed.
- Anything you could not fix, and what they can say to change it.

Then ask what they want changed, and offer one or two ideas from the settings list above.

## Things that go wrong

- **"No speech found"**: the clip is silent or music only. Tell them.
- **Captions in the wrong place or cut off**: check `inside_safe_zone` in the report; lower `size`.
- **Font not found**: the script falls back to Arial Black and prints a note. Offer one of the
  built in fonts (`docs/STYLE.md`), or download a free font (a `.ttf` from fonts.google.com)
  into `~/.reel-editor/fonts/` and set `captions.font` to the file name without `.ttf`.
- **A set up tool is missing**: run `scripts/setup.sh`. If Homebrew is missing, follow `CLAUDE.md`.
- **Edit takes very long**: 4K clips over 3 minutes are heavy. Say so and let it run.

## Hard rules

- Never delete or change the person's original video.
- Never ask for, or accept, a password or 6 digit code in the chat.
- No paid services and no uploading their video anywhere. Everything stays on this Mac, except the
  iCloud download.
- No scroll prompts or "follow me" overlays unless the person asks for them.
- Do not add anything the person did not say: captions show only what was spoken.
