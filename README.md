## Description

Captures both your microphone input and system audio (e.g., from meetings, videos) simultaneously, then transcribes the combined audio to German text using OpenAI's Whisper model. Ideal for transcribing Microsoft Teams calls, video conferences, or any conversation where you want to capture both sides.

## Installation

**Requirements:** Python 3.13+

1. Install dependencies with `uv`:
```bash
uv sync
```

2. Install BlackHole (virtual audio loopback for macOS):
```bash
brew install blackhole-2ch
```

BlackHole is a virtual audio device that captures system audio output. It's needed to record what's playing on your Mac (music, video, etc.) alongside your microphone input.

## Setup

## 1. Find your device IDs

**Your device list will be different from the example below.** Run this command to see all audio devices on your Mac:

```
python3 -c "import sounddevice as sd; devices = sd.query_devices(); print('\n'.join(f'{i}: {d[\"name\"]}' for i, d in enumerate(devices)))"
```

Example output (yours will likely be different):
```
0: BenQ GL2250H
1: TONOR TC30 Audio Device
2: BlackHole 2ch
3: MacBook Pro Microphone
4: MacBook Pro Speakers
5: Microsoft Teams Audio
```

**Note the device IDs for:**
- Your microphone (e.g., "MacBook Pro Microphone" or your external mic)
- BlackHole 2ch (this will be at a different position in your list)

### 2. Update device IDs in main.py

You **must** change the device IDs in `main.py` to match your devices:

- **Line 21** (microphone): Change `device=1` to your microphone's ID from step 1
  - Example: If "MacBook Pro Microphone" is at position 3, use `device=3`
  
- **Line 36** (system audio): Change `device=2` to BlackHole 2ch's ID from step 1
  - Example: If "BlackHole 2ch" is at position 4, use `device=4`

### 3. Create a multi-output device to both record and hear audio

1. Open **Audio Midi Setup** (search in Spotlight)
2. Click the "+" button at the bottom left and select **"Create Multi-Output Device"**
3. In the device list, enable **BlackHole 2ch** and your preferred speaker output device (e.g., MacBook Pro Speakers, external speakers, headphones, etc.)
4. Set your speaker device as the master device
5. Open **System Settings** → **Sound** → **Output** and select your new **Multiausgangsgerät**

This setup allows audio to be recorded (via BlackHole) while still playing through your speakers. Without this, audio would only go to BlackHole and you wouldn't hear anything on your speakers.

**Important:** After completing this step, run the device discovery command again:
```
python3 -c "import sounddevice as sd; devices = sd.query_devices(); print('\n'.join(f'{i}: {d[\"name\"]}' for i, d in enumerate(devices)))"
```

You will now see **Multiausgangsgerät** as a new device in your list. Example:
```
0: BenQ GL2250H
1: TONOR TC30 Audio Device
2: BlackHole 2ch
3: MacBook Pro Microphone
4: MacBook Pro Speakers
5: Microsoft Teams Audio
6: Multiausgangsgerät
```

**Important distinction:**
- **Multiausgangsgerät** is set only in System Settings (Output) — it routes audio to both BlackHole and your speakers so you can hear it
- **In main.py**, you still use **BlackHole 2ch** as the device ID — the script reads FROM BlackHole (which receives the audio via the Multiausgangsgerät routing)
- Do NOT use Multiausgangsgerät as a device ID in main.py

**Troubleshooting:** If you get an "Invalid number of channels" error when running the script, your device IDs have changed after creating the multi-output device — re-check them with the command above and update `main.py` accordingly.

## Run

```bash
uv run python main.py
```

Press `Ctrl+C` to stop recording. The transcript will be saved to `transcript.txt`.