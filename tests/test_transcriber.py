import numpy as np
import pytest
from pathlib import Path
from audio_transcriber.transcriber import run_transcription_session, TranscribeSession


class FixtureRecorder:
    """Loads pre-recorded audio from tests/recordings instead of live recording."""
    def __init__(self, filename: str):
        self.filename = filename

    def _resolve_path(self) -> Path:
        """Resolve audio file path relative to tests/recordings."""
        return Path(__file__).parent / "recordings" / self.filename

    def record(self, mic_id: int, system_id: int) -> np.ndarray | None:
        """Load audio from file and return as numpy array."""
        import whisper
        audio = whisper.load_audio(str(self._resolve_path()))
        return audio

class ZeroAudioRecorder:
    """Returns silence for testing."""
    def record(self, mic_id: int, system_id: int) -> np.ndarray | None:
        return np.zeros(16000, dtype=np.float32)

class MockTranscriber:
    """Returns fixed transcription for testing."""
    def __init__(self, text: str):
        self.text = text

    def transcribe(self, audio: np.ndarray) -> str:
        return self.text

class NullSummarizer:
    """Does nothing. For tests that don't care about summarization."""
    def summarize(self, text: str) -> None:
        pass

@pytest.fixture(params=[])
def fixture_audio():
    """Parametrized fixture for each recording file."""
    recordings_dir = Path(__file__).parent / "fixtures" / "recordings"
    for audio_file in sorted(recordings_dir.glob("*.m4a")):
        yield audio_file.name


@pytest.fixture
def default_session():
    """Default TranscribeSession for testing."""
    return TranscribeSession(mic_id=0, system_id=1, summarize=False)


def test_transcribe_fixture_audio(fixture_audio, default_session):
    """Transcribe fixture audio and verify it matches expected text."""
    from audio_transcriber.transcriber import WhisperTranscriber

    run_transcription_session(
        TranscribeSession(mic_id=0, system_id=1, summarize=False),
        recorder=FixtureRecorder(fixture_audio),
        transcriber=WhisperTranscriber(),
        summarizer=NullSummarizer(),
    )

    saved_file = Path("transcript_1.txt")
    assert saved_file.exists()

    expected_file = Path(__file__).parent / "fixtures" / "transcriptions" / f"{Path(fixture_audio).stem}.txt"
    expected_words = expected_file.read_text().lower().split()
    transcript = saved_file.read_text().lower()

    pos = 0
    for word in expected_words:
        pos = transcript.find(word, pos)
        assert pos != -1, f"'{word}' not found"

    saved_file.unlink()


def test_transcribe_saves_file(default_session):
    """Verify transcript is saved to file."""
    run_transcription_session(
        default_session,
        recorder=ZeroAudioRecorder(),
        transcriber=MockTranscriber("test transcript"),
        summarizer=NullSummarizer(),
    )

    saved_file = Path("transcript_1.txt")
    assert saved_file.exists()
    saved_file.unlink()


def test_transcribe_counter_logic(default_session):
    """Verify transcript counter increments for new files."""
    Path("transcript_1.txt").write_text("existing")
    Path("transcript_2.txt").write_text("existing")

    run_transcription_session(
        default_session,
        recorder=ZeroAudioRecorder(),
        transcriber=MockTranscriber("test transcript"),
        summarizer=NullSummarizer(),
    )

    saved_file = Path("transcript_3.txt")
    assert saved_file.exists()
    Path("transcript_1.txt").unlink()
    Path("transcript_2.txt").unlink()
    saved_file.unlink()
