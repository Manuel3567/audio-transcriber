from typing import Protocol
import numpy as np

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
