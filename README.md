# Reel Editor

Film a talking video on your phone. Tell Claude Code to edit it. Get back a finished vertical reel
with captions, clean studio sound, a gentle colour grade and the dead air cut out.

Everything runs on your own Mac. Nothing is paid for and your videos are not uploaded anywhere
(the only internet use is downloading the tools once, and fetching from your own iCloud if you
choose to).

## Start here: paste this into Claude Code

> Set up the reel editor from https://github.com/Seagey/reel-editor : clone it into a folder called reel-editor in my home folder, open it, read its CLAUDE.md, and walk me through the set up one step at a time.

That is all you have to do. Claude takes it from there, explains each step before doing it, and
checks that it worked. The set up takes about 15 to 20 minutes, most of it downloads.

Do not have Claude Code yet? Get it from claude.com/claude-code, open it, then paste the line above.

## What you get

- **Captions** burned in, word by word, in your fonts and colours, kept clear of the buttons and
  text that Instagram, Facebook and TikTok draw on top of a reel.
- **Studio sound.** Background noise removed, voice warmed up and made clear, volume set to the level
  the apps expect (about -14 LUFS), so you are not too quiet next to other reels.
- **Basic editing.** The quiet before you start talking and after you finish is cut, and long
  pauses are shortened. Nothing you said is removed.
- **Colour.** A gentle correction to exposure, contrast and colour. It checks itself so it never
  looks overdone, and shows you before and after.
- **Mirror fix.** Front camera videos can come out backwards (writing on signs reads the wrong way
  round). It checks by reading the text in your video and flips it back only when needed.
- **Your look.** Optional logo in a corner and an end card.

## What you need

- A **Mac**. Apple chip is what it was built and tested on. An Intel Mac should work but is untested. Windows is not supported yet, honestly: it needs different tools
  and has not been built or tested.
- About **3 GB free** for the tools and a few hundred MB per video while it works.
- **Claude Code** with a Claude account.
- An **iPhone** is ideal. If your videos are in **iCloud Photos**, Claude can fetch them for you.
  If not, you AirDrop them to your Mac, or drag them into the `Inbox` folder.

## After it is set up: how to ask for things

Open Terminal, then type `cd ~/reel-editor` and press Return, then type `claude` and press Return.
Then just talk:

- "Edit my latest video from iCloud."
- "Edit my three newest videos."
- "Edit the video called IMG_1234 in my Downloads."
- "Make the captions yellow." / "Make the captions bigger." / "Move the captions up."
- "Show one word at a time."
- "Less colour." / "No colour grading."
- "Cut it tighter." / "Leave more breathing room."
- "The sound is too processed, ease it back."
- "Add my logo in the top right." / "Add an end card that says Book a free trial."
- "My name is spelled wrong in the captions."

Finished reels are in the `Edited` folder inside `reel-editor`, ready to post.

## If Homebrew is missing

Claude will tell you if this applies. Homebrew is the standard Mac app installer, and the reel editor
uses it for its tools. It must be installed by you, because it asks for your Mac password (never type
that into a chat).

1. Open the **Terminal** app (press Command and Space, type Terminal, press Return).
2. Copy this whole line, paste it into Terminal, press Return, and follow what it asks:
   `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
3. If a pop up asks to install "command line developer tools", click Install and wait.
4. When it finishes it prints a "Next steps" box. Tell Claude it is done and Claude will finish the
   rest.

## Getting videos from iCloud

Step by step, with the honest trade offs (including the Advanced Data Protection switch): see
[docs/ICLOUD.md](docs/ICLOUD.md). Claude walks you through it when you get to that point.

## Changing the look

Everything is changed by asking Claude in plain words. The full list of what can be changed is in
[docs/STYLE.md](docs/STYLE.md).

## Updating

Say "update the reel editor" and Claude pulls the latest version. Your settings and videos are not
touched.

## What is in here

- `CLAUDE.md`: the instructions Claude follows to set you up
- `.claude/skills/edit-reel/`: the editing skill and its scripts
- `scripts/`: set up, iCloud and edit commands
- `config.default.json`: the default look (your own `config.json` is created for you)

MIT licence.
