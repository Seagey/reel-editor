# Getting your videos from iCloud

This lets Claude fetch your newest videos straight from iCloud Photos, so you can say "edit my
latest video" without moving files around. It takes about five minutes, once. Then about every two
months Apple asks you to sign in again.

If you would rather not do this, the simple way always works: AirDrop the video to your Mac, or
drag it into the `Inbox` folder, and say "edit the video in my Downloads" or "edit what is in my
Inbox".

The tool that does the fetching is called icloudpd. It is free, open source and made by the
community, not by Apple. Apple can change how iCloud works at any time, and if that ever breaks it,
the AirDrop way keeps working.

## Before you start

You need your iPhone, your Mac, and about five minutes.

### Step 1. Check your videos are going to iCloud

On your iPhone: **Settings**, tap your name at the top, **iCloud**, **Photos**. Make sure
**Sync this iPhone** is on.

Videos upload when your phone is on Wi-Fi and charging, so a video you filmed a minute ago may take a
while to appear.

### Step 2. Turn on web access

On your iPhone: **Settings**, tap your name, **iCloud**, scroll down to
**Access iCloud Data on the Web** and turn it on.

(Apple moves settings around between iOS versions. If you cannot find it, use the search box at the
top of Settings and search for "Access iCloud Data on the Web".)

### Step 3. Check Advanced Data Protection

On your iPhone: **Settings**, tap your name, **iCloud**, **Advanced Data Protection**.

- **It says Off, or you cannot see it**: perfect, carry on to Step 4.
- **It says On**: this fetching method will not work while it is on. You have two honest choices:
  1. **Keep it on** (the safer option for your privacy) and use the AirDrop way instead. You lose
     nothing.
  2. **Turn it off** to use iCloud fetching. The trade off: with it on, Apple cannot read most of your
     iCloud data at all, not even to help you if you lose your devices and your recovery details.
     With it off, Apple holds the keys to more of your data, so they can help you recover it, and
     can be compelled by law to hand it over. Most people run with it off, which is Apple's default.
     Turning it off is your call, and you can turn it back on later.

If you are unsure, pick option 1. Do not turn it off just to make this work.

### Step 4. Sign in (you do this part yourself, in Terminal)

Your Apple ID password and the 6 digit code are private. They go into Terminal on your own Mac
only, never into the Claude chat, so Claude never sees them.

1. On your Mac press **Command and Space**, type **Terminal**, press Return. A window with a blinking
   cursor opens.
2. Type this, then press Return (the `cd` bit moves into the reel editor folder):
   `cd ~/reel-editor && scripts/icloud-signin.sh`
3. It asks for your **Apple ID email**. Type it and press Return.
4. It asks for your **password**. Type it and press Return. You will not see anything appear as you
   type. That is normal, it is hiding it.
5. Your iPhone (or Mac) shows a message "Apple ID sign in requested" with a 6 digit code. Type the
   6 digits into Terminal and press Return. If your phone shows an Allow button, tap **Allow** first.
6. If it asks whether to save the password in your Mac's keychain, type **y** and press Return.
   (This keeps it on your Mac only, in the same place Safari keeps passwords.)
7. When you see **SIGNED IN**, you are done. Go back to Claude and tell it.

### Step 5. Try it

Tell Claude: "Fetch my newest videos from iCloud." Claude downloads them into the `Inbox` folder.
Then: "Edit my latest video."

## Signing in again

About every two months, Apple expires the sign in. Claude will tell you "the iCloud sign in has
expired". Do Step 4 again, nothing else. Everything else stays set.

## If it does not work

- **"Authentication failed" or "Invalid credentials"**: retype the password carefully, then try again.
- **It says web access is blocked, or the sign in is refused straight away**: Step 2 is off or Step
  3 (Advanced Data Protection) is on. Check both.
- **Fetch finds no videos**: the video has not finished uploading yet. Wait a few minutes and try
  again, or use AirDrop.
- **Anything else**: tell Claude the exact message and it will help. Do not paste your password.

## Taking it away again

To stop Claude being able to fetch from your iCloud: on your iPhone, turn **Access iCloud Data on the
Web** off. That cuts it off at Apple's end. On your Mac, ask Claude to
"remove the iCloud sign in": it deletes the sign in files in `~/.reel-editor/icloud`, and you can
remove the saved password yourself in the **Keychain Access** app (search for icloud).
