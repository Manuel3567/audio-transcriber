import subprocess
import whisper
import sounddevice as sd
import numpy as np
import threading
import time
from typing import Protocol
from dataclasses import dataclass

# Constants
SAMPLE_RATE = 16000
BLOCK_SIZE = 4096
MIC_CHANNELS = 1
SYSTEM_CHANNELS = 2
TARGET_RMS = 0.1
WHISPER_MODEL = "large"
LANGUAGE = "de"


class AudioRecorder(Protocol):
    """Protocol for audio recording."""
    def record(self, mic_id: int, system_id: int) -> np.ndarray | None:
        """Record from microphone and system audio, return merged audio or None."""
        ...


class Transcriber(Protocol):
    """Protocol for audio transcription."""
    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio and return text."""
        ...


class Summarizer(Protocol):
    """Protocol for transcript summarization."""
    def summarize(self, text: str) -> None:
        """Summarize transcript and print result."""
        ...


@dataclass
class TranscribeSession:
    """Configuration for a transcription session."""
    mic_id: int | None
    system_id: int | None
    summarize: bool = False


class WhisperTranscriber:
    """Real Whisper transcriber implementation."""
    def __init__(self, model_name: str = WHISPER_MODEL, language: str = LANGUAGE):
        self.model_name = model_name
        self.language = language
        self._model = None

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio with Whisper."""
        print("🎯 Transcribing...")
        if self._model is None:
            self._model = whisper.load_model(self.model_name)
        result = self._model.transcribe(audio, language=self.language)
        return result["text"]


class ClaudeSummarizer:
    """Real Claude summarizer implementation."""
    def summarize(self, text: str) -> None:
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


class SoundDeviceRecorder:
    """Real audio recorder using sounddevice."""
    def __init__(self):
        self.sample_rate = SAMPLE_RATE
        self.block_size = BLOCK_SIZE
        self.mic_channels = MIC_CHANNELS
        self.system_channels = SYSTEM_CHANNELS
        self.target_rms = TARGET_RMS

    def _create_and_start_stream(self, device_id: int, channels: int) -> sd.InputStream:
        """Create and start audio input stream."""
        stream = sd.InputStream(
            device=device_id,
            channels=channels,
            samplerate=self.sample_rate,
            blocksize=self.block_size,
        )
        stream.start()
        return stream

    def _read_chunks_from_stream(self, stream: sd.InputStream, chunks: list, recording: list, lock: threading.Lock) -> None:
        """Read chunks from stream until stopped."""
        while recording[0]:
            chunk, _ = stream.read(self.block_size)
            with lock:
                chunks.append(chunk)

    def _cleanup_stream(self, stream: sd.InputStream) -> None:
        """Stop and close audio stream."""
        stream.stop()
        stream.close()

    def _read_device_stream(self, device_id: int, channels: int, chunks: list, recording: list, lock: threading.Lock) -> None:
        """Read audio chunks from a single device until stopped."""
        try:
            stream = self._create_and_start_stream(device_id, channels)
            self._read_chunks_from_stream(stream, chunks, recording, lock)
            self._cleanup_stream(stream)
        except Exception as e:
            print(f"❌ Error: {e}")
            recording[0] = False

    def _start_recording(self, mic_id: int, system_id: int) -> tuple[list, list, list, threading.Lock]:
        """Start recording threads for microphone and system audio. Returns (mic_chunks, sys_chunks, recording, lock)."""
        mic_chunks = []
        sys_chunks = []
        recording = [True]
        lock = threading.Lock()

        print("🎤 Recording... (Ctrl+C to stop)")
        threading.Thread(
            target=self._read_device_stream, args=(mic_id, self.mic_channels, mic_chunks, recording, lock), daemon=True
        ).start()
        threading.Thread(
            target=self._read_device_stream, args=(system_id, self.system_channels, sys_chunks, recording, lock), daemon=True
        ).start()

        return mic_chunks, sys_chunks, recording, lock

    def _wait_for_keyboard_interrupt(self, recording: list) -> None:
        """Wait for user interrupt and stop recording."""
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("⏹ Stopping...")
            recording[0] = False
            time.sleep(0.5)

    def _merge_audio(self, mic_chunks: list, sys_chunks: list) -> np.ndarray | None:
        """Merge microphone and system audio. Return None if either is empty."""
        if not mic_chunks or not sys_chunks:
            print("No audio recorded")
            return None

        mic_audio = np.concatenate(mic_chunks, axis=0).astype(np.float32).flatten()
        sys_audio = np.concatenate(sys_chunks, axis=0).astype(np.float32).flatten()

        min_len = min(len(mic_audio), len(sys_audio))
        return (mic_audio[:min_len] + sys_audio[:min_len]) / 2

    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to target RMS level."""
        rms = np.sqrt(np.mean(audio ** 2))
        if rms > 0:
            audio = audio * (self.target_rms / rms)
            audio = np.clip(audio, -1.0, 1.0)
        return audio

    def record(self, mic_id: int, system_id: int) -> np.ndarray | None:
        """Record from microphone and system audio, return merged and normalized audio or None."""
        mic_chunks, sys_chunks, recording, lock = self._start_recording(mic_id, system_id)
        self._wait_for_keyboard_interrupt(recording)

        merged = self._merge_audio(mic_chunks, sys_chunks)
        if merged is None:
            return None

        return self._normalize_audio(merged)
