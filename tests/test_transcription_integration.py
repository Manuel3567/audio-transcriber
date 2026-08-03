import pytest
import whisper
import string
import numpy as np
import json
from pathlib import Path
from audio_transcriber.transcriber import transcribe_audio, record_audio, transcribe
from audio_transcriber.config import load_device_config
from audio_transcriber.setup import prompt_for_microphone_id, prompt_for_blackhole_id


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


@pytest.fixture(scope="session")
def whisper_model():
    """Load Whisper model once per test session."""
    return whisper.load_model("large")


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


def test_transcribe_fixture_audio(fixture_audio, whisper_model):
    """Transcribe all fixture audio files and verify word order."""
    audio_path, expected_words = fixture_audio
    raw_transcript = transcribe_audio(audio_path, model=whisper_model).lower()
    transcript = raw_transcript.translate(str.maketrans('', '', string.punctuation))

    pos = 0
    for word in expected_words:
        pos = transcript.find(word, pos)
        assert pos != -1, f"'{word}' not found in order in '{transcript}'"


@pytest.mark.live_audio
def test_record_and_transcribe_live_audio():
    """Record live audio from microphone+system, transcribe, and verify against user input."""
    config = load_device_config()
    mic_id = config.get("microphone_device_id")
    system_id = config.get("system_audio_device_id")

    if mic_id is None or system_id is None:
        pytest.skip("Microphone not configured")

    expected_text = input("\n📝 Type the text you'll speak: ").lower()
    expected_words = expected_text.split()

    if not expected_words:
        pytest.skip("No text provided")

    audio = record_audio(mic_id, system_id)

    if audio is None:
        pytest.skip("No audio recorded")

    transcript = transcribe_audio(audio).lower()

    pos = 0
    for word in expected_words:
        pos = transcript.find(word, pos)
        assert pos != -1, f"'{word}' not found in '{transcript}'"
        pos += len(word)


def test_transcribe_saves_file(tmp_path, monkeypatch, whisper_model):
    """Verify transcribe() saves transcript to file with correct content."""
    transcript_dir = tmp_path / "transcripts"
    transcript_dir.mkdir()
    monkeypatch.setattr(
        "audio_transcriber.transcriber.TRANSCRIPT_FILE",
        str(transcript_dir / "transcript.txt")
    )
    monkeypatch.chdir(transcript_dir)

    audio = np.zeros(16000, dtype=np.float32)
    monkeypatch.setattr("audio_transcriber.transcriber.record_audio", lambda *args: audio)

    transcribe(mic_id=0, system_id=1, summarize=False)

    assert (transcript_dir / "transcript_1.txt").exists()


def test_transcribe_counter_logic(tmp_path, monkeypatch, whisper_model):
    """Verify transcribe() uses correct counter for new files."""
    transcript_dir = tmp_path / "transcripts"
    transcript_dir.mkdir()
    monkeypatch.setattr(
        "audio_transcriber.transcriber.TRANSCRIPT_FILE",
        str(transcript_dir / "transcript.txt")
    )
    monkeypatch.chdir(transcript_dir)

    (transcript_dir / "transcript_1.txt").write_text("existing")
    (transcript_dir / "transcript_2.txt").write_text("existing")

    audio = np.zeros(16000, dtype=np.float32)
    monkeypatch.setattr("audio_transcriber.transcriber.record_audio", lambda *args: audio)

    transcribe(mic_id=0, system_id=1, summarize=False)

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

