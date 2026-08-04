import numpy as np
import pytest
from pathlib import Path
from audio_transcriber.models import TranscribeSession


class FakeAudioRecorder:
    """Loads pre-recorded audio files (m4a/wav) instead of recording."""
    def __init__(self, audio_path: str):
        self.audio_path = audio_path

    def record(self, mic_id: int, system_id: int) -> np.ndarray | None:
        """Load audio from file and return as numpy array."""
        import whisper

        # Use Whisper's built-in audio loading to get numpy array
        audio = whisper.load_audio(self.audio_path)
        return audio


class NullSummarizer:
    """Does nothing. For tests that don't care about summarization."""
    def summarize(self, text: str) -> None:
        pass


class MockTranscriber:
    """Returns fixed transcript. For tests that don't care about transcription quality."""
    def __init__(self, transcript: str = "test transcript"):
        self.transcript = transcript

    def transcribe(self, audio: np.ndarray) -> str:
        return self.transcript


class ZeroAudioRecorder:
    """Returns silence. For tests that only care about file I/O."""
    def record(self, mic_id: int, system_id: int) -> np.ndarray | None:
        return np.zeros(16000, dtype=np.float32)


@pytest.fixture
def temp_transcript_dir(tmp_path):
    """Create and return a temp transcript directory with file path."""
    transcript_dir = tmp_path / "transcripts"
    transcript_dir.mkdir()
    return transcript_dir, str(transcript_dir / "transcript.txt")


@pytest.fixture
def default_session():
    """Default TranscribeSession for testing."""
    return TranscribeSession(mic_id=0, system_id=1, summarize=False)
