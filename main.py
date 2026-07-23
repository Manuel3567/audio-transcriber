import whisper
import sounddevice as sd
import numpy as np
import threading
import time
import sys
import subprocess
import requests
import json

# Audio Configuration
SAMPLE_RATE = 16000
BLOCK_SIZE = 4096
MICROPHONE_DEVICE_ID = 2
MICROPHONE_CHANNELS = 1
SYSTEM_AUDIO_DEVICE_ID = 4
SYSTEM_AUDIO_CHANNELS = 2

# Audio Processing
TARGET_RMS_LEVEL = 0.1
AUDIO_CLIP_MIN = -1.0
AUDIO_CLIP_MAX = 1.0

# Transcription
WHISPER_MODEL = "large"
TRANSCRIPT_LANGUAGE = "de"
TRANSCRIPT_FILEPATH = "transcript.txt"

# Timing
RECORDING_LOOP_SLEEP = 0.1
THREAD_JOIN_TIMEOUT = 2
CLAUDE_SUMMARIZATION_TIMEOUT = 30


def normalize_audio(audio):
    rms = np.sqrt(np.mean(audio ** 2))
    if rms > 0:
        audio = audio * (TARGET_RMS_LEVEL / rms)
        audio = np.clip(audio, AUDIO_CLIP_MIN, AUDIO_CLIP_MAX)
    return audio


def merge_audio_streams(microphone_audio, system_audio):
    min_length = min(len(microphone_audio), len(system_audio))
    return (microphone_audio[:min_length] + system_audio[:min_length]) / 2


def save_transcript_to_file(text, filepath=TRANSCRIPT_FILEPATH, append=True):
    mode = "a" if append else "w"
    with open(filepath, mode) as f:
        f.write(text + "\n")


def summarize_transcript_with_claude(transcript_text):
    try:
        result = subprocess.run(
            ["claude", "-"],
            input=f"Summarize this German transcript concisely in German:\n\n{transcript_text}",
            capture_output=True,
            text=True,
            timeout=CLAUDE_SUMMARIZATION_TIMEOUT
        )
        if result.stdout:
            print("\nSummary:")
            print(result.stdout)
    except Exception as e:
        print(f"Summarization error: {e}")


def record_microphone_audio(device_id, sample_rate, block_size, chunks_list, recording_flag, thread_lock):
    try:
        stream = sd.InputStream(device=device_id, channels=MICROPHONE_CHANNELS, samplerate=sample_rate, blocksize=block_size)
        stream.start()
        while recording_flag[0]:
            chunk, _ = stream.read(block_size)
            with thread_lock:
                chunks_list.append(chunk)
        stream.stop()
        stream.close()
    except Exception as e:
        print(f"Microphone error: {e}")


def record_system_audio(device_id, sample_rate, block_size, chunks_list, recording_flag, thread_lock):
    try:
        stream = sd.InputStream(device=device_id, channels=SYSTEM_AUDIO_CHANNELS, samplerate=sample_rate, blocksize=block_size)
        stream.start()
        while recording_flag[0]:
            chunk, _ = stream.read(block_size)
            with thread_lock:
                chunks_list.append(chunk)
        stream.stop()
        stream.close()
    except Exception as e:
        print(f"System audio error: {e}")


def combine_audio_chunks(chunks):
    return np.concatenate(chunks, axis=0).astype(np.float32).flatten()


def transcribe_audio_with_whisper(audio):
    print("Transcribing...")
    model = whisper.load_model(WHISPER_MODEL)
    return model.transcribe(audio, language=TRANSCRIPT_LANGUAGE)


def get_user_microphone_device_id():
    devices = sd.query_devices()
    print("\nAvailable devices:")
    for i, device in enumerate(devices):
        print(f"{i}: {device['name']}")

    while True:
        try:
            device_id = int(input("\nSelect microphone device ID: "))
            if 0 <= device_id < len(devices):
                return device_id
            print("Invalid device ID")
        except ValueError:
            print("Please enter a valid number")


def record_audio_from_devices(mic_device_id):
    mic_chunks = []
    sys_chunks = []
    recording = [True]
    thread_lock = threading.Lock()

    print("Recording (press Ctrl+C to stop)...")
    mic_thread = threading.Thread(
        target=record_microphone_audio,
        args=(mic_device_id, SAMPLE_RATE, BLOCK_SIZE, mic_chunks, recording, thread_lock),
        daemon=True
    )
    sys_thread = threading.Thread(
        target=record_system_audio,
        args=(SYSTEM_AUDIO_DEVICE_ID, SAMPLE_RATE, BLOCK_SIZE, sys_chunks, recording, thread_lock),
        daemon=True
    )
    mic_thread.start()
    sys_thread.start()

    try:
        while True:
            time.sleep(RECORDING_LOOP_SLEEP)
    except KeyboardInterrupt:
        print("\nStopping...")
        recording[0] = False

    mic_thread.join(timeout=THREAD_JOIN_TIMEOUT)
    sys_thread.join(timeout=THREAD_JOIN_TIMEOUT)

    return mic_chunks, sys_chunks


def process_recorded_audio(mic_chunks, sys_chunks):
    if not mic_chunks or not sys_chunks:
        print("No audio recorded")
        return None

    microphone_audio = combine_audio_chunks(mic_chunks)
    system_audio = combine_audio_chunks(sys_chunks)
    merged_audio = merge_audio_streams(microphone_audio, system_audio)
    return normalize_audio(merged_audio)


def transcribe_and_save_audio(audio):
    transcription_result = transcribe_audio_with_whisper(audio)
    print(transcription_result["text"])
    save_transcript_to_file(transcription_result["text"], append=False)
    print("✓ Saved")
    return transcription_result["text"]


def main():
    mic_device_id = get_user_microphone_device_id()
    mic_chunks, sys_chunks = record_audio_from_devices(mic_device_id)
    audio = process_recorded_audio(mic_chunks, sys_chunks)
    if audio is None:
        return
    transcript = transcribe_and_save_audio(audio)
    summarize_transcript_with_claude(transcript)


if __name__ == "__main__":
    main()
