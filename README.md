## Description

Captures both your microphone input and system audio (e.g., from meetings, videos) simultaneously, then transcribes the combined audio to German text using OpenAI's Whisper model. Ideal for transcribing Microsoft Teams calls, video conferences, or any conversation where you want to capture both sides.

## Installation

**Requirements:** Python 3.13+, macOS

The setup script will:
1. ✓ Install BlackHole 2ch
2. ✓ Auto-detect your microphone and BlackHole devices
3. ✓ Configure device IDs automatically

Choose your installation method:

### Option 1: From GitHub (Recommended for users)
One-liner from anywhere:
```bash
uvx --from https://github.com/user/repo audio-transcriber setup
```

### Option 2: Local development (after cloning)
```bash
git clone <repo>
cd audio-transcriber
uv sync
audio-transcriber setup
```

After setup completes, follow the one-time manual setup below.

---

## Why BlackHole?

**The Problem:** macOS blocks internal sound capture by default for privacy, you must route the audio or use a dedicated app.

**The Solution:** BlackHole is a virtual audio device that acts as a "loopback" — it captures system audio output so your app can record it.

**What happens:**
```
System Audio (Teams, music, etc.)
    ↓
BlackHole (virtual device captures it)
    ↓
Your app records from BlackHole + Microphone simultaneously
    ↓
Both sides of the conversation are transcribed
```

Without BlackHole, you'd only record yourself (microphone), not what the other person is saying.

---

## Setup: Create Multi-Output Device (One-time)

After running `audio-transcriber setup`, the terminal will print the next steps. You need to configure macOS to send system audio to BlackHole while still hearing it through your speakers.

### Why this step is needed:
By default, system audio goes to your speakers. We need to make it go to **both** BlackHole (for recording) **and** your speakers (so you can hear it).

### Steps:

1. **Open Audio MIDI Setup**
   - Press Cmd+Space, type "Audio MIDI Setup", hit Enter

2. **Create a new multi-output device**
   - Click the "+" button at the bottom left
   - Select "Create Multi-Output Device"

3. **Configure the device**
   - In the device list on the right, check the boxes for:
     - ✓ BlackHole 2ch
     - ✓ Your speaker output (e.g., "MacBook Pro Speakers", headphones, external speakers, etc.)
   - Set your speaker/headphone device as the master (it should have a diamond icon)

4. **Activate it in System Settings**
   - Open System Settings → Sound → Output
   - Select your new multi-output device (it will be named something like "Multiausgangsgerät" or "Multi-output")

### Result:
- ✓ System audio now flows to both BlackHole and your speakers
- ✓ You can hear everything (speaker output)
- ✓ Your app records everything (BlackHole input)

### Verification:
If you get an "Invalid number of channels" error when running the app, re-run the setup:
```bash
audio-transcriber setup
```
Device IDs may have shifted after creating the multi-output device.

## Usage

After setup is complete, record and transcribe audio:

**Record & transcribe:**
```bash
audio-transcriber transcribe
```

**Record, transcribe & summarize with Claude:**
```bash
audio-transcriber transcribe --summary
```

Press `Ctrl+C` to stop recording. The transcript is saved to `transcript.txt`.

## Uninstall

Remove BlackHole and dependencies:
```bash
audio-transcriber teardown
```

This will:
- ✓ Uninstall BlackHole 2ch
- ✓ Remove Python dependencies

**Manual cleanup** (optional):
- Delete multi-output device in Audio MIDI Setup
- Restore system sound output in System Settings

## Run

```bash
uv run python main.py
```

Press `Ctrl+C` to stop recording. The transcript will be saved to `transcript.txt`.