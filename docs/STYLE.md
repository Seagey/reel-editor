# Changing how your reels look and sound

You never edit a file. Tell Claude in plain words, it changes the setting and re edits the video so
you can see it. This page is the full list, for the curious.

| You say | What changes |
|---|---|
| "Make the captions yellow" | the highlighted (current) word colour, or all captions, whichever you mean |
| "Use my brand colour #1A7F5A" | the highlight colour |
| "Bigger / smaller captions" | caption size (default 78) |
| "Move the captions up / to the middle" | caption position: lower, middle or upper |
| "One word at a time" | caption style `word` |
| "Back to lines of text" | caption style `line` |
| "Use capital letters" | `uppercase` on |
| "Show the full stops and commas" | `show_punctuation` on |
| "Thicker outline" | outline width (default 9) |
| "Use the Impact font" | font. Built in: Arial Black, Impact, Arial Rounded Bold, DIN Alternate Bold. Any font on your Mac works by name. |
| "No captions" | captions off |
| "Less colour" / "more colour" | grade strength (0 to 1, default 0.7) |
| "No colour grading" | grade off |
| "A warmer look" / "punchier" / "softer" | grade look: warm, punchy, soft (default natural) |
| "Cut it tighter" | cuts tightness `tight` |
| "Leave more breathing room" | cuts tightness `gentle` (default is `normal`) |
| "The sound is too processed" | audio strength `light` |
| "Don't touch the sound" | audio strength `off` (only the volume is levelled) |
| "Closer on my face" | zoom (1.0 is no zoom, 1.15 is a gentle push in) |
| "Do not flip my video" / "always flip it" | mirror fix `never` / `always` (default `auto` checks by reading text) |
| "Add my logo top right" | logo on, corner top-right, with the file you give |
| "End the video with a card saying..." | end card on with your words |
| "My name keeps coming out wrong" | the word goes in your vocabulary list, and a spelling fix if needed |

Your settings live in `config.json`. The defaults live in `config.default.json` and are never
changed, so you can always ask Claude to "put everything back to default".

## What every reel always gets

- 1080 by 1920, 30 frames a second, MP4 (works on Instagram, Facebook, TikTok and YouTube Shorts)
- Captions inside the phone safe zones
- Volume at about -14 LUFS
- A check of the finished file, written to `Edited/checks/<video name>/`
