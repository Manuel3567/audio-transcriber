import whisper
import sounddevice as sd
import numpy as np
import threading
import time
import subprocess
from pathlib import Path

# Constants
SAMPLE_RATE = 16000
BLOCK_SIZE = 4096
MIC_CHANNELS = 1
SYSTEM_CHANNELS = 2
TARGET_RMS = 0.1
TRANSCRIPT_FILE = "transcript.txt"
WHISPER_MODEL = "large"
LANGUAGE = "de"


def record_audio(mic_id: int, system_id: int) -> np.ndarray | None:
    """Record from microphone and system audio, return merged audio or None."""
    mic_chunks = []
    sys_chunks = []
    recording = [True]
    lock = threading.Lock()

    def read_device(device_id: int, channels: int, target_list: list) -> None:
        try:
            stream = sd.InputStream(device=device_id, channels=channels, samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE)
            stream.start()
            while recording[0]:
                chunk, _ = stream.read(BLOCK_SIZE)
                with lock:
                    target_list.append(chunk)
            stream.stop()
            stream.close()
        except Exception as e:
            print(f"❌ Error: {e}")
            recording[0] = False

    print("🎤 Recording... (Ctrl+C to stop)")
    threading.Thread(target=read_device, args=(mic_id, MIC_CHANNELS, mic_chunks), daemon=True).start()
    threading.Thread(target=read_device, args=(system_id, SYSTEM_CHANNELS, sys_chunks), daemon=True).start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("⏹ Stopping...")
        recording[0] = False
        time.sleep(0.5)

    if not mic_chunks or not sys_chunks:
        print("No audio recorded")
        return None

    mic_audio = np.concatenate(mic_chunks, axis=0).astype(np.float32).flatten()
    sys_audio = np.concatenate(sys_chunks, axis=0).astype(np.float32).flatten()

    # Merge and normalize
    min_len = min(len(mic_audio), len(sys_audio))
    merged = (mic_audio[:min_len] + sys_audio[:min_len]) / 2

    # Normalize
    rms = np.sqrt(np.mean(merged ** 2))
    if rms > 0:
        merged = merged * (TARGET_RMS / rms)
        merged = np.clip(merged, -1.0, 1.0)

    return merged


def transcribe_audio(audio: np.ndarray) -> str:
    """Transcribe audio with Whisper."""
    print("🎯 Transcribing...")
    model = whisper.load_model(WHISPER_MODEL)
    result = model.transcribe(audio, language=LANGUAGE)
    return result["text"]


def summarize_with_claude(text: str) -> None:
    """Summarize transcript using Claude."""
    try:
        result = subprocess.run(
            ["claude", "-"],
            input=f"Summarize this German transcript concisely in German:\n\n{text}",
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.stdout:
            print("\n📝 Summary:")
            print(result.stdout)
    except Exception as e:
        print(f"Summary error: {e}")


def transcribe(mic_id: int | None, system_id: int | None, summarize: bool = False) -> None:
    """Main transcription workflow."""
    if mic_id is None or system_id is None:
        print("❌ Device not configured. Run: audio-transcriber setup")
        return

    audio = record_audio(mic_id, system_id)
    if audio is None:
        return

    transcript = transcribe_audio(audio)
    print(transcript)

    base_path = Path(TRANSCRIPT_FILE)
    counter = 1
    while (base_path.parent / f"{base_path.stem}_{counter}{base_path.suffix}").exists():
        counter += 1

    file_path = base_path.parent / f"{base_path.stem}_{counter}{base_path.suffix}"
    with open(file_path, "w") as f:
        f.write(transcript + "\n")
    print(f"✓ Saved to {file_path}")

    if summarize:
        summarize_with_claude(transcript)
