import pytest
import string
import json
from pathlib import Path
from audio_transcriber.transcriber import transcribe
from audio_transcriber.models import (
    WhisperTranscriber,
    SoundDeviceRecorder,
    TranscribeSession,
)
from audio_transcriber.config import load_device_config
from audio_transcriber.setup import prompt_for_microphone_id, prompt_for_blackhole_id
from conftest import FakeAudioRecorder, NullSummarizer, MockTranscriber, ZeroAudioRecorder


def _discover_fixtures():
    """Discover all fixture pairs (m4a + txt files with matching names)."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    transcriptions_dir = fixtures_dir / "transcriptions"

    fixtures = []
    for audio_file in sorted(fixtures_dir.glob("*.m4a")):
        basename = audio_file.stem
        text_file = transcriptions_dir / f"{basename}.txt"
        if text_file.exists():
            fixtures.append(basename)

    return fixtures

FIXTURES = _discover_fixtures()

@pytest.fixture(params=FIXTURES)
def fixture_audio(request):
    """Parametrized fixture that loads all m4a files and their expected transcriptions."""
    basename = request.param
    audio_path = Path(__file__).parent / "fixtures" / f"{basename}.m4a"
    text_path = Path(__file__).parent / "fixtures" / "transcriptions" / f"{basename}.txt"

    if not audio_path.exists():
        pytest.skip(f"Test audio fixture not found at {audio_path}")

    if not text_path.exists():
        pytest.skip(f"Expected transcription not found at {text_path}")

    expected = text_path.read_text().strip()
    words = expected.lower().split()
    words = [word.strip(string.punctuation) for word in words]
    return str(audio_path), words


def test_transcribe_fixture_audio(fixture_audio, temp_transcript_dir, default_session):
    """Transcribe fixture audio files and verify word order."""
    audio_path, expected_words = fixture_audio
    transcript_dir, transcript_file_path = temp_transcript_dir

    transcribe(
        default_session,
        recorder=FakeAudioRecorder(audio_path),
        transcriber=WhisperTranscriber(),
        summarizer=NullSummarizer(),
        transcript_file=transcript_file_path,
    )

    saved_file = transcript_dir / "transcript_1.txt"
    assert saved_file.exists()

    saved_transcript = saved_file.read_text().lower()
    transcript_clean = saved_transcript.translate(str.maketrans('', '', string.punctuation))

    pos = 0
    for word in expected_words:
        pos = transcript_clean.find(word, pos)
        assert pos != -1, f"'{word}' not found in order in '{transcript_clean}'"


@pytest.mark.live_audio
def test_record_and_transcribe_live_audio(temp_transcript_dir):
    """Record live audio and verify transcript against user input."""
    config = load_device_config()
    mic_id = config.get("microphone_device_id")
    system_id = config.get("system_audio_device_id")

    if mic_id is None or system_id is None:
        pytest.skip("Microphone not configured")

    expected_text = input("\n📝 Type the text you'll speak: ").lower()

    if not expected_text.strip():
        pytest.skip("No text provided")

    transcript_dir, transcript_file_path = temp_transcript_dir
    session = TranscribeSession(mic_id=mic_id, system_id=system_id, summarize=False)

    transcribe(
        session,
        recorder=SoundDeviceRecorder(),
        transcriber=WhisperTranscriber(),
        summarizer=NullSummarizer(),
        transcript_file=transcript_file_path,
    )

    saved_file = transcript_dir / "transcript_1.txt"
    assert saved_file.exists()

    saved_transcript = saved_file.read_text().lower()
    expected_words = expected_text.split()

    pos = 0
    for word in expected_words:
        pos = saved_transcript.find(word, pos)
        assert pos != -1, f"'{word}' not found in '{saved_transcript}'"
        pos += len(word)


def test_transcribe_saves_file(temp_transcript_dir, default_session):
    """Verify transcribe() saves transcript to file with correct content."""
    transcript_dir, transcript_file_path = temp_transcript_dir

    transcribe(
        default_session,
        recorder=ZeroAudioRecorder(),
        transcriber=MockTranscriber("test transcript"),
        summarizer=NullSummarizer(),
        transcript_file=transcript_file_path,
    )

    assert (transcript_dir / "transcript_1.txt").exists()


def test_transcribe_counter_logic(temp_transcript_dir, default_session):
    """Verify transcribe() uses correct counter for new files."""
    transcript_dir, transcript_file_path = temp_transcript_dir

    (transcript_dir / "transcript_1.txt").write_text("existing")
    (transcript_dir / "transcript_2.txt").write_text("existing")

    transcribe(
        default_session,
        recorder=ZeroAudioRecorder(),
        transcriber=MockTranscriber("test transcript"),
        summarizer=NullSummarizer(),
        transcript_file=transcript_file_path,
    )

    assert (transcript_dir / "transcript_3.txt").exists()


def test_setup_saves_microphone_id(tmp_path, monkeypatch):
    """Verify setup saves microphone ID to config.json."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("builtins.input", lambda *args: "2")

    devices = [
        {"name": "Microphone 1", "max_input_channels": 1},
        {"name": "Microphone 2", "max_input_channels": 1},
        {"name": "BlackHole 2ch", "max_input_channels": 2},
    ]

    mic_id = prompt_for_microphone_id(devices)
    config_dict = {"microphone_device_id": mic_id, "system_audio_device_id": 0}
    with open(tmp_path / "config.json", "w") as f:
        json.dump(config_dict, f, indent=2)

    assert (tmp_path / "config.json").exists()
    assert json.load(open(tmp_path / "config.json"))["microphone_device_id"] == 2


def test_setup_saves_blackhole_id(tmp_path, monkeypatch):
    """Verify setup saves BlackHole 2ch ID to config.json."""
    monkeypatch.chdir(tmp_path)

    devices = [
        {"name": "Microphone", "max_input_channels": 1},
        {"name": "Speaker", "max_input_channels": 0},
        {"name": "BlackHole 2ch", "max_input_channels": 2},
    ]

    blackhole_id = prompt_for_blackhole_id(devices, auto_detected_id=2)
    config_dict = {"microphone_device_id": 0, "system_audio_device_id": blackhole_id}
    with open(tmp_path / "config.json", "w") as f:
        json.dump(config_dict, f, indent=2)

    assert json.load(open(tmp_path / "config.json"))["system_audio_device_id"] == 2

